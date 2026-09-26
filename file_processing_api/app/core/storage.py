import boto3
from fastapi import HTTPException
from botocore.exceptions import ClientError
from app.core.config import S3_BUCKET_NAME, URL_EXPIRATION


print("Creating S3 client...")
s3_client = boto3.client("s3",
                        endpoint_url="http://localhost:4566",
                        region_name="us-east-1",
                        aws_access_key_id="test",
                        aws_secret_access_key="test"
                        )


def generate_presigned_url(storage_key):

    url = s3_client.generate_presigned_url(
    ClientMethod="get_object",
    Params={
        "Bucket": S3_BUCKET_NAME,
        "Key": storage_key
    },
    ExpiresIn=URL_EXPIRATION

    )
    return url


def delete_file_in_storage(storage_key):
    try:
        response = s3_client.delete_object(
        Bucket="file-upload",
        Key=storage_key
        )

        return True
    
    except ClientError as e:
        raise

    







# print("S3 client created")
# with open(
#     r"C:\Users\HP\Desktop\Omnicopy\file_processing_api\uploads\2a37161f.png",
#     "rb"
# ) as file:
#     print("Uploading...")
#     s3_client.put_object(
#         Bucket="file-upload",
#         Key="uploads/2a37161f.png",
#         Body=file
#     )
# print("Upload completed")

# response = s3_client.list_objects_v2(
#     Bucket="file-upload",
#     Prefix="uploads/"
# )
# print("List response received")
# print(response)

# for obj in response.get("Contents", []):
#     print(obj["Key"])