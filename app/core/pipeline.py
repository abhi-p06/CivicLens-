import uuid
from datetime import datetime, timezone
from typing import Optional, List

from app.models.issue import (
    Issue,
    IssueCreate,
    IssueStatus,
    IssueCategory,
    PriorityLevel
)
from app.core.demo_store import demo_store
from app.modules.nlp.classifier import nlp_classifier
from app.modules.nlp.location import location_extractor
from app.modules.nlp.deduplication import deduplication_engine
from app.modules.vision.yolo_detector import yolo_detector
from app.modules.vision.severity import visual_severity_estimator
from app.modules.cross_validation import validator
from app.modules.cross_validation.validator import cross_validation_engine
from app.modules.spatiotemporal.analyzer import spatiotemporal_analyzer
from app.modules.priority.engine import priority_engine
from app.modules.routing.dispatcher import department_dispatcher

class CivicIssueIntelligencePipeline:
    """
    End-to-End Orchestrator executing the 12-stage multimodal pipeline:
    CITIZEN COMPLAINT -> TEXT ANALYSIS -> CATEGORY / URGENCY / SEVERITY ->
    LOCATION EXTRACTION -> DUPLICATE CHECK -> IMAGE ANALYSIS / YOLO ->
    TEXT-IMAGE CROSS-VALIDATION -> SPATIOTEMPORAL ANALYSIS -> RISK-AWARE PRIORITY ->
    DEPARTMENT ROUTING -> ISSUE LIFECYCLE
    """

    def process_complaint(self, payload: IssueCreate) -> Issue:
        existing_issues = demo_store.list_issues()
        now_iso = datetime.now(timezone.utc).isoformat()
        issue_id = f"CIVIC-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"

        # Stage 1 & 2: Text Analysis -> Category, Urgency, Severity
        category, urgency, text_severity = nlp_classifier.analyze(payload.complaintText)

        # Stage 3: Location Extraction & Geocoding
        if payload.latitude and payload.longitude:
            resolved_location = payload.location or "Reported GPS Coordinates"
            lat, lng = payload.latitude, payload.longitude
        else:
            resolved_location, lat, lng = location_extractor.extract_and_geocode(
                text=payload.complaintText,
                user_location=payload.location
            )

        # Stage 4: Duplicate / Near-Duplicate Detection
        is_dup, dup_group, near_count = deduplication_engine.check_duplicate(
            new_text=payload.complaintText,
            lat=lat,
            lng=lng,
            existing_issues=existing_issues
        )

        # Stage 5: Image Analysis / YOLO Road Damage Detection
        vis_primary, vis_conf, detected_objs = yolo_detector.detect(payload.imageUrl)
        vis_severity = visual_severity_estimator.estimate_severity(detected_objs)

        # Stage 6: Text-Image Evidence Consistency / Cross-Validation
        consistency_score, consistency_flag = cross_validation_engine.validate_consistency(
            category=category,
            visual_detection=vis_primary
        )

        # Stage 7: Spatiotemporal Analysis & Hotspot Detection
        recurrence, is_hotspot, cluster_id = spatiotemporal_analyzer.analyze_location_context(
            lat=lat,
            lng=lng,
            existing_issues=existing_issues
        )

        # Stage 8: Risk-Aware Priority Advisory Score
        priority_score, priority_level, priority_breakdown = priority_engine.calculate_priority(
            urgency=urgency,
            visual_severity=vis_severity,
            recurrence=recurrence,
            is_hotspot=is_hotspot,
            is_recent=True
        )

        # Stage 9: Department Routing & Recommended Actions
        department, recommended_action, sla_hours = department_dispatcher.route_issue(
            category=category,
            priority=priority_level
        )

        # Stage 10: Issue Creation & Lifecycle Status
        issue = Issue(
            issueId=issue_id,
            complaintText=payload.complaintText,
            category=category,
            urgency=urgency,
            severity=max(text_severity, vis_severity),
            location=resolved_location,
            latitude=lat,
            longitude=lng,
            timestamp=now_iso,
            duplicateGroup=dup_group,
            isDuplicate=is_dup,
            nearDuplicateCount=near_count,
            visualDetection=vis_primary,
            visualConfidence=vis_conf,
            visualSeverity=vis_severity,
            detectedObjects=detected_objs,
            evidenceConsistency=consistency_score,
            consistencyFlag=consistency_flag,
            recurrence=recurrence,
            hotspot=is_hotspot,
            hotspotClusterId=cluster_id,
            priorityScore=priority_score,
            priorityLevel=priority_level,
            priorityBreakdown=priority_breakdown,
            department=department,
            recommendedAction=recommended_action,
            slaHours=sla_hours,
            status=IssueStatus.REPORTED,
            metadata={"source": payload.source}
        )

        # Register in demo store
        demo_store.add_issue(issue)
        return issue

pipeline = CivicIssueIntelligencePipeline()
