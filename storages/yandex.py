from datetime import datetime

import requests
from cryptography.fernet import Fernet
from urllib3.exceptions import ResponseError

from storages.types import File


class YandexDiskClient:
    def __init__(self, token, encryption_key: str):
        self.token = token
        self.__encryption_key = encryption_key
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {
            "Authorization": f"OAuth {self.token}",
        }

    def upload_and_encrypt_file(self, local_path, remote_path):
        """Читаем файл и шифруем его"""
        with open(local_path, "rb") as file:
            file_data = file.read()
            cipher_suite = Fernet(self.__encryption_key)
            encrypted_data = cipher_suite.encrypt(file_data)

        # Загружаем зашифрованный файл на Яндекс.Диск
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

        upload_response = requests.put(
            upload_info["href"], data=encrypted_data, headers=self.headers
        )

        if upload_response.status_code != 201:
            raise ResponseError(
                f"Failed to upload the file. Status: {response.status_code}"
            )

    def decrypt_file(self, remote_path, local_path):
        """Скачиваем зашифрованный файл с яндекс диска"""
        response = requests.get(
            f"{self.base_url}/resources/download",
            params={"path": remote_path},
            headers=self.headers,
        )

        if response.status_code != 200:
            raise ResponseError(
                f"Failed to download the file. Status: {response.status_code}"
            )
        encrypted_data = requests.get(response.json()["href"]).content

        # Дешифруем файл
        cipher_suite = Fernet(self.__encryption_key)
        decrypted_data = cipher_suite.decrypt(encrypted_data)

        # Записываем дешифрованные данные в локальный файл
        with open(local_path, "wb") as file:
            file.write(decrypted_data)

    def list_files(self, remote_path):
        # Получаем список файлов в указанной директории
        response = requests.get(
            f"{self.base_url}/resources",
            params={"path": remote_path},
            headers=self.headers,
        )

        if response.status_code != 200:
            raise ResponseError(
                f"Failed to list files.  Status: {response.status_code}"
            )

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
