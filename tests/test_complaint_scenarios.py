import pytest
from app.models.issue import IssueCreate, IssueCategory, PriorityLevel, IssueStatus
from app.core.pipeline import pipeline
from app.core.demo_store import demo_store

@pytest.fixture(autouse=True)
def reset_store_before_each():
    demo_store.reload()

def test_scenario_1_pothole_complaint():
    """
    Scenario 1: Severe Pothole / Road Damage Complaint
    Input: Citizen complaint mentioning accidents and crater near Vidyavihar gate with image.
    Expected Outputs:
    - Category: Roads & Footpaths (ML predicted)
    - Urgency: High/Critical (>= 0.75 due to 'accident' / 'skid')
    - Location: Resolved to Vidyavihar coordinates
    - Duplicate check: Identified as duplicate of existing Vidyavihar cluster
    - Vision: Pothole detected with bounding boxes
    - Cross-validation: Consistent
    - Priority: Critical or High
    - Department: MCGM Roads & Traffic
    """
    complaint = IssueCreate(
        complaintText="Huge dangerous pothole near Somaiya Vidyavihar campus gate, bikes skidding causing serious accident risk",
        location="Vidyavihar",
        imageUrl="data/sample_pothole.jpg"
    )

    # 1. Stateless Analysis Test
    analysis = pipeline.analyze(complaint)
    assert analysis["category"] == IssueCategory.ROAD_DAMAGE
    assert analysis["urgency"] >= 0.75
    assert "accident" in analysis["urgencyCues"] or "skid" in [c[:4] for c in analysis["urgencyCues"]]
    assert analysis["resolvedLocation"] == "Vidyavihar"
    assert analysis["latitude"] == 19.0728
    assert analysis["isDuplicate"] is True
    assert "pothole" in analysis["visualDetection"].lower()
    assert analysis["evidenceConsistency"] >= 0.90
    assert analysis["consistencyFlag"].upper().startswith("CONSISTENT")
    assert analysis["priorityScore"] >= 0.75
    assert "Roads" in analysis["department"]

    # 2. Persistence / Intake Test
    issue = pipeline.process_complaint(complaint)
    assert issue.issueId.startswith("CIVIC-")
    assert issue.status in [IssueStatus.OPEN, IssueStatus.REPORTED]
    assert issue.duplicateGroup is not None

def test_scenario_2_garbage_complaint():
    """
    Scenario 2: Sanitation & Garbage Waste Spill Complaint
    Input: Citizen report describing overflowing garbage dump and terrible stench on LBS Marg.
    Expected Outputs:
    - Category: Sanitation & Garbage
    - Urgency: Moderate to High (due to stench & hazard)
    - Location: Resolved to LBS Marg, Ghatkopar West
    - Vision: Refuse pile / garbage debris detected
    - Cross-validation: Consistent
    - Department: Solid Waste Management (SWM Dept)
    - Action: Compactor truck deployment
    """
    complaint = IssueCreate(
        complaintText="Massive overflowing garbage dump on LBS Marg, rotten food waste and flies creating extreme stench",
        location="LBS Marg, Ghatkopar West",
        imageUrl="data/sample_garbage.jpg"
    )

    analysis = pipeline.analyze(complaint)
    assert analysis["category"] == IssueCategory.SANITATION
    assert analysis["resolvedLocation"] == "LBS Marg, Ghatkopar West"
    assert analysis["latitude"] == 19.0911
    assert "garbage" in analysis["visualDetection"].lower()
    assert analysis["evidenceConsistency"] >= 0.85
    assert "Solid Waste" in analysis["department"]
    assert "compactor" in analysis["recommendedAction"].lower() or "collection" in analysis["recommendedAction"].lower()

def test_scenario_3_water_drainage_complaint():
    """
    Scenario 3: Water Supply & Pipeline Burst Complaint
    Input: Citizen report of burst drinking water pipe flooding street in Dharavi.
    Expected Outputs:
    - Category: Water Supply & Drainage
    - Urgency: High (burst drinking water pipe, flooding)
    - Location: Resolved to 90 Feet Road, Dharavi
    - Vision: Water leak / flooding confirmed
    - Cross-validation: Consistent
    - Priority: High or Critical
    - Department: Hydraulic Engineering Department (HED)
    """
    complaint = IssueCreate(
        complaintText="Major drinking water pipeline burst flooding 90 Feet Road Dharavi, millions of liters wasted",
        location="Dharavi",
        imageUrl="data/sample_water_leak.jpg"
    )

    analysis = pipeline.analyze(complaint)
    assert analysis["category"] == IssueCategory.WATER_SUPPLY
    assert analysis["urgency"] >= 0.70
    assert analysis["latitude"] == 19.0435
    assert "water" in analysis["visualDetection"].lower()
    assert analysis["evidenceConsistency"] >= 0.85
    assert "Hydraulic" in analysis["department"]
    assert analysis["slaHours"] <= 18

def test_scenario_4_unreported_issue_auto_draft():
    """
    Scenario 4: Unreported Issue Detection (Image Only)
    Input: Camera survey passes road damage image with no text.
    Expected Outputs:
    - Auto-drafted flag: True
    - Category: Roads & Footpaths
    - Status: Triaged
    - Text: Formulated synthetic description
    """
    complaint = IssueCreate(
        complaintText="",
        location="Kurla West",
        imageUrl="data/patrol_survey_pothole.jpg"
    )

    result = pipeline.process_complaint(complaint)
    assert result.metadata.get("isAutoDrafted") is True
    assert result.category == IssueCategory.ROAD_DAMAGE
    assert result.status == IssueStatus.TRIAGED
    assert "Auto-detected" in result.complaintText
