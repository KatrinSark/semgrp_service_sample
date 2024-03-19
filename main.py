import asyncio
import logging
import os

from inotify_service import InotifyMonitoring
from rabbit_sevice import AsyncRabbitMQConnector


async def run_consumer():
    consumer = AsyncRabbitMQConnector()
    try:
        await consumer.connect()
        await consumer.consume()
        await asyncio.Event().wait()
    finally:
        await consumer.close()


async def run_inotify():
    connector = AsyncRabbitMQConnector()
    try:
        await connector.connect()
        while True:
            await InotifyMonitoring().detection(connector)
            await asyncio.sleep(5)
    finally:
        await connector.close()


async def main():
    logging.basicConfig(level=logging.INFO)
    minio_url = os.environ.get("MINIO_URL")
    notify_dir = os.environ.get("NOTIFY_DIR")
    if not minio_url and notify_dir:
        await asyncio.gather(run_inotify())
    elif not notify_dir and minio_url:
        await asyncio.gather(run_consumer())
    elif minio_url and notify_dir:
        await asyncio.gather(run_consumer(), run_inotify())


if __name__ == "__main__":
    asyncio.run(main())
