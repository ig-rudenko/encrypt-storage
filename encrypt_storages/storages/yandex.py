import pathlib
from datetime import datetime

import requests
from urllib3.exceptions import ResponseError

from .abstract import AbstractStorage
from ..encryptor.encryptor import FernetEncryptor
from ..slicer.encrypt import EncryptSlicer
from ..types import File


class YandexDiskStorage(AbstractStorage):
    encryptor_class = FernetEncryptor

    def __init__(self, token, encryption_key: str, file_chunk_size: int = 1024):
        self.token = token
        self._encryptor = self.encryptor_class(encryption_key)
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {
            "Authorization": f"OAuth {self.token}",
        }
        self._chunk_size: int = file_chunk_size

    def upload_and_encrypt_file(self, local_file_path: str | pathlib.Path, encrypted_file_path: str):
        """Читаем файл и шифруем его"""

        upload_url = self._get_upload_url(encrypted_file_path)

        with open(local_file_path, "rb") as file:
            slicer = EncryptSlicer(file, self._encryptor, chunk_size=self._chunk_size)
            upload_response = requests.put(
                upload_url, data=slicer.encrypt_with_slicing(), headers=self.headers
            )

        if upload_response.status_code != 201:
            raise ResponseError(
                f"Failed to upload the file. Status: {upload_response.status_code}"
            )

    def download_and_decrypt_file(self, encrypted_file_path: str, local_file_path: str | pathlib.Path):
        """Скачиваем зашифрованный файл с яндекс диска"""
        download_url = self._get_download_url(encrypted_file_path)

        with requests.get(download_url) as r:
            r.raise_for_status()

            # Записываем дешифрованные данные в локальный файл
            with open(local_file_path, "wb") as f:
                for encrypted_chunk in r.iter_content(chunk_size=self._chunk_size):
                    # Дешифруем файл
                    decrypted_chunk = self._encryptor.decrypt(encrypted_chunk)
                    f.write(decrypted_chunk)

    def list_files(self, path: str) -> list[File]:
        # Получаем список файлов в указанной директории
        response = requests.get(
            f"{self.base_url}/resources",
            params={"path": path},
            headers=self.headers,
        )
        response.raise_for_status()

        return [
            File(
                name=item["name"],
                path=item["path"][6:],
                size=item.get("size", 0),
                modified=datetime.fromisoformat(item["modified"]),
                is_dir=item["type"] == "dir",
            )
            for item in response.json()["_embedded"]["items"]
        ]

    def _get_upload_url(self, remote_path: str):
        response = requests.get(
            f"{self.base_url}/resources/upload",
            params={"path": remote_path},
            headers=self.headers,
        )

        if response.status_code == 409:
            raise ResponseError("File already exists")
        if response.status_code != 200:
            raise ResponseError(f"Failed to get the upload URL. Status: {response.status_code}")

        upload_info = response.json()
        if "href" not in upload_info:
            raise ResponseError(f"Failed to get the upload URL. No href key")

        return upload_info["href"]

    def _get_download_url(self, remote_path: str):
        response = requests.get(
            f"{self.base_url}/resources/download",
            params={"path": remote_path},
            headers=self.headers,
        )
        response.raise_for_status()

        download_info = response.json()
        if "href" not in download_info:
            raise ResponseError(f"Failed to get the upload URL. No href key")

        return download_info["href"]
