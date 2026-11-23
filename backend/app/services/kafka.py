import json
import ssl
import threading

from kafka import KafkaConsumer, KafkaProducer

from app.core.config import settings


def security_protocol() -> str:
    explicit = (settings.KAFKA_SECURITY_PROTOCOL or "").strip().upper()
    if explicit:
        return explicit
    if settings.KAFKA_USERNAME or settings.KAFKA_PASSWORD:
        # TLS-порты: 8092 - SASL_SSL снаружи (внутренний 8292 - SASL_PLAINTEXT, 8290 - PLAINTEXT localhost)
        return "SASL_SSL" if settings.KAFKA_PORT in (8092,) else "SASL_PLAINTEXT"
    return "SSL" if settings.KAFKA_PORT in (8092,) else "PLAINTEXT"


def _ssl_context() -> ssl.SSLContext:
    if settings.KAFKA_SSL_CA_FILE:
        context = ssl.create_default_context(cafile=settings.KAFKA_SSL_CA_FILE)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = settings.KAFKA_SSL_CHECK_HOSTNAME
        return context

    # Самоподписанный сертификат без CA - поведение как раньше (только для локальной разработки)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def connection_kwargs(**extra) -> dict:
    """Общие kwargs для KafkaProducer/KafkaConsumer/KafkaAdminClient."""
    protocol = security_protocol()
    kwargs = {
        "bootstrap_servers": f"{settings.KAFKA_HOST}:{settings.KAFKA_PORT}",
        "api_version_auto_timeout_ms": 5000,
        "security_protocol": protocol,
    }
    if protocol in ("SSL", "SASL_SSL"):
        kwargs["ssl_context"] = _ssl_context()
    if protocol in ("SASL_SSL", "SASL_PLAINTEXT"):
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


def results_consumer(topic: str, group_id: str) -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda raw: json.loads(raw.decode()),  # type: ignore
        **connection_kwargs(),
    )
