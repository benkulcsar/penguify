import json
import logging
from datetime import datetime, timezone
from os import getenv, listdir, path

import boto3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

S3_BUCKET_NAME = getenv("S3_BUCKET_NAME", "")
if not S3_BUCKET_NAME:
    raise RuntimeError("S3_BUCKET_NAME environment variable must be set.")

IMAGES_BASE_DIR = getenv("IMAGES_BASE_DIR", "./imgs")
MANIFEST_S3_KEY = getenv("MANIFEST_S3_KEY", "manifest.json")


def upload_directory_to_s3(directory: str, prefix: str) -> None:
    s3 = boto3.client("s3")
    for filename in listdir(directory):
        file_path = path.join(directory, filename)
        if path.isfile(file_path):
            s3_object_key = f"{prefix}/{filename}"
            try:
                with open(file_path, "rb") as image_file:
                    s3.upload_fileobj(image_file, S3_BUCKET_NAME, s3_object_key)
                logger.info(f"File uploaded to s3://[penguify-bucket]/{s3_object_key}")
            except Exception as e:
                logger.error(f"Failed to upload {file_path}: {e}")


def update_manifest_json_in_s3(
    s3_bucket: str, manifest_s3_key: str, date_prefix: str, date_label: str, now: datetime
) -> None:
    s3 = boto3.client("s3")
    manifest_updated_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        manifest_obj = s3.get_object(Bucket=s3_bucket, Key=manifest_s3_key)
        manifest_json = json.loads(manifest_obj["Body"].read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to fetch manifest: {e}")
        return

    if not any(item["prefix"] == date_prefix for item in manifest_json.get("items", [])):
        manifest_json.setdefault("items", []).insert(0, {"label": date_label, "prefix": date_prefix})
    manifest_json["updatedAt"] = manifest_updated_at

    s3.put_object(
        Bucket=s3_bucket,
        Key=manifest_s3_key,
        Body=json.dumps(manifest_json, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    return manifest_json


def run_upload_and_manifest_update():
    now = datetime.now(timezone.utc)
    date_prefix = now.strftime("%Y-%m-%d")
    date_label = now.strftime("%d %b")
    logger.info(f"Datestamp: {date_prefix}")
    images_directory = f"{IMAGES_BASE_DIR}/{date_prefix}"
    upload_directory_to_s3(directory=images_directory, prefix=date_prefix)
    update_manifest_json_in_s3(
        s3_bucket=S3_BUCKET_NAME,
        manifest_s3_key=MANIFEST_S3_KEY,
        date_prefix=date_prefix,
        date_label=date_label,
        now=now,
    )


if __name__ == "__main__":
    run_upload_and_manifest_update()
