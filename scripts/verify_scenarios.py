import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from app.models.issue import IssueCreate
from app.core.pipeline import pipeline

def run_scenarios():
    scenarios = [
        {
            "name": "Scenario 1: Road Damage / Severe Pothole",
            "payload": IssueCreate(
                complaintText="Deep crater and huge pothole in front of Somaiya Vidyavihar campus gate. Two bikers skidded this morning causing severe accident risk.",
                location="Vidyavihar",
                imageUrl="data/sample_pothole.jpg",
                source="citizen_mobile_app"
            )
        },
        {
            "name": "Scenario 2: Sanitation / Overflowing Garbage Spill",
            "payload": IssueCreate(
                complaintText="Massive overflowing garbage dump on LBS Marg, Ghatkopar West. Debris and rotting waste spreading onto main road creating unbearable stench.",
                location="LBS Marg, Ghatkopar West",
                imageUrl="data/sample_garbage.jpg",
                source="ward_portal"
            )
        },
        {
            "name": "Scenario 3: Water Supply / Burst Pipeline Flooding",
            "payload": IssueCreate(
                complaintText="Underground drinking water main line burst on 90 Feet Road, Dharavi. Clean potable water gushing and flooding entire street for 12 hours.",
                location="Dharavi",
                imageUrl="data/sample_water_leak.jpg",
                source="whatsapp_helpline"
            )
        }
    ]

    print("=" * 80)
    print("CIVILENS MULTIMODAL PIPELINE VERIFICATION RUN")
    print("=" * 80)

    for sc in scenarios:
        print(f"\n>>> Running {sc['name']}")
        result = pipeline.analyze(sc["payload"])
        print(f"  • Complaint Text     : {result['complaintText'][:70]}...")
        print(f"  • Category (NLP)     : {result['category'].value} (conf: {result['categoryConfidence']}, mode: {result['classificationMode']})")
        print(f"  • Urgency Score (U)  : {result['urgency']} (Cues: {result['urgencyCues']})")
        print(f"  • Resolved Location  : {result['resolvedLocation']} (Ward: {result['ward']}, Lat: {result['latitude']}, Lng: {result['longitude']})")
        print(f"  • Duplicate Match    : {result['isDuplicate']} (Group: {result['duplicateGroup']}, Near Count: {result['nearDuplicateCount']})")
        print(f"  • Vision Detection   : {result['visualDetection']} (Severity V: {result['visualSeverity']}, Mode: {result['visionMode']})")
        print(f"  • Text-CV Alignment  : {result['consistencyFlag']} (Score: {result['evidenceConsistency']})")
        print(f"  • Spatiotemporal     : Recurrence={result['recurrence']}, Hotspot={result['isHotspot']}, Cluster={result['hotspotClusterId']}")
        print(f"  • Priority Advisory  : {result['priorityLevel'].value} ({result['priorityScore']:.2f}) [Formula: 20U + 20T + 20V + 15F + 10R + 15L = 100 pts]")
        print(f"  • Dept Routing       : {result['department']}")
        print(f"  • Action Directive   : {result['recommendedAction']} (SLA: {result['slaHours']}h)")

    print("\n" + "=" * 80)
    print("ALL 3 SCENARIOS EXECUTED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    run_scenarios()
