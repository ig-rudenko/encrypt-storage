from abc import ABC, abstractmethod


class AbstractEncryptor(ABC):

    @abstractmethod
    def encrypt(self, data: bytes) -> bytes:
        pass

    @abstractmethod
    def decrypt(self, data: bytes) -> bytes:
        pass
