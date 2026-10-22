# CIVILENS — Academic Demonstration Guide
## Scope Freeze: Two Core Civic Use Cases

This guide provides the authoritative step-by-step presentation script for demonstrating **CIVILENS** during academic reviews, vivas, and faculty evaluations.

Following faculty feedback, the demonstration is strictly frozen to **two well-developed core civic use cases**:
1. **Pothole & Road-Damage Detection** (YOLOv8s RDD2022)
2. **Garbage & Street-Litter Detection** (YOLO11s TACO)

All broader civic categories (flooding, waterlogging, streetlights) are treated as **out of scope** for automated vision and deferred to a dedicated Future Work section.

---

## Prerequisites Before the Demo

1. Backend running: `uvicorn app.main:app --port 8000`
2. Frontend running: `cd frontend && npm run dev` (`http://localhost:5173`)
3. Primary fixture images in `data/test_samples/`:
   - `repair_pothole_before.jpg` (Pothole defect)
   - `bottle.jpg` or `litter.jpg` (Municipal street litter)
   - `repair_pothole_after_repaired.jpg` (Repaired asphalt patch)

> **Pre-Seeded Data**: Seed issues `CIVIC-2026-001` through `CIVIC-2026-006` are stored in persistent SQLite to immediately demonstrate spatial clustering, near-duplicate detection, and historical recurrence.

---

## Primary 5-Step Demonstration Sequence

```
Step 1: Pothole Intake & Vision (YOLOv8s)
    ↓
Step 2: Garbage Intake & Vision (YOLO11s TACO)
    ↓
Step 3: Cross-Category Mismatch Validation (Road Text + Garbage Photo)
    ↓
Step 4: Pothole Before-and-After Repair Verification (SSIM + YOLO)
    ↓
Step 5: Prioritization, GIS Locations & Department Routing (Dual-Category Synthesis)
```

---

### STEP 1: Submit a Pothole Complaint with Image

#### Objective
Demonstrate genuine computer vision road-damage inference (`YOLOv8s RDD2022`), bounding box localization, visual severity estimation, and automated dispatch routing.

#### Actions
1. In the Web UI, navigate to **"Analyze Complaint"** (or click **"+ New Issue"** in the top bar).
2. Click the preset button **"1. Pothole / Road"** (or manually input):
   - **Complaint Text**: `"Critical deep pothole crater breaking wheel rims and causing major skidding risk near school entrance."`
   - **Location**: `"Somaiya Vidyavihar Main Gate, Vidyavihar East"`
   - **Attach Image**: `data/test_samples/repair_pothole_before.jpg`
3. Click **"Run Analysis Pipeline"** (or **"Submit Complaint"**).

#### Expected System Behavior
- **Category Identified**: `Roads & Footpaths` (NLP TF-IDF confidence ~0.85+).
- **Vision Model Selected**: `RoadDamageDetector` invokes genuine `YOLOv8s RDD2022` inference.
- **Detected Object**: `Pothole (D40)` with normalized bounding box coordinates.
- **Visual Severity**: Estimated from normalized bounding box area (~0.35–0.60).
- **Evidence Consistency**: **CONSISTENT** (score ~0.96) — text claim matches detected asphalt crater.
- **Department Routing**: Routed to **Roads & Traffic Infrastructure Dept (MCGM)** (SLA: 12 Hours).
- **Priority Score**:
  - *Isolated Submission*: ~45–55 pts (**MEDIUM**).
  - *Corridor Cluster* (e.g. `CIVIC-2026-001` with duplicate amplification): escalates to **~85–88 pts (CRITICAL)**.

---

### STEP 2: Submit a Garbage / Street-Litter Complaint with Image

#### Objective
Demonstrate the task-specific municipal waste detector (`YOLO11s TACO`), multi-object litter bounding boxes, sanitation routing, and transparent disclosure of model uncertainty.

