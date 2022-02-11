from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys

secret_id = ''
secret_key = ''
region = 'ap-guangzhou'

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
client = CosS3Client(config)

response = client.upload_file(
    Bucket='bugmind-',
    LocalFilePath="base.py",
    Key="base.py",
)

print(response['ETag'])
