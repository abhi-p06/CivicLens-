import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint_contract():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()

    # Core health fields
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "totalIssuesTracked" in data
    assert "activeIssues" in data
    assert data["totalIssuesTracked"] == data["activeIssues"]
    assert data["storageMode"] in ["sqlite_persistent_store", "in_memory_demo_store"]
    assert data["storageMode"] == "sqlite_persistent_store"

    # Subsystems dictionary
    assert "subsystems" in data
    subs = data["subsystems"]
    expected_subsystems = [
        "nlp_classifier",
        "vision_detector",
        "cross_validation",
        "hotspot_clustering",
        "priority_engine",
        "resolution_verification",
    ]
    for k in expected_subsystems:
        assert k in subs, f"Missing subsystem telemetry: {k}"
        sub = subs[k]
        assert "name" in sub
        assert "tech" in sub
        assert "status" in sub
        assert "mode" in sub
        assert "is_model_available" in sub
        assert "metric_name" in sub
        assert "metric_display" in sub
        assert "metric_provenance" in sub
        assert sub["measurement_status"] in ["measured", "configured", "unavailable"]

def test_health_subsystems_provenance_and_honesty():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    subs = res.json()["subsystems"]

    # YOLO Detector honesty verification:
    vision = subs["vision_detector"]
    if vision["is_model_available"]:
        assert vision["status"] == "ONLINE"
        assert vision["measurement_status"] == "measured"
        assert "mAP@50" in vision["metric_display"]
        assert "yolov8s_rdd2022.pt" in vision["metric_provenance"]
    else:
        assert vision["status"] in ["UNAVAILABLE", "DEMO_FALLBACK"]
        assert vision["measurement_status"] == "unavailable"
        assert "Not evaluated" in vision["metric_display"]

    # Resolution Verification honesty verification:
    res_ver = subs["resolution_verification"]
    if res_ver["status"] == "ONLINE":
        assert res_ver["measurement_status"] == "measured"
        assert "OpenCV SSIM" in res_ver["tech"]
        assert "OpenCV SSIM" in res_ver["metric_provenance"]
    else:
        assert res_ver["status"] == "ONLINE_HEURISTIC"
        assert res_ver["measurement_status"] == "unavailable"
        assert "Not evaluated" in res_ver["metric_display"]

    # NLP Classifier status
    nlp = subs["nlp_classifier"]
    assert nlp["status"] in ["ONLINE", "FALLBACK_KEYWORDS"]
    assert nlp["is_model_available"] is True
