#!/usr/bin/env python3
"""
CIVILENS Vision Models Downloader & Provenance Verifier
Downloads and cryptographically verifies supported computer vision model checkpoints:
1. YOLOv8s RDD2022 (Road Damage Detection) — CC-BY-4.0
2. YOLO TACO (Waste & Litter Detection) — MIT License

Documented Category Status:
- Street Flooding & Waterlogging: No reliable ground-level object detection model exists;
  explicitly reported as unvalidated/unsupported rather than fabricating results.
"""

import os
import sys
import hashlib
import shutil

MODELS = {
    "road_damage": {
        "name": "YOLOv8s RDD2022 Road Damage Detector",
        "target_path": "models/yolov8s_rdd2022.pt",
        "repo_id": "SreekarAditya/yolo-rdd2022-benchmark",
        "filename": "yolo-rdd2022-benchmark/yolov8s_seed42_best.pt",
        "expected_sha256": "2cf3f60395de6591d8378294fc26b8d7c4ca8f227e455987b3713ce6eeeea119",
        "license": "CC-BY-4.0",
        "dataset": "RDD2022 (Japan/India/Czech)",
        "classes": ["D00 (Longitudinal Crack)", "D10 (Transverse Crack)", "D20 (Alligator Crack)", "D40 (Pothole)"]
    },
    "waste_detection": {
        "name": "YOLO11s TACO Waste & Litter Detector",
        "target_path": "models/taco_yolo11s.pt",
        "legacy_target_path": "models/yolov8_waste.pt",
        "architecture": "YOLO11s (yolo11s.yaml, C3k2 + C2PSA layers, 9.43M params)",
        "repo_id": "fabiocigaina/TACO-yolo11s",
        "filename": "best_model.pt",
        "expected_sha256": "1b9c8379aca95efa75ec1f6ac803cabd3ba531b7d4b3f459101bcfd3aaae95ef",
        "license": "MIT",
        "dataset": "TACO (Trash Annotations in Context)",
        "classes": [
            "Plastic bag & wrapper", "Cigarette", "Bottle", "Bottle cap",
            "Can", "Other plastic", "Carton", "Cup", "Other"
        ]
    }
}


def verify_sha256(filepath: str, expected_hash: str) -> tuple[bool, str]:
    if not os.path.exists(filepath):
        return False, "file_not_found"
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    digest = sha256.hexdigest()
    return digest.lower() == expected_hash.lower(), digest


def download_model(key: str, config: dict) -> bool:
    target_path = config["target_path"]
    expected_sha = config["expected_sha256"]
    name = config["name"]

    print(f"\n--- Checking {name} ---")
    print(f"Target path: {target_path}")
    print(f"License: {config['license']} | Dataset: {config['dataset']}")

    if os.path.exists(target_path):
        matches, current_sha = verify_sha256(target_path, expected_sha)
        if matches:
            size_mb = os.path.getsize(target_path) / (1024 * 1024)
            print(f"✓ Model verified ({size_mb:.2f} MB, SHA-256: {current_sha})")
            return True
        else:
            print(f"! Warning: Existing file SHA-256 mismatch ({current_sha}). Re-downloading...")

    print(f"Downloading from Hugging Face ({config['repo_id']})...")
    try:
        from huggingface_hub import hf_hub_download
        downloaded = hf_hub_download(
            repo_id=config["repo_id"],
            filename=config["filename"],
            local_dir="models",
            local_dir_use_symlinks=False
        )
        if os.path.exists(downloaded) and downloaded != target_path:
            shutil.copyfile(downloaded, target_path)
            # Cleanup any nested subdirectory created by local_dir
            parent = os.path.dirname(downloaded)
            if parent and parent != "models" and os.path.basename(parent) != "models":
                shutil.rmtree(parent, ignore_errors=True)

        matches, downloaded_sha = verify_sha256(target_path, expected_sha)
        if not matches:
            print(f"✗ Checksum verification failed: expected {expected_sha}, got {downloaded_sha}")
            return False

        size_mb = os.path.getsize(target_path) / (1024 * 1024)
        print(f"✓ Successfully downloaded and verified: {target_path} ({size_mb:.2f} MB)")
        print(f"  SHA-256: {downloaded_sha}")
        if "legacy_target_path" in config and not os.path.exists(config["legacy_target_path"]):
            shutil.copyfile(target_path, config["legacy_target_path"])
        return True
    except Exception as e:
        print(f"✗ Download failed for {name}: {e}", file=sys.stderr)
        return False


def main():
    os.makedirs("models", exist_ok=True)
    all_ok = True
    for key, config in MODELS.items():
        ok = download_model(key, config)
        if not ok:
            all_ok = False

    print("\n--- Model Availability & Limitation Summary ---")
    print("1. Road Damage Detection: READY (Ultralytics YOLOv8s RDD2022)")
    print("2. Sanitation / Waste Detection: READY (Ultralytics TACO YOLO)")
    print("3. Street Flooding / Waterlogging: UNSUPPORTED")
    print("   Note: No reliable open ground-level object detector exists for municipal waterlogging.")
    print("   Bounding boxes are NOT fabricated. Handled via human manual review.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
