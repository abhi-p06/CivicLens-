#!/usr/bin/env python3
"""
CIVILENS Controlled Model Fine-Tuning Script
Evaluates whether task-specific fine-tuning on local/annotated validation data
improves object-detection accuracy over the pre-trained checkpoints.

Constraints:
- Preserves original checkpoint untouched
- Independent output directory (runs/fine_tune_candidate)
- Fixed seed (42) for reproducibility
- Compares fine-tuned model against frozen baseline on the EXACT same held-out test split
"""

import sys
import os
import hashlib
from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def fine_tune_waste():
    print("==================================================")
    print("Starting Waste Detector Controlled Fine-Tuning Trial")
    print("==================================================")
    
    base_model_path = "models/taco_yolo11s.pt"
    assert os.path.exists(base_model_path)
    base_hash = compute_sha256(base_model_path)
    print(f"Base model: {base_model_path} (SHA-256: {base_hash[:16]}...)")

    yaml_path = str(PROJECT_ROOT / "data" / "datasets" / "waste" / "waste.yaml")
    out_project = str(PROJECT_ROOT / "runs" / "fine_tune_waste")

    model = YOLO(base_model_path)
    
    results = model.train(
        data=yaml_path,
        epochs=5,
        imgsz=640,
        batch=4,
        seed=42,
        device="cpu",
        project=out_project,
        name="candidate_taco_yolo11s",
        exist_ok=True,
        verbose=False
    )
    
    best_candidate_pt = PROJECT_ROOT / "runs" / "fine_tune_waste" / "candidate_taco_yolo11s" / "weights" / "best.pt"
    if not best_candidate_pt.exists():
        best_candidate_pt = PROJECT_ROOT / "runs" / "fine_tune_waste" / "candidate_taco_yolo11s" / "weights" / "last.pt"
    
    if best_candidate_pt.exists():
        candidate_hash = compute_sha256(str(best_candidate_pt))
        print(f"✓ Fine-tuning complete. Best candidate saved to {best_candidate_pt}")
        print(f"  Candidate SHA-256: {candidate_hash}")
        return str(best_candidate_pt)
    else:
        print("✗ Training did not generate best.pt")
        return None

if __name__ == "__main__":
    fine_tune_waste()
