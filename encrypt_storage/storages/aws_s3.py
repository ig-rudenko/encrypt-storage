import pathlib

from .abstract import AbstractStorage
from ..types import File


class AwsS3Storage(AbstractStorage):
    def __init__(
        self,
        bucket_name: str,
        encryption_key: str | bytes,
        algorithm: str = "AES256",
        *args,
        **kwargs,
    ):
        import boto3

        self._s3 = boto3.client("s3", *args, **kwargs)
        self._bucket_name: str = bucket_name

        if isinstance(encryption_key, str):
            encryption_key: bytes = bytes.fromhex(encryption_key)
        elif isinstance(encryption_key, bytes):
            encryption_key: bytes = encryption_key
        else:
            raise TypeError(f"Encryption key must be `str` or `bytes`")

        # Определяем параметры загрузки, включая шифрование
        self._extra_args = {
            "SSECustomerAlgorithm": algorithm,
            "SSECustomerKey": encryption_key,
        }

    def upload_and_encrypt_file(
        self, local_file_path: str | pathlib.Path, encrypted_file_path: str
    ):
        self._s3.upload_file(
            local_file_path,
            self._bucket_name,
            encrypted_file_path,
            ExtraArgs=self._extra_args,
        )

    def download_and_decrypt_file(
        self, encrypted_file_path: str, local_file_path: str | pathlib.Path
    ):
        self._s3.download_file(
            self._bucket_name,
            encrypted_file_path,
            local_file_path,
            ExtraArgs=self._extra_args,
        )

    def list_files(self, path: str = "") -> list[File]:
        # Получаем список объектов в указанной папке
        response = self._s3.list_objects_v2(Bucket=self._bucket_name, Prefix=path)
        return self._format_list_files_response(response, path)

    @staticmethod
    def _format_list_files_response(response: dict, path: str) -> list[File]:
        # Обрабатываем каждый объект и создаем объекты File
        files = []
        for obj in response.get("Contents", []):
            file_name = obj["Key"]
            file_size = obj["Size"]
            file_modified = obj["LastModified"]
            file_is_dir = False

            # Если объект заканчивается на '/', считаем его директорией
            if file_name.endswith("/"):
                file_is_dir = True

            file_path = file_name[len(path) :] if path else file_name

            # Создаем объект File
            file_obj = File(
                name=file_name,
                path=file_path,
                size=file_size,
                modified=file_modified,
                is_dir=file_is_dir,
            )
            files.append(file_obj)

        return files
