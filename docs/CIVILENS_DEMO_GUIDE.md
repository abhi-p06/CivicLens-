# CIVILENS — Live Academic Demonstration & Viva Presentation Guide

**Domain**: Multimodal AI, Computer Vision, Spatiotemporal GIS, Civic Tech  
**Presentation Audience**: College Professors, Project Evaluators, Viva Examination Committee  
**Target Environment**: Local Demonstration (`http://localhost:5173` & `http://localhost:8000`)  
**Demo Duration**: 10–15 Minutes  

---

## 1. Demonstration Preparation Checklist

Before the faculty arrives or the demonstration begins, complete the following verification steps:

```bash
# 1. Start the FastAPI Backend Daemon (Port 8000)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. In a separate terminal, start the Vite Frontend Dev Server (Port 5173)
cd frontend && npm run dev

# 3. Verify System Health Endpoint
curl -s http://localhost:8000/api/v1/health | grep '"status":"healthy"'

# 4. Open Application in Chrome (Recommended Resolution: 1600 × 900)
open http://localhost:5173
```

### Demonstration Accounts:
- **Citizen Account**: `citizen@civilens.org` / `Citizen@123` (Name: Abhinay)
- **Municipal Officer Account**: `inspector@civilens.org` / `Inspector@123` (Name: Abhinay)
- **Administrator Account**: `admin@civilens.org` / `Admin@123` (Name: Municipal Operations Administrator)
*(Quick-fill buttons: Click **"Fill demo account"** on any login card).*

### Key Test Fixtures in `data/test_samples/`:
- `repair_pothole_before.jpg`: Severe road surface asphalt crater (pothole).
- `bottle.jpg` or `litter.jpg`: Discarded plastic beverage bottles and sidewalk litter.
- `repair_pothole_after_repaired.jpg`: Repaired road patch (asphalt cold-mix).

---

## 2. Core 5-Scenario Live Demonstration Sequence

```
┌────────────────────────────────────────────────────────────────────────┐
│  SCENARIO 1: Citizen Files a Pothole Grievance (GPS & Map Picker)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  SCENARIO 2: Citizen Files a Garbage Grievance (TACO YOLO11s)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  SCENARIO 3: Multimodal Discrepancy (Road Text + Trash Photo)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  SCENARIO 4: Officer Operations (Command Center, Guidance & Dossier)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  SCENARIO 5: Vision Model Comparison (Production YOLO vs Roboflow)     │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Scenario 1: Citizen Files a Pothole Grievance with GPS Capture

#### Objective:
Demonstrate citizen complaint intake, browser GPS detection (`navigator.geolocation`), geographic boundary validation (Mumbai/Navi Mumbai), genuine local YOLOv8s road defect detection, and explainable priority scoring.

#### Step-by-Step Procedure:
1. Navigate to `http://localhost:5173/login/citizen`.
2. Click **"Fill demo account"** and sign in.
3. On the Citizen Portal, click the **"+ File New Grievance"** button.
4. **Demonstrate Location Options**:
   - **Option A (GPS Detection)**: Click **"📍 Detect My Location"**. Observe the browser location prompt and the reverse-geocoded Mumbai street address preview (e.g. *Somaiya Vidyavihar, Vidyavihar East*).
   - **Option B (Interactive Map Picker)**: Click **"Select Location on Map"**. Click any intersection on the Leaflet map within Mumbai. Note how coordinates and ward code update dynamically.
5. Enter Grievance Narrative:
   - **Complaint Text**: `"Severe deep crater pothole near Vidyavihar arterial road breaking vehicle suspensions and creating accident hazard."`
   - **Select Category**: `Roads & Footpaths` (or leave as Auto-Detect).
   - **Attach Image**: Browse and upload `data/test_samples/repair_pothole_before.jpg`.
6. Click **"Submit Grievance"**.

#### Expected System Response:
- Success notification with a unique Tracking ID (e.g. `CIVIC-2026-XXXX`).
- Grievance immediately appears in the citizen's personal tracking list.
- Click **"View Details"**:
  - **Category**: `Roads & Footpaths`
  - **AI Optical Evidence**: Confirms `Pothole (D40)` with normalized bounding box.
  - **Evidence Consistency**: **CONSISTENT** (score ~0.96).
  - **Department Assigned**: **Roads & Traffic Infrastructure Dept (MCGM)**.
  - **Security Gate**: Confirm that internal model comparison diagnostics and technical metadata are **completely hidden from the Citizen view**.

#### Presenter Viva Script:
> *"Notice that CIVILENS doesn't just store the text. It uses browser GPS with strict bounding-box validation restricted to the Mumbai and Navi Mumbai metropolitan region. When the image is submitted, our backend PyTorch YOLOv8s RDD2022 detector inspects the pixels, localizes the D40 cavity, cross-validates the text claim, and routes the complaint directly to the MCGM Roads department with an explainable 24-hour SLA."*

