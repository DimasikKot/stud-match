import json
import ssl
import threading

from kafka import KafkaConsumer, KafkaProducer

from app.core.config import settings

TASKS_TOPIC = "llm.tasks"
RESULTS_TOPIC = "llm.results"

# TLS-порты: 9093 — SSL-листенер, 9193 — внешний SASL_SSL (внутренний 19094 — SASL_PLAINTEXT)
TLS_PORTS = (9093, 9193)
SASL_PROTOCOLS = ("SASL_SSL", "SASL_PLAINTEXT")
SSL_PROTOCOLS = ("SSL", "SASL_SSL")


def security_protocol() -> str:
    return _security_protocol()


def _security_protocol() -> str:
    explicit = (settings.KAFKA_SECURITY_PROTOCOL or "").strip().upper()
    if explicit:
        return explicit
    if settings.KF_USERNAME or settings.KF_PASSWORD:
        return "SASL_SSL" if settings.KAFKA_PORT in TLS_PORTS else "SASL_PLAINTEXT"
    return "SSL" if settings.KAFKA_PORT in (9093, 9193) else "PLAINTEXT"


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
        if not settings.KF_USERNAME or not settings.KF_PASSWORD:
            raise ValueError("KF_USERNAME/KF_PASSWORD обязательны для SASL")
        kwargs.update(
            sasl_mechanism=(settings.KAFKA_SASL_MECHANISM or "PLAIN").upper(),
            sasl_plain_username=settings.KF_USERNAME,
            sasl_plain_password=settings.KF_PASSWORD,
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


def results_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        RESULTS_TOPIC,
        group_id=settings.KAFKA_RESULTS_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda raw: json.loads(raw.decode()),
        **connection_kwargs(),
    )
