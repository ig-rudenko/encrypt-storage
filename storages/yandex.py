from datetime import datetime

import requests
from cryptography.fernet import Fernet
from urllib3.exceptions import ResponseError

from .slicer.encrypt import EncryptSlicer
from .types import File


class YandexDiskClient:
    def __init__(self, token, encryption_key: str, file_chunk_size: int = 1024):
        self.token = token
        self.__encryption_key = encryption_key
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {
            "Authorization": f"OAuth {self.token}",
        }
        self._chunk_size: int = file_chunk_size

    def upload_and_encrypt_file(self, local_path, remote_path):
        """Читаем файл и шифруем его"""

        upload_url = self._get_upload_url(remote_path)

        cipher_suite = Fernet(self.__encryption_key)

        with open(local_path, "rb") as file:
            slicer = EncryptSlicer(file, cipher_suite, chunk_size=self._chunk_size)
            upload_response = requests.put(
                upload_url, data=slicer.encrypt_with_slicing(), headers=self.headers
            )

        if upload_response.status_code != 201:
            raise ResponseError(
                f"Failed to upload the file. Status: {upload_response.status_code}"
            )

    def decrypt_file(self, remote_path, local_path):
        """Скачиваем зашифрованный файл с яндекс диска"""
        response = requests.get(
            f"{self.base_url}/resources/download",
            params={"path": remote_path},
            headers=self.headers,
        )
        response.raise_for_status()

        cipher_suite = Fernet(self.__encryption_key)
        with requests.get(response.json()["href"]) as r:
            r.raise_for_status()

            # Записываем дешифрованные данные в локальный файл
            with open(local_path, 'wb') as f:
                for encrypted_chunk in r.iter_content(chunk_size=self._chunk_size):
                    # Дешифруем файл
                    decrypted_chunk = cipher_suite.decrypt(encrypted_chunk)
                    f.write(decrypted_chunk)

    def list_files(self, remote_path):
        # Получаем список файлов в указанной директории
        response = requests.get(
            f"{self.base_url}/resources",
            params={"path": remote_path},
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

    def _get_upload_url(self, remote_path):
        response = requests.get(
            f"{self.base_url}/resources/upload",
            params={"path": remote_path},
            headers=self.headers,
        )

        if response.status_code == 409:
            raise ResponseError("File already exists")
        if response.status_code != 200:
            raise ResponseError(
                f"Failed to get the upload URL. Status: {response.status_code}"
            )

        upload_info = response.json()
        if "href" not in upload_info:
            raise ResponseError(f"Failed to get the upload URL. No href key")

        return upload_info["href"]
