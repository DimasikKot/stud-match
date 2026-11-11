import time
from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.db import ROLE_ADMIN, UserDB
from app.services.security_deps import get_async_redis, get_optional_user

import redis.asyncio as aioredis

import httpx
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

router: APIRouter = APIRouter(prefix="/healths", tags=["Healths"])


class HealthResponse(BaseModel):
    success: bool
    detail: str
    metrics: dict[str, Any] | None = None


async def _backend_health() -> HealthResponse:
    return HealthResponse(
        success=True,
        detail="Backend is healthy",
        metrics={
            "server": settings.VITE_BACKEND_URL,
            "cookie_settings": {
                "httpOnly": settings.COOKIE_HTTPONLY,
                "secure": settings.COOKIE_SECURE,
                "sameSite": settings.COOKIE_SAMESITE,
            },
        },
    )


def _postgres_health(db: Session) -> HealthResponse:
    start_time = time.perf_counter()

    try:
        # 1. Базовый пинг
        db.execute(text("SELECT 1"))

        # 2. Версия
        version_raw = db.execute(text("SELECT version()")).scalar()
        version = version_raw.split()[1] if version_raw else "Unknown"

        # 3. Размер БД
        db_size_bytes = db.execute(
            text("SELECT pg_database_size(:db_name)"), {"db_name": settings.POSTGRES_DB}
        ).scalar()

        # 4. Проверка SSL текущего соединения
        ssl_row = db.execute(text("""
                SELECT s.ssl, s.version, s.cipher
                FROM pg_stat_ssl s
                WHERE s.pid = pg_backend_pid()
                """)).first()

        ssl_enabled = bool(ssl_row and ssl_row.ssl)
        ssl_info = {
            "enabled": ssl_enabled,
            "version": ssl_row.version if ssl_row else None,
            "cipher": ssl_row.cipher if ssl_row else None,
        }

        rows = db.execute(text("""
            SELECT table_schema, table_name, column_name,
                data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name, ordinal_position
        """)).mappings().all()

        tables: dict[str, dict[str, str]] = {}
        for r in rows:
            key = (
                r["table_name"]
                if r["table_schema"] == "public"
                else f'{r["table_schema"]}.{r["table_name"]}'
            )
            col_type = r["data_type"]
            if r["character_maximum_length"]:
                col_type += f'({r["character_maximum_length"]})'
            tables.setdefault(key, {})[r["column_name"]] = col_type

        latency_ms = (time.perf_counter() - start_time) * 1000

        return HealthResponse(
            success=True,
            detail=f"PostgreSQL is healthy",
            metrics={
                "server": f"{settings.DB_HOST}:{settings.DB_PORT}",
                "auth": f"{settings.POSTGRES_USER}@{settings.POSTGRES_DB}",
                "ssl": ssl_info,
                "version": f"{version}",
                "latency_ms": round(latency_ms, 2),
                "db_size_mb": (
                    round(db_size_bytes / (1024 * 1024), 2) if db_size_bytes else 0
                ),
                "table_count": len(tables),
                "tables": tables,
            },
        )

    except Exception as e:
        return HealthResponse(
            success=False,
            detail="PostgreSQL is not healthy",
            metrics={
                "server": f"{settings.DB_HOST}:{settings.DB_PORT}",
                "auth": f"{settings.POSTGRES_USER} in {settings.POSTGRES_DB}",
                "error": str(e),
            },
        )


async def _redis_health(redis: aioredis.Redis) -> HealthResponse:
    use_tls = settings.REDIS_PORT == 6150

    start_time = time.perf_counter()

    try:
        await redis.ping()

        info = await redis.info(section="memory")
        clients_info = await redis.info(section="clients")

        latency_ms = (time.perf_counter() - start_time) * 1000

        return HealthResponse(
            success=True,
            detail="Redis is healthy",
            metrics={
                "server": f"{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                "ssl": {
                    "enabled": use_tls,
                },
                "latency_ms": round(latency_ms, 2),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "N/A"),
                "connected_clients": clients_info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            },
        )

    except Exception as e:
        return HealthResponse(
            success=False,
            detail="Redis is not healthy",
            metrics={
                "server": f"{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                "error": str(e),
            },
        )
    finally:
        await redis.aclose()


async def _rustfs_health() -> HealthResponse:
    """
    Проверка здоровья RustFS:
    1. HTTP-пинг /health (liveness/readiness, без аутентификации)
    2. Опционально — проверка доступа к S3 API через boto3 (head_bucket)
    """
    start_time = time.perf_counter()
    endpoint = settings.RUSTFS_URL

    metrics: dict[str, Any] = {
        "server": endpoint,
        "bucket": settings.RUSTFS_BUCKET,
        "ssl": {
            "enabled": settings.RUSTFS_URL[-4:] == "9050",
        },
    }

    try:
        # --- 1. Проверка нативного health-эндпоинта RustFS ---
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            resp = await client.get(f"{endpoint.rstrip('/')}/health")
            # /health возвращает 200, пока процесс жив[reference:1]
            metrics["health_endpoint"] = {
                "status_code": resp.status_code,
                "body": resp.json(),
            }
            if resp.status_code != 200:
                raise RuntimeError(f"RustFS /health returned {resp.status_code}")

        # --- 2. Опциональная проверка S3-доступа (если заданы ключи) ---
        if settings.RUSTFS_ACCESS_KEY and settings.RUSTFS_SECRET_KEY:
            s3 = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=settings.RUSTFS_ACCESS_KEY,
                aws_secret_access_key=settings.RUSTFS_SECRET_KEY,
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                    retries={"max_attempts": 2},
                ),
                region_name=settings.RUSTFS_REGION or "us-east-1",
                verify=False,  # отключаем проверку TLS для botocore
            )
            try:
                s3.head_bucket(Bucket=settings.RUSTFS_BUCKET)
                metrics["s3_bucket_access"] = "ok"
            except ClientError as e:
                metrics["s3_bucket_access"] = f"error: {e}"
                # Не считаем весь сервис нездоровым, если health-эндпоинт жив,
                # но сообщаем о проблеме с бакетом/правами
                metrics["s3_bucket_access_detail"] = str(e)

        latency_ms = (time.perf_counter() - start_time) * 1000
        metrics["latency_ms"] = round(latency_ms, 2)

        return HealthResponse(
            success=True,
            detail="RustFS is healthy",
            metrics=metrics,
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        metrics["latency_ms"] = round(latency_ms, 2)
        metrics["error"] = str(e)
        return HealthResponse(
            success=False,
            detail="RustFS is not healthy",
            metrics=metrics,
        )


def _visible(health: HealthResponse, user: UserDB | None) -> HealthResponse:
    """Статус доступен всем, метрики — только администратору."""
    if user is None or user.role != ROLE_ADMIN:
        health.metrics = None
    return health


@router.get("/backend", response_model=HealthResponse)
async def get_backend_health(user: UserDB | None = Depends(get_optional_user)):
    return _visible(await _backend_health(), user)


@router.get("/postgres", response_model=HealthResponse)
def get_postgres_health(
    db: Session = Depends(get_db),
    user: UserDB | None = Depends(get_optional_user),
):
    return _visible(_postgres_health(db), user)


@router.get("/redis", response_model=HealthResponse)
async def get_redis_health(
    redis: aioredis.Redis = Depends(get_async_redis),
    user: UserDB | None = Depends(get_optional_user),
):
    return _visible(await _redis_health(redis), user)


@router.get("/rustfs", response_model=HealthResponse)
async def get_rustfs_health(user: UserDB | None = Depends(get_optional_user)):
    return _visible(await _rustfs_health(), user)
