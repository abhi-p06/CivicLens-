import json
import hashlib
from typing import List, Dict, Any

SEED_GUIDANCE_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "id": "DOC-MORTH-3004",
        "source_id": "SRC-MORTH-01",
        "source_domain": "morth.nic.in",
        "source_org": "Ministry of Road Transport and Highways (MoRTH)",
        "title": "MoRTH Specifications for Road and Bridge Works (Section 3004: Maintenance of Bituminous Surfaces)",
        "url": "https://morth.nic.in/standard-specifications-road-and-bridge-works-section-3004",
        "publication_date": "2020-04-15",
        "document_version": "5th Revision / IRC:82-2023",
        "document_status": "CURRENT",
        "applicable_category": "Roads & Footpaths",
        "content_type": "application/pdf",
        "summary": "Authoritative standard specifications for pothole preparation, vertical edge trimming, cationic tack coat, cold/hot mix bituminous asphalt placement, and vibratory compaction.",
        "sections": [
            {
                "section_id": "sec-3004.1",
                "section_title": "Section 3004.1: Work Zone Traffic Control & Site Safety Precautions",
                "page_number": 12,
                "content": "Advance retro-reflective warning signs must be posted 50m and 100m ahead of the work area. Reflective traffic cones must be placed in a tapering formation with 15m intervals to guide traffic away from the repair zone. All crew members must wear Class-3 retro-reflective safety vests. Safe pedestrian passage must be demarcated.",
                "is_statutory": True,
            },
            {
                "section_id": "sec-3004.2",
                "section_title": "Section 3004.2: Damage Inspection, Base Course Stability & Rectangular Edge Trimming",
                "page_number": 14,
                "content": "Before placing repair material, the site inspector must inspect the sub-base for underlying water saturation or structural base failure. The perimeter of the pothole must be cut with a pavement saw or pneumatic chisel into neat rectangular or square shapes with vertical faces into sound asphalt. All loose aggregate, debris, and standing water must be completely removed using compressed air or stiff wire brooms.",
                "is_statutory": True,
            },
            {
                "section_id": "sec-3004.3",
                "section_title": "Section 3004.3: Bituminous Tack Coat Application",
                "page_number": 16,
                "content": "A uniform tack coat of RS-1 rapid setting cationic bitumen emulsion complying with IS:8887 must be sprayed or brushed onto all vertical cut faces and the clean bottom surface at a rate of 0.25 to 0.30 kg/sqm prior to placing mix.",
                "is_statutory": True,
            },
            {
                "section_id": "sec-3004.4",
                "section_title": "Section 3004.4: Material Selection, Layer Thickness & Mechanical Compaction",
                "page_number": 18,
                "content": "Potholes should be filled with Bituminous Cold Mix complying with IRC:116 or Hot Mix Dense Bituminous Macadam. Mix must be placed in lifts not exceeding 75mm loose thickness. Each lift must be thoroughly compacted with a minimum 500kg vibratory plate compactor or 8-10 ton roller until zero deflection is observed. Finished surface must be flush with surrounding pavement (+/- 3mm). Hand-tamping on vehicular carriageways is non-compliant.",
                "is_statutory": True,
            },
            {
                "section_id": "sec-3004.5",
                "section_title": "Section 3004.5: Handover Documentation & Photographic Verification",
                "page_number": 21,
                "content": "The site supervisor must record geo-tagged before, excavation, and post-compaction photographs. Log patch dimensions (length, width, depth), material batch serials, and equipment utilized. Formal municipal engineer sign-off is required before lane reopening.",
                "is_statutory": True,
            },
        ],
    },
    {
        "id": "DOC-MCGM-RDS-2023",
        "source_id": "SRC-MCGM-01",
        "source_domain": "mcgm.gov.in",
        "source_org": "Municipal Corporation of Greater Mumbai (MCGM / BMC)",
        "title": "MCGM Standard Operating Procedure for Monsoon Pothole Filling & Cold Mix Asphalt",
        "url": "https://portal.mcgm.gov.in/irj/portal/anonymous/qlpotholeguidelines",
        "publication_date": "2023-05-20",
        "document_version": "MCGM-ENG-RDS-2023-V2",
        "document_status": "CURRENT",
        "applicable_category": "Roads & Footpaths",
        "content_type": "text/html",
        "summary": "BMC urban corridor specifications for rapid monsoonal cold mix pothole response, subgrade moisture drainage checks, mechanical compaction, and civic portal verification.",
        "sections": [
            {
                "section_id": "cl-2.1",
                "section_title": "Clause 2.1: Urban Monsoon Response & Cold Mix Deployment",
                "page_number": 3,
                "content": "During active monsoon periods, road repair crews must deploy approved proprietary polymer-modified cold mix asphalt designed to cure in damp conditions. Hot mix plants cannot operate during rainfall; cold mix is the mandatory municipal standard during wet weather.",
                "is_statutory": True,
            },
            {
                "section_id": "cl-2.4",
                "section_title": "Clause 2.4: Utility Leakage & Subsurface Water Drain Assessment",
                "page_number": 5,
                "content": "If water is bubbling or oozing from the pothole sub-base indicating a municipal water main or stormwater drain rupture, the road crew must NOT apply patch asphalt. Immediate emergency escalation to the BMC Hydraulic Engineer / Storm Water Drain department is mandatory.",
                "is_statutory": True,
            },
            {
                "section_id": "cl-4.1",
                "section_title": "Clause 4.1: Citizen Closure Protocol & Geo-Stamped Photo Audit",
                "page_number": 8,
                "content": "The Ward Sub-Engineer must verify on-site that patch edges are smooth, non-ravelling, and level with the corridor. Two geo-stamped completion photographs (one close-up, one wide-angle) must be uploaded to the official system before complaint status changes to Resolved.",
                "is_statutory": True,
            },
        ],
    },
    {
        "id": "DOC-CPCB-SWM-2016",
        "source_id": "SRC-CPCB-01",
        "source_domain": "cpcb.nic.in",
        "source_org": "Central Pollution Control Board (CPCB)",
        "title": "Solid Waste Management Rules 2016 (Schedule II: Standards for Processing and Management of Municipal Solid Waste)",
        "url": "https://cpcb.nic.in/solid-waste-management-rules-2016-schedule-ii",
        "publication_date": "2016-04-08",
        "document_version": "Statutory S.O. 1357(E)",
        "document_status": "CURRENT",
        "applicable_category": "Sanitation & Garbage",
        "content_type": "application/pdf",
        "summary": "National statutory standards for municipal solid waste collection, worker PPE, segregation of domestic recyclables vs organic waste, covered transport, and sanitary platform maintenance.",
        "sections": [
            {
                "section_id": "rule-15f",
                "section_title": "Rule 15(f): Sanitation Worker Occupational Safety & Mandatory PPE",
                "page_number": 19,
                "content": "Local authorities must ensure all sanitation workers and waste collectors are provided with appropriate personal protective equipment including heavy-duty puncture-resistant nitrile or leather gloves, slip-resistant safety boots, particulate dust masks, and high-visibility neon waistcoats. Direct manual contact with mixed waste is prohibited.",
                "is_statutory": True,
            },
            {
                "section_id": "rule-15h",
                "section_title": "Rule 15(h): Source Segregation & Non-Burning Mandate",
                "page_number": 22,
                "content": "Municipal waste must be handled in segregated streams: wet biodegradable waste, dry recyclable materials, and domestic hazardous waste. Open burning of street litter, leaves, packaging, or biomass is strictly prohibited under Environment (Protection) Act, 1986, with statutory environmental damages.",
                "is_statutory": True,
            },
            {
                "section_id": "rule-15u",
                "section_title": "Rule 15(u): Enclosed and Spill-Proof Waste Transportation",
                "page_number": 25,
                "content": "Waste transport vehicles must be fully enclosed with mechanical tippers or securely covered with tarpaulins to eliminate waste spillage, airborne littering, and leachate leakage onto public streets during transport to transfer stations.",
                "is_statutory": True,
            },
            {
                "section_id": "rule-15v",
                "section_title": "Rule 15(v): Storage Platform Sanitization & Vector Control",
                "page_number": 27,
                "content": "Secondary waste collection sites and public bin surrounds must be placed on impermeable concrete bases. Upon waste clearance, the ground surface must be washed and treated with disinfectant powder (hydrated lime/bleaching powder) to prevent fly breeding and rodent infestation.",
                "is_statutory": True,
            },
        ],
    },
    {
        "id": "DOC-CPHEEO-MSW-2021",
        "source_id": "SRC-CPHEEO-01",
        "source_domain": "cpheeo.gov.in",
        "source_org": "Central Public Health & Environmental Engineering Organisation (CPHEEO)",
        "title": "CPHEEO Manual on Municipal Solid Waste Management (Chapter 3: Primary Collection, Street Cleansing & Safety)",
        "url": "https://cpheeo.gov.in/upload/uploadfiles/files/Part2_MSW_Manual_Chapter3.pdf",
        "publication_date": "2021-01-18",
        "document_version": "Revised Edition 2021",
        "document_status": "CURRENT",
        "applicable_category": "Sanitation & Garbage",
        "content_type": "application/pdf",
        "summary": "Engineering guidelines for street cleansing operations, chronic waste blackspot clearance, ergonomic brooms, wheelbarrows, and traffic zone safety for conservancy staff.",
        "sections": [
            {
                "section_id": "sec-3.2",
                "section_title": "Section 3.2: Ergonomic Street Cleansing & Tool Selection",
                "page_number": 34,
                "content": "Conservancy workers must be equipped with long-handled straight brooms, flat metal scrapers for compacted street muck, dual-bin containerized wheelbarrows, and metal dustpans to avoid stooping and prevent musculoskeletal injury.",
                "is_statutory": False,
            },
            {
                "section_id": "sec-3.4",
                "section_title": "Section 3.4: Worker Traffic Safety in Heavy Urban Corridors",
                "page_number": 38,
                "content": "When cleaning roadside gutters and medians, high-visibility waistcoats must be worn at all times. In high-speed traffic zones, two retro-reflective safety cones must be placed 20m behind the cleaning crew.",
                "is_statutory": True,
            },
            {
                "section_id": "sec-3.7",
                "section_title": "Section 3.7: Remediation of Overflowing Chronic Dump Spots",
                "page_number": 42,
                "content": "For chronic illegal dumping spots, primary collection crew must clear the accumulated volume using skid-steer loader or shovel, follow with pressurized water washing if stained with food waste, and apply calcium hypochlorite (bleaching powder) at 50g per square meter.",
                "is_statutory": False,
            },
        ],
    },
    {
        "id": "DOC-MPCB-HAZ-2016",
        "source_id": "SRC-MPCB-01",
        "source_domain": "mpcb.gov.in",
        "source_org": "Maharashtra Pollution Control Board (MPCB)",
        "title": "MPCB Protocol for Identification and Escalation of Biomedical and Hazardous Waste Contaminants",
        "url": "https://mpcb.gov.in/waste-management/hazardous-waste-guidelines-escalation",
        "publication_date": "2016-03-28",
        "document_version": "BMW-HW-SOP-2016-REV",
        "document_status": "CURRENT",
        "applicable_category": "Sanitation & Garbage",
        "content_type": "text/html",
        "summary": "Mandatory protocol prohibiting ordinary municipal sanitation staff from handling biomedical waste, toxic chemicals, batteries, and animal carcasses. Immediate hazardous escalation and cordoning.",
        "sections": [
            {
                "section_id": "prot-4.1",
                "section_title": "Protocol 4.1: Hazardous & Biomedical Waste Visual Cues",
                "page_number": 2,
                "content": "Visual cues for hazardous or biomedical contamination include: red/yellow biohazard bags, discarded medical syringes/needles/catheters, expired blister pharmaceuticals, chemical carboys, leaking acid containers, lithium-ion battery banks, or dead animal carcasses.",
                "is_statutory": True,
            },
            {
                "section_id": "prot-4.2",
                "section_title": "Protocol 4.2: Mandatory Cordoning & Emergency Escalation Directive",
                "page_number": 4,
                "content": "MANDATORY SAFETY DIRECTIVE: General municipal sanitation workers, sweepers, and standard compactor trucks are strictly prohibited from touching, collecting, compacting, or transporting hazardous or biomedical waste. The field officer must immediately cordon the area with yellow barrier tape (minimum 5m perimeter), halt general collection, and transmit an emergency escalation notice to the MPCB-Authorized Common Bio-Medical / Hazardous Waste Operator within 2 hours.",
                "is_statutory": True,
            },
        ],
    },
]

def get_seed_documents() -> List[Dict[str, Any]]:
    docs = []
    for d in SEED_GUIDANCE_DOCUMENTS:
        raw_text_parts = [d["title"], d["summary"]]
        for s in d["sections"]:
            raw_text_parts.append(f"{s['section_title']}: {s['content']}")
        raw_text = "\n\n".join(raw_text_parts)
        file_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

        docs.append({
            "id": d["id"],
            "source_id": d["source_id"],
            "source_domain": d["source_domain"],
            "source_org": d["source_org"],
            "title": d["title"],
            "url": d["url"],
            "publication_date": d["publication_date"],
            "document_version": d["document_version"],
            "document_status": d["document_status"],
            "applicable_category": d["applicable_category"],
            "content_type": d["content_type"],
            "file_hash": file_hash,
            "raw_text": raw_text,
            "summary": d["summary"],
            "sections_json": json.dumps(d["sections"]),
            "is_approved": True,
        })
    return docs

