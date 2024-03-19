import logging

import boto3
import os


class S3Downloader:
    """
    Сервис для работы с облачным хранилищем
    """
    def __init__(self):
        self.minio_url = os.environ.get("MINIO_URL")
        self.minio_login = os.environ.get("MINIO_LOGIN", "temp")
        self.minio_password = os.environ.get("MINIO_PASSWORD")
        self.s3 = boto3.client('s3',
                               endpoint_url=self.minio_url,
                               aws_access_key_id=self.minio_login,
                               aws_secret_access_key=self.minio_password)

    async def download_file(self, bucket_name, file_name, save_dir):
        try:
            if save_dir is not None:
                save_path = os.path.join(save_dir, file_name)
                os.makedirs(save_dir, exist_ok=True)
            else:
                save_path = file_name
            with open(save_path, 'wb') as f:
                self.s3.download_fileobj(bucket_name, file_name, f)
            return save_path
        except Exception as e:
            logging.exception(f"Error downloading file from bucket: {e}")
            return None