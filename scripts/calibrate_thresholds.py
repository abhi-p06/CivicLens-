#!/usr/bin/env python3
"""
CIVILENS Threshold Calibration Engine
Performs a rigorous confidence threshold sweep over the VALIDATION split:
- Road Damage Detector: conf 0.10 to 0.50 (step 0.05)
- Waste / Litter Detector: conf 0.10 to 0.60 (step 0.05)

Optimizes for:
1. Minimizing municipal false dispatches (lowering Hard Negative False Alarm Rate and total False Positives)
2. Preserving actionable recall on true safety/civic hazards
3. Maximizing F1-score and Precision-Recall balance
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_detection_accuracy import evaluate_dataset

def sweep_thresholds(
    model_path: str,
    manifest_path: str,
    task_name: str,
    thresholds: List[float],
    output_path: str
) -> List[Dict[str, Any]]:
    results = []
    print(f"\n{'='*70}")
    print(f"SWEEPING CONFIDENCE THRESHOLDS FOR {task_name} (VALIDATION SPLIT)")
    print(f"{'='*70}")
    print(f"{'Conf':<6} | {'Precision':<10} | {'Recall':<8} | {'F1':<8} | {'TP':<5} | {'FP':<5} | {'FN':<5} | {'Neg Alarms':<12}")
    print("-" * 70)

    for conf in thresholds:
        metrics = evaluate_dataset(
            model_path=model_path,
            manifest_path=manifest_path,
            split="val",
            conf_threshold=conf,
            iou_threshold=0.45,
            task_name=task_name
        )
        row = {
            "conf": round(conf, 2),
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1_score": metrics["f1_score"],
            "mAP_50": metrics["mAP_50"],
            "true_positives": metrics["true_positives"],
            "false_positives": metrics["false_positives"],
            "false_negatives": metrics["false_negatives"],
            "hard_neg_false_alarms": metrics["hard_neg_images_with_false_alarms"],
            "hard_neg_evaluated": metrics["hard_neg_images_evaluated"],
            "hard_neg_alarm_rate": metrics["hard_neg_false_alarm_rate"],
            "latency_mean_ms": metrics["latency_ms"]["mean"]
        }
        results.append(row)
        neg_str = f"{row['hard_neg_false_alarms']}/{row['hard_neg_evaluated']} ({row['hard_neg_alarm_rate']*100:.1f}%)"
        print(f"{conf:<6.2f} | {row['precision']*100:<9.2f}% | {row['recall']*100:<7.2f}% | {row['f1_score']*100:<7.2f}% | {row['true_positives']:<5} | {row['false_positives']:<5} | {row['false_negatives']:<5} | {neg_str:<12}")

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Saved sweep results to {out_p}")
    return results

def main():
    road_manifest = str(PROJECT_ROOT / "data" / "datasets" / "road_damage" / "dataset_manifest.json")
    waste_manifest = str(PROJECT_ROOT / "data" / "datasets" / "waste" / "dataset_manifest.json")

    # 1. Road Damage Sweep
    road_confs = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    sweep_thresholds(
        model_path="models/yolov8s_rdd2022.pt",
        manifest_path=road_manifest,
        task_name="ROAD_DAMAGE",
        thresholds=road_confs,
        output_path="data/evaluation/threshold_sweep_road.json"
    )

    # 2. Waste Sweep
    waste_confs = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
    sweep_thresholds(
        model_path="models/taco_yolo11s.pt",
        manifest_path=waste_manifest,
        task_name="SANITATION",
        thresholds=waste_confs,
        output_path="data/evaluation/threshold_sweep_waste.json"
    )

if __name__ == "__main__":
    main()
