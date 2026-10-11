# CIVILENS — Academic Demonstration Guide

This guide provides a step-by-step walkthrough for demonstrating the core capabilities of the **CIVILENS** civic issue intelligence platform during academic presentations and technical reviews.

---

## Prerequisites Before the Demo

1. Backend running: `uvicorn app.main:app --port 8000`
2. Frontend running: `cd frontend && npm run dev` (`http://localhost:5173`)
3. Test sample images available in `data/test_samples/`:
   - `repair_pothole_before.jpg` (Pothole defect)
   - `litter.jpg` or `bottle.jpg` (Sanitation defect)
   - `street_flooding.jpg` (Street flooding defect)
   - `repair_pothole_after_repaired.jpg` (Repaired asphalt patch)

> **Demo Seed Data**: Issues `CIVIC-2026-001` through `CIVIC-2026-006` are pre-seeded in SQLite to demonstrate deduplication, spatial clustering, and historical recurrence out of the box.

---

## STEP 1: Submit a Road Damage (Pothole) Complaint with Image

### Objective
Demonstrate genuine computer vision road-damage inference (`YOLOv8s RDD2022`), localized bounding box extraction, visual severity calculation, and multimodal consistency.

### Actions
1. In the Web UI, click **"+ New Issue"** in the top bar.
2. Fill out the complaint:
   - **Complaint Text**: `"Critical deep pothole crater breaking wheel rims and causing major slowdown near bus stop."`
   - **Location**: `"Linking Road, Bandra West"`
   - **Attach Image**: Select `data/test_samples/repair_pothole_before.jpg`
3. Click **"Submit Complaint"** (or use API: `POST /api/v1/issues`).

### Expected System Behavior
- **Category Identified**: `Roads & Footpaths` (NLP TF-IDF confidence ~0.85+).
- **Vision Inference**: `RoadDamageDetector` executes genuine YOLOv8s inference.
- **Detected Object**: `Pothole (D40)` with normalized bounding box coordinates.
- **Visual Severity**: Evaluated at ~0.35–0.60 based on bounding box area.
- **Evidence Consistency**: **CONSISTENT** (score ~0.96) — text claim matches detected asphalt crater.
- **Department Routing**: Routed to **Road Maintenance Division** (code `RMD-01`).
- **Priority Level & Score**:
  - *Isolated Submission*: Freshly submitted isolated ticket without near-duplicates or corridor history scores **~45–55 pts (MEDIUM)**.
  - *Corridor Cluster*: Pre-seeded hotspot issues in active corridors with duplicate amplification (e.g. `CIVIC-2026-001`) escalate to **~85–88 pts (CRITICAL)**.

### Recovery / Troubleshooting
If the image upload times out, check that `uploads/` directory exists with write permissions or test directly via `POST /api/v1/analyze`.

---

## STEP 2: Submit a Street Litter / Sanitation Complaint with Image

### Objective
Demonstrate the task-specific municipal waste detector (`YOLO11s TACO`), multi-object litter bounding boxes, and sanitation routing.

### Actions
1. Click **"+ New Issue"**.
2. Fill out the complaint:
   - **Complaint Text**: `"Accumulated municipal garbage dump with discarded plastic bottles, cups, and decaying cartons along sidewalk."`
   - **Location**: `"Station Road, Kurla West"`
   - **Attach Image**: Select `data/test_samples/litter.jpg` (or `bottle.jpg`)
3. Click **"Submit Complaint"**.

### Expected System Behavior
- **Category Identified**: `Sanitation & Garbage`.
- **Vision Inference**: `WasteDetector` executes genuine YOLO11s inference.
- **Detected Objects**: Multi-item detection (e.g. `Plastic Waste / Wrapper`, `Bottle / Container`, `Disposable Cup`).
- **Visual Severity**: Modulated by detection bounding box scale (~0.50–0.75).
- **Evidence Consistency**: **CONSISTENT** (score ~0.94) — text hazard aligns with visible waste.
- **Department Routing**: Routed to **Solid Waste Management** (code `SWM-02` or `MCGM-SWM`).
- **Priority Score**: ~45–55 pts (**MEDIUM**) for an isolated new submission; escalates if recurrence accumulates.

---

## STEP 3: Submit a Flooding Complaint & Show Manual-Review Routing

### Objective
Demonstrate scientific honesty: the system **refuses to fabricate synthetic bounding boxes** for unvalidated visual tasks and transparently flags issues for manual engineering inspection.

### Actions
1. Click **"+ New Issue"**.
2. Fill out the complaint:
   - **Complaint Text**: `"Storm water drain blocked causing severe waterlogging during rain, municipal drainage backup."`
   - **Location**: `"Hindmata Underpass, Dadar"`
   - **Attach Image**: Select `data/test_samples/street_flooding.jpg`
3. Click **"Submit Complaint"**.

### Expected System Behavior
- **Category Identified**: `Water Supply & Drainage` (NLP TF-IDF confidence ~0.71+).
- **Vision Inference**: `FloodingDetector` identifies task as unsupported.
- **Zero Fabricated Bounding Boxes**: `detectedObjects` is strictly empty (`[]`).
- **Visual Severity**: Strictly `0.0` (zero artificial visual points generated).
- **Evidence Consistency**: **MANUAL REVIEW** (score `0.50`) with explainable rationale:
  > *"Inspection pending: Photographic evidence cannot confirm subsurface municipal water pipe rupture or source of leakage. Routed for field engineer pressure inspection."*
- **Department Routing**: Routed to **Hydraulic Engineering Department (HED)**.
- **Priority Integrity**: Text urgency (~0.55+) and text severity (~0.78) continue to calculate legitimate priority points (Score ~40–50, **MEDIUM**).

---

