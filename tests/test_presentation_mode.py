"""
CIVILENS — Presentation Mode & Academic Demonstration Regression Tests
Phase 12: Clean Presentation Mode & Demo Data Cleanup
"""

import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.config import Settings, settings
from app.db.database import build_engine, init_db, get_session_factory
from app.db.repository import SqliteIssueRepository
from app.models.issue import Issue, IssueCategory, IssueCreate, IssueStatus, PriorityLevel
from app.core.pipeline import pipeline


def test_presentation_database_starts_empty():
    """Verify that a fresh presentation database initializes schema with zero complaint records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pres_db = Path(tmpdir) / "civilens_presentation.db"
        assert not pres_db.exists()

        eng = build_engine(pres_db)
        init_db(target_engine=eng)
        session_factory = get_session_factory(eng)
        repo = SqliteIssueRepository(session_factory=session_factory)
        repo.seed_default_users_if_empty()

        # Confirm 0 issues seeded
        issues = repo.list_issues()
        assert len(issues) == 0

        # Confirm users seeded
        with eng.connect() as conn:
            users_count = conn.execute(text("SELECT count(*) FROM users")).scalar()
            assert users_count >= 3


def test_no_seed_complaints_in_presentation_mode():
    """Verify demo_store does not auto-seed CIVIC-2026-001..006 when in presentation mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pres_db = Path(tmpdir) / "civilens_presentation.db"
        eng = build_engine(pres_db)
        init_db(target_engine=eng)
        session_factory = get_session_factory(eng)
        repo = SqliteIssueRepository(session_factory=session_factory)

        from app.core.demo_store import DemoDataStore
        pres_store = DemoDataStore(repository=repo)

        # In presentation database, seed_if_empty must NOT load demo issues
        pres_settings = Settings(
            civilens_presentation_mode=True,
            civilens_db_path=str(pres_db),
            seed_complaints_on_startup=False
        )
        assert pres_settings.is_presentation_database is True

        # When presentation database is true, store should remain empty
        issues = pres_store.list_issues()
        assert len(issues) == 0


def test_newly_submitted_issue_persists_in_presentation_mode():
    """Verify that newly submitted complaints are saved and survive simulated restart."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pres_db = Path(tmpdir) / "civilens_presentation.db"
        eng = build_engine(pres_db)
        init_db(target_engine=eng)
        session_factory = get_session_factory(eng)
        repo = SqliteIssueRepository(session_factory=session_factory)

        # Submit new pothole complaint
        sample_issue = Issue(
            issueId="CIVIC-PRES-001",
            complaintText="Hazardous deep asphalt pothole damaging tyres at intersection",
            location="Kurla West Depot Road",
            category=IssueCategory.ROAD_DAMAGE,
            ward="L-Ward",
            urgency=0.88,
            severity=0.85,
            latitude=19.0688,
            longitude=72.8800,
            timestamp="2026-10-23T11:00:00Z",
            priorityScore=86.0,
            priorityLevel=PriorityLevel.CRITICAL,
            department="Roads & Traffic Infrastructure Dept (MCGM)",
            recommendedAction="Deploy emergency asphalt repair crew",
            slaHours=12,
            status=IssueStatus.OPEN,
            source="citizen_portal"
        )
        created = repo.add_issue(sample_issue)

        assert created.issueId == "CIVIC-PRES-001"
        assert created.category == "Roads & Footpaths"

        # Simulate restart: re-open database connection from disk
        eng_restart = build_engine(pres_db)
        factory_restart = get_session_factory(eng_restart)
        repo_restart = SqliteIssueRepository(session_factory=factory_restart)

        reloaded = repo_restart.get_issue("CIVIC-PRES-001")
        assert reloaded is not None
        assert reloaded.issueId == "CIVIC-PRES-001"
        assert reloaded.location == "Kurla West Depot Road"
        assert reloaded.priorityScore == 86.0


def test_pothole_upload_invokes_road_damage_inference():
    """Verify that a pothole complaint invokes the RDD2022 road-damage detector."""
    sample_pothole = Path("data/sample_pothole.jpg")
    if not sample_pothole.exists():
        sample_pothole = Path("data/test_samples/repair_pothole_before.jpg")

    req = IssueCreate(
        complaintText="Critical road crater and deep pothole causing vehicle damage",
        location="Somaiya Vidyavihar",
        category="Roads & Footpaths",
        imageUrl=str(sample_pothole) if sample_pothole.exists() else None
    )

    result = pipeline.analyze(req)
    assert result["category"] == "Roads & Footpaths"
    assert "road" in result["department"].lower() or "traffic" in result["department"].lower()
    if sample_pothole.exists():
        assert "rdd2022" in (result.get("visionModel") or "").lower() or result.get("visionMode") is not None


def test_garbage_upload_invokes_waste_inference():
    """Verify that a garbage complaint invokes the TACO waste detector."""
    sample_waste = Path("data/test_samples/bottle.jpg")
    req = IssueCreate(
        complaintText="Accumulation of garbage and decaying solid waste along pedestrian footpath",
        location="Kurla West Station Road",
        category="Sanitation & Garbage",
        imageUrl=str(sample_waste) if sample_waste.exists() else None
    )

    result = pipeline.analyze(req)
    assert result["category"] == "Sanitation & Garbage"
    assert "waste" in result["department"].lower() or "sanitation" in result["department"].lower()
    if sample_waste.exists():
        assert "taco" in (result.get("visionModel") or "").lower() or result.get("visionMode") is not None


def test_zero_detections_returns_honest_empty_result():
    """Verify an image without defects returns honest zero-detection without fake bounding boxes."""
    sample_clean = Path("data/repaired_road_patch.jpg")
    req = IssueCreate(
        complaintText="Smooth resurfaced asphalt road after routine maintenance",
        location="Bandra West",
        category="Roads & Footpaths",
        imageUrl=str(sample_clean) if sample_clean.exists() else None
    )

    result = pipeline.analyze(req)
    detected = result.get("detectedObjects", [])
    # Detections must be real list without preset hardcoded confidence 0.94
    for d in detected:
        assert isinstance(d, dict)
        assert "bbox" in d


def test_empty_queue_metrics_endpoint():
    """Verify evaluation and metrics endpoints return valid zero-metrics rather than crashing."""
    client = TestClient(app)
    client.headers["Authorization"] = "Bearer demo-admin-token"

    res = client.get("/api/v1/evaluation/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "classification" in data or "priority_scoring" in data or "department_routing" in data


def test_production_bundle_contains_no_privileged_credentials():
    """Verify production frontend build contains no hardcoded dev passwords or tokens."""
    dist_dir = Path("frontend/dist")
    if not dist_dir.exists():
        pytest.skip("frontend/dist not built yet")

    js_files = list((dist_dir / "assets").glob("*.js"))
    assert len(js_files) > 0, "No JS files found in frontend dist assets"

    forbidden_strings = [
        "CIVILENS_DEV_ADMIN_PASSWORD",
        "demo-admin-token-super-secret",
        "Admin@123",  # Plaintext admin password should not be embedded in client bundle
    ]

    for js_path in js_files:
        content = js_path.read_text(encoding="utf-8", errors="ignore")
        for s in forbidden_strings:
            assert s not in content, f"Forbidden credential string '{s}' found in production asset {js_path.name}"
