import boto3
from botocore.config import Config
from django.conf import settings


_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        client_config = Config(signature_version="s3v4")
        _s3_client = boto3.client(
            "s3",
            region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
            endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            config=client_config,
        )
    return _s3_client


def build_file_url(field_file):
    if not field_file:
        return None

    if not settings.USE_S3:
        return field_file.url

    name = getattr(field_file, "name", None)
    if not name:
        return field_file.url

    expires = getattr(settings, "AWS_PRESIGNED_URL_EXPIRES", 3600)
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": name,
        },
        ExpiresIn=expires,
    )
