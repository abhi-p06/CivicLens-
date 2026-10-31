#!/usr/bin/env python3
"""
CIVILENS Phase 13.2 — Road Damage Candidate Training Pipeline
Trains:
1. YOLO11s candidate on the balanced road damage dataset with hard negatives
2. YOLOv8s fine-tuned candidate on the exact same dataset
Both use:
- Seed 42 for deterministic reproducibility
- 5 epochs (to assess transfer without catastrophic forgetting)
- Batch size 4, CPU device
- Identical train (200 imgs), val (100 imgs), and test splits
"""

import os
import sys
import hashlib
from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def train_yolo11s():
    print("="*70)
    print("TRAINING CANDIDATE 1: YOLO11s (ROAD DAMAGE + HARD NEGATIVES)")
    print("="*70)

    base_weights = PROJECT_ROOT / "models" / "candidates" / "yolo11s_base.pt"
    assert base_weights.exists(), f"Missing {base_weights}"

    yaml_path = PROJECT_ROOT / "data" / "datasets" / "road_damage" / "road_damage.yaml"
    out_project = PROJECT_ROOT / "runs" / "road_candidates"

    model = YOLO(str(base_weights))
    model.train(
        data=str(yaml_path),
        epochs=5,
        imgsz=640,
        batch=4,
        seed=42,
        device="cpu",
        project=str(out_project),
        name="candidate_yolo11s",
        exist_ok=True,
        verbose=True
    )

    best_pt = out_project / "candidate_yolo11s" / "weights" / "best.pt"
    if not best_pt.exists():
        best_pt = out_project / "candidate_yolo11s" / "weights" / "last.pt"

    if best_pt.exists():
        h = compute_sha256(best_pt)
        print(f"✓ YOLO11s training complete. Weights: {best_pt} (SHA-256: {h})")
        return str(best_pt)
    else:
        print("✗ YOLO11s training did not yield weights file.")
        return None

def train_yolov8s_hardneg():
    print("="*70)
    print("TRAINING CANDIDATE 2: YOLOv8s FINE-TUNED (WITH HARD NEGATIVES)")
    print("="*70)

    base_weights = PROJECT_ROOT / "models" / "baseline_checkpoints" / "yolov8s_rdd2022.pt"
    assert base_weights.exists(), f"Missing {base_weights}"

    yaml_path = PROJECT_ROOT / "data" / "datasets" / "road_damage" / "road_damage.yaml"
    out_project = PROJECT_ROOT / "runs" / "road_candidates"

    model = YOLO(str(base_weights))
    model.train(
        data=str(yaml_path),
        epochs=5,
        imgsz=640,
        batch=4,
        seed=42,
        device="cpu",
        project=str(out_project),
        name="candidate_yolov8s_hardneg",
        exist_ok=True,
        verbose=True
    )

    best_pt = out_project / "candidate_yolov8s_hardneg" / "weights" / "best.pt"
    if not best_pt.exists():
        best_pt = out_project / "candidate_yolov8s_hardneg" / "weights" / "last.pt"

    if best_pt.exists():
        h = compute_sha256(best_pt)
        print(f"✓ YOLOv8s fine-tuning complete. Weights: {best_pt} (SHA-256: {h})")
        return str(best_pt)
    else:
        print("✗ YOLOv8s training did not yield weights file.")
        return None

if __name__ == "__main__":
    train_yolo11s()
    train_yolov8s_hardneg()

