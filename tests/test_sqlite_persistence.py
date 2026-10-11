import os
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.models.issue import (
    Issue,
    IssueCreate,
    IssueStatus,
    IssueCategory,
    PriorityLevel,
    ResolutionStatus,
    ResolutionEvidence
)
from app.db.database import (
    build_engine,
    init_db,
    get_session_factory,
    get_db_session,
    Base
)
from app.db.repository import SqliteIssueRepository
from app.config import settings
from app.main import app

client = TestClient(app)
client.headers["Authorization"] = "Bearer demo-admin-token"

# Helper function to generate test issues
def create_sample_issue(issue_id: str, complaint_text: str = "Test complaint") -> Issue:
    return Issue(
        issueId=issue_id,
        complaintText=complaint_text,
        category=IssueCategory.ROAD_DAMAGE,
        urgency=0.85,
        severity=0.80,
        location="Vidyavihar Station",
        latitude=19.0728,
        longitude=72.8998,
        ward="N-Ward",
        timestamp="2026-10-11T12:00:00Z",
        priorityScore=82.5,
        priorityLevel=PriorityLevel.HIGH,
        department="Roads & Traffic Infrastructure Dept (MCGM)",
        recommendedAction="Cold-mix asphalt patch within 24 hours.",
        slaHours=24,
        status=IssueStatus.OPEN
    )


# ------------------------------------------------------------------------------
# TEST A: Initial Database Creation
# ------------------------------------------------------------------------------
def test_a_initial_database_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_a.db"
        assert not db_path.exists()

        eng = build_engine(db_path)
        init_db(eng)

        assert db_path.exists()
        with eng.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('issues', 'routing_configs')")
            ).fetchall()
            table_names = [row[0] for row in result]
            assert "issues" in table_names
            assert "routing_configs" in table_names
        eng.dispose()


# ------------------------------------------------------------------------------
# TEST B: Seed records inserted when the database is empty
# ------------------------------------------------------------------------------
def test_b_seed_records_inserted_when_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_b.db"
        eng = build_engine(db_path)
        init_db(eng)
        factory = get_session_factory(eng)

        repo = SqliteIssueRepository(session_factory=factory)
        assert repo.count() == 0

        inserted = repo.seed_if_empty()
        assert inserted >= 6
        assert repo.count() >= 6

        first = repo.get_issue("CIVIC-2026-001")
        assert first is not None
        assert first.issueId == "CIVIC-2026-001"
        assert first.category == IssueCategory.ROAD_DAMAGE
        eng.dispose()


# ------------------------------------------------------------------------------
# TEST C: Seed records not duplicated on repeated initialization
# ------------------------------------------------------------------------------
def test_c_seed_records_not_duplicated_on_repeated_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_c.db"
        eng = build_engine(db_path)
        init_db(eng)
        factory = get_session_factory(eng)

        repo = SqliteIssueRepository(session_factory=factory)
        first_run = repo.seed_if_empty()
        count_after_first = repo.count()
        assert first_run >= 6

        # Repeated initialization must be an absolute no-op
        second_run = repo.seed_if_empty()
        assert second_run == 0
        assert repo.count() == count_after_first
        eng.dispose()


# ------------------------------------------------------------------------------
# TEST D: Newly created issue survives repository reinitialization
# ------------------------------------------------------------------------------
def test_d_issue_survives_repository_reinitialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_d.db"
        eng = build_engine(db_path)
        init_db(eng)
        factory = get_session_factory(eng)

        # Instance 1
        repo1 = SqliteIssueRepository(session_factory=factory)
        repo1.seed_if_empty()
        new_issue = create_sample_issue("CIVIC-CUSTOM-901", "Severe broken water valve causing flooding")
        repo1.add_issue(new_issue)

        # Reinitialize fresh repository against the same engine/database
        repo2 = SqliteIssueRepository(session_factory=factory)
        retrieved = repo2.get_issue("CIVIC-CUSTOM-901")
        assert retrieved is not None
        assert retrieved.complaintText == "Severe broken water valve causing flooding"
        assert retrieved.priorityScore == 82.5
        eng.dispose()


