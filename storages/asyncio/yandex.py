from datetime import datetime
from urllib.parse import urlparse

from aiohttp import ClientSession
from cryptography.fernet import Fernet
from urllib3.exceptions import ResponseError

from ..types import File


class YandexDiskClient:
    def __init__(self, token, encryption_key: str):
        self.token = token
        self.__encryption_key = encryption_key
        self.base_url = "https://cloud-api.yandex.net"
        self.headers = {
            "Authorization": f"OAuth {self.token}",
        }

    async def upload_and_encrypt_file(self, local_path, remote_path):
        """Читаем файл и шифруем его"""
        with open(local_path, "rb") as file:
            file_data = file.read()
            cipher_suite = Fernet(self.__encryption_key)
            encrypted_data = cipher_suite.encrypt(file_data)

        # Загружаем зашифрованный файл на Яндекс.Диск
        async with ClientSession(self.base_url) as session:
            response = await session.get(
                "/v1/disk/resources/upload",
                params={"path": remote_path},
                headers=self.headers,
            )

            if response.status == 409:
                raise ResponseError("File already exists")

            if response.status != 200:
                raise ResponseError(
                    f"Failed to get the upload URL. Status: {response.status}"
                )

            upload_info = await response.json()
            if "href" in upload_info:
                upload_response = await session.put(
                    upload_info["href"], data=encrypted_data, headers=self.headers
                )
                if upload_response.status != 201:
                    raise ResponseError(
                        f"Failed to upload the file. Status: {response.status}"
                    )
            else:
                raise ResponseError("Failed to get the upload URL.")

    async def decrypt_file(self, remote_path, local_path):
        """Скачиваем зашифрованный файл с яндекс диска"""
        async with ClientSession(self.base_url) as session:
            response = await session.get(
                "/v1/disk/resources/download",
                params={"path": remote_path},
                headers=self.headers,
            )

        if response.status != 200:
            raise ResponseError(
                f"Failed to download the file. Status: {response.status}"
            )

        json_data = await response.json()

        parsed_uri = urlparse(json_data["href"])
        async with ClientSession(
            f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        ) as session:
            remote_file = await session.get(f"{parsed_uri.path}?{parsed_uri.query}")

        # Дешифруем файл
        cipher_suite = Fernet(self.__encryption_key)
        encrypted_data = await remote_file.text()
        decrypted_data = cipher_suite.decrypt(encrypted_data)

        # Записываем дешифрованные данные в локальный файл
        with open(local_path, "wb") as file:
            file.write(decrypted_data)

    async def list_files(self, remote_path):
        # Получаем список файлов в указанной директории
        async with ClientSession(self.base_url) as session:
            response = await session.get(
                "/v1/disk/resources", params={"path": remote_path}, headers=self.headers
            )

            if response.status != 200:
                raise ResponseError(f"Failed to list files. Status: {response.status}")

            files_data = await response.json()

            return [
                File(
                    name=item["name"],
                    path=item["path"][6:],
                    size=item.get("size", 0),
                    modified=datetime.fromisoformat(item["modified"]),
                    is_dir=item["type"] == "dir",
                )
                for item in files_data["_embedded"]["items"]
            ]
