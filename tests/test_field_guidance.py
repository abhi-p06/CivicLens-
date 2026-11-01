import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db_session
from app.db.models import GuidanceDocumentRecord, GuidanceSourceRecord
from app.services.guidance.registry import (
    SourceRegistry,
    is_domain_allowlisted,
    validate_source_url,
    INITIAL_ALLOWLIST_SOURCES
)
from app.services.guidance.scraper import DocumentScraper
from app.services.guidance.knowledge_base import GuidanceKnowledgeBase
from app.services.guidance.guidance_engine import GuidanceEngine, ENGINEERING_DISCLAIMER, FALLBACK_MESSAGE
from app.models.issue import (
    Issue,
    IssueCategory,
    PriorityLevel,
    TaskAssignment
)
from app.models.field_guidance import (
    DocumentStatus,
    OfficerDecisionType,
    FieldGuidanceResult
)
from app.core.security import create_access_token, UserRole
from app.core.demo_store import demo_store

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_guidance_environment():
    demo_store.seed_if_empty()
    demo_store.seed_default_users_if_empty()
    kb = GuidanceKnowledgeBase()
    kb.seed_if_empty()

def get_auth_headers(username: str, role: UserRole) -> dict:
    token = create_access_token(user_id=username, role=role, name=username)
    return {"Authorization": f"Bearer {token}"}

# ------------------------------------------------------------------------------
# 1. Allowlist & Registry Tests
# ------------------------------------------------------------------------------

def test_allowlist_domain_filtering():
    reg = SourceRegistry()
    assert reg.is_url_allowed("https://morth.nic.in/guidelines") is True
    assert reg.is_url_allowed("https://mcgm.gov.in/pothole/sop") is True
    assert reg.is_url_allowed("https://portal.mcgm.gov.in/irj/portal") is True
    assert reg.is_url_allowed("https://cpcb.nic.in/swm-rules") is True
    assert reg.is_url_allowed("https://mpcb.gov.in/hazardous") is True
    assert reg.is_url_allowed("https://cpheeo.gov.in/manual") is True

    # Commercial & social media rejection
    assert reg.is_url_allowed("https://reddit.com/r/mumbai/potholes") is False
    assert reg.is_url_allowed("https://twitter.com/civic_updates") is False
    assert reg.is_url_allowed("https://contractorblog.com/tips") is False
    assert reg.is_url_allowed("https://random-commercial-site.com/repair") is False
    assert reg.is_url_allowed("ftp://unknown-server.net") is False

def test_validate_source_url_helper():
    valid, domain, err = validate_source_url("https://morth.nic.in/specs")
    assert valid is True
    assert domain == "morth.nic.in"
    assert err is None

    valid_bad, domain_bad, err_bad = validate_source_url("https://unknown-blog.com/post")
    assert valid_bad is False
    assert "not in the approved government allowlist" in err_bad

def test_is_domain_allowlisted_helper():
    assert is_domain_allowlisted("morth.nic.in") is True
    assert is_domain_allowlisted("mcgm.gov.in") is True
    assert is_domain_allowlisted("evilcorp.com") is False

# ------------------------------------------------------------------------------
# 2. Scraper & Content Parsing Tests
# ------------------------------------------------------------------------------

def test_scraper_clean_html_and_hash():
    scraper = DocumentScraper()
    raw_html = """
    <html>
        <head><title>BMC Monsoonal Protocol</title></head>
        <body>
            <nav>Header Links</nav>
            <script>alert('run');</script>
            <main>
                <h1>Monsoon Pothole Repair Specifications</h1>
                <p>All road repairs during heavy rainfall must deploy polymer-modified cold mix asphalt complying with IRC:116 specifications.</p>
                <div class="footer">Copyright 2023 BMC</div>
            </main>
        </body>
    </html>
    """
    cleaned = scraper.clean_html(raw_html)
    assert "Monsoon Pothole Repair Specifications" in cleaned
    assert "IRC:116" in cleaned
    assert "alert('run')" not in cleaned
    assert "<nav>" not in cleaned

    h1 = scraper.compute_sha256(cleaned)
    h2 = scraper.compute_sha256(cleaned)
    assert h1 == h2
    assert len(h1) == 64

# ------------------------------------------------------------------------------
# 3. Knowledge Base & Versioning Tests
# ------------------------------------------------------------------------------

