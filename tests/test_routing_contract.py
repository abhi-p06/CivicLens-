import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.issue import IssueCategory, PriorityLevel
from app.modules.routing.dispatcher import department_dispatcher

client = TestClient(app)
client.headers["Authorization"] = "Bearer demo-admin-token"

@pytest.fixture(autouse=True)
def reset_dispatcher_defaults():
    department_dispatcher.reset_to_defaults()
    yield
    department_dispatcher.reset_to_defaults()

def test_get_routing_config():
    res = client.get("/api/v1/routing/config")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    assert IssueCategory.ROAD_DAMAGE.value in data
    assert IssueCategory.SANITATION.value in data
    assert "department" in data[IssueCategory.ROAD_DAMAGE.value]
    assert "code" in data[IssueCategory.ROAD_DAMAGE.value]
    assert "actions" in data[IssueCategory.ROAD_DAMAGE.value]

def test_update_routing_config_flat_payload():
    payload = {
        "category": IssueCategory.ROAD_DAMAGE.value,
        "department": "Custom Road Maintenance Bureau",
        "code": "CRMB-01",
        "actions": {
            PriorityLevel.CRITICAL.value: ["Immediate emergency patch crew within 4 hours", 4],
            PriorityLevel.HIGH.value: ["Next-day resurfacing", 24]
        }
    }
    res = client.post("/api/v1/routing/config", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["category"] == IssueCategory.ROAD_DAMAGE.value
    assert data["config"]["department"] == "Custom Road Maintenance Bureau"
    assert data["config"]["code"] == "CRMB-01"

    # Verify GET reflects the update
    get_res = client.get("/api/v1/routing/config")
    assert get_res.status_code == 200
    cfg = get_res.json()
    assert cfg[IssueCategory.ROAD_DAMAGE.value]["department"] == "Custom Road Maintenance Bureau"

    # Verify dispatcher actually routes with the new config
    dept, action, sla, code = department_dispatcher.route_issue(
        IssueCategory.ROAD_DAMAGE,
        PriorityLevel.CRITICAL
    )
    assert dept == "Custom Road Maintenance Bureau"
    assert sla == 4
    assert code == "CRMB-01"
    assert "Immediate emergency patch crew" in action

def test_update_routing_config_nested_payload():
    # Shape matching frontend api.ts / SettingsModal.tsx
    payload = {
        "category": IssueCategory.SANITATION.value,
        "config": {
            "department": "Metropolitan Waste Authority",
            "code": "MWA-99",
            "actions": {
                PriorityLevel.CRITICAL.value: "Emergency bulk compactor dispatch within 6 hours",
                PriorityLevel.HIGH.value: "Standard route pickup"
            },
            "slaHours": {
                PriorityLevel.CRITICAL.value: 6,
                PriorityLevel.HIGH.value: 24
            }
        }
    }
    res = client.post("/api/v1/routing/config", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["category"] == IssueCategory.SANITATION.value
    assert data["config"]["department"] == "Metropolitan Waste Authority"
    assert data["config"]["code"] == "MWA-99"

    # Verify GET reflects update
    get_res = client.get("/api/v1/routing/config")
    cfg = get_res.json()
    assert cfg[IssueCategory.SANITATION.value]["department"] == "Metropolitan Waste Authority"

    # Verify dispatcher route_issue handles string action + slaHours correctly
    dept, action, sla, code = department_dispatcher.route_issue(
        IssueCategory.SANITATION,
        PriorityLevel.CRITICAL
    )
    assert dept == "Metropolitan Waste Authority"
    assert sla == 6
    assert code == "MWA-99"
    assert "Emergency bulk compactor" in action

def test_update_routing_config_invalid_missing_category():
    payload = {
        "category": "   ",
        "department": "Test Dept",
        "code": "TEST",
        "actions": {}
    }
    res = client.post("/api/v1/routing/config", json=payload)
    assert res.status_code == 422
    errors = res.json()["detail"]
    assert any("Category name is required" in str(e) for e in errors)

def test_update_routing_config_invalid_missing_department():
    payload = {
        "category": IssueCategory.ROAD_DAMAGE.value,
        "code": "PWD-01",
        "actions": {}
    }
    res = client.post("/api/v1/routing/config", json=payload)
    assert res.status_code == 422
    errors = res.json()["detail"]
    assert any("Department name is required" in str(e) for e in errors)

def test_update_routing_config_invalid_missing_code():
    payload = {
        "category": IssueCategory.ROAD_DAMAGE.value,
        "department": "Highways Dept",
        "actions": {}
    }
    res = client.post("/api/v1/routing/config", json=payload)
    assert res.status_code == 422
    errors = res.json()["detail"]
    assert any("code is required" in str(e).lower() for e in errors)

def test_update_routing_config_invalid_actions_type():
    payload = {
        "category": IssueCategory.ROAD_DAMAGE.value,
        "department": "Highways Dept",
        "code": "HWD",
        "actions": "invalid_string_not_dict"
    }
    res = client.post("/api/v1/routing/config", json=payload)
    assert res.status_code == 422
    errors = res.json()["detail"]
    assert any("Actions must be a dictionary" in str(e) or "mapping" in str(e) for e in errors)


def test_storm_water_category_fallback_and_routing_boundary():
    """
    Verify boundary between 5-category trained ML model and 6-category routing:
    - IssueCategory.STORM_WATER has 0 samples in CIVIC_TRAINING_CORPUS.
    - Complaints with storm water / culvert keywords honestly fall back to demo_fallback mode.
    - Routing correctly routes to Storm Water Drains Department (MCGM-SWD).
    - Pipeline produces valid intelligence without fabricated bounding boxes.
    """
    from app.modules.nlp.classifier import CIVIC_TRAINING_CORPUS, nlp_classifier
    from app.core.pipeline import pipeline
    from app.models.issue import IssueCreate

    # 1. Verify ML training corpus only contains 5 categories (not STORM_WATER)
    training_categories = {cat for _, cat in CIVIC_TRAINING_CORPUS}
    assert len(training_categories) == 5
    assert IssueCategory.STORM_WATER not in training_categories

    # 2. Test fallback classification on dedicated storm water complaint without ML training data
    text = "nullah desilting required before monsoon season"
    cat, conf, mode = nlp_classifier.predict_category(text)
    assert cat == IssueCategory.STORM_WATER
    assert mode == "demo_fallback"  # Honest reporting: not claiming real_ml

    # 3. Test routing dispatcher routes to Storm Water Drains Department (SWD)
    dept, action, sla, code = department_dispatcher.route_issue(
        IssueCategory.STORM_WATER,
        PriorityLevel.HIGH
    )
    assert dept == "Storm Water Drains Department (SWD)"
    assert code == "MCGM-SWD"
    assert "culvert" in action.lower() or "drain" in action.lower()

    # 4. Test pipeline integration
    analysis = pipeline.analyze(IssueCreate(
        complaintText="nullah desilting required before monsoon season",
        location="Kurla West"
    ))
    assert analysis["category"] == IssueCategory.STORM_WATER
    assert analysis["classificationMode"] == "demo_fallback"
    assert analysis["department"] == "Storm Water Drains Department (SWD)"
    assert analysis["departmentCode"] == "MCGM-SWD"
    # Zero fabricated vision boxes
    assert len(analysis["detectedObjects"]) == 0

