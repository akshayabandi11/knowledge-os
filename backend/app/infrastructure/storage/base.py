import abc
from typing import BinaryIO


class IStorageProvider(abc.ABC):
    """
    Interface for file storage providers.
    Allows swapping between local disk storage and cloud storage (S3/Cloudflare R2).
    """

    @abc.abstractmethod
    def upload_file(self, file_data: BinaryIO, storage_key: str) -> str:
        """
        Uploads file stream to the storage provider.
        Returns the absolute path or identifier of the stored file.
        """
        pass

    @abc.abstractmethod
    def get_file(self, storage_key: str) -> BinaryIO:
        """
        Retrieves file stream from the storage provider.
        """
        pass

    @abc.abstractmethod
    def delete_file(self, storage_key: str) -> None:
        """
        Deletes the file associated with the storage key.
        """
        pass