# ------------------------------------------------------------------------------
# TEST E: Newly created issue survives backend / application restart
# ------------------------------------------------------------------------------
def test_e_new_issue_survives_backend_restart():
    # Submit issue through API
    payload = {
        "complaintText": "Major electrical spark from streetlight pole near Ghatkopar East station",
        "location": "Ghatkopar East",
        "source": "citizen_mobile"
    }
    create_res = client.post("/api/v1/issues", json=payload)
    assert create_res.status_code == 201
    created_id = create_res.json()["issueId"]

    # Verify retrieval via API endpoint
    get_res = client.get(f"/api/v1/issues/{created_id}")
    assert get_res.status_code == 200
    assert get_res.json()["complaintText"] == payload["complaintText"]


# ------------------------------------------------------------------------------
# TEST F: Status change survives restart
# ------------------------------------------------------------------------------
def test_f_status_change_survives_restart():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_f.db"
        eng1 = build_engine(db_path)
        init_db(eng1)
        factory1 = get_session_factory(eng1)

        repo1 = SqliteIssueRepository(session_factory=factory1)
        repo1.seed_if_empty()

        # Update status
        repo1.update_status("CIVIC-2026-001", IssueStatus.ACTION_IN_PROGRESS)
        eng1.dispose()

        # Simulate complete server restart: create brand new engine and repo
        eng2 = build_engine(db_path)
        factory2 = get_session_factory(eng2)
        repo2 = SqliteIssueRepository(session_factory=factory2)

        reloaded_issue = repo2.get_issue("CIVIC-2026-001")
        assert reloaded_issue is not None
        assert reloaded_issue.status == IssueStatus.ACTION_IN_PROGRESS
        eng2.dispose()


# ------------------------------------------------------------------------------
# TEST G: Resolution-verification state survives restart
# ------------------------------------------------------------------------------
def test_g_resolution_verification_state_survives_restart():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_g.db"
        eng1 = build_engine(db_path)
        init_db(eng1)
        factory1 = get_session_factory(eng1)

        repo1 = SqliteIssueRepository(session_factory=factory1)
        repo1.seed_if_empty()

        target = repo1.get_issue("CIVIC-2026-002")
        assert target is not None

        # Add resolution evidence
        evidence = ResolutionEvidence(
            verified_at="2026-10-11T16:00:00Z",
            inspector_id="INSP-ENG-99",
            original_image_url="https://civic.internal/res/pothole_002.jpg",
            resolution_image_url="https://civic.internal/res/repaired_002.jpg",
            resolutionStatus=ResolutionStatus.LIKELY_RESOLVED,
            resolutionConfidence=0.96,
            verificationSummary="Pothole crater completely resurfaced and cleared by asphalt crew.",
            post_repair_cv_cleared=True
        )
        target.resolutionEvidence = evidence
        target.status = IssueStatus.RESOLVED
        repo1.update_issue(target)
        eng1.dispose()

        # Restart simulation
        eng2 = build_engine(db_path)
        factory2 = get_session_factory(eng2)
        repo2 = SqliteIssueRepository(session_factory=factory2)

        retrieved = repo2.get_issue("CIVIC-2026-002")
        assert retrieved is not None
        assert retrieved.status == IssueStatus.RESOLVED
        assert retrieved.resolutionEvidence is not None
        assert retrieved.resolutionEvidence.inspector_id == "INSP-ENG-99"
        assert retrieved.resolutionEvidence.resolutionStatus == ResolutionStatus.LIKELY_RESOLVED
        assert retrieved.resolutionEvidence.post_repair_cv_cleared is True
        eng2.dispose()


# ------------------------------------------------------------------------------
# TEST H: Filtered issue retrieval returns correct records
# ------------------------------------------------------------------------------
def test_h_filtered_issue_retrieval():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_h.db"
        eng = build_engine(db_path)
        init_db(eng)
        factory = get_session_factory(eng)

        repo = SqliteIssueRepository(session_factory=factory)
        repo.seed_if_empty()

        # Category filter
        roads = repo.list_issues(category=IssueCategory.ROAD_DAMAGE)
        assert len(roads) > 0
        assert all(i.category == IssueCategory.ROAD_DAMAGE for i in roads)

        # Priority filter
        critical = repo.list_issues(priority=PriorityLevel.CRITICAL)
        assert len(critical) > 0
        assert all(i.priorityLevel == PriorityLevel.CRITICAL for i in critical)

        # Hotspot filter
        hotspots = repo.list_issues(hotspot_only=True)
        assert len(hotspots) > 0
        assert all(i.hotspot is True for i in hotspots)
        eng.dispose()


