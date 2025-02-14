# This file loads to the S3 bucket (which will serve as our external stage when loading to Snowflake) from local
# Multipart load with a part size of 10MB is the reason this push is possible from local to S3 with Python

import os
import boto3
import math
from tqdm import tqdm
from botocore.exceptions import BotoCoreError, NoCredentialsError, ConnectionClosedError

# Initialize S3 client with session
session = boto3.Session()
s3 = session.client("s3")

def multipart_upload_with_progress(file_path, bucket_name, s3_key, part_size_mb=10):
    """
    Uploads a file to S3 using Multipart Upload.

    :param file_path: Local file path
    :param bucket_name: Target S3 bucket
    :param s3_key: S3 destination key
    :param part_size_mb: Size of each part in MB (default: 10MB)
    """
    try:
        file_size = os.path.getsize(file_path)
        part_size = part_size_mb * 1024 * 1024  # Convert MB to bytes
        num_parts = math.ceil(file_size / part_size)

        # Create multipart upload
        response = s3.create_multipart_upload(Bucket=bucket_name, Key=s3_key)
        upload_id = response["UploadId"]

        print(f"🚀 Starting Multipart Upload: {file_path} → s3://{bucket_name}/{s3_key}")
        
        parts = []
        progress = tqdm(total=file_size, unit="B", unit_scale=True, desc="Uploading")

        with open(file_path, "rb") as file:
            for part_number in range(1, num_parts + 1):
                data = file.read(part_size)
                part_response = s3.upload_part(
                    Bucket=bucket_name,
                    Key=s3_key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=data
                )
                parts.append({"PartNumber": part_number, "ETag": part_response["ETag"]})
                progress.update(len(data))

        progress.close()

        # Complete multipart upload
        s3.complete_multipart_upload(
            Bucket=bucket_name,
            Key=s3_key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
        print(f"✅ Upload completed successfully!")

    except (BotoCoreError, NoCredentialsError, ConnectionClosedError) as e:
        print(f"❌ Upload failed: {e}")
        # Abort multipart upload if there's a failure
        s3.abort_multipart_upload(Bucket=bucket_name, Key=s3_key, UploadId=upload_id)
        print("⚠️ Multipart upload aborted.")

# Example Usage
multipart_upload_with_progress(
    file_path=r"C:\Users\pooja\Desktop\NEU\Spring '25\DAMG 7374\yelp\yelp_academic_dataset_user.json",
    #file_path = r"C:\Users\pooja\Desktop\NEU\Spring '25\DAMG 7374\yelp\yelp_academic_dataset_review.json"
    #file_path = r"C:\Users\pooja\Desktop\NEU\Spring '25\DAMG 7374\yelp\yelp_academic_dataset_business.json"
    bucket_name="street-fairy",
    s3_key="raw/yelp_academic_dataset_user.json",
    #s3_key = "raw/yelp_academic_dataset_review.json"
    part_size_mb=10  # Adjust part size as needed
)
