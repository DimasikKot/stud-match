import time
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

router: APIRouter = APIRouter(prefix="/healths", tags=["Healths"])


class HealthResponse(BaseModel):
    success: bool
    detail: str
    metrics: dict | None = None


@router.get("/backend", response_model=HealthResponse)
async def get_backend_health():
    return HealthResponse(
        success=True, detail="Backend is healthy", metrics={"status": "running"}
    )


@router.get("/postgres", response_model=HealthResponse)
def get_postgres_health(db: Session = Depends(get_db)):
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

        latency_ms = (time.perf_counter() - start_time) * 1000

        return HealthResponse(
            success=True,
            detail="PostgreSQL is healthy",
            metrics={
                "latency_ms": round(latency_ms, 2),
                "version": version,
                "db_size_mb": (
                    round(db_size_bytes / (1024 * 1024), 2) if db_size_bytes else 0
                ),
                "ssl": ssl_info,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"PostgreSQL connection failed: {str(e)}"
        )


@router.get("/redis", response_model=HealthResponse)
async def get_redis_health():
    import redis.asyncio as aioredis

    start_time = time.perf_counter()

    redis_client = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_timeout=5.0,
    )

    try:
        await redis_client.ping()

        info = await redis_client.info(section="memory")
        clients_info = await redis_client.info(section="clients")

        latency_ms = (time.perf_counter() - start_time) * 1000

        return HealthResponse(
            success=True,
            detail="Redis is healthy",
            metrics={
                "latency_ms": round(latency_ms, 2),
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "N/A"),
                "connected_clients": clients_info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Redis connection failed: {str(e)}"
        )
    finally:
        await redis_client.aclose()
