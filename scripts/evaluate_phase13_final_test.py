#!/usr/bin/env python3
"""
CIVILENS Phase 13.2 — Task 7 Final Selection on Held-Out Test Split
Evaluates:
1. Baseline YOLOv8s (conf=0.15, imgsz=640)
2. Best Per-Class Threshold Candidate (D00=0.22, D10=0.22, D20=0.20, D40=0.35)
3. Best Geometric Filter Candidate (Thresholds + Min Area Filter)
4. Fine-Tuned YOLOv8s Candidate (with Hard Negatives, best.pt)
5. YOLO11s Architecture Candidate (best.pt)
Strictly on the frozen held-out test split (N=100: 50 pos, 50 neg, 72 GT objects).
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase13_road_experiments import RoadExperimentRunner, compute_sha256

def main():
    print("="*75)
    print("TASK 7: COMPREHENSIVE FINAL EVALUATION ON FROZEN HELD-OUT TEST SPLIT")
    print("="*75)

    manifest_path = "data/datasets/road_damage/dataset_manifest.json"

    # Define all models and configurations
    baseline_path = "models/baseline_checkpoints/yolov8s_rdd2022.pt"
    yolo11s_path = "runs/road_candidates/candidate_yolo11s/weights/best.pt"
    yolov8s_hardneg_path = "runs/road_candidates/candidate_yolov8s_hardneg/weights/best.pt"

    runner_baseline = RoadExperimentRunner(model_path=baseline_path, manifest_path=manifest_path)

    print("\n[Caching] Extracting test predictions for Baseline YOLOv8s (imgsz=640, conf=0.02)...")
    test_cached_baseline = runner_baseline.extract_raw_predictions(split="test", imgsz=640, base_conf=0.02)

    candidates = []

    # 1. Baseline YOLOv8s (Uniform 0.15)
    print("\n--- Evaluating 1. Baseline YOLOv8s (Uniform 0.15) ---")
    res_baseline = runner_baseline.evaluate_with_filters(
        cached_preds=test_cached_baseline,
        class_thresholds={0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15},
        aspect_ratio_filter=False,
        min_area_filter=False
    )
    res_baseline["candidate_id"] = "1_baseline_yolov8s"
    res_baseline["candidate_name"] = "Baseline YOLOv8s (Uniform conf=0.15)"
    candidates.append(res_baseline)

    # 2. Best Per-Class Threshold Candidate
    print("\n--- Evaluating 2. Best Per-Class Threshold Candidate ---")
    res_perclass = runner_baseline.evaluate_with_filters(
        cached_preds=test_cached_baseline,
        class_thresholds={0: 0.22, 1: 0.22, 2: 0.20, 3: 0.35},
        aspect_ratio_filter=False,
        min_area_filter=False
    )
    res_perclass["candidate_id"] = "2_perclass_thresholds"
    res_perclass["candidate_name"] = "Per-Class Thresholds (D00=0.22, D10=0.22, D20=0.20, D40=0.35)"
    candidates.append(res_perclass)

    # 3. Geometric Filter Candidate (Per-Class Thresholds + Min Box Area >= 0.003)
    print("\n--- Evaluating 3. Geometric Filter Candidate (Min Box Area 0.003) ---")
    res_geo_area = runner_baseline.evaluate_with_filters(
        cached_preds=test_cached_baseline,
        class_thresholds={0: 0.22, 1: 0.22, 2: 0.20, 3: 0.35},
        aspect_ratio_filter=False,
        min_area_filter=True,
        min_area_ratio=0.003
    )
    res_geo_area["candidate_id"] = "3_geometric_min_area"
    res_geo_area["candidate_name"] = "Per-Class Thresholds + Min Area Filter (Area >= 0.003)"
    candidates.append(res_geo_area)

    # 3b. Geometric Filter with Aspect Ratio (to test effect on test set)
    print("\n--- Evaluating 3b. Per-Class Thresholds + Crack Aspect Ratio (AR >= 1.5) ---")
    res_geo_ar = runner_baseline.evaluate_with_filters(
        cached_preds=test_cached_baseline,
        class_thresholds={0: 0.22, 1: 0.22, 2: 0.20, 3: 0.35},
        aspect_ratio_filter=True,
        min_ar_crack=1.5,
        min_area_filter=False
    )
    res_geo_ar["candidate_id"] = "3b_geometric_aspect_ratio"
    res_geo_ar["candidate_name"] = "Per-Class Thresholds + Crack Aspect Ratio Filter (AR >= 1.5)"
    candidates.append(res_geo_ar)

    # 4. Fine-Tuned YOLOv8s Candidate (with Hard Negatives)
    if Path(yolov8s_hardneg_path).exists():
        print(f"\n--- Evaluating 4. Fine-Tuned YOLOv8s Candidate ({yolov8s_hardneg_path}) ---")
        runner_v8_hn = RoadExperimentRunner(model_path=yolov8s_hardneg_path, manifest_path=manifest_path)
        test_cached_v8_hn = runner_v8_hn.extract_raw_predictions(split="test", imgsz=640, base_conf=0.02)
        res_v8_hn = runner_v8_hn.evaluate_with_filters(
            cached_preds=test_cached_v8_hn,
            class_thresholds={0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15},
            aspect_ratio_filter=False,
            min_area_filter=False
        )
        res_v8_hn["candidate_id"] = "4_finetuned_yolov8s_hardneg"
        res_v8_hn["candidate_name"] = "Fine-Tuned YOLOv8s (Hard Negatives, conf=0.15)"
        candidates.append(res_v8_hn)
    else:
        print(f"[Notice] {yolov8s_hardneg_path} not found yet.")

    # 5. YOLO11s Architecture Candidate
    if Path(yolo11s_path).exists():
        print(f"\n--- Evaluating 5. YOLO11s Architecture Candidate ({yolo11s_path}) ---")
        runner_y11 = RoadExperimentRunner(model_path=yolo11s_path, manifest_path=manifest_path)
        test_cached_y11 = runner_y11.extract_raw_predictions(split="test", imgsz=640, base_conf=0.02)
        res_y11 = runner_y11.evaluate_with_filters(
            cached_preds=test_cached_y11,
            class_thresholds={0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15},
            aspect_ratio_filter=False,
            min_area_filter=False
        )
        res_y11["candidate_id"] = "5_yolo11s_candidate"
        res_y11["candidate_name"] = "YOLO11s Architecture Candidate (conf=0.15)"
        candidates.append(res_y11)
    else:
        print(f"[Notice] {yolo11s_path} not found yet.")

    # Print Comparison Table
    print("\n" + "="*115)
    print("FINAL HELD-OUT TEST SPLIT BENCHMARK SUMMARY (N=100, 50 POS / 50 NEG, 72 GT OBJECTS)")
    print("="*115)
    print(f"{'Candidate Model / Configuration':<50} | {'Prec':<7} | {'Recall':<7} | {'F1':<7} | {'mAP50':<7} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Neg Alarms':<12}")
    print("-" * 115)

    for c in candidates:
        neg_s = f"{c['hard_neg_alarms']}/{c['hard_neg_total']} ({c['hard_neg_alarm_rate']*100:.1f}%)"
        print(f"{c['candidate_name']:<50} | {c['precision']*100:<6.2f}% | {c['recall']*100:<6.2f}% | {c['f1_score']*100:<6.2f}% | {c['mAP50']*100:<6.2f}% | {c['tp']:<4} | {c['fp']:<4} | {c['fn']:<4} | {neg_s:<12}")

    out_file = PROJECT_ROOT / "data" / "evaluation" / "phase13_final_test_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2)
    print(f"\n✓ Saved final test evaluation results to {out_file}")

if __name__ == "__main__":
    main()

