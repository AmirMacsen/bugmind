from django.conf import settings
from qcloud_cos import CosConfig, CosServiceError
from qcloud_cos import CosS3Client

secret_id = settings.TENCENT_COS_SECRET_ID
secret_key = settings.TENCENT_COS_SECRET_KEY


def create_bucket(bucket, region="ap-guangzhou"):
    """
    创建桶
    :param bucket: 桶名称
    :param region: 区域
    :return:
    """
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    client.create_bucket(
        Bucket=bucket,
        ACL='public-read',
    )

    cors_config = {
        'CORSRule': [
            {
                'AllowedOrigin': '*',
                'AllowedMethod': ['GET', 'PUT', 'HEAD', 'POST', 'DELETE'],
                'AllowedHeader': "*",
                'ExposeHeader': "*",
                'MaxAgeSeconds': 500
            }
        ]
    }
    client.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration=cors_config
    )


def upload_file_from_buffer(file_obj, key, bucket, region="ap-guangzhou"):
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)
    response = client.upload_file_from_buffer(
        Bucket=bucket,
        Key=key,
        Body=file_obj
    )
    return "https://{}.cos.{}.myqcloud.com/{}".format(
        bucket, region, key
    )


def delete_file(key, bucket, region="ap-guangzhou"):
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    client.delete_object(
        Bucket=bucket,
        Key=key
    )


def delete_file_list(key_list, bucket, region="ap-guangzhou"):
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    client.delete_objects(
        Bucket=bucket,
        Delete=key_list
    )


def credential(bucket, region):
    """ 获取cos上传临时凭证 """

    from sts.sts import Sts

    config = {
        # 临时密钥有效时长，单位是秒（30分钟=1800秒）
        'duration_seconds': 5,
        # 固定密钥 id
        'secret_id': settings.TENCENT_COS_SECRET_ID,
        # 固定密钥 key
        'secret_key': settings.TENCENT_COS_SECRET_KEY,
        # 换成你的 bucket
        'bucket': bucket,
        # 换成 bucket 所在地区
        'region': region,
        # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
        # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
        'allow_prefix': '*',
        # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
        'allow_actions': [
            # "name/cos:PutObject",
            # 'name/cos:PostObject',
            # 'name/cos:DeleteObject',
            # "name/cos:UploadPart",
            # "name/cos:UploadPartCopy",
            # "name/cos:CompleteMultipartUpload",
            # "name/cos:AbortMultipartUpload",
            "*",
        ],

    }

    sts = Sts(config)
    result_dict = sts.get_credential()
    return result_dict


def check_file(key, bucket, region="ap-guangzhou"):
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    response = client.head_object(
        Bucket=bucket,
        Key=key
    )

    return response


def delete_bucket(bucket, region="ap-guangzhou"):
    """删除桶"""
    # 删除桶中所有文件
    # 删除桶中所有碎片
    # 删除桶
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)

    # 找到桶中所有文件bi
    try:
        while True:
            part_objects = client.list_objects(bucket)
            contents = part_objects.get("Contents")
            if not contents:
                break
            objects = {
                "Quiet": "true",
                "Object": [{"Key": item['Key']} for item in contents]
            }
            client.delete_objects(bucket, objects)

            if part_objects['IsTruncated'] == "false":
                break

        # 找到碎片 删除
        while True:
            part_uploads = client.list_multipart_uploads(bucket)
            uploads = part_uploads.get("Upload")
            if not uploads:
                break
            for item in uploads:
                client.abort_multipart_upload(bucket, item["Key"], item["UploadId"])

            if part_uploads['IsTruncated'] == "false":
                break

        # 删除桶
        client.delete_bucket(bucket)
    except CosServiceError as e:
        pass

