#!/usr/bin/env python3
"""
CIVILENS Phase 13.2 — Controlled Road Damage Detector Experiments
Evaluates:
- Baseline metrics recording (Task 1)
- Per-class confidence threshold sweeps (Task 2)
- Geometric filter ablations (Task 3)
- Resolution experiments (Task 5)
Strictly adheres to data splits: tuning on validation, testing only on held-out test.
"""

import os
import sys
import time
import json
import copy
import hashlib
import tracemalloc
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ultralytics import YOLO

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

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
    """101-point COCO-style interpolated AP calculation."""
    mrec = np.concatenate(([0.0], recalls, [1.0]))
    mpre = np.concatenate(([0.0], precisions, [0.0]))

    for i in range(len(mpre) - 1, 0, -1):
        mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])

    # 101 points
    recall_thresholds = np.linspace(0.0, 1.0, 101)
    inds = np.searchsorted(mrec, recall_thresholds, side="left")
    interp_precisions = mpre[inds]
    return float(np.mean(interp_precisions))

class RoadExperimentRunner:
    def __init__(self, model_path: str, manifest_path: str):
        self.model_path = model_path
        self.manifest_path = manifest_path
        self.model = YOLO(model_path)
        self.class_names = getattr(self.model, "names", {0: "D00", 1: "D10", 2: "D20", 3: "D40"})

        with open(manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

        self.val_records = [r for r in self.manifest["records"] if r["split"] == "val"]
        self.test_records = [r for r in self.manifest["records"] if r["split"] == "test"]

    def extract_raw_predictions(self, split: str = "val", imgsz: int = 640, base_conf: float = 0.02) -> List[Dict[str, Any]]:
        """
        Runs low-confidence inference once and caches raw predictions with timings and memory usage.
        """
        records = self.val_records if split == "val" else self.test_records
        cached = []

        tracemalloc.start()
        latencies = []

        print(f"Extracting raw predictions for {split} split (N={len(records)}, imgsz={imgsz}, base_conf={base_conf})...")
        for rec in records:
            img_path = PROJECT_ROOT / rec["image_path"]
            t0 = time.time()
            res = self.model(str(img_path), conf=base_conf, iou=0.45, imgsz=imgsz, device="cpu", verbose=False)
            elapsed_ms = (time.time() - t0) * 1000.0
            latencies.append(elapsed_ms)

            pred_boxes = []
            if res and len(res) > 0:
                for b in res[0].boxes:
                    cls_id = int(b.cls[0])
                    conf = float(b.conf[0])
                    xmin, ymin, xmax, ymax = b.xyxyn[0].tolist()
                    pred_boxes.append({
                        "class_id": cls_id,
                        "confidence": conf,
                        "bbox": [ymin, xmin, ymax, xmax]  # normalized [ymin, xmin, ymax, xmax]
                    })

            cached.append({
                "record": rec,
                "pred_boxes": pred_boxes,
                "latency_ms": elapsed_ms
            })

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"  Extraction done. Mean latency: {np.mean(latencies):.2f} ms, Peak memory: {peak / 1024 / 1024:.2f} MB")
        return cached

    def evaluate_with_filters(
        self,
        cached_preds: List[Dict[str, Any]],
        class_thresholds: Dict[int, float],
        aspect_ratio_filter: bool = False,
        min_ar_crack: float = 1.5,
        min_area_filter: bool = False,
        min_area_ratio: float = 0.003,
        match_iou_thresh: float = 0.50
    ) -> Dict[str, Any]:
        """
        Evaluates predictions with specific class thresholds and optional geometric filters.
        """
        total_tp = 0
        total_fp = 0
        total_fn = 0
        total_gt = 0

        class_stats = {c: {"gt": 0, "tp": 0, "fp": 0, "fn": 0} for c in [0, 1, 2, 3]}
        neg_images_count = 0
        neg_images_with_fp = 0

        all_detections_by_class = {c: [] for c in [0, 1, 2, 3]}

        for item in cached_preds:
            rec = item["record"]
            gt_boxes = rec.get("annotations", [])
            is_pos = rec["is_positive"]
            if not is_pos:
                neg_images_count += 1

            for g in gt_boxes:
                c = g["class_id"]
                if c in class_stats:
                    class_stats[c]["gt"] += 1
                total_gt += 1

            # Filter predictions
            filtered_boxes = []
            for p in item["pred_boxes"]:
                c = p["class_id"]
                conf = p["confidence"]
                thresh = class_thresholds.get(c, 0.15)
                if conf < thresh:
                    continue

                ymin, xmin, ymax, xmax = p["bbox"]
                w = max(0.0, xmax - xmin)
                h = max(0.0, ymax - ymin)
                area = w * h
                ar = max(w / max(h, 1e-6), h / max(w, 1e-6))

                # Geometric Filter 1: Min box area
                if min_area_filter and area < min_area_ratio:
                    continue

                # Geometric Filter 2: Crack aspect ratio (D00 and D10 only, protect D20 and D40)
                if aspect_ratio_filter and c in [0, 1]:
                    if ar < min_ar_crack:
                        continue

                filtered_boxes.append(p)

            if not is_pos and len(filtered_boxes) > 0:
                neg_images_with_fp += 1

            # Match against GT
            filtered_boxes.sort(key=lambda b: b["confidence"], reverse=True)
            gt_matched = [False] * len(gt_boxes)

            for p in filtered_boxes:
                c = p["class_id"]
                best_iou = 0.0
                best_gt_idx = -1

                for g_idx, g in enumerate(gt_boxes):
                    if not gt_matched[g_idx] and g["class_id"] == c:
                        iou = calculate_iou(p["bbox"], g["bbox_normalized"])
                        if iou > best_iou:
                            best_iou = iou
                            best_gt_idx = g_idx

                if best_iou >= match_iou_thresh and best_gt_idx >= 0:
                    total_tp += 1
                    gt_matched[best_gt_idx] = True
                    class_stats[c]["tp"] += 1
                    all_detections_by_class[c].append((p["confidence"], 1))
                else:
                    total_fp += 1
                    class_stats[c]["fp"] += 1
                    all_detections_by_class[c].append((p["confidence"], 0))

            for g_idx, matched in enumerate(gt_matched):
                if not matched:
                    total_fn += 1
                    c = gt_boxes[g_idx]["class_id"]
                    if c in class_stats:
                        class_stats[c]["fn"] += 1

        # Per-class AP50 calculation
        per_class_summary = {}
        ap_list = []
        for c in [0, 1, 2, 3]:
            s = class_stats[c]
            c_tp = s["tp"]
            c_fp = s["fp"]
            c_fn = s["fn"]
            c_gt = s["gt"]
            p = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0.0
            r = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0.0
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

            # Compute AP
            dets = all_detections_by_class[c]
            if dets and c_gt > 0:
                dets.sort(key=lambda x: x[0], reverse=True)
                acc_tp = 0
                acc_fp = 0
                rec_arr = []
                prec_arr = []
                for conf, is_tp in dets:
                    if is_tp:
                        acc_tp += 1
                    else:
                        acc_fp += 1
                    rec_arr.append(acc_tp / c_gt)
                    prec_arr.append(acc_tp / (acc_tp + acc_fp))
                ap50 = compute_ap(np.array(rec_arr), np.array(prec_arr))
            else:
                ap50 = 0.0

            if c_gt > 0:
                ap_list.append(ap50)

            per_class_summary[str(c)] = {
                "name": self.class_names.get(c, str(c)),
                "gt": c_gt,
                "tp": c_tp,
                "fp": c_fp,
                "fn": c_fn,
                "precision": round(p, 4),
                "recall": round(r, 4),
                "f1_score": round(f1, 4),
                "ap50": round(ap50, 4)
            }

        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0
        mAP50 = float(np.mean(ap_list)) if ap_list else 0.0
        hard_neg_alarm_rate = neg_images_with_fp / neg_images_count if neg_images_count > 0 else 0.0

        return {
            "class_thresholds": {str(k): round(v, 3) for k, v in class_thresholds.items()},
            "filters": {
                "aspect_ratio_filter": aspect_ratio_filter,
                "min_ar_crack": min_ar_crack,
                "min_area_filter": min_area_filter,
                "min_area_ratio": min_area_ratio
            },
            "total_gt": total_gt,
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn,
            "precision": round(overall_precision, 4),
            "recall": round(overall_recall, 4),
            "f1_score": round(overall_f1, 4),
            "mAP50": round(mAP50, 4),
            "hard_neg_alarms": neg_images_with_fp,
            "hard_neg_total": neg_images_count,
            "hard_neg_alarm_rate": round(hard_neg_alarm_rate, 4),
            "per_class": per_class_summary
        }

if __name__ == "__main__":
    runner = RoadExperimentRunner(
        model_path="models/yolov8s_rdd2022.pt",
        manifest_path="data/datasets/road_damage/dataset_manifest.json"
    )
    print("RoadExperimentRunner loaded successfully.")

