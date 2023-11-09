import pathlib
from datetime import datetime

import aiofiles
from aiohttp import ClientSession
from urllib3.exceptions import ResponseError

from encrypt_storages.types import File
from ..encryptor.encryptor import FernetEncryptor
from ..slicer.encrypt import AsyncEncryptSlicer
from ..storages.abstract import AbstractStorage


class YandexDiskStorage(AbstractStorage):
    encryptor_class = FernetEncryptor

    def __init__(self, token, encryption_key: str, file_chunk_size: int = 1024):
        self.token = token
        self._encryptor = self.encryptor_class(encryption_key)
        self.base_url = "https://cloud-api.yandex.net"
        self.headers = {
            "Authorization": f"OAuth {self.token}",
        }
        self._chunk_size = file_chunk_size

    async def upload_and_encrypt_file(
        self, local_file_path: str | pathlib.Path, encrypted_file_path: str
    ):
        """Читаем файл и шифруем его"""

        async with ClientSession() as session:
            upload_url = await self._get_upload_url(encrypted_file_path, session)
            async with aiofiles.open(local_file_path, "rb") as file:
                slicer = AsyncEncryptSlicer(
                    file, self._encryptor, chunk_size=self._chunk_size
                )
                # Загружаем зашифрованный файл на Яндекс.Диск
                upload_response = await session.put(
                    upload_url, data=slicer.encrypt_with_slicing(), headers=self.headers
                )

            if upload_response.status != 201:
                raise ResponseError(
                    f"Failed to upload the file. Status: {upload_response.status}"
                )

    async def download_and_decrypt_file(
        self, encrypted_file_path: str, local_file_path: str | pathlib.Path
    ):
        """Скачиваем зашифрованный файл с яндекс диска"""

        async with ClientSession() as session:
            download_url = await self._get_download_url(encrypted_file_path, session)

            # Записываем дешифрованные данные в локальный файл
            async with aiofiles.open(local_file_path, "wb") as file:
                resp = await session.get(download_url)
                async for chunk in resp.content.iter_chunked(self._chunk_size):
                    # Дешифруем chunk
                    await file.write(self._encryptor.decrypt(chunk))

    async def list_files(self, remote_path: str) -> list[File]:
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

    async def _get_upload_url(self, remote_path: str, session: ClientSession):
        response = await session.get(
            f"{self.base_url}/v1/disk/resources/upload",
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
        if "href" not in upload_info:
            raise ResponseError("Failed to get the upload URL.")
        return upload_info["href"]

    async def _get_download_url(self, remote_path: str, session: ClientSession):
        response = await session.get(
            f"{self.base_url}/v1/disk/resources/download",
            params={"path": remote_path},
            headers=self.headers,
        )

        if response.status != 200:
            raise ResponseError(
                f"Failed to download the file. Status: {response.status}"
            )
        download_info = await response.json()
        if "href" not in download_info:
            raise ResponseError("Failed to get the download URL.")

        return download_info["href"]