---

### Scenario 2: Citizen Files a Garbage / Street-Litter Grievance

#### Objective:
Demonstrate the task-specific municipal waste detector (`YOLO11s TACO`), multi-object litter segmentation, solid waste department dispatching, and scientific transparency regarding model uncertainty.

#### Step-by-Step Procedure:
1. In the Citizen Portal, click **"+ File New Grievance"**.
2. Select or enter locality: `"Station Road, Kurla West"` (or pick on map).
3. Enter Complaint Text: `"Overflowing garbage dump with discarded plastic bottles, cups, and food cartons spilling onto pedestrian sidewalk."`
4. Attach Image: `data/test_samples/bottle.jpg` (or `litter.jpg`).
5. Click **"Submit Grievance"**.

#### Expected System Response:
- AI classifies grievance under `Sanitation & Garbage`.
- Backend invokes the task-specific `WasteDetector` (`YOLO11s TACO`).
- Detects multiple waste items (e.g. `Bottle / Container`, `Plastic Waste / Wrapper`).
- Routed to **Solid Waste Management (SWM Dept)** with a 24-hour SLA.
- Explainable priority score calculated (~45–65 pts).

#### Presenter Viva Script:
> *"Unlike naive systems that use a single generic image classifier, CIVILENS uses specialized models. For street litter, we deploy YOLO11s trained on the TACO taxonomy. It detects discrete recyclable materials like bottles, cans, and plastic packaging, allowing municipal teams to dispatch the correct waste compactor trucks."*

---

### Scenario 3: Multimodal Discrepancy Triage (Road Text + Garbage Photo)

#### Objective:
Demonstrate multimodal cross-validation detecting discrepancies between citizen narrative and attached photographic evidence without calling the citizen fraudulent.

#### Step-by-Step Procedure:
1. File a new complaint with contradictory information:
   - **Complaint Text**: `"Dangerous deep asphalt pothole breaking car axles on arterial carriageway."` (Claims road defect).
   - **Location**: `"S.V. Road, Bandra West"`
   - **Attach Image**: `data/test_samples/bottle.jpg` (Depicts a beverage bottle, NOT a road defect).
2. Click **"Submit Grievance"**.

#### Expected System Response:
- NLP identifies reported text category as `Roads & Footpaths`.
- Visual detector runs: `RoadDamageDetector` finds 0 road defects.
- Cross-modal check triggers `WasteDetector`, which detects `Bottle / Container` (confidence > 0.90).
- Evidence Consistency Flag: **`INCONSISTENT`** (Consistency Score: `0.25`).
- System Rationale:
  > *"Evidence discrepancy: Attached photograph indicates sanitation / waste debris rather than road defect. Routed for manual supervisory triage."*

#### Presenter Viva Script:
> *"This is a key technical differentiator. Traditional systems blindly accept photographs as dumb attachments. CIVILENS cross-checks the text against the image. When a citizen accidentally uploads a picture of a bottle while complaining about a pothole, the system flags the inconsistency and routes it for supervisory triage. Crucially, following ethical AI guidelines, we never mark the citizen as fraudulent."*

---

### Scenario 4: Municipal Officer Command Center & Ward Operations

#### Objective:
Demonstrate the upgraded Ward Operations Management System: Command Center database KPIs, action filters, task assignment to field teams, scheduling, AI Field Guidance with official statutory citations, and work order completion.

#### Step-by-Step Procedure:
1. Log out of Citizen and navigate to `http://localhost:5173/login/municipal`.
2. Click **"Fill demo account"** (`inspector@civilens.org` / `Inspector@123`) and log in.
3. **Inspector Command Center Overview**:
   - Highlight the **4 KPI Cards** with animated CountUp counters: Unassigned Complaints, High-Priority Complaints, Work in Progress, Resolved This Month.
   - Point out the **Secondary Metrics Strip**: Road vs Sanitation workload split and Ward-level distribution.
4. **My Action Queue**:
   - Demonstrate the filter pills: Click **"Unassigned"**, **"In Progress"**, **"High Priority"**, and **"All"**.
5. **Open the Issue Dossier**:
   - Click on the high-priority pothole complaint (`CIVIC-2026-23363092` or `CIVIC-2026-001`).
   - The **Issue Detail Drawer** slides open from the right.
