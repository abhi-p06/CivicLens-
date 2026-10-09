import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.models.issue import (
    Issue,
    IssueCreate,
    IssueStatus,
    IssueCategory,
    PriorityLevel,
    ConsistencyLevel,
    EvidenceConsistencyResult,
    HotspotInfo,
    RecurrenceInfo
)
from app.core.demo_store import demo_store
from app.modules.nlp.classifier import nlp_classifier
from app.modules.nlp.location import location_extractor
from app.modules.nlp.deduplication import deduplication_engine
from app.modules.vision.yolo_detector import yolo_detector
from app.modules.vision.severity import visual_severity_estimator
from app.modules.cross_validation.validator import cross_validation_engine
from app.modules.spatiotemporal.analyzer import spatiotemporal_analyzer
from app.modules.spatiotemporal.hotspot import hotspot_detector
from app.modules.spatiotemporal.recurring import recurring_detector
from app.modules.priority.engine import priority_engine
from app.modules.routing.dispatcher import department_dispatcher

class CivicIssueIntelligencePipeline:
    """
    Unified, Reusable End-to-End Analysis Pipeline.
    
    Transforms:
        Complaint Text + Optional Image + Optional Location
             ↓
        Unified Multimodal Analysis Pipeline (14 Original + 5 New Features)
             ↓
        Structured Decision-Support Intelligence Result
    """

    def analyze(self, payload: IssueCreate) -> Dict[str, Any]:
        """
        Pure, stateless analysis returning all model and heuristic outputs
        without mutating database/store state.
        """
        existing_issues = demo_store.list_issues()
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # -------------------------------------------------------------
        # Feature 11: Unreported Issue Auto-Drafting Check
        # -------------------------------------------------------------
        is_auto_draft = False
        text = payload.complaintText.strip() if payload.complaintText else ""
        if len(text) < 4 and payload.imageUrl:
            is_auto_draft = True
            text = "Auto-detected road surface damage detected from visual surveillance inspection."

        # -------------------------------------------------------------
        # Features 1, 2, 3: Text NLP (Category, Urgency, Severity)
        # -------------------------------------------------------------
        nlp_out = nlp_classifier.analyze(text)
        category = nlp_out["category"]
        category_conf = nlp_out["categoryConfidence"]
        nlp_mode = nlp_out["classificationMode"]
        urgency = nlp_out["urgency"]
        urgency_cues = nlp_out["urgencyCues"]
        text_severity = nlp_out["severity"]

        # -------------------------------------------------------------
        # Feature 4: Location Extraction & Geocoding
        # -------------------------------------------------------------
        if payload.latitude and payload.longitude:
            resolved_location = payload.location or "Reported GPS Coordinates"
            lat, lng = payload.latitude, payload.longitude
            loc_mode = "user_gps_coordinates"
            ward = "User GPS"
        else:
            loc_out = location_extractor.extract_and_geocode(
                text=text,
                user_location=payload.location
            )
            resolved_location = loc_out["resolvedLocation"]
            lat = loc_out["latitude"]
            lng = loc_out["longitude"]
            loc_mode = loc_out["extractionMode"]
            ward = loc_out["ward"]

        # -------------------------------------------------------------
        # Features 5, 6: Duplicate & Near-Duplicate Detection
        # -------------------------------------------------------------
        dedup_out = deduplication_engine.check_duplicate(
            new_text=text,
            lat=lat,
            lng=lng,
            category=category,
            existing_issues=existing_issues
        )
        is_dup = dedup_out["isDuplicate"]
        dup_group = dedup_out["duplicateGroup"]
        near_count = dedup_out["nearDuplicateCount"]
        matched_master_id = dedup_out["matchedMasterIssueId"]
        dedup_sim = dedup_out["similarityScore"]

        # -------------------------------------------------------------
        # Features 8, 9: YOLO Road Damage Detection & Visual Severity
        # -------------------------------------------------------------
        vision_out = yolo_detector.detect(
            image_path_or_url=payload.imageUrl,
            category_hint=category.value
        )
        vis_primary = vision_out["visualDetection"]
        vis_conf = vision_out["visualConfidence"]
        detected_objs = vision_out["detectedObjects"]
        vision_mode = vision_out["visionExecutionMode"]
        vis_severity = visual_severity_estimator.estimate_severity(detected_objs)

        # -------------------------------------------------------------
        # Feature 13 & Feature 18: Text–Image Evidence Consistency
        # -------------------------------------------------------------
        if is_auto_draft:
            consistency_detail = EvidenceConsistencyResult(
                consistencyScore=1.0,
                consistencyLevel=ConsistencyLevel.CONSISTENT,
                textEvidence="Auto-drafted from visual detection.",
                visualEvidence=f"CV confirmed {vis_primary} ({vis_conf:.2f}).",
                reason="Unreported issue generated directly from verified camera detection."
            )
        else:
            consistency_detail = cross_validation_engine.validate_consistency(
                category=category,
                complaint_text=text,
                visual_detection=vis_primary,
                visual_confidence=vis_conf
            )

        # -------------------------------------------------------------
        # Feature 7 & Feature 16: Spatiotemporal Analysis & Hotspot Detection
        # -------------------------------------------------------------
        st_out = spatiotemporal_analyzer.analyze_location_context(
            lat=lat,
            lng=lng,
            existing_issues=existing_issues
        )
        recurrence = st_out["recurrence"]
        is_hotspot = st_out["isHotspot"]
        cluster_id = st_out["hotspotClusterId"]

        # Hotspot Detection Evaluation
        active_hotspots = hotspot_detector.detect_hotspots(existing_issues)
        matched_hotspot = next((h for h in active_hotspots if h.hotspotId == cluster_id), None)

        # -------------------------------------------------------------
        # Feature 17: Recurring Issue Detection
        # -------------------------------------------------------------
        recurrence_detail = recurring_detector.evaluate_recurrence(
            lat=lat,
            lng=lng,
            category=category,
            location_name=resolved_location,
            existing_issues=existing_issues
        )

        # -------------------------------------------------------------
        # Feature 10 & Feature 15: Risk-Aware Dynamic Priority Engine
        # -------------------------------------------------------------
        priority_score, priority_level, priority_breakdown, priority_reasoning = priority_engine.calculate_priority(
            urgency=urgency,
            text_severity=text_severity,
            visual_severity=vis_severity,
            visual_confidence=vis_conf,
            related_reports_count=near_count,
            hours_elapsed=1.0,
            recurrence_count=recurrence_detail.reportCount,
            is_hotspot=is_hotspot
        )

        # -------------------------------------------------------------
        # Feature 19: Configurable Department Routing & Recommended Action
        # -------------------------------------------------------------
        department, recommended_action, sla_hours, dept_code = department_dispatcher.route_issue(
            category=category,
            priority=priority_level
        )

        overall_severity = max(text_severity, vis_severity)

        return {
            "complaintText": text,
            "category": category,
            "categoryConfidence": category_conf,
            "classificationMode": nlp_mode,
            "urgency": urgency,
            "urgencyCues": urgency_cues,
            "textSeverity": text_severity,
            "visualSeverity": vis_severity,
            "overallSeverity": overall_severity,
            "resolvedLocation": resolved_location,
            "latitude": lat,
            "longitude": lng,
            "ward": ward,
            "locationMode": loc_mode,
            "isDuplicate": is_dup,
            "duplicateGroup": dup_group,
            "nearDuplicateCount": near_count,
            "matchedMasterIssueId": matched_master_id,
            "dedupSimilarityScore": dedup_sim,
            "visualDetection": vis_primary,
            "visualConfidence": vis_conf,
            "detectedObjects": detected_objs,
            "visionMode": vision_mode,
            
            # Feature 18 Output
            "evidenceConsistency": consistency_detail.consistencyScore,
            "consistencyLevel": consistency_detail.consistencyLevel,
            "consistencyFlag": consistency_detail.consistencyLevel.value,
            "consistencyDetail": consistency_detail,
            
            # Features 7 & 16 Output
            "recurrence": recurrence,
            "isHotspot": is_hotspot,
            "hotspotClusterId": cluster_id,
            "hotspotDetail": matched_hotspot,
            
            # Feature 17 Output
            "recurringDetail": recurrence_detail,
            
            # Feature 15 Output (Explainable 0-100 Score)
            "priorityScore": priority_score,
            "priorityLevel": priority_level,
            "priorityBreakdown": priority_breakdown,
            "priorityReasoning": priority_reasoning,
            
            # Feature 19 Output
            "department": department,
            "recommendedAction": recommended_action,
            "slaHours": sla_hours,
            "departmentCode": dept_code,
            
            "isAutoDrafted": is_auto_draft,
            "timestamp": now_iso
        }

    def process_complaint(self, payload: IssueCreate) -> Issue:
        """
        Executes analysis and registers the resulting structured Issue in storage.
        """
        analysis = self.analyze(payload)
        issue_id = f"CIVIC-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"

        status = IssueStatus.TRIAGED if analysis["isAutoDrafted"] else IssueStatus.OPEN

        issue = Issue(
            issueId=issue_id,
            complaintText=analysis["complaintText"],
            category=analysis["category"],
            urgency=analysis["urgency"],
            severity=analysis["overallSeverity"],
            location=analysis["resolvedLocation"],
            latitude=analysis["latitude"],
            longitude=analysis["longitude"],
            timestamp=analysis["timestamp"],
            duplicateGroup=analysis["duplicateGroup"],
            isDuplicate=analysis["isDuplicate"],
            nearDuplicateCount=analysis["nearDuplicateCount"],
            visualDetection=analysis["visualDetection"],
            visualConfidence=analysis["visualConfidence"],
            visualSeverity=analysis["visualSeverity"],
            detectedObjects=analysis["detectedObjects"],
            evidenceConsistency=analysis["evidenceConsistency"],
            consistencyLevel=analysis["consistencyLevel"],
            consistencyFlag=analysis["consistencyFlag"],
            consistencyDetail=analysis["consistencyDetail"],
            recurrence=analysis["recurrence"],
            hotspot=analysis["isHotspot"],
            hotspotClusterId=analysis["hotspotClusterId"],
            hotspotDetail=analysis["hotspotDetail"],
            recurringDetail=analysis["recurringDetail"],
            priorityScore=analysis["priorityScore"],
            priorityLevel=analysis["priorityLevel"],
            priorityBreakdown=analysis["priorityBreakdown"],
            priorityReasoning=analysis["priorityReasoning"],
            department=analysis["department"],
            recommendedAction=analysis["recommendedAction"],
            slaHours=analysis["slaHours"],
            status=status,
            metadata={
                "source": payload.source,
                "ward": analysis["ward"],
                "classificationMode": analysis["classificationMode"],
                "visionMode": analysis["visionMode"],
                "isAutoDrafted": analysis["isAutoDrafted"],
                "departmentCode": analysis["departmentCode"]
            }
        )

        demo_store.add_issue(issue)
        return issue

pipeline = CivicIssueIntelligencePipeline()
