"""
Standalone S3 connection test -- verifies the AWS credentials, bucket name,
region, and IAM permissions actually work, entirely independent of the
Django app. Run this before testing S3 through the full app, so any
problem found is clearly about the AWS setup itself, not something else in
the codebase.

Usage: run from the backend project root (same folder as manage.py, so it
can find the same .env file the app itself reads):

    python test_s3_connection.py

Requires: pip install boto3 python-decouple --break-system-packages
(python-decouple is already a project dependency; boto3 comes in via
django-storages[s3], already in requirements.txt)
"""
import sys
from decouple import config

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("boto3 isn't installed in this environment. Run:")
    print("  pip install boto3 --break-system-packages")
    sys.exit(1)

BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default=None)
ACCESS_KEY = config("AWS_ACCESS_KEY_ID", default=None)
SECRET_KEY = config("AWS_SECRET_ACCESS_KEY", default=None)
REGION = config("AWS_S3_REGION_NAME", default=None)

TEST_KEY = "connection-test/hello.txt"
TEST_CONTENT = b"RealmOpus S3 connection test"


def fail(step: str, exc: Exception):
    print(f"\nFAILED at: {step}")
    print(f"  {type(exc).__name__}: {exc}")
    sys.exit(1)


def main():
    missing = [
        name
        for name, val in [
            ("AWS_STORAGE_BUCKET_NAME", BUCKET_NAME),
            ("AWS_ACCESS_KEY_ID", ACCESS_KEY),
            ("AWS_SECRET_ACCESS_KEY", SECRET_KEY),
            ("AWS_S3_REGION_NAME", REGION),
        ]
        if not val
    ]
    if missing:
        print("Missing from your .env:", ", ".join(missing))
        sys.exit(1)

    print(f"Bucket: {BUCKET_NAME}")
    print(f"Region: {REGION}")
    print(f"Access key: {ACCESS_KEY[:4]}...{ACCESS_KEY[-4:]}")  # never print the full key
    print()

    client = boto3.client(
        "s3",
        region_name=REGION,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )

    try:
        client.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=1)
        print("[OK] ListBucket -- credentials, bucket name, and region are all valid")
    except ClientError as e:
        fail("ListBucket (check bucket name, region, and that ListBucket is granted)", e)

    try:
        client.put_object(Bucket=BUCKET_NAME, Key=TEST_KEY, Body=TEST_CONTENT)
        print("[OK] PutObject -- upload succeeded")
    except ClientError as e:
        fail("PutObject (check the IAM policy grants s3:PutObject)", e)

    try:
        response = client.get_object(Bucket=BUCKET_NAME, Key=TEST_KEY)
        body = response["Body"].read()
        assert body == TEST_CONTENT, "downloaded content didn't match what was uploaded"
        print("[OK] GetObject -- download succeeded and content matches")
    except (ClientError, AssertionError) as e:
        fail("GetObject (check the IAM policy grants s3:GetObject)", e)

    try:
        url = client.generate_presigned_url(
            "get_object", Params={"Bucket": BUCKET_NAME, "Key": TEST_KEY}, ExpiresIn=60
        )
        print("[OK] Presigned URL generated -- this is what the app actually uses for private access:")
        print(f"     {url[:90]}...")
    except ClientError as e:
        fail("generate_presigned_url", e)

    try:
        client.delete_object(Bucket=BUCKET_NAME, Key=TEST_KEY)
        print("[OK] DeleteObject -- cleanup succeeded, test file removed from the bucket")
    except ClientError as e:
        fail("DeleteObject (check the IAM policy grants s3:DeleteObject)", e)

    print("\nAll checks passed -- your S3 setup is correctly wired up.")


if __name__ == "__main__":
    main()
