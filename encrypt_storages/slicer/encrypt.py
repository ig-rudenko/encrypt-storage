from typing import BinaryIO, Protocol


class EncryptProtocol(Protocol):
    def encrypt(self, data: bytes) -> bytes:
        pass


class EncryptSlicer:
    def __init__(
        self, file: BinaryIO, encryptor: EncryptProtocol, chunk_size: int = 1024
    ):
        self._file: BinaryIO = file
        self._encryptor: EncryptProtocol = encryptor
        self.chunk_size: int = chunk_size

    def encrypt_with_slicing(self):
        while True:
            data = self._file.read(self.chunk_size)
            if not data:
                break
            yield self._encryptor.encrypt(data)


class AsyncEncryptSlicer:
    def __init__(self, file, encryptor: EncryptProtocol, chunk_size: int = 1024):
        self._file = file
        self._encryptor: EncryptProtocol = encryptor
        self.chunk_size: int = chunk_size

    async def encrypt_with_slicing(self):
        while True:
            data = await self._file.read(self.chunk_size)
            if not data:
                break
            yield self._encryptor.encrypt(data)