def test_knowledge_base_retrieval_and_draft_exclusion():
    kb = GuidanceKnowledgeBase()
    # Pothole search
    results = kb.search_sections(
        query="traffic safety edge trimming compaction cold mix",
        category="Roads & Footpaths",
        allowed_statuses=["CURRENT"],
        top_k=5
    )
    assert len(results) > 0
    assert any("Section 3004" in r["section_title"] or "MoRTH" in r["doc_title"] for r in results)

    # Garbage search
    swm_results = kb.search_sections(
        query="worker protective equipment gloves mask bleaching powder",
        category="Sanitation & Garbage",
        allowed_statuses=["CURRENT"],
        top_k=5
    )
    assert len(swm_results) > 0
    assert any("Rule 15" in r["section_title"] or "CPCB" in r["doc_title"] for r in swm_results)

def test_knowledge_base_document_versioning_superseded():
    kb = GuidanceKnowledgeBase()
    # Add a document then re-ingest with modified hash to verify superseding
    doc_url = "https://morth.nic.in/mock-version-test-guideline"
    doc1 = kb.save_ingested_document(
        doc_data={
            "source_domain": "morth.nic.in",
            "source_org": "MoRTH Test",
            "title": "Road Maintenance Guideline Version 1",
            "url": doc_url,
            "content_type": "text/html",
            "file_hash": "hash-v1-initial-state-12345",
            "raw_text": "Initial guideline text content.",
            "sections": [{"section_id": "s1", "section_title": "General", "content": "Initial"}]
        },
        source_id="SRC-MORTH-01",
        category="Roads & Footpaths",
        version="V1.0"
    )
    assert doc1["document_status"] == "CURRENT"

    # Ingest updated document with changed hash
    doc2 = kb.save_ingested_document(
        doc_data={
            "source_domain": "morth.nic.in",
            "source_org": "MoRTH Test",
            "title": "Road Maintenance Guideline Version 2 (Amended)",
            "url": doc_url,
            "content_type": "text/html",
            "file_hash": "hash-v2-amended-state-67890",
            "raw_text": "Updated guideline text content with new standards.",
            "sections": [{"section_id": "s1", "section_title": "General", "content": "Updated"}]
        },
        source_id="SRC-MORTH-01",
        category="Roads & Footpaths",
        version="V2.0"
    )
    assert doc2["id"] != doc1["id"]
    assert doc2["document_status"] == "CURRENT"

    # Verify original document is marked SUPERSEDED
    old_doc = kb.get_document(doc1["id"])
    assert old_doc["document_status"] == "SUPERSEDED"

# ------------------------------------------------------------------------------
# 4. Guidance Engine Synthesis Tests
# ------------------------------------------------------------------------------

def test_pothole_guidance_synthesis():
    engine = GuidanceEngine()
    issue = Issue(
        issueId="TEST-POT-001",
        complaintText="Severe deep pothole on Andheri Kurla Road near metro pillar 42 causing traffic bottleneck.",
        category=IssueCategory.ROAD_DAMAGE,
        urgency=0.8,
        severity=0.85,
        location="Andheri Kurla Road, Andheri East",
        latitude=19.1136,
        longitude=72.8697,
        timestamp=datetime.now(timezone.utc).isoformat(),
        priorityScore=82.5,
        priorityLevel=PriorityLevel.CRITICAL
    )

    res = engine.generate_guidance(issue, force_regenerate=True)
    assert res.category == "Roads & Footpaths"
    assert res.has_insufficient_sources is False
    assert res.engineering_disclaimer == ENGINEERING_DISCLAIMER
    assert len(res.immediate_precautions) >= 2
    assert len(res.recommended_field_actions) >= 3
    assert len(res.disagreements) >= 1  # Conflict between MoRTH Hot Mix & MCGM Monsoon Cold Mix

    # Verify citation grounding on action items
    for item in res.immediate_precautions + res.recommended_field_actions:
        assert item.citation is not None
        assert item.citation.doc_id in ["DOC-MORTH-3004", "DOC-MCGM-RDS-2023"]
        assert item.citation.section != ""

