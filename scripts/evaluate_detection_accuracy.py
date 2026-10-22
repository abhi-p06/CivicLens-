#!/usr/bin/env python3
"""
CIVILENS Detection Accuracy & Evaluation Engine
Computes rigorous, reproducible object-detection metrics for civic models:
- Precision, Recall, F1-score (at IoU >= 0.50)
- True Positives, False Positives, False Negatives
- mAP@50 and mAP@50-95 (via COCO/VOC protocol)
- Hard-Negative Specificity and False Alarm Rate
- Per-class performance breakdown
- Latency statistics (mean, median, p95)
- Full machine-readable export (JSON and CSV)
- Detailed FP/FN failure case records for hard-negative analysis
"""

import os
import sys
import time
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def calculate_iou(boxA: List[float], boxB: List[float]) -> float:
    """
    Computes IoU for boxes in [ymin, xmin, ymax, xmax] format.
    """
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


def evaluate_dataset(
    model_path: str,
    manifest_path: str,
    split: str = "val",
    conf_threshold: float = 0.25,
    iou_threshold: float = 0.45,
    match_iou_thresh: float = 0.50,
    class_agnostic_matching: bool = False,
    task_name: str = "ROAD_DAMAGE"
) -> Dict[str, Any]:
    from ultralytics import YOLO

    model = YOLO(model_path)
    model_names = getattr(model, "names", {})

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    records = [r for r in manifest["records"] if r["split"] == split]
    assert records, f"No records found for split '{split}' in {manifest_path}"

    all_detections = []
    total_gt_count = 0
    total_tp = 0
    total_fp = 0
    total_fn = 0

    class_stats = {}
    latencies = []

    fp_records = []
    fn_records = []

    pos_images_count = sum(1 for r in records if r["is_positive"])
    neg_images_count = sum(1 for r in records if not r["is_positive"])
    neg_images_with_fps = 0

    for rec in records:
        img_path = PROJECT_ROOT / rec["image_path"]
        assert img_path.exists(), f"Image {img_path} does not exist!"

        gt_boxes = rec.get("annotations", [])
        total_gt_count += len(gt_boxes)

        for g in gt_boxes:
            c = g["class_id"]
            if c not in class_stats:
                class_stats[c] = {"gt": 0, "tp": 0, "fp": 0, "fn": 0}
            class_stats[c]["gt"] += 1

        # Run inference
        t0 = time.time()
        results = model(
            str(img_path),
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=640,
            device="cpu",
            verbose=False
        )
        elapsed_ms = (time.time() - t0) * 1000.0
        latencies.append(elapsed_ms)

        pred_boxes = []
        if results and len(results) > 0:
            r = results[0]
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                # convert [xmin, ymin, xmax, ymax] normalized to [ymin, xmin, ymax, xmax]
                xmin, ymin, xmax, ymax = box.xyxyn[0].tolist()
                pred_boxes.append({
                    "class_id": cls_id,
                    "confidence": conf,
                    "bbox": [ymin, xmin, ymax, xmax]
                })

        # Track FP on negative images
        if not rec["is_positive"] and len(pred_boxes) > 0:
            neg_images_with_fps += 1

        # Match predictions against ground truth
        # Sort predictions by descending confidence
        pred_boxes.sort(key=lambda b: b["confidence"], reverse=True)

        gt_matched = [False] * len(gt_boxes)
        img_fp_count = 0

        for p in pred_boxes:
            best_iou = 0.0
            best_gt_idx = -1

            for g_idx, g in enumerate(gt_boxes):
                if not gt_matched[g_idx]:
                    if class_agnostic_matching or (g["class_id"] == p["class_id"]):
                        iou = calculate_iou(p["bbox"], g["bbox_normalized"])
                        if iou > best_iou:
                            best_iou = iou
                            best_gt_idx = g_idx

            cls_key = p["class_id"]
            if cls_key not in class_stats:
                class_stats[cls_key] = {"gt": 0, "tp": 0, "fp": 0, "fn": 0}

            if best_iou >= match_iou_thresh and best_gt_idx >= 0:
                total_tp += 1
                gt_matched[best_gt_idx] = True
                class_stats[cls_key]["tp"] += 1
                all_detections.append({
                    "confidence": p["confidence"],
                    "is_tp": 1,
                    "is_fp": 0
                })
            else:
                total_fp += 1
                img_fp_count += 1
                class_stats[cls_key]["fp"] += 1
                all_detections.append({
                    "confidence": p["confidence"],
                    "is_tp": 0,
                    "is_fp": 1
                })
                fp_records.append({
                    "image_name": rec["filename"],
                    "is_negative_image": not rec["is_positive"],
                    "detected_class": p["class_id"],
                    "detected_label": model_names.get(p["class_id"], str(p["class_id"])),
                    "confidence": round(p["confidence"], 4),
                    "bbox": [round(x, 4) for x in p["bbox"]]
                })

        # Unmatched GTs are False Negatives
        for g_idx, matched in enumerate(gt_matched):
            if not matched:
                total_fn += 1
                g = gt_boxes[g_idx]
                cls_key = g["class_id"]
                class_stats[cls_key]["fn"] += 1
                fn_records.append({
                    "image_name": rec["filename"],
                    "class_id": g["class_id"],
                    "class_label": manifest.get("classes", {}).get(str(g["class_id"]), str(g["class_id"])),
                    "bbox": g["bbox_normalized"]
                })

    # Precision, Recall, F1
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Per-class metrics
    per_class_summary = {}
    for c, s in class_stats.items():
        c_tp = s["tp"]
        c_fp = s["fp"]
        c_fn = s["fn"]
        c_p = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0.0
        c_r = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0.0
        c_f1 = 2 * (c_p * c_r) / (c_p + c_r) if (c_p + c_r) > 0 else 0.0
        raw_name = model_names.get(c, str(c))
        per_class_summary[str(c)] = {
            "name": raw_name,
            "ground_truth_count": s["gt"],
            "true_positives": c_tp,
            "false_positives": c_fp,
            "false_negatives": c_fn,
            "precision": round(c_p, 4),
            "recall": round(c_r, 4),
            "f1_score": round(c_f1, 4)
        }

    # Precision-Recall curve calculation across all detections
    pr_curve = []
    if all_detections and total_gt_count > 0:
        all_detections.sort(key=lambda d: d["confidence"], reverse=True)
        acc_tp = 0
        acc_fp = 0
        for i, d in enumerate(all_detections):
            acc_tp += d["is_tp"]
            acc_fp += d["is_fp"]
            cur_p = acc_tp / (acc_tp + acc_fp)
            cur_r = acc_tp / total_gt_count
            if (i % max(1, len(all_detections) // 20)) == 0 or i == len(all_detections) - 1:
                pr_curve.append({
                    "rank": i + 1,
                    "confidence": round(d["confidence"], 4),
                    "precision": round(cur_p, 4),
                    "recall": round(cur_r, 4)
                })

    # Hard-negative false alarm rate
    hard_neg_false_alarm_rate = neg_images_with_fps / neg_images_count if neg_images_count > 0 else 0.0

    # Compute official Ultralytics mAP metrics
    dataset_yaml = Path(manifest_path).parent / ("road_damage.yaml" if "road" in str(manifest_path) else "waste.yaml")
    map50 = None
    map50_95 = None
    if dataset_yaml.exists():
        try:
            val_out = model.val(
                data=str(dataset_yaml),
                split=split,
                conf=conf_threshold,
                iou=iou_threshold,
                imgsz=640,
                device="cpu",
                verbose=False
            )
            map50 = float(val_out.box.map50)
            map50_95 = float(val_out.box.map)
        except Exception as e:
            print(f"[Warning] Ultralytics val failed: {e}")

    summary = {
        "model_path": model_path,
        "task": task_name,
        "split": split,
        "sample_count": len(records),
        "positive_images": pos_images_count,
        "negative_images": neg_images_count,
        "confidence_threshold": conf_threshold,
        "iou_nms_threshold": iou_threshold,
        "match_iou_threshold": match_iou_thresh,
        "total_ground_truth_objects": total_gt_count,
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "mAP_50": round(map50, 4) if map50 is not None else None,
        "mAP_50_95": round(map50_95, 4) if map50_95 is not None else None,
        "hard_neg_images_evaluated": neg_images_count,
        "hard_neg_images_with_false_alarms": neg_images_with_fps,
        "hard_neg_false_alarm_rate": round(hard_neg_false_alarm_rate, 4),
        "latency_ms": {
            "mean": round(float(np.mean(latencies)), 2) if latencies else 0.0,
            "median": round(float(np.median(latencies)), 2) if latencies else 0.0,
            "p95": round(float(np.percentile(latencies, 95)), 2) if latencies else 0.0
        },
        "per_class": per_class_summary,
        "pr_curve_sample": pr_curve[:10],
        "false_positives_sample": fp_records[:15],
        "false_negatives_sample": fn_records[:15]
    }

    return summary


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CIVILENS Computer Vision Accuracy Evaluator")
    parser.add_argument("--model", type=str, required=True, help="Path to YOLO model checkpoint (.pt)")
    parser.add_argument("--manifest", type=str, required=True, help="Path to dataset_manifest.json")
    parser.add_argument("--split", type=str, default="val", choices=["val", "test"])
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--iou", type=float, default=0.45, help="NMS IoU threshold")
    parser.add_argument("--task", type=str, default="ROAD_DAMAGE", choices=["ROAD_DAMAGE", "SANITATION"])
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    print(f"Evaluating {args.model} on {args.manifest} [{args.split}] at conf={args.conf}...")
    metrics = evaluate_dataset(
        model_path=args.model,
        manifest_path=args.manifest,
        split=args.split,
        conf_threshold=args.conf,
        iou_threshold=args.iou,
        task_name=args.task
    )

    print("\n" + "=" * 60)
    print(f"EVALUATION SUMMARY: {metrics['task']} ({metrics['split'].upper()} SPLIT)")
    print("=" * 60)
    print(f"• Images:               {metrics['sample_count']} ({metrics['positive_images']} pos, {metrics['negative_images']} neg)")
    print(f"• Confidence Threshold: {metrics['confidence_threshold']}")
    print(f"• Precision@50:         {metrics['precision'] * 100:.2f}%")
    print(f"• Recall@50:            {metrics['recall'] * 100:.2f}%")
    print(f"• F1-Score@50:          {metrics['f1_score'] * 100:.2f}%")
    if metrics['mAP_50'] is not None:
        print(f"• mAP@50:               {metrics['mAP_50'] * 100:.2f}%")
        print(f"• mAP@50-95:            {metrics['mAP_50_95'] * 100:.2f}%")
    print(f"• TP / FP / FN:         {metrics['true_positives']} / {metrics['false_positives']} / {metrics['false_negatives']}")
    print(f"• Hard Negative Alarms: {metrics['hard_neg_images_with_false_alarms']}/{metrics['hard_neg_images_evaluated']} ({metrics['hard_neg_false_alarm_rate']*100:.1f}%)")
    print(f"• Latency (Mean):       {metrics['latency_ms']['mean']} ms / image")

    print("\n[Per-Class Performance]")
    for cid, cinfo in metrics["per_class"].items():
        print(f"  Class {cid} ({cinfo['name']}): GT={cinfo['ground_truth_count']} | P={cinfo['precision']*100:.1f}% | R={cinfo['recall']*100:.1f}% | F1={cinfo['f1_score']*100:.1f}%")

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"\n✓ Saved metrics to {out_p}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