#### Actions
1. Click **"2. Garbage / Litter"** preset:
   - **Complaint Text**: `"Accumulated municipal garbage dump with discarded plastic bottles, cups, and decaying cartons along sidewalk creating extreme stench."`
   - **Location**: `"Station Road, Kurla West"`
   - **Attach Image**: `data/test_samples/bottle.jpg` (or `litter.jpg`)
2. Click **"Run Analysis Pipeline"** (or **"Submit Complaint"**).

#### Expected System Behavior
- **Category Identified**: `Sanitation & Garbage`.
- **Vision Model Selected**: `WasteDetector` invokes genuine `YOLO11s TACO` inference.
- **Detected Objects**: Multi-item detection (e.g. `Bottle / Container`, `Bottle Cap / Small Plastic`).
- **Evidence Consistency**: **CONSISTENT** (score ~0.94) — text hazard aligns with visible waste.
- **Department Routing**: Routed to **Solid Waste Management (SWM Dept)** (SLA: 24 Hours).
- **Scientific Honesty & Uncertainty Disclosure**:
  - Upstream published benchmark: `mAP50 = 0.311`.
  - Local street-level precision: **27.3% Prec@50** due to complex asphalt and debris backgrounds.
  - Transparent policy: Issues are routed for human supervisory review; detections are never overstated.

---

### STEP 3: Test Cross-Category Evidence Mismatch (Road Complaint + Garbage Image)

#### Objective
Demonstrate multimodal cross-validation detecting discrepancies between citizen narrative and attached photographic evidence. The waste detector assists in identifying the alternative defect.

#### Actions
1. Click **"3. Cross-Check Mismatch"** preset:
   - **Complaint Text**: `"Massive asphalt crater and structural road fissure breaking vehicle suspensions on main transit corridor."` (Claims severe road damage)
   - **Location**: `"S.V. Road, Santacruz"`
   - **Attach Image**: `data/test_samples/bottle.jpg` (Shows beverage container, NOT road damage)
2. Click **"Run Analysis Pipeline"** (or **"Submit Complaint"**).

#### Expected System Behavior
- **Text Category Identified**: `Roads & Footpaths` (based on citizen text).
- **Vision Detector Cross-Modal Execution**:
  - `RoadDamageDetector` finds 0 road defects.
  - Pipeline executes cross-modal check using `WasteDetector`.
  - `WasteDetector` confirms `Bottle / Container` (confidence > 0.90).
- **Cross-Modal Consistency**: **INCONSISTENT** (Consistency Score: `0.25`).
- **Explainable Triage Rationale**:
  > *"Evidence discrepancy: Attached photograph indicates sanitation / waste debris rather than road defect. Routed for manual supervisory triage."*
- **Ethical Integrity**: The issue is **never marked as fake or fraudulent**. It is routed for human supervisory review with an explainable flag.

---

### STEP 4: Compare Pothole Before-and-After Repair Images

#### Objective
Demonstrate genuine computer-vision lifecycle verification using OpenCV Structural Similarity (SSIM), color histogram correlation, and dual YOLO defect clearance before ticket closure.

#### Actions
1. In the Web UI, navigate to **"Resolution Center"** (or click on issue `CIVIC-2026-001` in the queue and select **"Verify Resolution"**).
2. Inspect the pre-repair defect image: `data/test_samples/repair_pothole_before.jpg`.
3. Attach post-action repaired image: `data/test_samples/repair_pothole_after_repaired.jpg`.
4. Enter inspector remarks: `"Asphalt cold-mix patch completed by Ward N road maintenance team."`
5. Click **"Verify & Close Issue"** (or via API: `POST /api/v1/issues/{id}/verify`).

