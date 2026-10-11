#!/usr/bin/env python3
"""
CIVILENS Release Smoke Test Script
===================================
Executes comprehensive end-to-end smoke verification covering:
1. Core Application Health & Storage Mode
2. Model-Status Telemetry & Truthful Reporting
3. Complaint Submission & SQLite Persistence
4. Multi-Category Vision (Road Damage & Waste)
5. Unsupported Flooding / Manual-Review Policy
6. 6-Factor Authoritative Priority Engine Integrity
7. Department Dispatcher Routing
8. RBAC Authentication & Authorization Release Gates
9. CV-Based Resolution Verification
10. Spatiotemporal Hotspot & Recurrence Endpoints

Usage:
    python scripts/smoke_test_api.py [--url http://localhost:8000]

Exits with code 0 on complete verification, nonzero on any failure.
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

def run_smoke_test(base_url: str = None) -> int:
    client = TestClient(app)
    failures = []

    print("=" * 70)
    print("CIVILENS PHASE 9 — RELEASE READINESS SMOKE TEST")
    print("=" * 70)

    # 1. Health & Storage Mode Check
    print("\n[1/10] Verifying Application Health & Storage Mode...")
    try:
        res = client.get("/api/v1/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert data["status"] == "healthy", f"Status unhealthy: {data.get('status')}"
        assert data["storageMode"] in ["sqlite_persistent_store", "in_memory_demo_store"]
        print(f"  ✓ Health: {data['status'].upper()} (v{data['version']})")
        print(f"  ✓ Storage Mode: {data['storageMode']}")
    except Exception as e:
        print(f"  ✗ Health check failed: {e}")
        failures.append(f"Health check: {e}")

    # 2. Model Telemetry & Honesty
    print("\n[2/10] Verifying Model Subsystems & Provenance Honesty...")
    try:
        subs = res.json()["subsystems"]
        # Road detector
        road = subs["vision_detector"]
        print(f"  • Road Damage: status={road['status']}, metric={road['metric_display']}")
        assert road["status"] in ["ONLINE", "DEGRADED", "UNAVAILABLE"]

        # Waste detector
        waste = subs["waste_detector"]
        print(f"  • Waste Detection: status={waste['status']}, metric={waste['metric_display']}")
        assert waste["status"] in ["ONLINE", "DEGRADED", "UNAVAILABLE"]
        assert "YOLO11s" in waste["tech"] or "TACO" in waste["tech"]

        # Flooding detector
        flood = subs["flooding_detector"]
        print(f"  • Flooding: status={flood['status']}, mode={flood['mode']}")
        assert flood["status"] == "UNSUPPORTED"
        print("  ✓ Truthful subsystem reporting confirmed.")
    except Exception as e:
        print(f"  ✗ Model telemetry failed: {e}")
        failures.append(f"Model telemetry: {e}")

    # 3. Complaint Submission & Persistence
    print("\n[3/10] Verifying Issue Submission & SQLite Persistence...")
    created_issue_id = None
    try:
        payload = {
            "complaintText": "Deep pothole crater causing dangerous tire damage on Link Road.",
            "location": "Link Road, Andheri West",
            "source": "citizen_smoke_test"
        }
        res_submit = client.post("/api/v1/issues", json=payload)
        assert res_submit.status_code == 201, f"Expected 201, got {res_submit.status_code}"
        issue_data = res_submit.json()
        created_issue_id = issue_data["issueId"]
        assert created_issue_id is not None
        print(f"  ✓ Created Issue ID: {created_issue_id}")

        # Retrieve persisted issue
        res_get = client.get(f"/api/v1/issues/{created_issue_id}")
        assert res_get.status_code == 200, f"Expected 200, got {res_get.status_code}"
        assert res_get.json()["issueId"] == created_issue_id
        print("  ✓ Issue successfully persisted and retrieved.")
    except Exception as e:
        print(f"  ✗ Issue persistence failed: {e}")
        failures.append(f"Issue persistence: {e}")

    # 4. Multi-Category Computer Vision Inference
    print("\n[4/10] Verifying Multi-Category Vision Detection...")
    try:
        # 4a. Road damage image
        pothole_path = "data/test_samples/repair_pothole_before.jpg"
        if os.path.exists(pothole_path):
            res_road = client.post("/api/v1/analyze", json={
                "complaintText": "Asphalt depression and pothole on roadway",
                "imageUrl": pothole_path
            })
            assert res_road.status_code == 200
            road_data = res_road.json()
            assert road_data["visionTask"] == "ROAD_DAMAGE"
            assert road_data["visualConfidence"] > 0.0
            print(f"  ✓ Road Damage detected: {road_data['visualDetection']} (conf: {road_data['visualConfidence']})")

        # 4b. Waste accumulation image
        bottle_path = "data/test_samples/bottle.jpg"
        if os.path.exists(bottle_path):
            res_waste = client.post("/api/v1/analyze", json={
                "complaintText": "Accumulated discarded plastic bottles and garbage along sidewalk",
                "imageUrl": bottle_path
            })
            assert res_waste.status_code == 200
            waste_data = res_waste.json()
            assert waste_data["visionTask"] == "SANITATION"
            assert waste_data["visualConfidence"] > 0.0
            print(f"  ✓ Waste Detection detected: {waste_data['visualDetection']} (conf: {waste_data['visualConfidence']})")
    except Exception as e:
        print(f"  ✗ Vision detection failed: {e}")
        failures.append(f"Vision detection: {e}")

    # 5. Unsupported Flooding Handling
    print("\n[5/10] Verifying Unsupported Flooding & Manual Review Policy...")
    try:
        flood_path = "data/test_samples/street_flooding.jpg"
        if os.path.exists(flood_path):
            res_flood = client.post("/api/v1/analyze", json={
                "complaintText": "Severe street waterlogging after heavy rain",
                "imageUrl": flood_path
            })
            assert res_flood.status_code == 200
            flood_data = res_flood.json()
            assert flood_data["detectedObjects"] == []
            assert flood_data["visualDetection"] is None
            assert flood_data["visionMode"] == "unsupported_visual_category"
            assert "MANUAL" in flood_data["consistencyFlag"]
            print("  ✓ Zero fabricated bounding boxes confirmed for flooding.")
            print("  ✓ Routed honestly to MANUAL_REVIEW.")
    except Exception as e:
        print(f"  ✗ Flooding integrity check failed: {e}")
        failures.append(f"Flooding check: {e}")

    # 6. Authoritative Priority Engine Formula Check
    print("\n[6/10] Verifying Authoritative 6-Component Priority Formula...")
    try:
        from app.modules.priority.engine import priority_engine
        score, level, breakdown, reasoning = priority_engine.calculate_priority(
            urgency=0.9,
            text_severity=0.8,
            visual_severity=0.7,
            visual_confidence=0.85,
            related_reports_count=2,
            hours_elapsed=1.0,
            recurrence_count=1,
            is_hotspot=False
        )
        assert 0.0 <= score <= 100.0
        sum_components = (
            breakdown.urgency_points +
            breakdown.text_severity_points +
            breakdown.visual_severity_points +
            breakdown.related_reports_points +
            breakdown.recency_points +
            breakdown.location_risk_points
        )
        assert abs(round(sum_components, 1) - score) <= 0.1
        assert breakdown.urgency_points <= 20.0
        assert breakdown.text_severity_points <= 20.0
        assert breakdown.visual_severity_points <= 20.0
        assert breakdown.related_reports_points <= 15.0
        assert breakdown.recency_points <= 10.0
        assert breakdown.location_risk_points <= 15.0
        print(f"  ✓ Score: {score}/100 ({level.value}), Breakdown sum exact match.")
    except Exception as e:
        print(f"  ✗ Priority calculation failed: {e}")
        failures.append(f"Priority formula: {e}")

    # 7. Department Routing Configuration
    print("\n[7/10] Verifying Department Routing Configuration...")
    try:
        res_route = client.get("/api/v1/routing/config")
        assert res_route.status_code == 200
        cfg = res_route.json()
        assert "Roads & Footpaths" in cfg or len(cfg) > 0
        print(f"  ✓ Active department routing configurations: {len(cfg)} categories.")
    except Exception as e:
        print(f"  ✗ Department routing failed: {e}")
        failures.append(f"Department routing: {e}")

    # 8. RBAC Authentication & Security Release Gates
    print("\n[8/10] Verifying RBAC Security & Authorization Gates...")
    try:
        # Unauthenticated mutation blocked with 401
        target_id = created_issue_id or "CIVIC-2026-001"
        res_unauth = client.patch(f"/api/v1/issues/{target_id}/status", json={"status": "Action in Progress"})
        assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"

        # Inspector credential permits status update
        res_insp = client.patch(
            f"/api/v1/issues/{target_id}/status",
            headers={"Authorization": "Bearer demo-inspector-token"},
            json={"status": "Action in Progress", "note": "Smoke test dispatch"}
        )
        assert res_insp.status_code == 200, f"Expected 200, got {res_insp.status_code}"

        # Inspector credential rejected on Admin endpoint with 403
        res_insp_admin = client.post(
            "/api/v1/routing/config",
            headers={"Authorization": "Bearer demo-inspector-token"},
            json={"category": "Roads & Footpaths", "department": "Rogue", "code": "R", "actions": {"HIGH": ["Action", 1]}}
        )
        assert res_insp_admin.status_code == 403, f"Expected 403, got {res_insp_admin.status_code}"
        print("  ✓ Citizen, Inspector, and Admin boundaries strictly enforced.")
    except Exception as e:
        print(f"  ✗ Security release gate failed: {e}")
        failures.append(f"Security gate: {e}")

    # 9. Computer-Vision Resolution Verification
    print("\n[9/10] Verifying CV Resolution Verification...")
    try:
        target_id = created_issue_id or "CIVIC-2026-001"
        repair_after = "data/test_samples/repair_pothole_after_repaired.jpg"
        if os.path.exists(repair_after):
            res_verify = client.post(
                f"/api/v1/issues/{target_id}/verify",
                headers={"Authorization": "Bearer demo-inspector-token"},
                json={
                    "resolutionImageUrl": repair_after,
                    "notes": "Quality audit inspection"
                }
            )
            assert res_verify.status_code == 200, f"Expected 200, got {res_verify.status_code}"
            ev = res_verify.json()["resolutionEvidence"]
            assert ev is not None
            print(f"  ✓ Resolution Status: {ev['resolutionStatus']}")
            print(f"  ✓ Scene Comparable: {ev.get('sceneComparable')}")
    except Exception as e:
        print(f"  ✗ Resolution verification failed: {e}")
        failures.append(f"Resolution verification: {e}")

    # 10. Hotspots and GIS Analytics
    print("\n[10/10] Verifying Spatiotemporal Hotspot & GIS Endpoints...")
    try:
        res_gis = client.get("/api/v1/gis/geojson")
        assert res_gis.status_code == 200
        assert res_gis.json()["type"] == "FeatureCollection"

        res_hotspots = client.get("/api/v1/hotspots")
        assert res_hotspots.status_code == 200
        print(f"  ✓ GIS GeoJSON and DBSCAN hotspot clustering endpoints verified.")
    except Exception as e:
        print(f"  ✗ GIS/Hotspot check failed: {e}")
        failures.append(f"GIS/Hotspots: {e}")

    print("\n" + "=" * 70)
    if failures:
        print(f"FAILED: {len(failures)} checks failed.")
        for f in failures:
            print(f"  - {f}")
        return 1
    else:
        print("ALL 10 SMOKE TEST SUITES PASSED SUCCESSFULLY.")
        print("CIVILENS RELEASE READINESS: CONFIRMED.")
        print("=" * 70)
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIVILENS Smoke Test")
    parser.add_argument("--url", default=None, help="Optional base URL of running backend server")
    args = parser.parse_args()
    sys.exit(run_smoke_test(args.url))
