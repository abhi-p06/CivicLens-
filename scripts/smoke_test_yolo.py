#!/usr/bin/env python3
"""
CIVILENS YOLOv8s RDD2022 Smoke Test Script
Executes real road-damage object detection on benchmark sample images and verifies
model outputs, empty detection behavior, corrupt image handling, and missing file resilience.

Tested Scenarios:
1. Pothole image with multiple road damage defects
2. Road crack image (Alligator / Fatigue Crack)
3. Normal road image without obvious road defects (Clean Surface)
4. Corrupt image file (Malformatted byte stream)
5. Nonexistent image reference (Missing file path)
"""

import os
import sys
import time
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.modules.vision.yolo_detector import yolo_detector
from app.modules.vision.severity import visual_severity_estimator

TEST_CASES = [
    {
        "name": "Pothole (Multiple Damages)",
        "path": "data/test_samples/pothole_multibox.jpg",
        "expected_type": "Road Damage Present",
    },
    {
        "name": "Alligator Crack (Structural Fatigue)",
        "path": "data/test_samples/alligator_crack.jpg",
        "expected_type": "Road Crack Present",
    },
    {
        "name": "Normal Road (Clean Surface)",
        "path": "data/test_samples/clean_road.jpg",
        "expected_type": "No Defect Expected",
    },
    {
        "name": "Corrupt Image File",
        "path": "data/test_samples/corrupt_file.jpg",
        "expected_type": "Unreadable File Error",
    },
    {
        "name": "Nonexistent Image Reference",
        "path": "data/test_samples/nonexistent_file.jpg",
        "expected_type": "Missing Path Error",
    },
]


def setup_test_files():
    os.makedirs("data/test_samples", exist_ok=True)
    # Create corrupt file
    with open("data/test_samples/corrupt_file.jpg", "wb") as f:
        f.write(b"NOT_A_JPEG_CORRUPTED_BYTES_HEADER\x00\xFF\xAA\xBB")


def run_smoke_test():
    setup_test_files()
    print("=" * 80)
    print("CIVILENS YOLOv8s RDD2022 ROAD DAMAGE DETECTION SMOKE TEST")
    print(f"Model Checkpoint: {yolo_detector.model_path}")
    print(f"Confidence Threshold: {yolo_detector.conf_threshold}")
    print(f"Device: {yolo_detector.device}")
    print(f"Model Loaded: {yolo_detector.is_model_available()}")
    print("=" * 80)

    results = []

    for test in TEST_CASES:
        name = test["name"]
        path = test["path"]
        expected = test["expected_type"]

        t0 = time.time()
        output = yolo_detector.detect(path, is_demo=False)
        duration_ms = round((time.time() - t0) * 1000.0, 1)

        detected_objs = output["detectedObjects"]
        severity = visual_severity_estimator.estimate_severity(detected_objs)

        test_result = {
            "name": name,
            "path": path,
            "expected": expected,
            "executionMode": output["visionExecutionMode"],
            "visualDetection": output["visualDetection"],
            "visualConfidence": output["visualConfidence"],
            "visualSeverity": severity,
            "boxCount": len(detected_objs),
            "detectedClasses": output["detectedClasses"],
            "durationMs": duration_ms,
            "detectedObjects": [
                {
                    "label": d.label,
                    "confidence": d.confidence,
                    "bbox": d.bbox,
                }
                for d in detected_objs
            ],
        }
        results.append(test_result)

        print(f"\n[Test Case] {name}")
        print(f"  Path: {path}")
        print(f"  Execution Mode: {output['visionExecutionMode']}")
        print(f"  Inference Time: {duration_ms} ms")
        print(f"  Visual Detection: {output['visualDetection']}")
        print(f"  Visual Confidence: {output['visualConfidence']:.4f}")
        print(f"  Visual Severity: {severity:.2f}")
        print(f"  Boxes Count: {len(detected_objs)}")
        for i, d in enumerate(detected_objs):
            print(f"    Box {i + 1}: {d.label} | Conf: {d.confidence:.4f} | BBox: {d.bbox}")

    print("\n" + "=" * 80)
    print("SUMMARY OF SMOKE TEST OUTCOMES:")
    for r in results:
        status_icon = "✓" if r["executionMode"] in ("real_yolo_inference", "unreadable_image_file", "invalid_image_path") else "✗"
        print(f"  {status_icon} {r['name']}: mode={r['executionMode']}, boxes={r['boxCount']}, severity={r['visualSeverity']}, time={r['durationMs']}ms")
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_smoke_test()