#### Expected System Behavior
- **Inspector Identity Recorded**: Server-side authenticated inspector `INSP-MUMBAI-01` recorded in audit trail.
- **OpenCV SSIM & Color Correlation**: Scene comparability calculated between before and after images (SSIM: `0.83`, Color correlation: `0.95`, Scene comparability: `0.86`).
- **YOLO Delta Clearance**: Dual `YOLOv8s` runs on the post-repair image, verifying 0 remaining `D40` pothole craters.
- **Resolution Status**: Updated to **LIKELY RESOLVED** (with transparent probabilistic phrasing; never claiming absolute certainty).
- **Audit History**: Permanent verification record added to `GET /api/v1/issues/{id}/verifications`.

---

### STEP 5: Inspect Priority Scores, GIS Locations & Department Routing

#### Objective
Demonstrate how both core categories are synthesized across the Tactical Spatial GIS Map, the 6-factor composite priority formula, and departmental SLA routing.

#### Actions
1. Open the **"Tactical Spatial Map"** (or Command Center Overview):
   - Left Column (55%): Deep Midnight GIS canvas showing Mumbai ward coordinates.
   - Right Column (45%): Priority Incident Queue ranked by multi-factor score.
2. Select the pothole incident (`CIVIC-2026-001`) and the garbage incident in the queue.
3. Compare the **Priority Breakdown**:
   - $\text{Urgency Points (0–20)}$: Text urgency keyword extraction.
   - $\text{Text Severity Points (0–20)}$: Lexical hazard severity.
   - $\text{Visual Severity Points (0–20)}$: Bounding box area scaled by confidence.
   - $\text{Related Reports Points (0–15)}$: Near-duplicate cluster amplification.
   - $\text{Recency Points (0–10)}$: Time decay over hours elapsed.
   - $\text{Location Risk Points (0–15)}$: DBSCAN hotspot corridor amplification.
   - **Total Composite Score**: Exactly 0–100 pts.
4. Compare **Department Routing & SLA**:
   - Pothole: Routed to **Roads & Traffic Infrastructure Dept (MCGM)** | SLA: 12h
   - Garbage: Routed to **Solid Waste Management (SWM Dept)** | SLA: 24h

---

## Out of Scope & Future Work

To maintain scientific integrity and project focus, the following categories are **explicitly out of scope** for the automated vision pipeline:

| Category | Operational Handling in Current Release | Future Work Roadmap |
|---|---|---|
| **Street Flooding / Waterlogging** | Zero synthetic bounding boxes. Text NLP routes to Hydraulic Engineering Dept (HED) with **`MANUAL REVIEW`** status. | Integrate IoT ultrasonic storm drain depth sensors and municipal SCADA telemetry. |
| **Streetlight & Electrical Failures** | Categorized and routed via text NLP to Electricity & Street Lighting Dept. | Deploy nighttime luminescent lux sensor networks and drone thermal imaging. |
| **Traffic Signal Failures** | Text NLP triage to Traffic Police & Safety Dept. | Integrate ATCS (Adaptive Traffic Control System) camera feeds. |
| **Unauthorized Construction** | Manual inspection flag. | Satellite multi-temporal SAR change detection. |

---

## Security & Role-Based Access Control (RBAC) Verification

```bash
# 1. Unauthenticated mutation rejected (401)
curl -X PATCH http://localhost:8000/api/v1/issues/CIVIC-2026-001/status \
  -H "Content-Type: application/json" \
  -d '{"status": "Resolved"}'
# Response: 401 Unauthorized

# 2. Inspector privilege escalation rejected (403)
curl -X POST http://localhost:8000/api/v1/routing/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-inspector-token" \
  -d '{"category": "Roads & Footpaths", "department": "Rogue", "code": "R", "actions": {"HIGH": ["Action", 1]}}'
# Response: 403 Forbidden ("Operation requires ADMIN privileges")
```

---

## Resetting Demonstration State

To restore the clean baseline seed dataset (`CIVIC-2026-001` through `CIVIC-2026-006`):
- Click **"Settings"** → **"Reset Demo Data"** in the Web UI.
- Or call API: `curl -X POST http://localhost:8000/api/v1/demo/reset -H "Authorization: Bearer demo-admin-token"`
