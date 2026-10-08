import pytest
from app.models.issue import IssueCreate, IssueStatus, PriorityLevel, IssueCategory
from app.core.demo_store import demo_store
from app.core.pipeline import pipeline

def test_demo_store_baseline_loading():
    issues = demo_store.list_issues()
    assert len(issues) >= 6
    # Verify first issue fields
    first = demo_store.get_issue("CIVIC-2026-001")
    assert first is not None
    assert first.category == IssueCategory.ROAD_DAMAGE
    assert first.priorityLevel == PriorityLevel.CRITICAL
    assert first.latitude == 19.0728
    assert first.longitude == 72.8998
    assert first.evidenceConsistency > 0.90
    assert first.hotspot is True

def test_pipeline_execution():
    test_complaint = IssueCreate(
        complaintText="Deep dangerous crater on Somaiya Vidyavihar campus road, severe accident hazard",
        location="Vidyavihar",
        source="test_runner"
    )
    result = pipeline.process_complaint(test_complaint)
    
    assert result.issueId.startswith("CIVIC-")
    assert result.category == IssueCategory.ROAD_DAMAGE
    assert result.urgency >= 0.70
    assert result.latitude == 19.0728
    assert result.longitude == 72.8998
    # Should identify proximity to existing Vidyavihar issues
    assert result.isDuplicate is True
    assert result.priorityScore >= 0.65
    assert "Roads" in result.department

def test_pipeline_with_image_evidence():
    test_complaint = IssueCreate(
        complaintText="Massive dangerous pothole near Vidyavihar gate with skidding hazard",
        location="Vidyavihar",
        imageUrl="data/sample_pothole.jpg"
    )
    result = pipeline.process_complaint(test_complaint)
    assert result.visualDetection is not None
    assert result.visualSeverity > 0.0
    assert result.priorityScore >= 0.70
    assert result.priorityLevel in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]

def test_status_transition():
    first = demo_store.get_issue("CIVIC-2026-001")
    updated = demo_store.update_status(first.issueId, IssueStatus.IN_PROGRESS)
    assert updated.status == IssueStatus.IN_PROGRESS
