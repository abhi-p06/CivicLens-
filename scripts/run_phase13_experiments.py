#!/usr/bin/env python3
"""
CIVILENS Phase 13.2 Runner
Executes Tasks 1, 2, 3, and 5 and exports structured results.
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
    print("="*70)
    print("CIVILENS PHASE 13.2: ROAD DETECTOR EXPERIMENT SUITE")
    print("="*70)

    model_path = "models/yolov8s_rdd2022.pt"
    backup_path = "models/baseline_checkpoints/yolov8s_rdd2022.pt"
    manifest_path = "data/datasets/road_damage/dataset_manifest.json"

    # Task 1: Record baseline provenance
    model_p = Path(model_path)
    backup_p = Path(backup_path)
    assert model_p.exists(), f"Missing {model_p}"
    assert backup_p.exists(), f"Missing backup {backup_p}"

    h_active = compute_sha256(model_p)
    h_backup = compute_sha256(backup_p)
    print(f"[Task 1] Active checkpoint SHA-256: {h_active}")
    print(f"[Task 1] Backup checkpoint SHA-256: {h_backup}")
    assert h_active == h_backup, "Checksum mismatch between active and backup!"

    runner = RoadExperimentRunner(model_path=model_path, manifest_path=manifest_path)

    # Cache raw predictions at conf=0.02, imgsz=640 on VALIDATION split
    print("\n[Caching] Running raw low-threshold prediction cache (imgsz=640, conf=0.02)...")
    val_cached_640 = runner.extract_raw_predictions(split="val", imgsz=640, base_conf=0.02)

    # -------------------------------------------------------------
    # Task 2: Per-Class Threshold Experiments (Validation Split Only)
    # -------------------------------------------------------------
    print("\n" + "="*70)
    print("TASK 2: PER-CLASS THRESHOLD EXPERIMENTS (VAL SPLIT)")
    print("="*70)

    threshold_configs = [
        {"name": "Baseline Uniform (0.15)", "th": {0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15}},
        {"name": "Uniform 0.10", "th": {0: 0.10, 1: 0.10, 2: 0.10, 3: 0.10}},
        {"name": "Uniform 0.20", "th": {0: 0.20, 1: 0.20, 2: 0.20, 3: 0.20}},
        {"name": "Uniform 0.25", "th": {0: 0.25, 1: 0.25, 2: 0.25, 3: 0.25}},
        {"name": "Uniform 0.30", "th": {0: 0.30, 1: 0.30, 2: 0.30, 3: 0.30}},
        {"name": "Roadmap Candidate (D00=0.22, D10=0.22, D20=0.20, D40=0.35)", "th": {0: 0.22, 1: 0.22, 2: 0.20, 3: 0.35}},
        {"name": "Roadmap Alt A (D00=0.20, D10=0.20, D20=0.20, D40=0.35)", "th": {0: 0.20, 1: 0.20, 2: 0.20, 3: 0.35}},
        {"name": "Roadmap Alt B (D00=0.25, D10=0.25, D20=0.20, D40=0.40)", "th": {0: 0.25, 1: 0.25, 2: 0.20, 3: 0.40}},
        {"name": "Roadmap Alt C (D00=0.18, D10=0.18, D20=0.18, D40=0.30)", "th": {0: 0.18, 1: 0.18, 2: 0.18, 3: 0.30}},
        {"name": "High Precision (D00=0.25, D10=0.25, D20=0.25, D40=0.45)", "th": {0: 0.25, 1: 0.25, 2: 0.25, 3: 0.45}},
        {"name": "High Recall (D00=0.12, D10=0.12, D20=0.15, D40=0.25)", "th": {0: 0.12, 1: 0.12, 2: 0.15, 3: 0.25}}
    ]

    # Individual class sweeps (holding others at baseline 0.15)
    for d40_t in [0.10, 0.20, 0.30, 0.35, 0.40, 0.50]:
        threshold_configs.append({
            "name": f"Sweep D40={d40_t:.2f} (others=0.15)",
            "th": {0: 0.15, 1: 0.15, 2: 0.15, 3: d40_t}
        })
    for d20_t in [0.10, 0.15, 0.20, 0.25, 0.30]:
        threshold_configs.append({
            "name": f"Sweep D20={d20_t:.2f} (others=0.15)",
            "th": {0: 0.15, 1: 0.15, 2: d20_t, 3: 0.15}
        })
    for d00_t in [0.10, 0.15, 0.20, 0.25, 0.30]:
        threshold_configs.append({
            "name": f"Sweep D00={d00_t:.2f} (others=0.15)",
            "th": {0: d00_t, 1: 0.15, 2: 0.15, 3: 0.15}
        })

    task2_results = []
    print(f"{'Config Name':<42} | {'Prec':<7} | {'Recall':<7} | {'F1':<7} | {'mAP50':<7} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Neg Alarms':<12}")
    print("-" * 105)

    for cfg in threshold_configs:
        res = runner.evaluate_with_filters(
            cached_preds=val_cached_640,
            class_thresholds=cfg["th"],
            aspect_ratio_filter=False,
            min_area_filter=False
        )
        res["config_name"] = cfg["name"]
        task2_results.append(res)
        neg_s = f"{res['hard_neg_alarms']}/{res['hard_neg_total']} ({res['hard_neg_alarm_rate']*100:.1f}%)"
        print(f"{cfg['name']:<42} | {res['precision']*100:<6.2f}% | {res['recall']*100:<6.2f}% | {res['f1_score']*100:<6.2f}% | {res['mAP50']*100:<6.2f}% | {res['tp']:<4} | {res['fp']:<4} | {res['fn']:<4} | {neg_s:<12}")

    # -------------------------------------------------------------
    # Task 3: Geometric Filter Ablations (Validation Split Only)
    # -------------------------------------------------------------
    print("\n" + "="*70)
    print("TASK 3: GEOMETRIC FILTER ABLATION (VAL SPLIT)")
    print("="*70)

    # Test under two baseline threshold conditions:
    # A: Baseline uniform 0.15
    # B: Roadmap candidate (D00=0.22, D10=0.22, D20=0.20, D40=0.35)
    geo_test_cases = [
        {"desc": "Uniform 0.15 - Condition 1: No Geometric Filter", "th": {0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15}, "ar": False, "ar_val": 1.5, "area": False, "area_val": 0.003},
        {"desc": "Uniform 0.15 - Condition 2: Crack Aspect Ratio (AR >= 1.5, D00/D10)", "th": {0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15}, "ar": True, "ar_val": 1.5, "area": False, "area_val": 0.003},
        {"desc": "Uniform 0.15 - Condition 2b: Crack Aspect Ratio (AR >= 1.2, D00/D10)", "th": {0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15}, "ar": True, "ar_val": 1.2, "area": False, "area_val": 0.003},
        {"desc": "Uniform 0.15 - Condition 2c: Crack Aspect Ratio (AR >= 1.8, D00/D10)", "th": {0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15}, "ar": True, "ar_val": 1.8, "area": False, "area_val": 0.003},
        {"desc": "Uniform 0.15 - Condition 3: Min Box Area (Area >= 0.3% / 0.003)", "th": {0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15}, "ar": False, "ar_val": 1.5, "area": True, "area_val": 0.003},
        {"desc": "Uniform 0.15 - Condition 3b: Min Box Area (Area >= 0.1% / 0.001)", "th": {0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15}, "ar": False, "ar_val": 1.5, "area": True, "area_val": 0.001},
        {"desc": "Uniform 0.15 - Condition 4: Both Filters (AR >= 1.5 & Area >= 0.003)", "th": {0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15}, "ar": True, "ar_val": 1.5, "area": True, "area_val": 0.003},

        {"desc": "Roadmap Candidate - Condition 1: No Geometric Filter", "th": {0: 0.22, 1: 0.22, 2: 0.20, 3: 0.35}, "ar": False, "ar_val": 1.5, "area": False, "area_val": 0.003},
        {"desc": "Roadmap Candidate - Condition 2: Crack Aspect Ratio (AR >= 1.5)", "th": {0: 0.22, 1: 0.22, 2: 0.20, 3: 0.35}, "ar": True, "ar_val": 1.5, "area": False, "area_val": 0.003},
        {"desc": "Roadmap Candidate - Condition 3: Min Box Area (Area >= 0.003)", "th": {0: 0.22, 1: 0.22, 2: 0.20, 3: 0.35}, "ar": False, "ar_val": 1.5, "area": True, "area_val": 0.003},
        {"desc": "Roadmap Candidate - Condition 4: Both Filters (AR >= 1.5 & Area >= 0.003)", "th": {0: 0.22, 1: 0.22, 2: 0.20, 3: 0.35}, "ar": True, "ar_val": 1.5, "area": True, "area_val": 0.003},
    ]

    task3_results = []
    print(f"{'Filter Condition':<55} | {'Prec':<7} | {'Recall':<7} | {'F1':<7} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Neg Alarms':<12}")
    print("-" * 115)

    for gc in geo_test_cases:
        res = runner.evaluate_with_filters(
            cached_preds=val_cached_640,
            class_thresholds=gc["th"],
            aspect_ratio_filter=gc["ar"],
            min_ar_crack=gc["ar_val"],
            min_area_filter=gc["area"],
            min_area_ratio=gc["area_val"]
        )
        res["condition_desc"] = gc["desc"]
        task3_results.append(res)
        neg_s = f"{res['hard_neg_alarms']}/{res['hard_neg_total']} ({res['hard_neg_alarm_rate']*100:.1f}%)"
        print(f"{gc['desc']:<55} | {res['precision']*100:<6.2f}% | {res['recall']*100:<6.2f}% | {res['f1_score']*100:<6.2f}% | {res['tp']:<4} | {res['fp']:<4} | {res['fn']:<4} | {neg_s:<12}")

    # -------------------------------------------------------------
    # Task 5: Inference-Resolution Experiments (640 vs 960)
    # -------------------------------------------------------------
    print("\n" + "="*70)
    print("TASK 5: INFERENCE RESOLUTION EXPERIMENTS (640 vs 960 on VAL SPLIT)")
    print("="*70)

    print("Extracting predictions at imgsz=960...")
    val_cached_960 = runner.extract_raw_predictions(split="val", imgsz=960, base_conf=0.02)

    # Measure timings for 640 vs 960
    lat_640 = [item["latency_ms"] for item in val_cached_640]
    lat_960 = [item["latency_ms"] for item in val_cached_960]

    # Evaluate at baseline conf=0.15
    res_640_baseline = runner.evaluate_with_filters(
        cached_preds=val_cached_640,
        class_thresholds={0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15}
    )
    res_960_baseline = runner.evaluate_with_filters(
        cached_preds=val_cached_960,
        class_thresholds={0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15}
    )

    # Evaluate at calibrated roadmap candidate
    res_640_roadmap = runner.evaluate_with_filters(
        cached_preds=val_cached_640,
        class_thresholds={0: 0.22, 1: 0.22, 2: 0.20, 3: 0.35}
    )
    res_960_roadmap = runner.evaluate_with_filters(
        cached_preds=val_cached_960,
        class_thresholds={0: 0.22, 1: 0.22, 2: 0.20, 3: 0.35}
    )

    task5_results = {
        "640": {
            "baseline": res_640_baseline,
            "roadmap": res_640_roadmap,
            "latency": {
                "mean_ms": round(float(np.mean(lat_640)), 2),
                "median_ms": round(float(np.median(lat_640)), 2),
                "p95_ms": round(float(np.percentile(lat_640, 95)), 2)
            }
        },
        "960": {
            "baseline": res_960_baseline,
            "roadmap": res_960_roadmap,
            "latency": {
                "mean_ms": round(float(np.mean(lat_960)), 2),
                "median_ms": round(float(np.median(lat_960)), 2),
                "p95_ms": round(float(np.percentile(lat_960, 95)), 2)
            }
        }
    }

    print("\nResolution Comparison Summary (conf=0.15 baseline):")
    print(f"  • 640px: Precision={res_640_baseline['precision']*100:.2f}%, Recall={res_640_baseline['recall']*100:.2f}%, F1={res_640_baseline['f1_score']*100:.2f}%, TP={res_640_baseline['tp']}, FP={res_640_baseline['fp']}, FN={res_640_baseline['fn']}, Neg Alarms={res_640_baseline['hard_neg_alarms']}/50 ({res_640_baseline['hard_neg_alarm_rate']*100:.1f}%), Latency Mean={task5_results['640']['latency']['mean_ms']}ms")
    print(f"  • 960px: Precision={res_960_baseline['precision']*100:.2f}%, Recall={res_960_baseline['recall']*100:.2f}%, F1={res_960_baseline['f1_score']*100:.2f}%, TP={res_960_baseline['tp']}, FP={res_960_baseline['fp']}, FN={res_960_baseline['fn']}, Neg Alarms={res_960_baseline['hard_neg_alarms']}/50 ({res_960_baseline['hard_neg_alarm_rate']*100:.1f}%), Latency Mean={task5_results['960']['latency']['mean_ms']}ms")

    # Save all results to JSON
    out_dir = PROJECT_ROOT / "data" / "evaluation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "phase13_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "task1_baseline_hash": h_active,
            "task2_threshold_experiments": task2_results,
            "task3_geometric_ablations": task3_results,
            "task5_resolution_experiments": task5_results
        }, f, indent=2)
    print(f"\n✓ Saved Task 2, 3, 5 results to {out_file}")

if __name__ == "__main__":
    main()

