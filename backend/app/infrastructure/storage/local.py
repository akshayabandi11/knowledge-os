import os
import shutil
from typing import BinaryIO

from app.core.config import settings
from app.core.exceptions import StorageDeletionFailed, StorageUploadFailed
from app.infrastructure.storage.base import IStorageProvider


class LocalStorageProvider(IStorageProvider):
    """
    Storage provider that reads and writes files directly to the local disk.
    Used during development and staging environments.
    """

    def __init__(self, base_path: str = settings.LOCAL_STORAGE_PATH):
        self.base_path = base_path
        # Ensure upload base directory exists
        os.makedirs(self.base_path, exist_ok=True)

    def _get_absolute_path(self, storage_key: str) -> str:
        return os.path.abspath(os.path.join(self.base_path, storage_key))

    def upload_file(self, file_data: BinaryIO, storage_key: str) -> str:
        dest_path = self._get_absolute_path(storage_key)
        # Ensure any sub-folders in key exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        try:
            with open(dest_path, "wb") as buffer:
                # Seek to beginning to make sure we read entire stream
                file_data.seek(0)
                shutil.copyfileobj(file_data, buffer)
            return dest_path
        except Exception as e:
            raise StorageUploadFailed(f"Local storage upload failed: {str(e)}") from e

    def get_file(self, storage_key: str) -> BinaryIO:
        source_path = self._get_absolute_path(storage_key)
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"File not found in local storage: {storage_key}")
        return open(source_path, "rb")

    def delete_file(self, storage_key: str) -> None:
        file_path = self._get_absolute_path(storage_key)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                raise StorageDeletionFailed(
                    f"Local storage deletion failed: {str(e)}"
                ) from e