6. **AI Field Guidance Section**:
   - Scroll to **"AI Field Guidance"**.
   - Show the grounded recommendations:
     - **Immediate Precautions**: Traffic warning signs (50m/100m advance), retro-reflective safety vests.
     - **Recommended Field Actions**: Subgrade moisture checks, neat rectangular saw-cut edge trimming, RS-1 cationic tack coat, mechanical vibratory compaction.
     - **Statutory Citations**: MoRTH Section 3004 / IRC:82-2023, MCGM Monsoon Pothole SOP.
   - Click **"Accept Recommendation"** on an item. Notice how it injects the statutory checklist into the officer's work instructions!
7. **Complaint Assignment & Scheduling**:
   - Under **"Operational Task Assignment"**:
     - Department: `Roads & Traffic Infrastructure Dept (MCGM)`
     - Predefined Field Team: Select `Ward N Asphalt Patch Crew (TEAM-RDS-N01)`
     - Assigned Officer: `Abhinay`
     - Scheduled Date: Select tomorrow's date.
     - Work Instructions: Add notes.
   - Click **"Assign & Schedule Work Order"**. Status updates to `ASSIGNED` / `SCHEDULED`.
8. **Field Execution & Closure**:
   - Demonstrate **Temporary Safety Measures**: Select `Barricades Erected` & `Hazard Cones Placed`.
   - Under **"Task Completion & Outcome"**:
     - Enter contractor ID: `CONT-RDS-402`
     - Completion notes: `Cold mix patch compacted to zero deflection. Finished flush with carriageway.`
     - Upload post-repair photo: `data/test_samples/repair_pothole_after_repaired.jpg`.
   - Click **"Submit Completion & Resolve"**. Issue transitions to `RESOLVED`.

#### Presenter Viva Script:
> *"The Municipal Officer workspace bridges the gap between AI triage and real-world municipal execution. The officer has full database-driven situational awareness. Furthermore, our AI Field Guidance system doesn't generate ungrounded text—it cites official Ministry of Road Transport and Highways specifications and MCGM Monsoon standard operating procedures, ensuring field crews follow statutory engineering standards."*

---

### Scenario 5: Vision Model Comparison (Production Baseline vs Roboflow Hosted)

#### Objective:
Demonstrate the deep learning evaluation panel in the Issue Dossier, comparing CIVILENS's local production baseline with the experimental Roboflow Serverless API candidate.

#### Step-by-Step Procedure:
1. In the Issue Dossier, scroll to **"Vision Model Comparison"** (located directly below Optical Evidence).
2. Highlight the **Metric Strip**:
   - Local Detections vs Hosted Detections.
   - Side-by-side Latency: Local PyTorch on CPU (~50ms) vs Cloud Serverless (~650ms).
   - Cache State: `cached: false` (or `cached: true` for repeated queries).
3. **Interactive Bounding Box Inspector**:
   - Click the **"🚗 Local YOLO Baseline"** tab: Shows purple/indigo bounding boxes localized by `YOLOv8s RDD2022` with granular class names (`Pothole D40`).
   - Click the **"⚡ Roboflow Hosted"** tab: Shows cyan bounding boxes from hosted candidate `potholes-krmk8/2` (YOLO26).
   - Note: They are never overlaid simultaneously by default to prevent visual confusion.
4. **Separated Breakdown Panels**:
   - Point out the **Production Baseline Panel**: Clearly explains that local YOLO drives production severity, priority scores, and department routing.
   - Point out the **Hosted Candidate Panel**: Clearly states that hosted results are for experimental evaluation only and do not alter production dispatching.
   - Note the **Ground-Truth Evaluation Disclaimer** at the bottom.

#### Presenter Viva Script:
> *"We integrated the Roboflow Serverless API to rigorously test cloud candidate models against our local models. Notice that our local model runs in 50 milliseconds directly on CPU without sending citizen images over the public internet. The hosted cloud model takes over 650 milliseconds and loses crack detection taxonomy. That's why CIVILENS keeps local YOLO authoritative while using Roboflow for benchmarking."*

---

## 3. Important Points NOT to Claim to Evaluators

To maintain scientific integrity during your presentation and viva, avoid the following exaggerations:

1. ❌ **Do NOT claim live municipal deployment**: CIVILENS is an academic research prototype and municipal operations model; it is not currently wired into the live BMC municipal SAP/ERP servers.
2. ❌ **Do NOT claim automated flooding vision**: Flooding and streetlights are categorized via text NLP only with zero synthetic bounding boxes.
3. ❌ **Do NOT claim 100% waste detection precision**: Be honest that municipal street litter precision is 81.33% at conf=0.45, with human supervisory review required.
4. ❌ **Do NOT claim hosted models run in production**: Roboflow models are strictly benchmarking candidates; local YOLO models drive production priority.
5. ❌ **Do NOT claim the demo images are field surveys**: Acknowledge that seed issues and test samples are curated verification fixtures.

