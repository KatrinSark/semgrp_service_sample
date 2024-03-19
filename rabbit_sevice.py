import os
import logging
from aio_pika import connect_robust, ExchangeType, IncomingMessage, Message
import json

from storage_service import S3Downloader as S3
from semgrep_service import SemgrepService as smgrp


class AsyncRabbitMQConnector:
    """
    Сервис для работы с RabbitMQ
    """
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None
        self.semgrep_logs_queue = None
        self.minio_queue_name = os.getenv("MINIO_QUEUE")
        self.semgrep_queue_name = os.getenv("SEMGREP_QUEUE")
        self.rabbit_mq_user = os.getenv("RABBITMQ_USER")
        self.rabbit_mq_password = os.getenv("RABBITMQ_PASSWORD")
        self.rabbit_mq_host = os.getenv("RABBITMQ_HOST")
        self.rabbit_mq_port = os.getenv("RABBITMQ_PORT")
        self.save_dir = os.getenv("SAVE_DIR", None)

    async def connect(self):
        self.connection = await connect_robust(
            f"amqp://{self.rabbit_mq_user}:{self.rabbit_mq_password}@{self.rabbit_mq_host}:{self.rabbit_mq_port}/",
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        await self.channel.declare_exchange(self.semgrep_queue_name, ExchangeType.FANOUT, durable=True)
        self.semgrep_logs_queue = await self.channel.declare_queue(self.semgrep_queue_name, durable=True)
        await self.semgrep_logs_queue.bind(self.semgrep_queue_name)

        await self.channel.declare_exchange(self.minio_queue_name, ExchangeType.FANOUT)
        self.queue = await self.channel.declare_queue(self.minio_queue_name, exclusive=False)
        await self.queue.bind(self.minio_queue_name)

    async def consume(self):
        await self.queue.consume(self.callback)

    async def callback(self, message: IncomingMessage):
        async with message.process():
            try:
                headers = message.headers
                minio_bucket = headers.get("minio-bucket")
                minio_event = headers.get("minio-event")

                if minio_event == "s3:ObjectCreated:Put" and minio_bucket == self.minio_queue_name:
                    body = json.loads(message.body)
                    object_key = body["Key"]
                    bucket_name = object_key.split("/")[0]
                    file_name = object_key.split("/")[-1]
                    local_file_path = await S3().download_file(bucket_name, file_name, self.save_dir)
                    await self.send_message(local_file_path, object_key)
                    os.remove(local_file_path)

            except Exception as e:
                logging.exception("Exception in QueueListener: %s", e)

    async def send_message(self, local_file_path, file_name):
        semgrep_result = await smgrp().run_semgrep_check(local_file_path)
        if semgrep_result:
            impact = semgrep_result.get("impact", "")
            data = semgrep_result.get("data", "")
            result = "success"
        else:
            impact = ""
            data = ""
            result = "error"
        message_properties = {
            "headers": {
                "result": result,
                "system": "minio_semgrp_checker",
                "source": file_name,
                "impact": impact
            }
        }
        if impact != "NO IMPACT":
            await self.channel.default_exchange.publish(
                Message(body=data.encode(), **message_properties, content_type='text/plain'),
                routing_key=self.semgrep_queue_name
            )

    async def close(self):
        if self.connection:
            await self.connection.close()

