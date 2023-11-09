from cryptography.fernet import Fernet

from .abstract import AbstractEncryptor


class FernetEncryptor(AbstractEncryptor):
    def __init__(self, key: str | bytes):
        self._encryptor = Fernet(key)

    def encrypt(self, data: bytes) -> bytes:
        return self._encryptor.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        return self._encryptor.decrypt(data)
