import json
from datetime import datetime, timezone
from pathlib import Path

import boto3

from .common.settings import production_settings as settings
from .tools.logger import get_logger

logger = get_logger(__name__)


def upload_directory_to_s3(directory: str | Path, prefix: str) -> None:
    s3 = boto3.client("s3")
    dir_path = Path(directory)
    for file_path in dir_path.iterdir():
        if file_path.is_file():
            s3_object_key = f"{prefix}/{file_path.name}"
            try:
                with open(file_path, "rb") as image_file:
                    s3.upload_fileobj(image_file, settings.S3_BUCKET_NAME, s3_object_key)
                logger.info(f"File uploaded to s3://[penguify-bucket]/{s3_object_key}")
            except Exception as e:
                logger.error(f"Failed to upload {file_path}: {e}")


def update_manifest_json_in_s3(s3_bucket: str, manifest_s3_key: str, date_prefix: str, date_label: str) -> None:
    s3 = boto3.client("s3")
    manifest_updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
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


def run_upload_and_manifest_update() -> None:
    images_dir = Path(settings.IMAGES_BASE_DIR) / settings.DATESTAMP
    upload_directory_to_s3(directory=images_dir, prefix=settings.DATESTAMP)
    update_manifest_json_in_s3(
        s3_bucket=settings.S3_BUCKET_NAME,
        manifest_s3_key=settings.MANIFEST_S3_KEY,
        date_prefix=settings.DATESTAMP,
        date_label=settings.DATE_LABEL,
    )


if __name__ == "__main__":
    run_upload_and_manifest_update()
