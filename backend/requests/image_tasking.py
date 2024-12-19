import boto3
from django.conf import settings


class ImageTasking:
    def __init__(self, bucket_name=None):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        )
        self.bucket_name = bucket_name or settings.AWS_STORAGE_BUCKET_NAME

    def upload_to_s3(self, file_name, file_content):
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=file_name,
            Body=file_content,
            ContentType="image/jpeg",
        )

    def download_from_s3(self, file_name):
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_name)
        return response['Body'].read()
