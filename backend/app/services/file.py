import boto3
from botocore.client import Config

from app.core.config import settings


def create_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.RUSTFS_URL,
        aws_access_key_id=settings.RUSTFS_ACCESS_KEY,
        aws_secret_access_key=settings.RUSTFS_SECRET_KEY,
        region_name=settings.RUSTFS_REGION,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},  # Обязательно для RustFS
        ),
        verify=False,  # отключаем проверку TLS для botocore
    )


s3_client = create_s3_client()
