"""Cloudflare R2 (Object Storage) service wrapper."""

from pathlib import Path
from typing import BinaryIO

import aioboto3
from botocore.exceptions import ClientError

from app.ensenia.core.config import settings


class R2Service:
    """Service wrapper for Cloudflare R2 operations."""

    def __init__(self) -> None:
        """Initialize R2 service with credentials from settings."""
        self.bucket_name = settings.cloudflare_r2_bucket
        self.endpoint_url = settings.cloudflare_r2_endpoint
        self.access_key = settings.cloudflare_r2_access_key
        self.secret_key = settings.cloudflare_r2_secret_key
        self.session = aioboto3.Session()

    async def _get_client(self):
        """Get S3 client configured for R2."""
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto",
        )

    async def upload_file(
        self, file_path: str | Path, key: str, content_type: str | None = None
    ) -> str:
        """Upload a file to R2.

        Args:
            file_path: Path to local file
            key: Object key (path) in R2 bucket
            content_type: Optional MIME type

        Returns:
            The object key

        Raises:
            ClientError: If upload fails

        """
        async with await self._get_client() as s3:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            await s3.upload_file(
                str(file_path), self.bucket_name, key, ExtraArgs=extra_args or None
            )

            return key

    async def upload_fileobj(
        self, file_obj: BinaryIO, key: str, content_type: str | None = None
    ) -> str:
        """Upload a file object to R2.

        Args:
            file_obj: File-like object
            key: Object key in R2 bucket
            content_type: Optional MIME type

        Returns:
            The object key

        """
        async with await self._get_client() as s3:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            await s3.upload_fileobj(
                file_obj, self.bucket_name, key, ExtraArgs=extra_args or None
            )

            return key

    async def download_file(self, key: str, local_path: str | Path) -> Path:
        """Download a file from R2.

        Args:
            key: Object key in R2 bucket
            local_path: Path to save downloaded file

        Returns:
            Path to downloaded file

        Raises:
            ClientError: If download fails

        """
        async with await self._get_client() as s3:
            await s3.download_file(self.bucket_name, key, str(local_path))

            return Path(local_path)

    async def get_object(self, key: str) -> bytes:
        """Get object content as bytes.

        Args:
            key: Object key in R2 bucket

        Returns:
            Object content as bytes

        Raises:
            ClientError: If object not found

        """
        async with await self._get_client() as s3:
            response = await s3.get_object(Bucket=self.bucket_name, Key=key)
            return await response["Body"].read()

    async def delete_object(self, key: str) -> None:
        """Delete an object from R2.

        Args:
            key: Object key to delete

        Raises:
            ClientError: If deletion fails

        """
        async with await self._get_client() as s3:
            await s3.delete_object(Bucket=self.bucket_name, Key=key)

    async def list_objects(self, prefix: str = "", max_keys: int = 1000) -> list[dict]:
        """List objects in the bucket.

        Args:
            prefix: Filter objects by prefix
            max_keys: Maximum number of objects to return

        Returns:
            List of object metadata dictionaries

        """
        async with await self._get_client() as s3:
            response = await s3.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, MaxKeys=max_keys
            )

            return response.get("Contents", [])

    async def object_exists(self, key: str) -> bool:
        """Check if an object exists in R2.

        Args:
            key: Object key to check

        Returns:
            True if object exists, False otherwise

        """
        async with await self._get_client() as s3:
            try:
                await s3.head_object(Bucket=self.bucket_name, Key=key)
                return True
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    return False
                raise

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for temporary access to an object.

        Args:
            key: Object key
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL string

        """
        async with await self._get_client() as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
