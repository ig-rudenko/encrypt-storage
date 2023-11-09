import pathlib
from abc import ABC, abstractmethod

from ..types import File


class AbstractStorage(ABC):

    @abstractmethod
    def upload_and_encrypt_file(self, local_file_path: str | pathlib.Path, encrypted_file_path: str):
        pass

    @abstractmethod
    def download_and_decrypt_file(self, encrypted_file_path: str, local_file_path: str | pathlib.Path):
        pass

    @abstractmethod
    def list_files(self, path: str) -> list[File]:
        pass
