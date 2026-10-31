#!/usr/bin/env python3
"""
CIVILENS Phase 13.2 — Hard Negative Dataset Preparation Pipeline
Extracts and validates a balanced, leak-free training dataset for Road Damage Detection:
- 100 positive images with verified annotations (D00, D10, D20, D40)
- 100 hard negative clean-road images with empty labels
- Enforces strict SHA-256 and duplicate isolation against val and test splits.
"""

import os
import sys
import json
import zipfile
import hashlib
from pathlib import Path
from PIL import Image
import io

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def compute_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def compute_sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*70)
    print("PREPARING BALANCED TRAINING DATASET WITH HARD NEGATIVES")
    print("="*70)

    road_dataset_dir = PROJECT_ROOT / "data" / "datasets" / "road_damage"
    img_train_dir = road_dataset_dir / "images" / "train"
    lbl_train_dir = road_dataset_dir / "labels" / "train"
    img_train_dir.mkdir(parents=True, exist_ok=True)
    lbl_train_dir.mkdir(parents=True, exist_ok=True)

    # 1. Collect all hashes from existing val and test sets to guarantee zero leakage
    existing_hashes = {}
    for split in ["val", "test"]:
        split_img_dir = road_dataset_dir / "images" / split
        for f in split_img_dir.glob("*.jpg"):
            h = compute_sha256_file(f)
            existing_hashes[h] = (split, f.name)

    print(f"Recorded {len(existing_hashes)} existing unique images in val and test splits.")

    # 2. Locate RDD2022_India.zip in Hugging Face cache
    hf_snapshots = list(Path.home().glob(".cache/huggingface/hub/datasets--aiswarya9302--RDD_2022India/snapshots/*/RDD2022_India.zip"))
    assert hf_snapshots, "Could not find RDD2022_India.zip in Hugging Face cache!"
    zip_path = hf_snapshots[0]
    print(f"Reading from cached archive: {zip_path}")

    with zipfile.ZipFile(zip_path) as zf:
        train_labels = [n for n in zf.namelist() if n.startswith("train/labels/") and n.endswith(".txt")]
        
        candidates_pos = []
        candidates_neg = []

        for lname in sorted(train_labels):
            stem = Path(lname).stem
            iname = f"train/images/{stem}.jpg"
            if iname not in zf.namelist():
                continue

            content = zf.read(lname).decode("utf-8").strip()
            img_bytes = zf.read(iname)
            img_hash = compute_sha256_bytes(img_bytes)

            # Strict duplicate / leak check
            if img_hash in existing_hashes:
                print(f"[Collision Alert] Skipping {stem} (matches {existing_hashes[img_hash]})")
                continue

            if content:
                # Validate labels
                lines = content.splitlines()
                boxes = []
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        cls_id = int(parts[0])
                        if cls_id in [0, 1, 2, 3]:
                            boxes.append((cls_id, [float(x) for x in parts[1:]]))
                if boxes:
                    candidates_pos.append({
                        "stem": stem,
                        "iname": iname,
                        "lname": lname,
                        "content": content,
                        "boxes": boxes,
                        "hash": img_hash,
                        "bytes": img_bytes
                    })
            else:
                candidates_neg.append({
                    "stem": stem,
                    "iname": iname,
                    "lname": lname,
                    "content": "",
                    "boxes": [],
                    "hash": img_hash,
                    "bytes": img_bytes
                })

        print(f"Discovered {len(candidates_pos)} leak-free positive candidates, {len(candidates_neg)} leak-free clean negative candidates.")

        # Select balanced 100 positive and 100 negative samples
        # For positives, balance across defect classes
        d00_samples = [c for c in candidates_pos if any(b[0] == 0 for b in c["boxes"])][:25]
        d10_samples = [c for c in candidates_pos if any(b[0] == 1 for b in c["boxes"])][:15]
        d20_samples = [c for c in candidates_pos if any(b[0] == 2 for b in c["boxes"])][:35]
        d40_samples = [c for c in candidates_pos if any(b[0] == 3 for b in c["boxes"])][:25]

        selected_pos_map = {}
        for group in [d00_samples, d10_samples, d20_samples, d40_samples]:
            for item in group:
                selected_pos_map[item["stem"]] = item

        # Fill remaining up to 100 if needed
        for c in candidates_pos:
            if len(selected_pos_map) >= 100:
                break
            selected_pos_map[c["stem"]] = c

        selected_pos = list(selected_pos_map.values())[:100]
        selected_neg = candidates_neg[:100]

        print(f"Selected {len(selected_pos)} balanced positive images and {len(selected_neg)} hard negative images.")

        train_manifest_records = []

        # Export Positives
        for item in selected_pos:
            out_img = img_train_dir / f"{item['stem']}.jpg"
            out_lbl = lbl_train_dir / f"{item['stem']}.txt"
            out_img.write_bytes(item["bytes"])
            out_lbl.write_text(item["content"] + "\n", encoding="utf-8")
            train_manifest_records.append({
                "filename": f"{item['stem']}.jpg",
                "image_path": str(out_img.relative_to(PROJECT_ROOT)),
                "label_path": str(out_lbl.relative_to(PROJECT_ROOT)),
                "split": "train",
                "is_positive": True,
                "sha256": item["hash"],
                "box_count": len(item["boxes"])
            })

        # Export Negatives
        for item in selected_neg:
            out_img = img_train_dir / f"{item['stem']}.jpg"
            out_lbl = lbl_train_dir / f"{item['stem']}.txt"
            out_img.write_bytes(item["bytes"])
            out_lbl.write_text("", encoding="utf-8")
            train_manifest_records.append({
                "filename": f"{item['stem']}.jpg",
                "image_path": str(out_img.relative_to(PROJECT_ROOT)),
                "label_path": str(out_lbl.relative_to(PROJECT_ROOT)),
                "split": "train",
                "is_positive": False,
                "sha256": item["hash"],
                "box_count": 0
            })

    # Save manifest
    manifest_out = road_dataset_dir / "train_manifest.json"
    with open(manifest_out, "w", encoding="utf-8") as f:
        json.dump({
            "dataset": "RDD2022_India_Train_Split",
            "provenance": "RDD2022 India (Arya et al., CC-BY-4.0)",
            "total_images": len(train_manifest_records),
            "positive_count": len(selected_pos),
            "negative_count": len(selected_neg),
            "records": train_manifest_records
        }, f, indent=2)

    # Update road_damage.yaml
    yaml_content = f"""path: {road_dataset_dir}
train: images/train
val: images/val
test: images/test

nc: 4
names:
  0: D00_longitudinal_crack
  1: D10_transverse_crack
  2: D20_alligator_crack
  3: D40_pothole
"""
    yaml_path = road_dataset_dir / "road_damage.yaml"
    yaml_path.write_text(yaml_content, encoding="utf-8")

    print(f"✓ Training set created: {len(train_manifest_records)} images in {img_train_dir}")
    print(f"✓ Manifest saved to {manifest_out}")
    print(f"✓ Updated {yaml_path}")

    # Final cross-split duplicate verification
    all_train_hashes = {r["sha256"] for r in train_manifest_records}
    val_test_hashes = set(existing_hashes.keys())
    inter = all_train_hashes.intersection(val_test_hashes)
    assert len(inter) == 0, f"Critical leakage detected! {len(inter)} hashes overlap between train and val/test!"
    print("✓ Cross-split integrity verified: 0 hash overlaps across train, val, and test splits.")

if __name__ == "__main__":
    main()