## STEP 4: Demonstrate Text–Image Discrepancy & Supervisory Triage

### Objective
Demonstrate multimodal cross-validation detecting discrepancies between citizen narrative and attached photographic evidence.

### Actions
1. Click **"+ New Issue"**.
2. Enter conflicting multimodal evidence:
   - **Complaint Text**: `"Massive asphalt crater and structural road fissure on main highway."` (Claims road damage)
   - **Location**: `"S.V. Road, Santacruz"`
   - **Attach Image**: Select `data/test_samples/litter.jpg` (Shows garbage, NOT asphalt damage)
3. Click **"Analyze"** or **"Submit Complaint"**.

### Expected System Behavior
- **Category Identified**: `Roads & Footpaths` (based on textual complaint).
- **Visual Detection**: `WasteDetector` detects litter items (`Bottle`, `Plastic`).
- **Cross-Modal Consistency**: **INCONSISTENT** (Consistency Score: `0.25`).
- **Reasoning Flagged**:
  > *"Evidence discrepancy: Attached photograph indicates sanitation / waste debris rather than road defect. Routed for manual supervisory triage."*
- **Ethical Integrity**: The complaint is **never marked as fake**. It is routed to supervisory triage with transparency.

---

## STEP 5: Spatiotemporal Prioritization, GIS Placement & Hotspot Clustering

### Objective
Demonstrate the GIS tactical map, spatial clustering (`DBSCAN`), near-duplicate detection, and the explainable 6-factor composite priority score.

### Actions
1. In the Web UI, view the **Tactical Spatial GIS Map** on the left panel (Dark GIS canvas, Mumbai base coordinates).
2. Hover over pins to inspect ward placement and hotspot polygons.
3. Select an issue from the queue (e.g. `CIVIC-2026-001` or the newly submitted pothole).
4. Inspect the **Priority Breakdown** card:
   - **Urgency Points**: 0–20 pts
   - **Text Severity Points**: 0–20 pts
   - **Visual Severity Points**: 0–20 pts (modulated by confidence)
   - **Related Reports Points**: 0–15 pts (duplicate amplification)
   - **Recency Points**: 0–10 pts (decay over hours)
   - **Location Risk Points**: 0–15 pts (hotspot corridor bonus)
   - **Total Composite Score**: Exactly 0–100 pts.
5. In the navigation sidebar, click **"Hotspot Analytics"** or open the API endpoint `GET /api/v1/hotspots` to show real Haversine DBSCAN clusters.

---

## STEP 6: Authorized Computer-Vision Resolution Verification

### Objective
Demonstrate genuine computer-vision lifecycle verification using OpenCV Structural Similarity (SSIM), color histogram correlation, and dual YOLO defect clearance.

### Actions
1. Click on an existing open road-damage issue (e.g. `CIVIC-2026-001`).
2. Click **"Verify Resolution"** button (opens Resolution Modal).
3. Attach post-action repaired image: `data/test_samples/repair_pothole_after_repaired.jpg`.
4. Enter notes: `"Patch repair completed by Ward N road maintenance team."`
5. Click **"Verify & Close Issue"** (invokes `POST /api/v1/issues/{id}/verify` with Inspector credentials).

### Expected System Behavior
- **Inspector Identity Recorded**: Server records authenticated inspector `INSP-MUMBAI-01`.
- **OpenCV SSIM & HSV Correlation**: Scene comparability calculated between before and after images.
- **YOLO Delta Inspection**: Dual YOLOv8s runs on the post-repair image.
- **Defect Clearance**: Confirms absence of active D40 pothole bounding boxes.
- **Resolution Status**: Updated to **LIKELY RESOLVED** (or **REQUIRES MANUAL VERIFICATION** if scene angle differs).
- **Audit History**: Permanent verification record added to `GET /api/v1/issues/{id}/verifications`.

---

## STEP 7: Unauthorized Requests Are Strictly Rejected

### Objective
Demonstrate RBAC security release gates: unauthenticated users cannot mutate data, inspectors cannot modify admin routing rules, and dev tokens are disabled in production.

### Actions (via Terminal or Postman)
1. **Unauthenticated Mutation Attempt**:
   ```bash
   curl -X PATCH http://localhost:8000/api/v1/issues/CIVIC-2026-001/status \
     -H "Content-Type: application/json" \
     -d '{"status": "Resolved"}'
   ```
   **Result**: `HTTP 401 Unauthorized` (`"Authentication required"`).

2. **Inspector Role Escalation Attempt** (trying to perform Admin action):
   ```bash
   curl -X POST http://localhost:8000/api/v1/routing/config \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer demo-inspector-token" \
     -d '{"category": "Roads & Footpaths", "department": "Rogue", "code": "R", "actions": {"HIGH": ["Illegal action", 1]}}'
   ```
   **Result**: `HTTP 403 Forbidden` (`"Operation requires ADMIN privileges. Current role: INSPECTOR."`).

3. **Admin Token Access**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/routing/config \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer demo-admin-token" \
     -d '{"category": "Roads & Footpaths", "department": "Roads & Traffic Infrastructure Dept (MCGM)", "code": "MCGM-ROADS", "actions": {"CRITICAL": ["Emergency crew dispatch", 2]}}'
   ```
   **Result**: `HTTP 200 OK` (`"status": "success"`).

---

## Resetting Demonstration State

If a demo session needs to be restarted from the baseline seed state:
1. In the Web UI, open **Settings** modal and click **"Reset Demo Data"**.
2. Or invoke via API with Admin credentials:
   ```bash
   curl -X POST http://localhost:8000/api/v1/demo/reset \
     -H "Authorization: Bearer demo-admin-token"
   ```
3. Baseline seed issues `CIVIC-2026-001` through `CIVIC-2026-006` are restored.
