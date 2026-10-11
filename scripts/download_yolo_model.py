#!/usr/bin/env python3
"""
CIVILENS Model Downloader
Downloads the benchmarked YOLOv8s RDD2022 road damage detection checkpoint
from Hugging Face and verifies its SHA-256 integrity.

Checkpoint: yolov8s_seed42_best.pt
Source: https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark
License: CC-BY-4.0
Dataset: RDD2022 (Road Damage Detection 2022)
Classes: D00 (Longitudinal Crack), D10 (Transverse Crack), D20 (Alligator Crack), D40 (Pothole)
"""

import os
import sys
import hashlib
import shutil

EXPECTED_SHA256 = "2cf3f60395de6591d8378294fc26b8d7c4ca8f227e455987b3713ce6eeeea119"
TARGET_PATH = "models/yolov8s_rdd2022.pt"
REPO_ID = "SreekarAditya/yolo-rdd2022-benchmark"
FILENAME = "yolo-rdd2022-benchmark/yolov8s_seed42_best.pt"


def verify_sha256(filepath: str, expected_hash: str) -> bool:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    digest = sha256.hexdigest()
    return digest == expected_hash, digest


def main():
    os.makedirs("models", exist_ok=True)

    if os.path.exists(TARGET_PATH):
        matches, current_sha = verify_sha256(TARGET_PATH, EXPECTED_SHA256)
        if matches:
            print(f"✓ Model checkpoint already exists and verified: {TARGET_PATH}")
            print(f"  SHA-256: {current_sha}")
            return 0
        else:
            print(f"! Warning: Existing file SHA-256 mismatch ({current_sha}). Re-downloading...")

    print(f"Downloading {FILENAME} from Hugging Face ({REPO_ID})...")
    try:
        from huggingface_hub import hf_hub_download
        downloaded = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir="models",
            local_dir_use_symlinks=False
        )
        if os.path.exists(downloaded) and downloaded != TARGET_PATH:
            shutil.copyfile(downloaded, TARGET_PATH)
            # Remove nested directory
            parent = os.path.dirname(downloaded)
            if parent and os.path.basename(parent) == "yolo-rdd2022-benchmark":
                shutil.rmtree(parent, ignore_errors=True)

        matches, downloaded_sha = verify_sha256(TARGET_PATH, EXPECTED_SHA256)
        if not matches:
            print(f"✗ Checksum verification failed: expected {EXPECTED_SHA256}, got {downloaded_sha}")
            return 1

        size_mb = os.path.getsize(TARGET_PATH) / (1024 * 1024)
        print(f"✓ Successfully downloaded and verified: {TARGET_PATH} ({size_mb:.2f} MB)")
        print(f"  SHA-256: {downloaded_sha}")
        return 0
    except Exception as e:
        print(f"✗ Failed to download checkpoint: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
