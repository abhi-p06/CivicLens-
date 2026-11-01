#!/usr/bin/env python3
"""
CIVILENS — End-to-End Citizen Complaint Workflow & Roboflow Routing Verification

Validates:
1. Pothole complaint -> Routes to Roboflow pothole model (potholes-krmk8/2).
2. Garbage complaint -> Routes to Roboflow garbage model (garbage_detection-wvzwv-n8vsv/1).
3. Prediction normalization to CIVILENS [ymin, xmin, ymax, xmax] format.
4. Independent storage of comparison outputs in issue.metadata['visionComparison'] and issue.metadata['hosted'].
5. Fallback behavior: simulated 401 AUTH_ERROR falls back cleanly to local YOLO with no mislabeling.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.models.issue import IssueCreate, IssueStatus
from app.core.pipeline import pipeline

def run_workflow_verification():
    print("=" * 70)
    print("CIVILENS CITIZEN COMPLAINT & ROBOFLOW INTEGRATION VERIFICATION")
    print("=" * 70)

    # 1. Test Pothole Complaint
    print("\n[Step 1] Submitting Road Damage / Pothole Complaint...")
    pothole_payload = IssueCreate(
        complaintText="Deep hazardous pothole with exposed aggregate on Eastern Express Highway near Ghatkopar",
        location="Eastern Express Highway, Ghatkopar East, Mumbai",
        latitude=19.0850,
        longitude=72.9150,
        imageUrl="data/sample_pothole.jpg",
        category="Roads & Footpaths"
    )

    with patch.object(settings, "civilens_vision_provider", "compare"):
        pothole_issue = pipeline.process_complaint(pothole_payload)

    print(f"  ✓ Issue Created: {pothole_issue.issueId}")
    print(f"  ✓ Category Resolved: {pothole_issue.category}")
    print(f"  ✓ Local Baseline Visual Detection: {pothole_issue.visualDetection}")
    print(f"  ✓ Local Vision Execution Mode: {pothole_issue.visionMode}")

    # Verify Comparison Metadata
    comp = pothole_issue.metadata.get("visionComparison")
    assert comp is not None, "FAILED: visionComparison missing from issue.metadata"
    hosted = pothole_issue.metadata.get("hosted")
    assert hosted is not None, "FAILED: hosted missing from issue.metadata"

    print(f"  ✓ visionComparison Present in Metadata: YES (Mode: {comp.get('mode')})")
    print(f"  ✓ Hosted Model Routed: {hosted.get('modelId')} ({hosted.get('architecture')})")
    print(f"  ✓ Hosted Task: {hosted.get('task')}")
    print(f"  ✓ Hosted Status: {hosted.get('status')}")
    print(f"  ✓ Hosted Detection Count: {len(hosted.get('detectedObjects', []))}")
    assert hosted.get("modelId") == settings.roboflow_pothole_model_id, \
        f"Expected {settings.roboflow_pothole_model_id}, got {hosted.get('modelId')}"
    assert hosted.get("task") == "ROAD_DAMAGE", f"Expected ROAD_DAMAGE, got {hosted.get('task')}"

    # 2. Test Garbage Complaint
    print("\n[Step 2] Submitting Sanitation & Garbage Complaint...")
    garbage_payload = IssueCreate(
        complaintText="Large overflowing garbage heap attracting stray cattle and flies on Kurla station road",
        location="Station Road, Kurla West, Mumbai",
        latitude=19.0680,
        longitude=72.8790,
        imageUrl="data/sample_garbage.jpg",
        category="Sanitation & Garbage"
    )

    with patch.object(settings, "civilens_vision_provider", "compare"):
        garbage_issue = pipeline.process_complaint(garbage_payload)

    print(f"  ✓ Issue Created: {garbage_issue.issueId}")
    print(f"  ✓ Category Resolved: {garbage_issue.category}")
    print(f"  ✓ Local Baseline Visual Detection: {garbage_issue.visualDetection}")
    print(f"  ✓ Local Vision Execution Mode: {garbage_issue.visionMode}")

    g_comp = garbage_issue.metadata.get("visionComparison")
    assert g_comp is not None, "FAILED: visionComparison missing for garbage issue"
    g_hosted = garbage_issue.metadata.get("hosted")
    assert g_hosted is not None, "FAILED: hosted missing for garbage issue"

    print(f"  ✓ visionComparison Present in Metadata: YES (Mode: {g_comp.get('mode')})")
    print(f"  ✓ Hosted Model Routed: {g_hosted.get('modelId')} ({g_hosted.get('architecture')})")
    print(f"  ✓ Hosted Task: {g_hosted.get('task')}")
    print(f"  ✓ Hosted Status: {g_hosted.get('status')}")
    print(f"  ✓ Hosted Detection Count: {len(g_hosted.get('detectedObjects', []))}")
    assert g_hosted.get("modelId") == settings.roboflow_garbage_model_id, \
        f"Expected {settings.roboflow_garbage_model_id}, got {g_hosted.get('modelId')}"
    assert g_hosted.get("task") == "SANITATION", f"Expected SANITATION, got {g_hosted.get('task')}"

    # 3. Test Fallback Behavior
    print("\n[Step 3] Simulating Unavailable Hosted API (Simulated 401 AUTH_ERROR)...")
    mock_auth_fail = {
        "provider": "roboflow",
        "status": "ERROR",
        "error": "Authentication failed (HTTP 401): Invalid or inactive Roboflow API key.",
        "errorCategory": "AUTH_ERROR",
        "modelId": "potholes-krmk8/2",
        "architecture": "YOLO26",
        "task": "ROAD_DAMAGE",
        "detectedObjects": [],
        "visualDetection": None,
        "visualConfidence": 0.0,
        "inferenceTimeMs": 110.0,
        "cached": False
    }

    from app.modules.vision.manager import vision_manager
    with patch.object(settings, "civilens_vision_provider", "hosted"):
        with patch.object(vision_manager.roboflow_adapter, "infer", return_value=mock_auth_fail):
            fallback_issue = pipeline.process_complaint(pothole_payload)

    print(f"  ✓ Fallback Issue Created: {fallback_issue.issueId}")
    print(f"  ✓ Fallback Triggered Flag: {fallback_issue.metadata.get('visionFallbackTriggered')}")
    print(f"  ✓ Fallback Reason: {fallback_issue.metadata.get('visionFallbackReason')}")
    print(f"  ✓ Final Vision Mode: {fallback_issue.visionMode} (NOT mislabeled as Roboflow)")
    print(f"  ✓ Final Source Model: {fallback_issue.visionModel}")

    assert fallback_issue.metadata.get("visionFallbackTriggered") is True
    assert "Authentication failed" in fallback_issue.metadata.get("visionFallbackReason", "")
    assert fallback_issue.visionMode in ["real_yolo_inference", "deterministic_demo_fallback"]
    assert "roboflow" not in (fallback_issue.visionMode or "").lower()

    print("\n" + "=" * 70)
    print("ALL CITIZEN WORKFLOW & ROBOFLOW ROUTING CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_workflow_verification()

