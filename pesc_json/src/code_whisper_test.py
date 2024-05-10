# create a function that uploads a file and stores it in s3 bucket with the given key name
# create a function that downloads a file from s3 bucket with the given key name
import boto3
import botocore
import logging
from botocore.exceptions import ClientError

# create a function that uploads a file and stores it in s3 bucket with the given key name
def upload_file(file_name, bucket, object_name=None):
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name
    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