def test_garbage_guidance_and_hazardous_escalation():
    engine = GuidanceEngine()
    # Standard garbage
    std_issue = Issue(
        issueId="TEST-GAR-001",
        complaintText="Heaped garbage and street litter overflowing from municipal bin near market.",
        category=IssueCategory.SANITATION,
        urgency=0.5,
        severity=0.6,
        location="Ghatkopar Station West",
        latitude=19.0860,
        longitude=72.9090,
        timestamp=datetime.now(timezone.utc).isoformat(),
        priorityScore=55.0,
        priorityLevel=PriorityLevel.MEDIUM
    )
    std_res = engine.generate_guidance(std_issue, force_regenerate=True)
    assert std_res.category == "Sanitation & Garbage"
    assert std_res.is_hazardous_escalation is False
    assert any("PPE" in item.title for item in std_res.immediate_precautions)

    # Hazardous waste trigger
    haz_issue = Issue(
        issueId="TEST-HAZ-001",
        complaintText="Discarded medical syringes, hospital needles and chemical carboys dumped on curb.",
        category=IssueCategory.SANITATION,
        urgency=0.95,
        severity=0.9,
        location="Kurla CST Road",
        latitude=19.0700,
        longitude=72.8800,
        timestamp=datetime.now(timezone.utc).isoformat(),
        priorityScore=94.0,
        priorityLevel=PriorityLevel.CRITICAL
    )
    haz_res = engine.generate_guidance(haz_issue, force_regenerate=True)
    assert haz_res.is_hazardous_escalation is True
    assert haz_res.escalation_notice is not None
    assert "MANDATORY HAZARDOUS ESCALATION" in haz_res.escalation_notice
    assert any("DOC-MPCB-HAZ-2016" == item.citation.doc_id for item in haz_res.immediate_precautions)

def test_unsupported_category_fallback():
    engine = GuidanceEngine()
    other_issue = Issue(
        issueId="TEST-OTHER-001",
        complaintText="Street light pole flickering in neighborhood park.",
        category=IssueCategory.UNSPECIFIED,
        urgency=0.2,
        severity=0.2,
        location="Dadar West",
        latitude=19.0178,
        longitude=72.8478,
        timestamp=datetime.now(timezone.utc).isoformat(),
        priorityScore=20.0,
        priorityLevel=PriorityLevel.LOW
    )
    res = engine.generate_guidance(other_issue, force_regenerate=True)
    assert res.has_insufficient_sources is True
    assert res.fallback_message == FALLBACK_MESSAGE
    assert len(res.recommended_field_actions) == 0

# ------------------------------------------------------------------------------
# 5. Officer Decision Workflow & Timeline Tests
# ------------------------------------------------------------------------------

def test_officer_decision_use_and_edit():
    issue = Issue(
        issueId="TEST-DEC-001",
        complaintText="Pothole in middle lane outside school.",
        category=IssueCategory.ROAD_DAMAGE,
        urgency=0.7,
        severity=0.75,
        location="Chembur East",
        latitude=19.0600,
        longitude=72.9000,
        timestamp=datetime.now(timezone.utc).isoformat(),
        priorityScore=72.0,
        priorityLevel=PriorityLevel.HIGH
    )
    demo_store.add_issue(issue)

    # 1. Accept an action item
    guidance = demo_store.get_or_generate_field_guidance("TEST-DEC-001")
    target_item_id = guidance.recommended_field_actions[0].id

    updated_guidance = demo_store.record_guidance_decision(
        issue_id="TEST-DEC-001",
        item_id=target_item_id,
        decision=OfficerDecisionType.ACCEPTED,
        actor="Officer Abhinay",
        role="inspector"
    )
    # Check action decision status
    item = next(i for i in updated_guidance.recommended_field_actions if i.id == target_item_id)
    assert item.officer_decision == OfficerDecisionType.ACCEPTED

    # Verify task instructions updated and timeline logged without auto-assigning team or closing issue
    refreshed_issue = demo_store.get_issue("TEST-DEC-001")
    assert refreshed_issue.assignment is not None
    assert "Adopted Guidance" in refreshed_issue.assignment.instructions
    assert refreshed_issue.status.value not in ["RESOLVED", "VERIFIED_CLOSED"]

    timeline_events = [e for e in refreshed_issue.timeline if e.event_type == "FIELD_GUIDANCE_ACCEPTED"]
    assert len(timeline_events) >= 1
    assert "Officer Abhinay" in timeline_events[-1].description

    # 2. Edit an action item
    target_item_id_2 = guidance.recommended_field_actions[1].id
    edited_text = "Apply RS-1 cationic emulsion with dual coat at 0.35 kg/m2 due to damp subgrade."
    updated_guidance_2 = demo_store.record_guidance_decision(
        issue_id="TEST-DEC-001",
        item_id=target_item_id_2,
        decision=OfficerDecisionType.EDITED,
        edited_text=edited_text,
        actor="Officer Abhinay",
        role="inspector"
    )
    item_2 = next(i for i in updated_guidance_2.recommended_field_actions if i.id == target_item_id_2)
    assert item_2.officer_decision == OfficerDecisionType.EDITED
    assert item_2.edited_text == edited_text

    refreshed_issue_2 = demo_store.get_issue("TEST-DEC-001")
    assert edited_text in refreshed_issue_2.assignment.instructions

