#!/usr/bin/env python3
"""
CIVILENS Performance Profiling Script
Measures actual wall-clock latencies in milliseconds for key system pipelines.
"""

import time
import statistics
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.models.issue import IssueCreate, Issue
from app.core.pipeline import pipeline
from app.modules.nlp.classifier import nlp_classifier
from app.modules.vision.yolo_detector import yolo_detector
from app.core.demo_store import demo_store
from app.modules.spatiotemporal.hotspot import hotspot_detector
from app.modules.spatiotemporal.recurring import recurring_detector
from app.modules.lifecycle.tracker import lifecycle_tracker


def measure(name, func, iterations=10, warmup=2):
    for _ in range(warmup):
        func()
    
    times_ms = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        func()
        t1 = time.perf_counter()
        times_ms.append((t1 - t0) * 1000.0)
    
    mean_lat = statistics.mean(times_ms)
    median_lat = statistics.median(times_ms)
    min_lat = min(times_ms)
    max_lat = max(times_ms)
    
    print(f"| {name:<38} | {mean_lat:8.2f} ms | {median_lat:8.2f} ms | {min_lat:8.2f} ms | {max_lat:8.2f} ms | {iterations:5d} runs |")
    return {
        "mean_ms": round(mean_lat, 2),
        "median_ms": round(median_lat, 2),
        "min_ms": round(min_lat, 2),
        "max_ms": round(max_lat, 2),
        "iterations": iterations
    }


def main():
    print("=" * 95)
    print("CIVILENS PERFORMANCE LATENCY BENCHMARK (MEASURED ON CURRENT HARDWARE)")
    print("=" * 95)
    print(f"| {'Pipeline Subsystem':<38} | {'Mean Latency':<11} | {'Median':<11} | {'Min':<11} | {'Max':<11} | {'Runs':<10} |")
    print("|" + "-" * 40 + "|" + "-" * 13 + "|" + "-" * 13 + "|" + "-" * 13 + "|" + "-" * 13 + "|" + "-" * 12 + "|")

    # 1. NLP Classification
    sample_text = "Massive deep pothole on Somaiya Vidyavihar campus approach road damaging vehicles."
    nlp_res = measure("1. NLP Classification", lambda: nlp_classifier.analyze(sample_text), iterations=20)

    # 2. YOLO Vision Inference
    sample_image = "data/test_samples/repair_pothole_before.jpg"
    yolo_res = measure("2. YOLOv8s Road Damage Inference", lambda: yolo_detector.detect(sample_image), iterations=10)

    # 3. Complete Complaint Analysis Pipeline
    sample_payload = IssueCreate(
        complaintText=sample_text,
        location="Vidyavihar",
        imageUrl=sample_image,
        source="benchmark_script"
    )
    pipeline_res = measure("3. Complete Complaint Analysis", lambda: pipeline.analyze(sample_payload), iterations=10)

    # 4. SQLite Issue Listing
    list_res = measure("4. SQLite Issue Listing", lambda: demo_store.list_issues(), iterations=30)

    # 5. Spatiotemporal Hotspot Detection
    issues = demo_store.list_issues()
    hotspot_res = measure("5. Spatiotemporal Hotspot Detection", lambda: hotspot_detector.detect_hotspots(issues), iterations=20)

    # 6. Recurring Issue Detection
    first = issues[0] if issues else None
    rec_res = measure(
        "6. Recurring Issue Detection",
        lambda: recurring_detector.evaluate_recurrence(
            lat=first.latitude,
            lng=first.longitude,
            category=first.category,
            location_name=first.location,
            existing_issues=issues
        ),
        iterations=20
    )

    # 7. Resolution Verification (Dual YOLO + OpenCV)
    if first:
        first.imageUrl = sample_image
        res_verif = measure(
            "7. CV Resolution Verification",
            lambda: lifecycle_tracker.verify_resolution(
                issue=first,
                inspector_id="PERF-INSP",
                resolution_image_url="data/test_samples/repair_pothole_after_repaired.jpg"
            ),
            iterations=10
        )

    print("=" * 95)


if __name__ == "__main__":
    main()
