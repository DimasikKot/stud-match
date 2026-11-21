import json
import ssl
import threading

from kafka import KafkaConsumer, KafkaProducer

from app.core.config import settings


# Воркеры Kafka: "tags" и "predict". Топики и группы настраиваются
# через KAFKA_<WORKER>_TASKS_TOPIC / KAFKA_<WORKER>_RESULTS_TOPIC /
# KAFKA_<WORKER>_RESULTS_GROUP_ID в .env.
def tasks_topic(worker: str = "tags") -> str:
    return getattr(settings, f"KAFKA_{worker.upper()}_TASKS_TOPIC")


def results_topic(worker: str = "tags") -> str:
    return getattr(settings, f"KAFKA_{worker.upper()}_RESULTS_TOPIC")


def results_group_id(worker: str = "tags") -> str:
    return getattr(settings, f"KAFKA_{worker.upper()}_RESULTS_GROUP_ID")


# TLS-порты: 8092 — SASL_SSL снаружи (внутренний 8292 — SASL_PLAINTEXT, 8290 — PLAINTEXT localhost)
TLS_PORTS = (8092,)
SASL_PROTOCOLS = ("SASL_SSL", "SASL_PLAINTEXT")
SSL_PROTOCOLS = ("SSL", "SASL_SSL")


def security_protocol() -> str:
    return _security_protocol()


def _security_protocol() -> str:
    explicit = (settings.KAFKA_SECURITY_PROTOCOL or "").strip().upper()
    if explicit:
        return explicit
    if settings.KAFKA_USERNAME or settings.KAFKA_PASSWORD:
        return "SASL_SSL" if settings.KAFKA_PORT in TLS_PORTS else "SASL_PLAINTEXT"
    return "SSL" if settings.KAFKA_PORT in (8092,) else "PLAINTEXT"


def _ssl_context() -> ssl.SSLContext:
    if settings.KAFKA_SSL_CA_FILE:
        context = ssl.create_default_context(cafile=settings.KAFKA_SSL_CA_FILE)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = settings.KAFKA_SSL_CHECK_HOSTNAME
        return context

    # Самоподписанный сертификат без CA — поведение как раньше (только для локальной разработки)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def connection_kwargs(**extra) -> dict:
    """Общие kwargs для KafkaProducer/KafkaConsumer/KafkaAdminClient."""
    protocol = _security_protocol()
    kwargs = {
        "bootstrap_servers": f"{settings.KAFKA_HOST}:{settings.KAFKA_PORT}",
        "api_version_auto_timeout_ms": 5000,
        "security_protocol": protocol,
    }
    if protocol in SSL_PROTOCOLS:
        kwargs["ssl_context"] = _ssl_context()
    if protocol in SASL_PROTOCOLS:
        if not settings.KAFKA_USERNAME or not settings.KAFKA_PASSWORD:
            raise ValueError("KF_USERNAME/KF_PASSWORD обязательны для SASL")
        kwargs.update(
            sasl_mechanism=(settings.KAFKA_SASL_MECHANISM or "PLAIN").upper(),
            sasl_plain_username=settings.KAFKA_USERNAME,
            sasl_plain_password=settings.KAFKA_PASSWORD,
        )
    kwargs.update(extra)
    return kwargs


_producer: KafkaProducer | None = None
_producer_lock = threading.Lock()


def get_producer() -> KafkaProducer:
    global _producer
    with _producer_lock:
        if _producer is None:
            _producer = KafkaProducer(
                value_serializer=lambda value: json.dumps(value).encode(),
                **connection_kwargs(),
            )
        return _producer


def produce(topic: str, payload: dict) -> None:
    get_producer().send(topic, value=payload).get(timeout=10)


def results_consumer(worker: str = "tags") -> KafkaConsumer:
    return KafkaConsumer(
        results_topic(worker),
        group_id=results_group_id(worker),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda raw: json.loads(raw.decode()),
        **connection_kwargs(),
    )