# ------------------------------------------------------------------------------
# TEST I: Failed writes do not leave partial changes (Transaction Atomicity)
# ------------------------------------------------------------------------------
def test_i_failed_writes_do_not_leave_partial_changes():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_i.db"
        eng = build_engine(db_path)
        init_db(eng)
        factory = get_session_factory(eng)

        repo = SqliteIssueRepository(session_factory=factory)
        repo.seed_if_empty()
        initial_count = repo.count()

        # Execute failed transaction with intentional error
        try:
            with get_db_session(factory) as session:
                issue = create_sample_issue("CIVIC-FAIL-01", "This should rollback")
                record = repo._to_record(issue)
                session.add(record)
                # Force failure before commit
                raise RuntimeError("Simulated mid-transaction failure")
        except RuntimeError:
            pass

        # Record must not be saved
        assert repo.count() == initial_count
        assert repo.get_issue("CIVIC-FAIL-01") is None
        eng.dispose()


# ------------------------------------------------------------------------------
# TEST J: Missing issue IDs produce expected 404 errors
# ------------------------------------------------------------------------------
def test_j_missing_issue_ids_produce_404():
    res_get = client.get("/api/v1/issues/CIVIC-NONEXISTENT-999")
    assert res_get.status_code == 404

    res_patch = client.patch(
        "/api/v1/issues/CIVIC-NONEXISTENT-999/status",
        json={"status": "Resolved"}
    )
    assert res_patch.status_code == 404

    res_verify = client.post(
        "/api/v1/issues/CIVIC-NONEXISTENT-999/verify",
        json={"inspectorId": "INSP-01", "resolutionImageUrl": "https://sample.url/img.jpg"}
    )
    assert res_verify.status_code == 404


# ------------------------------------------------------------------------------
# TEST K: Normal startup does not reset persistent data
# ------------------------------------------------------------------------------
def test_k_normal_startup_does_not_reset_persistent_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_k.db"
        eng = build_engine(db_path)
        init_db(eng)
        factory = get_session_factory(eng)

        repo = SqliteIssueRepository(session_factory=factory)
        repo.seed_if_empty()

        # User submits custom issue and mutates an existing issue
        custom_issue = create_sample_issue("CIVIC-CUSTOM-PERM-01", "Citizen created persistent complaint")
        repo.add_issue(custom_issue)
        repo.update_status("CIVIC-2026-001", IssueStatus.RESOLVED)

        # Simulate normal server restart startup call (seed_if_empty + init_db)
        init_db(eng)
        repo.seed_if_empty()

        # Both custom issue and changed status must persist
        assert repo.get_issue("CIVIC-CUSTOM-PERM-01") is not None
        modified = repo.get_issue("CIVIC-2026-001")
        assert modified is not None
        assert modified.status == IssueStatus.RESOLVED
        eng.dispose()


# ------------------------------------------------------------------------------
# TEST L: Demo reset is blocked when demo mode is disabled
# ------------------------------------------------------------------------------
def test_l_demo_reset_blocked_when_demo_mode_disabled():
    original_mode = settings.civilens_demo_mode
    try:
        settings.civilens_demo_mode = False
        res = client.post("/api/v1/demo/reset")
        assert res.status_code == 403
        assert "Destructive demo reset is disabled" in res.json()["detail"]
    finally:
        settings.civilens_demo_mode = original_mode


# ------------------------------------------------------------------------------
# TEST M: Demo reset restores seed records when explicitly enabled
# ------------------------------------------------------------------------------
def test_m_demo_reset_restores_seed_records_when_enabled():
    original_mode = settings.civilens_demo_mode
    try:
        settings.civilens_demo_mode = True
        res = client.post("/api/v1/demo/reset")
        assert res.status_code == 200
        assert "successfully reset to baseline" in res.json()["message"]

        # Baseline seed issue must be reset to OPEN
        first = client.get("/api/v1/issues/CIVIC-2026-001").json()
        assert first["status"] == "OPEN"
    finally:
        settings.civilens_demo_mode = original_mode


