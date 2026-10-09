import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["totalIssuesTracked"] >= 6

def test_api_list_issues():
    res = client.get("/api/v1/issues")
    assert res.status_code == 200
    issues = res.json()
    assert isinstance(issues, list)
    assert len(issues) >= 6

def test_api_submit_issue():
    payload = {
        "complaintText": "Sewage and dirty water leaking on LBS Marg, Ghatkopar West",
        "location": "Ghatkopar",
        "source": "api_test"
    }
    res = client.post("/api/v1/issues", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "issueId" in data
    assert data["category"] == "Water Supply & Drainage"
    assert data["latitude"] in [19.0856, 19.0911]
    assert data["department"] == "Hydraulic Engineering Department (HED)"

def test_api_gis_geojson():
    res = client.get("/api/v1/gis/geojson")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 6
    feat = data["features"][0]
    assert "geometry" in feat
    assert "coordinates" in feat["geometry"]
    assert "properties" in feat
    assert "priorityScore" in feat["properties"]

def test_api_status_update():
    res = client.patch(
        "/api/v1/issues/CIVIC-2026-003/status",
        json={"status": "Resolved"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "Resolved"

def test_api_verify_resolution():
    res = client.post(
        "/api/v1/issues/CIVIC-2026-003/verify",
        json={
            "inspectorId": "INSP-MUMBAI-04",
            "resolutionImageUrl": "https://civic.internal/res/003.jpg",
            "notes": "Debris cleared, bin washed and sanitized."
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Verified Closed"
    assert data["resolutionEvidence"]["post_repair_cv_cleared"] is True
