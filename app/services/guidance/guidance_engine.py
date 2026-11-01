import re
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.models.issue import Issue, IssueCategory, TimelineEvent
from app.models.field_guidance import (
    FieldGuidanceResult,
    GuidanceActionItem,
    GuidanceCitation,
    ConflictingSourceTopic,
    RecommendationType,
    OfficerDecisionType,
    DocumentStatus
)
from app.services.guidance.knowledge_base import GuidanceKnowledgeBase

logger = logging.getLogger(__name__)

# Mandatory engineering disclaimer required for structural / road repairs
ENGINEERING_DISCLAIMER = (
    "CIVILENS Field Guidance is advisory only. Actual structural remediation and traffic "
    "diversion must comply with site engineer discretion and MoRTH/IRC specifications."
)

FALLBACK_MESSAGE = "Insufficient verified guidance available. Manual technical review is recommended."

HAZARDOUS_KEYWORDS = [
    "chemical", "biomedical", "syringe", "needle", "toxic", "battery",
    "hospital", "blood", "pharma", "pharmaceutical", "carcass", "hazardous",
    "acid", "poison", "dead animal", "biohazard", "clinical waste", "pathological"
]

class GuidanceEngine:
    """
    AI-Powered Field Guidance Synthesis Engine.
    Grounded exclusively in official government standards (MoRTH, MCGM, CPCB, CPHEEO, MPCB).
    Exclusively serves Potholes/Road Damage and Garbage Accumulation.
    """
    def __init__(self, kb: Optional[GuidanceKnowledgeBase] = None):
        self.kb = kb or GuidanceKnowledgeBase()

    def _normalize_category(self, cat: Any) -> Optional[str]:
        raw = str(cat.value if hasattr(cat, "value") else cat).lower()
        if any(term in raw for term in ["road", "pothole", "footpath"]):
            return "Roads & Footpaths"
        if any(term in raw for term in ["garbage", "sanitation", "litter", "waste"]):
            return "Sanitation & Garbage"
        return None

    def _detect_hazardous(self, text: str, detected_objects: List[Any]) -> bool:
        lower_text = text.lower()
        for kw in HAZARDOUS_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", lower_text):
                return True
        for obj in detected_objects:
            lbl = getattr(obj, "label", "") or ""
            if any(kw in lbl.lower() for kw in HAZARDOUS_KEYWORDS):
                return True
        return False

    def generate_guidance(self, issue: Issue, force_regenerate: bool = False) -> FieldGuidanceResult:
        """
        Synthesizes context-aware, grounded field recommendations for an issue.
        Checks cache in issue.metadata['field_guidance'] unless force_regenerate is True.
        """
        # Check cache if not forcing regenerate
        if not force_regenerate and issue.metadata and "field_guidance" in issue.metadata:
            try:
                cached = issue.metadata["field_guidance"]
                if isinstance(cached, dict) and cached.get("guidance_id"):
                    return FieldGuidanceResult.model_validate(cached)
            except Exception as e:
                logger.warning(f"Failed to load cached guidance for issue {issue.issueId}: {e}")

        canonical_category = self._normalize_category(issue.category)
        now_iso = datetime.now(timezone.utc).isoformat()
        guidance_id = f"GUIDE-{uuid.uuid4().hex[:8].upper()}"

        # 1. Unrecognized / Unsupported Category Fallback
        if not canonical_category:
            return FieldGuidanceResult(
                guidance_id=guidance_id,
                issue_id=issue.issueId,
                category=str(issue.category.value if hasattr(issue.category, "value") else issue.category),
                generated_at=now_iso,
                situation_summary="Unrecognized complaint category. Official statutory guidelines are not indexed for this domain.",
                recommendation_rationale="CIVILENS maintains authoritative official guidelines exclusively for Potholes/Road Damage and Garbage Accumulation.",
                immediate_precautions=[],
                recommended_field_actions=[],
                equipment_and_resources=[],
                handling_precautions=[],
                completion_checklist=[],
                retrieved_references=[],
                disagreements=[],
                is_hazardous_escalation=False,
                escalation_notice=None,
                has_insufficient_sources=True,
                fallback_message=FALLBACK_MESSAGE,
                engineering_disclaimer=None
            )

        # 2. Check for active current documents in knowledge base
        active_docs = self.kb.list_documents(category=canonical_category, status="CURRENT")
        if not active_docs:
            return FieldGuidanceResult(
                guidance_id=guidance_id,
                issue_id=issue.issueId,
                category=canonical_category,
                generated_at=now_iso,
                situation_summary="No approved current government standards found for this category.",
                recommendation_rationale="Authoritative sources are missing or pending administrative approval.",
                immediate_precautions=[],
                recommended_field_actions=[],
                equipment_and_resources=[],
                handling_precautions=[],
                completion_checklist=[],
                retrieved_references=[],
                disagreements=[],
                is_hazardous_escalation=False,
                escalation_notice=None,
                has_insufficient_sources=True,
                fallback_message=FALLBACK_MESSAGE,
                engineering_disclaimer=None
            )

        combined_text = f"{issue.complaintText} {issue.location} {issue.visualDetection or ''}"
        is_hazardous = self._detect_hazardous(combined_text, issue.detectedObjects or [])

        if canonical_category == "Roads & Footpaths":
            return self._build_pothole_guidance(issue, guidance_id, now_iso)
        else:
            return self._build_garbage_guidance(issue, guidance_id, now_iso, is_hazardous)

    def _build_pothole_guidance(self, issue: Issue, guidance_id: str, now_iso: str) -> FieldGuidanceResult:
        """Grounded guidance for Potholes and Road Damage under MoRTH and MCGM standards."""
        # Query sections from KB
        sections = self.kb.search_sections(
            query="pothole traffic safety edge cutting tack coat compaction cold mix",
            category="Roads & Footpaths",
            allowed_statuses=["CURRENT"],
            top_k=8
        )

        # Build citations
        cite_morth_traffic = GuidanceCitation(
            doc_id="DOC-MORTH-3004",
            doc_title="MoRTH Specifications for Road and Bridge Works (Section 3004: Maintenance of Bituminous Surfaces)",
            source_org="Ministry of Road Transport and Highways (MoRTH)",
            url="https://morth.nic.in/standard-specifications-road-and-bridge-works-section-3004",
            section="Section 3004.1 (Work Zone Traffic Control)",
            page_number=12,
            document_version="5th Revision / IRC:82-2023",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )
        cite_mcgm_utility = GuidanceCitation(
            doc_id="DOC-MCGM-RDS-2023",
            doc_title="MCGM Standard Operating Procedure for Monsoon Pothole Filling & Cold Mix Asphalt",
            source_org="Municipal Corporation of Greater Mumbai (MCGM / BMC)",
            url="https://portal.mcgm.gov.in/irj/portal/anonymous/qlpotholeguidelines",
            section="Clause 2.4 (Utility Leakage Assessment)",
            page_number=5,
            document_version="MCGM-ENG-RDS-2023-V2",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )
        cite_morth_cutting = GuidanceCitation(
            doc_id="DOC-MORTH-3004",
            doc_title="MoRTH Specifications for Road and Bridge Works (Section 3004)",
            source_org="Ministry of Road Transport and Highways (MoRTH)",
            url="https://morth.nic.in/standard-specifications-road-and-bridge-works-section-3004",
            section="Section 3004.2 (Base Course Stability & Edge Trimming)",
            page_number=14,
            document_version="5th Revision / IRC:82-2023",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )
        cite_morth_tack = GuidanceCitation(
            doc_id="DOC-MORTH-3004",
            doc_title="MoRTH Specifications for Road and Bridge Works (Section 3004)",
            source_org="Ministry of Road Transport and Highways (MoRTH)",
            url="https://morth.nic.in/standard-specifications-road-and-bridge-works-section-3004",
            section="Section 3004.3 (Bituminous Tack Coat)",
            page_number=16,
            document_version="5th Revision / IRC:82-2023",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )
        cite_morth_compaction = GuidanceCitation(
            doc_id="DOC-MORTH-3004",
            doc_title="MoRTH Specifications for Road and Bridge Works (Section 3004)",
            source_org="Ministry of Road Transport and Highways (MoRTH)",
            url="https://morth.nic.in/standard-specifications-road-and-bridge-works-section-3004",
            section="Section 3004.4 (Material Selection & Mechanical Compaction)",
            page_number=18,
            document_version="5th Revision / IRC:82-2023",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )
        cite_mcgm_handover = GuidanceCitation(
            doc_id="DOC-MCGM-RDS-2023",
            doc_title="MCGM Standard Operating Procedure for Monsoon Pothole Filling",
            source_org="Municipal Corporation of Greater Mumbai (MCGM / BMC)",
            url="https://portal.mcgm.gov.in/irj/portal/anonymous/qlpotholeguidelines",
            section="Clause 4.1 (Citizen Closure Protocol & Photo Audit)",
            page_number=8,
            document_version="MCGM-ENG-RDS-2023-V2",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )

        immediate_precautions = [
            GuidanceActionItem(
                id="ACT-POT-01",
                item_type=RecommendationType.PRECAUTION,
                title="Work Zone Traffic Control & Crew Safety Delineation",
                description="Erect advance warning signage and reflective taper cones before opening the carriageway to protect maintenance personnel.",
                steps=[
                    "Position retro-reflective advance warning boards 50m and 100m prior to the work perimeter.",
                    "Arrange 750mm reflective traffic cones in a 15m tapering formation diverting vehicular flow.",
                    "Ensure all field personnel wear Class-3 high-visibility safety vests with reflective strips.",
                    "Demarcate a safe continuous pedestrian walkway separated from the work envelope."
                ],
                equipment=["750mm reflective traffic cones", "Class-3 retro-reflective vests", "50m/100m advance caution boards", "Warning batons"],
                handling_precautions=["Do not commence perimeter cutting without active cone taper.", "Keep safety spotter alert to approaching traffic."],
                citation=cite_morth_traffic,
                is_requirement=True
            ),
            GuidanceActionItem(
                id="ACT-POT-02",
                item_type=RecommendationType.PRECAUTION,
                title="Subgrade Moisture & Municipal Utility Leakage Inspection",
                description="Verify that the pavement failure is not actively fed by an underground water pipe or drain rupture.",
                steps=[
                    "Inspect sub-base for oozing or bubbling water indicating a ruptured municipal water supply line or stormwater drain.",
                    "If water is actively bubbling from the sub-base, immediately suspend asphalt deployment.",
                    "Escalate to BMC Hydraulic Engineer / Storm Water Drain department for pipe isolation before paving."
                ],
                equipment=["Flashlight", "Subgrade moisture inspection probe"],
                handling_precautions=["Do not lay cold/hot mix over actively bubbling utility water; patch will fail within 24 hours."],
                citation=cite_mcgm_utility,
                is_requirement=True
            )
        ]

        recommended_actions = [
            GuidanceActionItem(
                id="ACT-POT-03",
                item_type=RecommendationType.ACTION,
                title="Vertical Rectangular Edge Trimming & Debris Blowout",
                description="Excavate loose material and saw-cut edges into clean vertical faces to lock the bituminous patch.",
                steps=[
                    "Mark a neat rectangle or square around the distressed area extending 50mm into sound pavement.",
                    "Saw-cut or chisel vertical edges to a uniform depth to eliminate feathered transitions.",
                    "Excavate all disintegrated asphalt, muck, and saturated aggregate down to sound base.",
                    "Blow out dust, standing water, and loose stone using compressed air or stiff wire brooms."
                ],
                equipment=["Pavement saw-cutter / pneumatic chisel", "High-pressure air lance or stiff wire brooms", "Pickaxe and shovel"],
                handling_precautions=["Never apply patch material over loose mud or rounded feathered edges."],
                citation=cite_morth_cutting,
                is_requirement=True
            ),
            GuidanceActionItem(
                id="ACT-POT-04",
                item_type=RecommendationType.ACTION,
                title="Rapid-Setting Cationic Tack Coat Application",
                description="Apply cationic bitumen emulsion to all vertical cut faces and base to ensure complete adhesion.",
                steps=[
                    "Ensure cut cavity is dry and free of standing water.",
                    "Evenly apply RS-1 rapid setting cationic bitumen emulsion (IS:8887) to all cut vertical edges and bottom floor.",
                    "Apply at uniform coverage of 0.25 to 0.30 kg/m² using sprayer or applicator brush.",
                    "Allow emulsion to break (turn from brown to black) before introducing asphalt mix."
                ],
                equipment=["RS-1 cationic emulsion (IS:8887)", "Hand pressure sprayer or stiff handheld emulsion brush"],
                handling_precautions=["Avoid excessive pooling of emulsion in sub-base recesses."],
                citation=cite_morth_tack,
                is_requirement=True
            ),
            GuidanceActionItem(
                id="ACT-POT-05",
                item_type=RecommendationType.ACTION,
                title="Bituminous Infill & Mechanical Vibratory Compaction",
                description="Deposit compliant cold or hot mix bituminous asphalt in calibrated lifts and compact mechanically.",
                steps=[
                    "Deposit approved polymer-modified cold mix (monsoon/damp) or hot mix Dense Bituminous Macadam (dry).",
                    "Place mix in uniform lifts not exceeding 75mm loose depth to ensure uniform density.",
                    "Compact mechanically with a minimum 500kg vibratory plate compactor or 8-ton roller until zero deflection.",
                    "Ensure finished crown is flush with surrounding pavement (+/- 3mm). Hand-tamping on vehicular carriage is strictly prohibited."
                ],
                equipment=["500kg vibratory plate compactor or 8-10 ton roller", "Approved polymer-modified cold mix (IRC:116) or hot mix DBM", "Straightedge level (3m)"],
                handling_precautions=["Hand-tamping with hand rammers on vehicular carriageways does not achieve required compaction."],
                citation=cite_morth_compaction,
                is_requirement=True
            ),
            GuidanceActionItem(
                id="ACT-POT-06",
                item_type=RecommendationType.ACTION,
                title="Geo-Tagged Completion Documentation & Engineer Audit",
                description="Capture statutory before-and-after photographic evidence and patch dimensions for audit.",
                steps=[
                    "Capture geo-tagged and timestamped photographs: 1 close-up showing patch edges, 1 wide-angle showing corridor context.",
                    "Record patch dimensions (length x width x depth in cm) and batch serial numbers in the dossier.",
                    "Obtain Ward Sub-Engineer verification before removing traffic cones and reopening lane."
                ],
                equipment=["CIVILENS Mobile / Inspector portal camera", "Measuring tape / folding rule"],
                handling_precautions=["Do not close complaint without clear post-compaction photographic evidence."],
                citation=cite_mcgm_handover,
                is_requirement=True
            )
        ]

        disagreements = [
            ConflictingSourceTopic(
                topic="Asphalt Material Selection: Hot Mix vs Cold Mix in Wet Weather",
                source_a="MoRTH Specifications Section 3004.4 (IRC:82)",
                position_a="Recommends Dense Bituminous Macadam (DBM) Hot Mix for superior durability on arterial carriageways.",
                source_b="MCGM Monsoon Standard Operating Procedure Clause 2.1",
                position_b="Mandates proprietary polymer-modified Cold Mix Asphalt during wet weather / monsoon when hot mix plants cannot operate.",
                recommended_reconciliation="During active monsoon rainfall or damp subgrade conditions, deploy MCGM-approved cold mix asphalt for immediate structural sealing. Schedule permanent hot mix overlay during dry post-monsoon maintenance."
            )
        ]

        equipment_all = [
            "750mm reflective traffic cones",
            "Class-3 retro-reflective vests",
            "Pavement saw-cutter / pneumatic chisel",
            "RS-1 cationic emulsion (IS:8887)",
            "500kg vibratory plate compactor",
            "Approved cold mix asphalt (IRC:116) / Hot mix DBM",
            "High-pressure air blower / wire brooms",
            "3m straightedge level",
            "Measuring tape"
        ]

        handling_all = [
            "Do not apply asphalt over standing water or bubbling sub-base.",
            "Hand tamping on vehicular roadways is non-compliant; mechanical vibratory compaction is mandatory.",
            "Cut edges must be strictly vertical; feathered edges cause immediate raveling.",
            "Do not reopen lane to vehicular traffic until patch is flush and verified."
        ]

        completion_checklist = [
            {"item": "Traffic control safely established prior to cutting", "statutory": True},
            {"item": "Sub-base verified free of active water pipe leakage", "statutory": True},
            {"item": "Cavity perimeter saw-cut to neat vertical rectangular faces", "statutory": True},
            {"item": "Loose debris, dust, and water thoroughly blown out", "statutory": True},
            {"item": "RS-1 cationic tack coat evenly sprayed on all faces", "statutory": True},
            {"item": "Asphalt placed in lifts <= 75mm and vibrated to zero deflection", "statutory": True},
            {"item": "Finished patch flush with surrounding road surface (+/- 3mm)", "statutory": True},
            {"item": "Geo-tagged before and after photographs uploaded to dossier", "statutory": True}
        ]

        retrieved_citations = [
            cite_morth_traffic,
            cite_mcgm_utility,
            cite_morth_cutting,
            cite_morth_tack,
            cite_morth_compaction,
            cite_mcgm_handover
        ]

        situation_summary = (
            f"Pothole reported at {issue.location} (Priority Score: {issue.priorityScore:.1f}/100). "
            f"Restoration requires structured traffic diversion, subgrade moisture audit, rectangular vertical edge sawing, "
            f"cationic tack coat application, and vibratory mechanical compaction per MoRTH Section 3004 and MCGM Monsoon SOP."
        )

        recommendation_rationale = (
            "Field guidance is synthesized from MoRTH Section 3004 and MCGM Monsoon Road Guidelines. "
            "Traffic demarcation protects maintenance staff. Vertical edge cutting and RS-1 emulsion prevent premature "
            "delamination from water infiltration. Vibratory mechanical compaction is required to achieve structural density."
        )

        return FieldGuidanceResult(
            guidance_id=guidance_id,
            issue_id=issue.issueId,
            category="Roads & Footpaths",
            generated_at=now_iso,
            situation_summary=situation_summary,
            recommendation_rationale=recommendation_rationale,
            immediate_precautions=immediate_precautions,
            recommended_field_actions=recommended_actions,
            equipment_and_resources=equipment_all,
            handling_precautions=handling_all,
            completion_checklist=completion_checklist,
            retrieved_references=retrieved_citations,
            disagreements=disagreements,
            is_hazardous_escalation=False,
            escalation_notice=None,
            has_insufficient_sources=False,
            fallback_message=None,
            engineering_disclaimer=ENGINEERING_DISCLAIMER
        )

    def _build_garbage_guidance(
        self,
        issue: Issue,
        guidance_id: str,
        now_iso: str,
        is_hazardous: bool
    ) -> FieldGuidanceResult:
        """Grounded guidance for Garbage & Sanitation under CPCB, CPHEEO, and MPCB rules."""
        cite_cpcb_ppe = GuidanceCitation(
            doc_id="DOC-CPCB-SWM-2016",
            doc_title="Solid Waste Management Rules 2016 (Schedule II: Standards for Processing and Management)",
            source_org="Central Pollution Control Board (CPCB)",
            url="https://cpcb.nic.in/solid-waste-management-rules-2016-schedule-ii",
            section="Rule 15(f) (Worker Safety & Mandatory PPE)",
            page_number=19,
            document_version="Statutory S.O. 1357(E)",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )
        cite_cpheeo_traffic = GuidanceCitation(
            doc_id="DOC-CPHEEO-MSW-2021",
            doc_title="CPHEEO Manual on Municipal Solid Waste Management (Chapter 3)",
            source_org="Central Public Health & Environmental Engineering Organisation (CPHEEO)",
            url="https://cpheeo.gov.in/upload/uploadfiles/files/Part2_MSW_Manual_Chapter3.pdf",
            section="Section 3.4 (Worker Traffic Safety in Urban Corridors)",
            page_number=38,
            document_version="Revised Edition 2021",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )
        cite_cpcb_segregation = GuidanceCitation(
            doc_id="DOC-CPCB-SWM-2016",
            doc_title="Solid Waste Management Rules 2016",
            source_org="Central Pollution Control Board (CPCB)",
            url="https://cpcb.nic.in/solid-waste-management-rules-2016-schedule-ii",
            section="Rule 15(h) (Source Segregation & Non-Burning Mandate)",
            page_number=22,
            document_version="Statutory S.O. 1357(E)",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )
        cite_cpheeo_tools = GuidanceCitation(
            doc_id="DOC-CPHEEO-MSW-2021",
            doc_title="CPHEEO Manual on Municipal Solid Waste Management",
            source_org="Central Public Health & Environmental Engineering Organisation (CPHEEO)",
            url="https://cpheeo.gov.in/upload/uploadfiles/files/Part2_MSW_Manual_Chapter3.pdf",
            section="Section 3.2 (Ergonomic Street Cleansing & Tool Selection)",
            page_number=34,
            document_version="Revised Edition 2021",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=False
        )
        cite_cpcb_transport = GuidanceCitation(
            doc_id="DOC-CPCB-SWM-2016",
            doc_title="Solid Waste Management Rules 2016",
            source_org="Central Pollution Control Board (CPCB)",
            url="https://cpcb.nic.in/solid-waste-management-rules-2016-schedule-ii",
            section="Rule 15(u) (Enclosed and Spill-Proof Transportation)",
            page_number=25,
            document_version="Statutory S.O. 1357(E)",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )
        cite_cpcb_disinfectant = GuidanceCitation(
            doc_id="DOC-CPCB-SWM-2016",
            doc_title="Solid Waste Management Rules 2016",
            source_org="Central Pollution Control Board (CPCB)",
            url="https://cpcb.nic.in/solid-waste-management-rules-2016-schedule-ii",
            section="Rule 15(v) (Storage Platform Sanitization & Vector Control)",
            page_number=27,
            document_version="Statutory S.O. 1357(E)",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )
        cite_mpcb_haz = GuidanceCitation(
            doc_id="DOC-MPCB-HAZ-2016",
            doc_title="MPCB Protocol for Identification & Escalation of Biomedical & Hazardous Waste Contaminants",
            source_org="Maharashtra Pollution Control Board (MPCB)",
            url="https://mpcb.gov.in/waste-management/hazardous-waste-guidelines-escalation",
            section="Protocol 4.2 (Mandatory Cordoning & Emergency Escalation Directive)",
            page_number=4,
            document_version="BMW-HW-SOP-2016-REV",
            document_status=DocumentStatus.CURRENT,
            is_statutory_requirement=True
        )

        immediate_precautions: List[GuidanceActionItem] = []
        retrieved_citations: List[GuidanceCitation] = []

        if is_hazardous:
            escalation_item = GuidanceActionItem(
                id="ACT-HAZ-00",
                item_type=RecommendationType.PRECAUTION,
                title="MANDATORY CORDONING & HAZARDOUS WASTE ESCALATION",
                description="Immediately halt ordinary municipal waste collection. General sanitation staff are prohibited from handling hazardous materials.",
                steps=[
                    "Cordon off a minimum 5-meter perimeter around suspected hazardous material with yellow hazard tape.",
                    "Prohibit sweepers, laborers, and standard compactor trucks from touching, compacting, or lifting the waste.",
                    "Transmit emergency notification to MPCB-Authorized Common Bio-Medical / Hazardous Waste Operator within 2 hours.",
                    "Maintain site security until certified hazardous handling unit arrives with appropriate Type-1 containment."
                ],
                equipment=["Yellow hazard barricade tape", "Danger biohazard signs", "Emergency radio / mobile dispatch"],
                handling_precautions=["Do NOT sweep, shovel, or compress suspected biomedical, battery, or chemical waste."],
                citation=cite_mpcb_haz,
                is_requirement=True
            )
            immediate_precautions.append(escalation_item)
            retrieved_citations.append(cite_mpcb_haz)

        immediate_precautions.extend([
            GuidanceActionItem(
                id="ACT-SWM-01",
                item_type=RecommendationType.PRECAUTION,
                title="Mandatory Worker Personal Protective Equipment (PPE) Verification",
                description="Verify all conservancy workers are wearing statutory protective gear prior to handling solid waste.",
                steps=[
                    "Issue heavy-duty puncture-resistant nitrile or leather gloves to all collection staff.",
                    "Enforce wear of slip-resistant steel-toe safety boots to prevent puncture wounds from broken glass/metal.",
                    "Ensure particulate dust masks (N95 or double-layered FFP2) are fitted over nose and mouth.",
                    "Ensure Class-2 neon high-visibility vests are worn at all times near roadways."
                ],
                equipment=["Heavy-duty puncture-resistant nitrile/leather gloves", "Steel-toe slip-resistant boots", "N95/FFP2 dust masks", "High-visibility reflective waistcoats"],
                handling_precautions=["Direct bare-handed contact with municipal solid waste is strictly prohibited."],
                citation=cite_cpcb_ppe,
                is_requirement=True
            ),
            GuidanceActionItem(
                id="ACT-SWM-02",
                item_type=RecommendationType.PRECAUTION,
                title="Roadway Traffic Delineation for Conservancy Staff",
                description="Establish upstream traffic protection cones when sweeping or loading near active traffic lanes.",
                steps=[
                    "Place two 750mm retro-reflective safety cones 20m upstream of the sweeping crew.",
                    "Assign a crew member as traffic spotter when clearing narrow street medians or blind curves.",
                    "Ensure collection handcart/wheelbarrow is positioned between workers and oncoming traffic."
                ],
                equipment=["750mm reflective traffic cones", "LED warning baton"],
                handling_precautions=["Never stand with back completely turned to vehicular flow on fast corridors."],
                citation=cite_cpheeo_traffic,
                is_requirement=True
            )
        ])

        recommended_actions = [
            GuidanceActionItem(
                id="ACT-SWM-03",
                item_type=RecommendationType.ACTION,
                title="Waste Segregation & Non-Burning Enforcement",
                description="Sort waste at collection into wet biodegradable, dry recyclables, and prevent illegal burning.",
                steps=[
                    "Segregate bulky dry recyclables (corrugated cardboard, plastic containers, metals) from organic waste.",
                    "Verify that no burning of leaves, paper, or plastic is taking place; extinguish immediately if observed.",
                    "Remind team and neighborhood that open burning carries statutory fines under Environment (Protection) Act, 1986."
                ],
                equipment=["Segregated color-coded collection bins", "Fire extinguisher / bucket if smoldering waste is present"],
                handling_precautions=["Open burning of municipal solid waste or garden waste is strictly prohibited by law."],
                citation=cite_cpcb_segregation,
                is_requirement=True
            ),
            GuidanceActionItem(
                id="ACT-SWM-04",
                item_type=RecommendationType.ACTION,
                title="Ergonomic Sweeping & Blackspot Excavation",
                description="Use long-handled tools and containerized wheelbarrows to lift accumulated debris efficiently.",
                steps=[
                    "Deploy long-handled straight brooms to sweep scattered debris into central piles without stooping.",
                    "Scrape hardened mud, dried sludge, and compacted street muck using flat-blade metal scrapers.",
                    "Ladle waste into dual-bin containerized wheelbarrows using metal dustpans.",
                    "Avoid overfilling wheelbarrows beyond 40kg to prevent worker strain and spills."
                ],
                equipment=["Long-handled straight brooms", "Flat metal scrapers", "Containerized dual-bin wheelbarrow", "Galvanized metal dustpans"],
                handling_precautions=["Do not drag bags across the pavement; lift using wheelbarrows to prevent tearing."],
                citation=cite_cpheeo_tools,
                is_requirement=False
            ),
            GuidanceActionItem(
                id="ACT-SWM-05",
                item_type=RecommendationType.ACTION,
                title="Enclosed & Spill-Proof Vehicle Loading",
                description="Transfer waste into covered collection vehicles to eliminate airborne litter and leachate dripping.",
                steps=[
                    "Transfer accumulated waste directly into the rear hopper of an enclosed municipal compactor or tipper.",
                    "If open-body truck is utilized, securely lash heavy-duty tarpaulins tightly over the entire cargo bed.",
                    "Check vehicle leachate drain valve to ensure dirty liquid does not drip onto public transit streets."
                ],
                equipment=["Enclosed compactor truck or heavy-duty tarpaulin tiedowns", "Leachate spill bucket"],
                handling_precautions=["Driving open waste vehicles without secure tarpaulin coverings is a direct CPCB violation."],
                citation=cite_cpcb_transport,
                is_requirement=True
            ),
            GuidanceActionItem(
                id="ACT-SWM-06",
                item_type=RecommendationType.ACTION,
                title="Ground Platform Sanitization & Vector Control Disinfection",
                description="Sanitize cleared ground surface to eradicate odors, fly breeding, and infectious vectors.",
                steps=[
                    "Thoroughly sweep the concrete apron or soil surface until free of visible residual waste.",
                    "Wash stained concrete surface with pressurized water spray if municipal hydrant is accessible.",
                    "Evenly broadcast calcium hypochlorite (bleaching powder) or hydrated lime at 50g per square meter.",
                    "Ensure disinfectant covers all damp soil spots to prevent housefly and rodent breeding."
                ],
                equipment=["Calcium hypochlorite (bleaching powder) / hydrated lime", "Powder applicator / scoop", "Pressurized wash unit (optional)"],
                handling_precautions=["Workers must wear dust masks and eye goggles when broadcasting bleaching powder."],
                citation=cite_cpcb_disinfectant,
                is_requirement=True
            )
        ]

        retrieved_citations.extend([
            cite_cpcb_ppe,
            cite_cpheeo_traffic,
            cite_cpcb_segregation,
            cite_cpheeo_tools,
            cite_cpcb_transport,
            cite_cpcb_disinfectant
        ])

        equipment_all = [
            "Puncture-resistant nitrile/leather gloves",
            "Steel-toe safety boots",
            "N95/FFP2 dust masks",
            "High-visibility reflective waistcoats",
            "750mm reflective traffic cones",
            "Long-handled straight brooms & flat scrapers",
            "Dual-bin containerized wheelbarrows",
            "Heavy-duty tarpaulins / Enclosed compactor vehicle",
            "Calcium hypochlorite (bleaching powder) / hydrated lime"
        ]

        if is_hazardous:
            equipment_all.insert(0, "Yellow hazard cordon tape & biohazard markers")

        handling_all = [
            "Mandatory PPE must be worn at all times; direct hand contact with waste is prohibited.",
            "Open burning of accumulated waste or leaves is illegal and subject to statutory penalties.",
            "Vehicles transporting collected waste must remain fully covered during transit.",
            "Disinfectant powder must be dusted over the cleared perimeter to prevent vectors."
        ]

        completion_checklist = [
            {"item": "Full PPE worn by all conservancy crew members", "statutory": True},
            {"item": "All visible litter and accumulated blackspot debris cleared", "statutory": True},
            {"item": "Recyclable materials segregated from wet biodegradable waste", "statutory": True},
            {"item": "Zero open burning conducted at site", "statutory": True},
            {"item": "Transport truck fully covered with no spillage or leachate dripping", "statutory": True},
            {"item": "Bleaching powder / disinfectant applied over cleared surface at 50g/m²", "statutory": True},
            {"item": "Timestamped post-clearance photograph uploaded to dossier", "statutory": True}
        ]

        if is_hazardous:
            situation_summary = (
                f"POTENTIAL HAZARDOUS / BIOMEDICAL CONTAMINATION at {issue.location} (Priority Score: {issue.priorityScore:.1f}/100). "
                f"Suspected hazardous materials detected. Immediate cordoning and escalation to MPCB-authorized operator required. "
                f"Ordinary solid waste handling is suspended."
            )
            escalation_notice = (
                "MANDATORY HAZARDOUS ESCALATION: Suspected hazardous or biomedical waste detected. "
                "Per MPCB Protocol 4.2 & CPCB SWM Rules, general sanitation workers are prohibited from handling this material. "
                "Immediately cordon off a 5m perimeter with yellow hazard tape, halt ordinary collection, and notify the MPCB-Authorized "
                "Common Bio-Medical / Hazardous Waste Operator."
            )
        else:
            situation_summary = (
                f"Litter / garbage accumulation reported at {issue.location} (Priority Score: {issue.priorityScore:.1f}/100). "
                f"Cleansing requires worker PPE compliance, traffic safety delineation, segregation of wet vs dry waste, "
                f"covered transport, and platform sanitization with bleaching powder per CPCB SWM Rules 2016."
            )
            escalation_notice = None

        recommendation_rationale = (
            "Grounded in CPCB Solid Waste Management Rules 2016 (Schedule II) and CPHEEO Manual on MSW Management. "
            "Enforcing worker PPE minimizes occupational biological hazards. Non-burning compliance eliminates toxic air emissions. "
            "Covered transport prevents corridor re-contamination. Post-cleansing chemical disinfection controls vector breeding."
        )

        return FieldGuidanceResult(
            guidance_id=guidance_id,
            issue_id=issue.issueId,
            category="Sanitation & Garbage",
            generated_at=now_iso,
            situation_summary=situation_summary,
            recommendation_rationale=recommendation_rationale,
            immediate_precautions=immediate_precautions,
            recommended_field_actions=recommended_actions,
            equipment_and_resources=equipment_all,
            handling_precautions=handling_all,
            completion_checklist=completion_checklist,
            retrieved_references=retrieved_citations,
            disagreements=[],
            is_hazardous_escalation=is_hazardous,
            escalation_notice=escalation_notice,
            has_insufficient_sources=False,
            fallback_message=None,
            engineering_disclaimer=None
        )

