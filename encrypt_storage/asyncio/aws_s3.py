import asyncio
import pathlib
from concurrent.futures import ThreadPoolExecutor

from ..storages import AwsS3Storage as SyncAwsS3Storage
from ..types import File

executor = ThreadPoolExecutor()


def aio(func):
    async def aio_wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))

    return aio_wrapper


class AwsS3Storage(SyncAwsS3Storage):
    async def upload_and_encrypt_file(
        self, local_file_path: str | pathlib.Path, encrypted_file_path: str
    ):
        await aio(self._s3.upload_file)(
            local_file_path,
            self._bucket_name,
            encrypted_file_path,
            ExtraArgs=self._extra_args,
        )

    async def download_and_decrypt_file(
        self, encrypted_file_path: str, local_file_path: str | pathlib.Path
    ):
        await aio(self._s3.download_file)(
            self._bucket_name,
            encrypted_file_path,
            local_file_path,
            ExtraArgs=self._extra_args,
        )

    async def list_files(self, path: str = "") -> list[File]:
        # Получаем список объектов в указанной папке
        response = await aio(self._s3.list_objects_v2)(
            Bucket=self._bucket_name, Prefix=path
        )
        return self._format_list_files_response(response, path)
