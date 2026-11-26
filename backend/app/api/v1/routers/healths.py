import enum
import time
from typing import Any

import boto3
import httpx
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.database import get_db
from app.services import kafka as kafka_service
from app.services.get_redis import get_async_redis
from app.services.get_user import require_admin
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from kafka import KafkaAdminClient, KafkaConsumer, TopicPartition

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
            detail="PostgreSQL is healthy",
            metrics={
                "server": f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}",
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
                "server": f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}",
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
    2. Опционально - проверка доступа к S3 API через boto3 (head_bucket)
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
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
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


def _kafka_health() -> HealthResponse:

    start_time = time.perf_counter()
    bootstrap = f"{settings.KAFKA_HOST}:{settings.KAFKA_PORT}"
    protocol = kafka_service.security_protocol()

    metrics: dict[str, Any] = {
        "server": bootstrap,
        "security_protocol": protocol,
        "ssl": {
            "enabled": protocol in ("SSL", "SASL_SSL"),
        },
        "sasl": {
            "enabled": protocol in ("SASL_SSL", "SASL_PLAINTEXT"),
        },
    }

    client: KafkaAdminClient | None = None
    try:
        client = KafkaAdminClient(
            **kafka_service.connection_kwargs(
                api_version_auto_timeout_ms=15000,
                request_timeout_ms=15000,
            )
        )
        topics_raw = client.list_topics()

        topics = sorted(t for t in topics_raw if not t.startswith("_"))

        groups_raw = client.list_consumer_groups()
        group_ids = sorted(group for group, _ in groups_raw if group)
        group_descriptions = client.describe_consumer_groups(group_ids)

        consumers: list[dict[str, Any]] = []
        consumer_groups: list[dict[str, Any]] = []
        for description in group_descriptions:
            group_id = description.group
            members = []
            for member in description.members:
                member_info = {
                    "member_id": member.member_id,
                    "client_id": member.client_id,
                    "client_host": member.client_host,
                }
                consumers.append({"group": group_id, **member_info})
                members.append(member_info)
            consumer_groups.append(
                {
                    "group": group_id,
                    "state": str(description.state),
                    "protocol": description.protocol,
                    "protocol_type": description.protocol_type,
                    "members_count": len(members),
                    "members": members,
                }
            )

        latency_ms = (time.perf_counter() - start_time) * 1000

        metrics["latency_ms"] = round(latency_ms, 2)
        metrics["topic_count"] = len(topics)
        metrics["topics"] = topics
        metrics["consumer_count"] = len(consumers)
        metrics["consumers"] = consumers
        metrics["group_count"] = len(consumer_groups)
        metrics["consumer_groups"] = consumer_groups

        return HealthResponse(
            success=True,
            detail="Kafka is healthy",
            metrics=metrics,
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        metrics["latency_ms"] = round(latency_ms, 2)
        metrics["error"] = str(e)
        return HealthResponse(
            success=False,
            detail="Kafka is not healthy",
            metrics=metrics,
        )
    finally:
        if client is not None:
            client.close()


class KafkaTopic(str, enum.Enum):
    FEATURES_TASKS = "features.tasks"
    FEATURES_RESULTS = "features.results"
    DISTRIBUTION_TASKS = "distribution.tasks"
    DISTRIBUTION_RESULTS = "distribution.results"


class KafkaGroup(str, enum.Enum):
    FEATURES = "sm-backend-features"
    DISTRIBUTION = "sm-backend-distribution"
    W_FEATURES = "sm-worker-features"
    W_DISTRIBUTION = "sm-worker-distribution"


def _kafka_topic_messages(
    topic_name: KafkaTopic, group: KafkaGroup | None = None
) -> HealthResponse:
    """Подсчитывает количество сообщений в топике
    как разность end - beginning offset по всем партициям.
    Если передан group, дополнительно возвращает закоммиченные
    офсеты consumer group и lag (end - committed)."""
    consumer: KafkaConsumer | None = None
    admin: KafkaAdminClient | None = None
    try:
        consumer = KafkaConsumer(
            **kafka_service.connection_kwargs(
                api_version_auto_timeout_ms=15000,
                request_timeout_ms=15000,
            )
        )
        partition_ids = consumer.partitions_for_topic(topic_name.value)
        if not partition_ids:
            return HealthResponse(
                success=False,
                detail=f"Топик {topic_name.value} не найден",
                metrics={"topic": topic_name.value},
            )
        partitions = [TopicPartition(topic_name.value, p) for p in partition_ids]
        beginning = consumer.beginning_offsets(partitions)
        end = consumer.end_offsets(partitions)

        committed: dict[TopicPartition, int] = {}
        if group:
            admin = KafkaAdminClient(
                **kafka_service.connection_kwargs(
                    api_version_auto_timeout_ms=15000,
                    request_timeout_ms=15000,
                )
            )
            committed = {
                tp: offset.offset
                for tp, offset in admin.list_consumer_group_offsets(group).items()
            }

        partition_stats = {}
        total = 0
        total_lag = 0
        for tp in partitions:
            lag = end[tp] - beginning[tp]
            total += lag
            stats = {
                "beginning_offset": beginning[tp],
                "end_offset": end[tp],
                "messages": lag,
            }
            if group:
                committed_offset = committed.get(tp, -1)
                if committed_offset < 0:
                    committed_offset = beginning[tp]
                group_lag = end[tp] - committed_offset
                total_lag += group_lag
                stats["committed_offset"] = committed.get(tp, -1)
                stats["lag"] = group_lag
            partition_stats[str(tp.partition)] = stats

        metrics: dict[str, Any] = {
            "topic": topic_name.value,
            "message_count": total,
            "partitions": partition_stats,
        }
        if group:
            metrics["consumer_group"] = group
            metrics["group_lag"] = total_lag
            detail = (
                f"В топике {topic_name.value}: {total} сообщений, "
                f"необработанных для группы {group}: {total_lag}"
            )
        else:
            detail = f"В топике {topic_name.value}: {total} сообщений"

        return HealthResponse(
            success=True,
            detail=detail,
            metrics=metrics,
        )

    except Exception as e:
        return HealthResponse(
            success=False,
            detail="Не удалось получить статистику топика",
            metrics={"topic": topic_name.value, "error": str(e)},
        )
    finally:
        if consumer is not None:
            consumer.close()
        if admin is not None:
            admin.close()


@router.get("/backend", response_model=HealthResponse)
async def get_backend_health():
    return await _backend_health()


@router.get(
    "/postgres", response_model=HealthResponse, dependencies=[Depends(require_admin)]
)
def get_postgres_health(db: Session = Depends(get_db)):
    return _postgres_health(db)


@router.get(
    "/redis", response_model=HealthResponse, dependencies=[Depends(require_admin)]
)
async def get_redis_health(redis: aioredis.Redis = Depends(get_async_redis)):
    return await _redis_health(redis)


@router.get(
    "/rustfs", response_model=HealthResponse, dependencies=[Depends(require_admin)]
)
async def get_rustfs_health():
    return await _rustfs_health()


@router.get(
    "/kafka", response_model=HealthResponse, dependencies=[Depends(require_admin)]
)
def get_kafka_health():
    return _kafka_health()


@router.get(
    "/kafka/topics/{topic_name}",
    response_model=HealthResponse,
    dependencies=[Depends(require_admin)],
)
def get_kafka_topic_messages(topic_name: KafkaTopic, group: KafkaGroup | None = None):
    return _kafka_topic_messages(topic_name, group)
