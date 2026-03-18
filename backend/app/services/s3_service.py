import io

from minio import Minio

from app.config.settings import MINIO_CFG


def up_s3(data: bytes, name: str) -> str:
    client = Minio(
        MINIO_CFG["endpoint"],
        access_key=MINIO_CFG["access_key"],
        secret_key=MINIO_CFG["secret_key"],
        secure=MINIO_CFG["secure"],
    )
    bucket = MINIO_CFG["bucket"]
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    client.put_object(bucket, name, io.BytesIO(data), len(data))
    return f"S3/MinIO: '{name}' subido al bucket '{bucket}'"
