from typing import BinaryIO
from app.infrastructure.storage.base import IStorageProvider
from app.core.exceptions import StorageError


class StorageService:
    """
    Application service that coordinates file operations.
    Acts as a middleware layer decoupling storage use cases from specific S3 or Local disk providers.
    """

    def __init__(self, provider: IStorageProvider):
        self.provider = provider

    def upload(self, file_data: BinaryIO, storage_key: str) -> str:
        try:
            return self.provider.upload_file(file_data, storage_key)
        except Exception as e:
            if not isinstance(e, StorageError):
                raise StorageError(f"Unexpected upload failure: {str(e)}")
            raise e

    def download(self, storage_key: str) -> BinaryIO:
        try:
            return self.provider.get_file(storage_key)
        except Exception as e:
            if not isinstance(e, StorageError):
                raise StorageError(f"Unexpected retrieval failure: {str(e)}")
            raise e

    def delete(self, storage_key: str) -> None:
        try:
            self.provider.delete_file(storage_key)
        except Exception as e:
            if not isinstance(e, StorageError):
                raise StorageError(f"Unexpected deletion failure: {str(e)}")
            raise e
