### Позволяет использовать Яндекс диск как хранилище с шифрованием

Синхронное использование
```python
from storages import YandexDiskClient


# Замените 'YOUR_ACCESS_TOKEN' на ваш токен Яндекс.Диска
# Замените 'YOUR_ENCRYPTION_KEY' на ваш ключ шифрования
yandex_disk = YandexDiskClient(
    "YOUR_ACCESS_TOKEN",
    "YOUR_ENCRYPTION_KEY",
)

# Пример загрузки и шифрования файла
local_file = "docker-compose.yaml"
remote_path = "docker-compose.yaml"
yandex_disk.upload_and_encrypt_file(local_file, remote_path)

# Пример дешифрования файла
decrypted_local_file = "docker-compose2.yaml"
yandex_disk.decrypt_file(remote_path, decrypted_local_file)

# Пример получения данных файлов
files = yandex_disk.list_files("/")
print(files)
```

Асинхронное использование

```python
import asyncio

from storages.asyncio import YandexDiskClient


async def main():
    # Замените 'YOUR_ACCESS_TOKEN' на ваш токен Яндекс.Диска
    # Замените 'YOUR_ENCRYPTION_KEY' на ваш ключ шифрования
    yandex_disk = YandexDiskClient(
        "YOUR_ACCESS_TOKEN",
        "YOUR_ENCRYPTION_KEY",
    )

    # Пример загрузки и шифрования файла
    local_file = "docker-compose.yaml"
    remote_path = "docker-compose.yaml"
    await yandex_disk.upload_and_encrypt_file(local_file, remote_path)

    # Пример дешифрования файла
    decrypted_local_file = "docker-compose2.yaml"
    await yandex_disk.decrypt_file(remote_path, decrypted_local_file)

    # Пример получения метаданных файлов
    files = await yandex_disk.list_files("/")
    print(files)


if __name__ == "__main__":
    asyncio.run(main())

```