# ------------------------------------------------------------------------------
# 6. API Endpoints & RBAC Security Tests
# ------------------------------------------------------------------------------

def test_api_issue_guidance_endpoints():
    issue = Issue(
        issueId="TEST-API-001",
        complaintText="Large pothole near bus terminal.",
        category=IssueCategory.ROAD_DAMAGE,
        urgency=0.8,
        severity=0.8,
        location="Vashi Bus Station",
        latitude=19.0760,
        longitude=72.9990,
        timestamp=datetime.now(timezone.utc).isoformat(),
        priorityScore=80.0,
        priorityLevel=PriorityLevel.HIGH
    )
    demo_store.add_issue(issue)

    inspector_headers = get_auth_headers("inspector_abhinay", UserRole.INSPECTOR)
    citizen_headers = get_auth_headers("citizen_user", UserRole.CITIZEN)

    # Citizen access denied
    res_cit = client.get("/api/v1/issues/TEST-API-001/guidance", headers=citizen_headers)
    assert res_cit.status_code == 403

    # Inspector access allowed
    res_insp = client.get("/api/v1/issues/TEST-API-001/guidance", headers=inspector_headers)
    assert res_insp.status_code == 200
    data = res_insp.json()
    assert data["category"] == "Roads & Footpaths"
    assert len(data["recommended_field_actions"]) > 0

    # Regenerate
    res_regen = client.post("/api/v1/issues/TEST-API-001/guidance/regenerate", headers=inspector_headers)
    assert res_regen.status_code == 200

    # Decision API
    first_item_id = data["recommended_field_actions"][0]["id"]
    res_dec = client.post(
        "/api/v1/issues/TEST-API-001/guidance/decision",
        json={
            "item_id": first_item_id,
            "decision": "ACCEPTED"
        },
        headers=inspector_headers
    )
    assert res_dec.status_code == 200
    dec_data = res_dec.json()
    dec_item = next(i for i in dec_data["recommended_field_actions"] if i["id"] == first_item_id)
    assert dec_item["officer_decision"] == "ACCEPTED"

def test_api_document_detail_endpoint():
    auth_headers = get_auth_headers("inspector_abhinay", UserRole.INSPECTOR)
    res = client.get("/api/v1/guidance/documents/DOC-MORTH-3004", headers=auth_headers)
    assert res.status_code == 200
    doc = res.json()
    assert doc["id"] == "DOC-MORTH-3004"
    assert "Section 3004" in doc["title"]
    assert len(doc["sections"]) > 0

def test_api_admin_guidance_sources_and_documents():
    admin_headers = get_auth_headers("admin_user", UserRole.ADMIN)
    inspector_headers = get_auth_headers("inspector_abhinay", UserRole.INSPECTOR)

    # Inspector denied admin routes
    res_denied = client.get("/api/v1/admin/guidance/sources", headers=inspector_headers)
    assert res_denied.status_code == 403

    # Admin lists sources
    res_sources = client.get("/api/v1/admin/guidance/sources", headers=admin_headers)
    assert res_sources.status_code == 200
    sources = res_sources.json()
    assert len(sources) >= 6
    assert any(s["domain"] == "morth.nic.in" for s in sources)

    # Admin updates source status
    source_id = sources[0]["id"]
    res_patch = client.patch(
        f"/api/v1/admin/guidance/sources/{source_id}",
        json={"is_active": False},
        headers=admin_headers
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["is_active"] is False

    # Restore active
    client.patch(f"/api/v1/admin/guidance/sources/{source_id}", json={"is_active": True}, headers=admin_headers)

    # Admin lists documents
    res_docs = client.get("/api/v1/admin/guidance/documents", headers=admin_headers)
    assert res_docs.status_code == 200
    docs = res_docs.json()
    assert len(docs) >= 5

    # Admin ingests from invalid domain -> 400
    res_bad_ingest = client.post(
        "/api/v1/admin/guidance/ingest",
        json={"source_url": "https://unauthorized-commercial-site.com/repair"},
        headers=admin_headers
    )
    assert res_bad_ingest.status_code == 400
    assert "Disallowed or non-government source" in res_bad_ingest.json()["detail"]