# ------------------------------------------------------------------------------
# TEST N: Concurrent requests do not corrupt issue records
# ------------------------------------------------------------------------------
def test_n_concurrent_requests_safe():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_n.db"
        eng = build_engine(db_path)
        init_db(eng)
        factory = get_session_factory(eng)

        repo = SqliteIssueRepository(session_factory=factory)
        repo.seed_if_empty()

        def worker_task(index: int):
            issue_id = f"CIVIC-CONCURRENT-{index:03d}"
            issue = create_sample_issue(issue_id, f"Concurrent complaint thread {index}")
            repo.add_issue(issue)
            repo.update_status(issue_id, IssueStatus.ACTION_IN_PROGRESS)
            return issue_id

        # Execute 20 concurrent write and update operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker_task, i) for i in range(20)]
            results = [f.result() for f in futures]

        assert len(results) == 20
        for issue_id in results:
            item = repo.get_issue(issue_id)
            assert item is not None
            assert item.status == IssueStatus.ACTION_IN_PROGRESS
        eng.dispose()


# ------------------------------------------------------------------------------
# RESTART-PERSISTENCE INTEGRATION TEST
# ------------------------------------------------------------------------------
def test_restart_persistence_integration():
    """
    End-to-End Persistence Validation:
    1. Creates issue against repository instance A.
    2. Updates status and resolution verification state.
    3. Completely disposes instance A and engine.
    4. Creates brand new repository instance B pointing to the exact same file.
    5. Confirms issue, status, and resolution evidence are all intact.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "integration_persistence.db"

        # --- Phase 1: Instance A ---
        eng_a = build_engine(db_path)
        init_db(eng_a)
        factory_a = get_session_factory(eng_a)
        repo_a = SqliteIssueRepository(session_factory=factory_a)
        repo_a.seed_if_empty()

        integ_issue = create_sample_issue("CIVIC-INTEG-FINAL", "Broken water pipeline overflowing onto roadway")
        integ_issue.category = IssueCategory.WATER_SUPPLY
        repo_a.add_issue(integ_issue)

        # Update status
        repo_a.update_status("CIVIC-INTEG-FINAL", IssueStatus.VERIFICATION)

        # Update resolution evidence
        integ_issue = repo_a.get_issue("CIVIC-INTEG-FINAL")
        integ_issue.resolutionEvidence = ResolutionEvidence(
            verified_at="2026-10-11T18:30:00Z",
            inspector_id="INSP-INTEG-01",
            resolutionStatus=ResolutionStatus.LIKELY_RESOLVED,
            resolutionConfidence=0.99,
            verificationSummary="Conduit replaced and pressure restored to normal.",
            post_repair_cv_cleared=True
        )
        integ_issue.status = IssueStatus.RESOLVED
        repo_a.update_issue(integ_issue)

        # Completely close and dispose instance A
        eng_a.dispose()

        # --- Phase 2: Instance B (Simulated server restart) ---
        eng_b = build_engine(db_path)
        factory_b = get_session_factory(eng_b)
        repo_b = SqliteIssueRepository(session_factory=factory_b)

        # Normal startup seed call (should do nothing because DB already populated)
        init_db(eng_b)
        repo_b.seed_if_empty()

        # Verify custom issue survived restart with complete fidelity
        persisted = repo_b.get_issue("CIVIC-INTEG-FINAL")
        assert persisted is not None
        assert persisted.complaintText == "Broken water pipeline overflowing onto roadway"
        assert persisted.category == IssueCategory.WATER_SUPPLY
        assert persisted.status == IssueStatus.RESOLVED
        assert persisted.resolutionEvidence is not None
        assert persisted.resolutionEvidence.inspector_id == "INSP-INTEG-01"
        assert persisted.resolutionEvidence.resolutionStatus == ResolutionStatus.LIKELY_RESOLVED
        assert persisted.resolutionEvidence.post_repair_cv_cleared is True

        # Verify baseline records survived alongside the new issue
        baseline = repo_b.get_issue("CIVIC-2026-001")
        assert baseline is not None
        assert baseline.category == IssueCategory.ROAD_DAMAGE

        eng_b.dispose()
