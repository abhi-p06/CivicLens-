#!/usr/bin/env python3
"""
CIVILENS Phase 14 — Roboflow Hosted Model Evaluation Engine
Controlled, reproducible accuracy comparison between local and hosted models:
1. Pothole Detection: Local YOLOv8s RDD2022 vs. Roboflow Hosted YOLO26 ('potholes-krmk8/2')
2. Municipal Waste:   Local YOLO11s TACO vs. Roboflow Hosted RF-DETR Nano ('garbage_detection-wvzwv-n8vsv/1')

Adheres to:
- Strict sample limits (--sample-limit) to avoid credit exhaustion
- Identical held-out test splits and IoU matching (IoU >= 0.50)
- Preserves local model as production default
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.modules.vision.road_detector import RoadDamageDetector
from app.modules.vision.waste_detector import WasteDetector
from app.modules.vision.roboflow_adapter import roboflow_adapter

def calculate_iou(boxA: List[float], boxB: List[float]) -> float:
    # box format: [ymin, xmin, ymax, xmax]
    yA = max(boxA[0], boxB[0])
    xA = max(boxA[1], boxB[1])
    yB = min(boxA[2], boxB[2])
    xB = min(boxA[3], boxB[3])

    inter_w = max(0.0, xB - xA)
    inter_h = max(0.0, yB - yA)
    inter_area = inter_w * inter_h

    boxA_area = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
    boxB_area = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])

    union_area = boxA_area + boxB_area - inter_area
    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area

def compute_ap(recalls: np.ndarray, precisions: np.ndarray) -> float:
    mrec = np.concatenate(([0.0], recalls, [1.0]))
    mpre = np.concatenate(([0.0], precisions, [0.0]))
    for i in range(len(mpre) - 1, 0, -1):
        mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])
    recall_thresholds = np.linspace(0.0, 1.0, 101)
    inds = np.searchsorted(mrec, recall_thresholds, side="left")
    interp_precisions = mpre[inds]
    return float(np.mean(interp_precisions))

def evaluate_pothole_subsystem(
    manifest_path: str,
    split: str = "test",
    sample_limit: int = 10,
    conf_threshold: float = 0.25,
    match_iou: float = 0.50
) -> Dict[str, Any]:
    print("\n" + "="*70)
    print("EVALUATING ROAD / POTHOLE DETECTOR: LOCAL vs. ROBOFLOW HOSTED")
    print("="*70)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    records = [r for r in manifest["records"] if r["split"] == split]
    pos_recs = [r for r in records if r["is_positive"] and any(a["class_id"] == 3 for a in r.get("annotations", []))]
    neg_recs = [r for r in records if not r["is_positive"]]

    # Take balanced subset up to sample_limit
    half_limit = max(1, sample_limit // 2)
    eval_records = pos_recs[:half_limit] + neg_recs[:half_limit]
    print(f"Selected {len(eval_records)} evaluation images ({len(pos_recs[:half_limit])} pothole pos, {len(neg_recs[:half_limit])} clean neg)")

    local_model = RoadDamageDetector()

    # Track metrics
    stats = {
        "local": {"tp": 0, "fp": 0, "fn": 0, "gt": 0, "latencies": [], "neg_fps": 0, "neg_count": 0, "detections": []},
        "hosted": {"tp": 0, "fp": 0, "fn": 0, "gt": 0, "latencies": [], "neg_fps": 0, "neg_count": 0, "detections": [], "api_failures": 0, "new_api_calls": 0}
    }

    for rec in eval_records:
        img_path = str(PROJECT_ROOT / rec["image_path"])
        is_pos = rec["is_positive"]
        # Ground truth pothole boxes (class_id == 3: D40)
        gt_boxes = [a["bbox_normalized"] for a in rec.get("annotations", []) if a["class_id"] == 3]
        stats["local"]["gt"] += len(gt_boxes)
        stats["hosted"]["gt"] += len(gt_boxes)

        if not is_pos:
            stats["local"]["neg_count"] += 1
            stats["hosted"]["neg_count"] += 1

        # 1. Local Model
        t0 = time.time()
        loc_res = local_model.detect(img_path)
        loc_lat = (time.time() - t0) * 1000.0
        stats["local"]["latencies"].append(loc_lat)
        loc_preds = [
            d for d in loc_res.get("detectedObjects", [])
            if d.confidence >= conf_threshold and getattr(d, "class_id", None) == 3
        ]

        # 2. Hosted Model
        host_res = roboflow_adapter.infer(img_path, category_hint="Roads & Footpaths")
        if host_res.get("status") == "ERROR":
            stats["hosted"]["api_failures"] += 1
        if not host_res.get("cached", False):
            stats["hosted"]["new_api_calls"] += 1
        stats["hosted"]["latencies"].append(host_res.get("inferenceTimeMs", 0.0))
        host_preds = [
            d for d in host_res.get("detectedObjects", [])
            if d.confidence >= conf_threshold
        ]

        # Evaluate Local D40 Pothole Matching
        _match_boxes(loc_preds, gt_boxes, match_iou, stats["local"], is_pos)

        # Evaluate Hosted Pothole Matching
        _match_boxes(host_preds, gt_boxes, match_iou, stats["hosted"], is_pos)

    local_summary = _compute_summary(stats["local"], "YOLOv8s RDD2022 (Local D40)")
    hosted_summary = _compute_summary(stats["hosted"], f"{settings.roboflow_pothole_model_id} (Roboflow Hosted)")
    hosted_summary["new_api_calls_credits"] = stats["hosted"]["new_api_calls"]
    hosted_summary["api_failure_count"] = stats["hosted"]["api_failures"]

    return {
        "task": "ROAD_DAMAGE",
        "primary_defect": "Pothole (D40)",
        "sample_count": len(eval_records),
        "local": local_summary,
        "hosted": hosted_summary
    }

def evaluate_waste_subsystem(
    manifest_path: str,
    split: str = "test",
    sample_limit: int = 10,
    conf_threshold: float = 0.25,
    match_iou: float = 0.50
) -> Dict[str, Any]:
    print("\n" + "="*70)
    print("EVALUATING MUNICIPAL WASTE DETECTOR: LOCAL vs. ROBOFLOW HOSTED")
    print("="*70)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    records = [r for r in manifest["records"] if r["split"] == split]
    pos_recs = [r for r in records if r["is_positive"]]
    neg_recs = [r for r in records if not r["is_positive"]]

    half_limit = max(1, sample_limit // 2)
    eval_records = pos_recs[:half_limit] + neg_recs[:half_limit]
    print(f"Selected {len(eval_records)} evaluation images ({len(pos_recs[:half_limit])} waste pos, {len(neg_recs[:half_limit])} clean neg)")

    local_model = WasteDetector()

    stats = {
        "local": {"tp": 0, "fp": 0, "fn": 0, "gt": 0, "latencies": [], "neg_fps": 0, "neg_count": 0, "detections": []},
        "hosted": {"tp": 0, "fp": 0, "fn": 0, "gt": 0, "latencies": [], "neg_fps": 0, "neg_count": 0, "detections": [], "api_failures": 0, "new_api_calls": 0}
    }

    for rec in eval_records:
        img_path = str(PROJECT_ROOT / rec["image_path"])
        is_pos = rec["is_positive"]
        gt_boxes = [a["bbox_normalized"] for a in rec.get("annotations", [])]
        stats["local"]["gt"] += len(gt_boxes)
        stats["hosted"]["gt"] += len(gt_boxes)

        if not is_pos:
            stats["local"]["neg_count"] += 1
            stats["hosted"]["neg_count"] += 1

        # Local Model
        t0 = time.time()
        loc_res = local_model.detect(img_path)
        loc_lat = (time.time() - t0) * 1000.0
        stats["local"]["latencies"].append(loc_lat)
        loc_preds = [
            d for d in loc_res.get("detectedObjects", [])
            if d.confidence >= conf_threshold
        ]

        # Hosted Model
        host_res = roboflow_adapter.infer(img_path, category_hint="Sanitation & Garbage")
        if host_res.get("status") == "ERROR":
            stats["hosted"]["api_failures"] += 1
        if not host_res.get("cached", False):
            stats["hosted"]["new_api_calls"] += 1
        stats["hosted"]["latencies"].append(host_res.get("inferenceTimeMs", 0.0))
        host_preds = [
            d for d in host_res.get("detectedObjects", [])
            if d.confidence >= conf_threshold
        ]

        _match_boxes(loc_preds, gt_boxes, match_iou, stats["local"], is_pos)
        _match_boxes(host_preds, gt_boxes, match_iou, stats["hosted"], is_pos)

    local_summary = _compute_summary(stats["local"], "YOLO11s TACO (Local Waste)")
    hosted_summary = _compute_summary(stats["hosted"], f"{settings.roboflow_garbage_model_id} (Roboflow Hosted)")
    hosted_summary["new_api_calls_credits"] = stats["hosted"]["new_api_calls"]
    hosted_summary["api_failure_count"] = stats["hosted"]["api_failures"]

    return {
        "task": "SANITATION",
        "primary_defect": "Municipal Waste / Litter",
        "sample_count": len(eval_records),
        "local": local_summary,
        "hosted": hosted_summary
    }

def _match_boxes(pred_objects, gt_boxes, match_iou, target_stats, is_pos):
    preds = sorted(pred_objects, key=lambda x: x.confidence, reverse=True)
    gt_matched = [False] * len(gt_boxes)

    if not is_pos and len(preds) > 0:
        target_stats["neg_fps"] += 1

    for p in preds:
        best_iou = 0.0
        best_idx = -1
        for g_idx, g in enumerate(gt_boxes):
            if not gt_matched[g_idx]:
                iou = calculate_iou(p.bbox, g)
                if iou > best_iou:
                    best_iou = iou
                    best_idx = g_idx

        if best_iou >= match_iou and best_idx >= 0:
            target_stats["tp"] += 1
            gt_matched[best_idx] = True
            target_stats["detections"].append((p.confidence, 1))
        else:
            target_stats["fp"] += 1
            target_stats["detections"].append((p.confidence, 0))

    for matched in gt_matched:
        if not matched:
            target_stats["fn"] += 1

def _compute_summary(s: Dict[str, Any], model_name: str) -> Dict[str, Any]:
    tp = s["tp"]
    fp = s["fp"]
    fn = s["fn"]
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    # AP
    dets = s["detections"]
    if dets and s["gt"] > 0:
        dets.sort(key=lambda x: x[0], reverse=True)
        acc_tp = 0
        acc_fp = 0
        recs, precs = [], []
        for conf, is_tp in dets:
            if is_tp:
                acc_tp += 1
            else:
                acc_fp += 1
            recs.append(acc_tp / s["gt"])
            precs.append(acc_tp / (acc_tp + acc_fp))
        map50 = compute_ap(np.array(recs), np.array(precs))
    else:
        map50 = 0.0

    neg_rate = s["neg_fps"] / s["neg_count"] if s["neg_count"] > 0 else 0.0

    return {
        "model_name": model_name,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1_score": round(f1, 4),
        "mAP50": round(map50, 4),
        "clean_neg_alarms": s["neg_fps"],
        "clean_neg_total": s["neg_count"],
        "clean_neg_alarm_rate": round(neg_rate, 4),
        "latency_ms": {
            "mean": round(float(np.mean(s["latencies"])), 2) if s["latencies"] else 0.0,
            "median": round(float(np.median(s["latencies"])), 2) if s["latencies"] else 0.0
        }
    }

def main():
    parser = argparse.ArgumentParser(description="CIVILENS Phase 14: Roboflow Hosted Model Evaluation")
    parser.add_argument("--sample-limit", type=int, default=10, help="Max images to evaluate per category (preserves free credits)")
    parser.add_argument("--split", type=str, default="test", choices=["val", "test"], help="Dataset split to evaluate")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--output", type=str, default="data/evaluation/roboflow_evaluation_report.json", help="Output path")
    args = parser.parse_args()

    road_manifest = str(PROJECT_ROOT / "data" / "datasets" / "road_damage" / "dataset_manifest.json")
    waste_manifest = str(PROJECT_ROOT / "data" / "datasets" / "waste" / "dataset_manifest.json")

    pothole_results = evaluate_pothole_subsystem(
        manifest_path=road_manifest,
        split=args.split,
        sample_limit=args.sample_limit,
        conf_threshold=args.conf
    )

    waste_results = evaluate_waste_subsystem(
        manifest_path=waste_manifest,
        split=args.split,
        sample_limit=args.sample_limit,
        conf_threshold=args.conf
    )

    # Print Comparison Table
    print("\n" + "="*110)
    print(f"CIVILENS PHASE 14: LOCAL VS. HOSTED ROBOFLOW BENCHMARK ({args.split.upper()} SPLIT)")
    print("="*110)
    print(f"{'Task / Defect':<22} | {'Model Name':<35} | {'Prec':<7} | {'Recall':<7} | {'F1':<7} | {'mAP50':<7} | {'Lat(ms)':<8} | {'Neg Alarms':<10}")
    print("-" * 110)

    for item in [pothole_results, waste_results]:
        tname = item["primary_defect"]
        for mkey in ["local", "hosted"]:
            m = item[mkey]
            neg_s = f"{m['clean_neg_alarms']}/{m['clean_neg_total']}"
            print(f"{tname:<22} | {m['model_name']:<35} | {m['precision']*100:<6.1f}% | {m['recall']*100:<6.1f}% | {m['f1_score']*100:<6.1f}% | {m['mAP50']*100:<6.1f}% | {m['latency_ms']['mean']:<8.1f} | {neg_s:<10}")

    out_p = Path(args.output)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump({
            "split": args.split,
            "sample_limit_per_category": args.sample_limit,
            "confidence_threshold": args.conf,
            "results": {
                "road_damage": pothole_results,
                "sanitation": waste_results
            }
        }, f, indent=2)

    print(f"\n✓ Saved evaluation report to {out_p}")

if __name__ == "__main__":
    main()

