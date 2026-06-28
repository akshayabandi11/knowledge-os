import io
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError
from app.infrastructure.storage.base import IStorageProvider
from app.core.config import settings
from app.core.exceptions import StorageUploadFailed, StorageDeletionFailed


class S3StorageProvider(IStorageProvider):
    """
    Storage provider interfacing with AWS S3 or Cloudflare R2.
    """

    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable is not configured.")

        session_kwargs = {}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            session_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            session_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

        client_kwargs = {"region_name": settings.AWS_REGION}
        if settings.S3_ENDPOINT_URL:
            # Enforce custom endpoints for Cloudflare R2 target buckets
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        self.s3 = boto3.client("s3", **client_kwargs)

    def upload_file(self, file_data: BinaryIO, storage_key: str) -> str:
        try:
            file_data.seek(0)
            self.s3.upload_fileobj(file_data, self.bucket_name, storage_key)
            # Return logical S3 URI string reference
            return f"s3://{self.bucket_name}/{storage_key}"
        except ClientError as e:
            raise StorageUploadFailed(f"Cloud storage upload failed: {str(e)}")

    def get_file(self, storage_key: str) -> BinaryIO:
        try:
            file_buffer = io.BytesIO()
            self.s3.download_fileobj(self.bucket_name, storage_key, file_buffer)
            file_buffer.seek(0)
            return file_buffer
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                raise FileNotFoundError(
                    f"File not found in cloud storage: {storage_key}"
                )
            raise StorageDeletionFailed(f"Cloud storage retrieval failed: {str(e)}")

    def delete_file(self, storage_key: str) -> None:
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=storage_key)
        except ClientError as e:
            raise StorageDeletionFailed(f"Cloud storage deletion failed: {str(e)}")
