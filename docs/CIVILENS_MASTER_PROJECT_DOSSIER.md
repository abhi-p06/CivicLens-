# CIVILENS — Master Project Documentation & AI Handover Dossier
## Multimodal Civic Issue Detection & Priority Advisory Engine (NLP + YOLO + GIS)

**Repository**: `chiragwalaproj`  
**Document Version**: 2.4 (Comprehensive Master Handover Edition)  
**Publication Date**: November 2026  
**Target Audience**: Academic Evaluators, University Faculty, Technical Auditors, AI Systems (ChatGPT, Claude) for Viva & Presentation Preparation  
**Lead Developer / Maintainer**: Abhinay  

---

# TABLE OF CONTENTS

1. **Part 1 — Project Audit & Empirical Verification Status**
2. **Part 2 — Project Overview & Problem Statement**
3. **Part 3 — Problem Statement and Solution Mapping**
4. **Part 4 — Complete System Architecture & Data Flow**
5. **Part 5 — User Roles and Functional Workflows**
6. **Part 6 — Artificial Intelligence & Computer Vision Pipeline**
7. **Part 7 — Explainable Severity & 6-Factor Dynamic Prioritization**
8. **Part 8 — Tactical GIS, Geolocation & Geographic Boundaries**
9. **Part 9 — Municipal Ward Operations & Grievance Lifecycle**
10. **Part 10 — AI Field Guidance & Statutory Standards Knowledge Base**
11. **Part 11 — Datasets, Training Provenance & Empirical Experiments**
12. **Part 12 — Comprehensive Technology Stack & Justifications**
13. **Part 13 — Complete REST API & Relational Database Reference**
14. **Part 14 — Project Security, Cryptography & Privacy Boundaries**
15. **Part 15 — Testing, Verification & Regression Test Suite**
16. **Part 16 — Repository Structure & File Organization Map**
17. **Part 17 — Reproducible Setup, Installation & Execution Guide**
18. **Part 18 — Live Academic Demonstration Walkthrough**
19. **Part 19 — Architectural History & Key Engineering Decisions**
20. **Part 20 — Known Limitations & Future Scope**
21. **Part 21 — Student-Friendly Technical Glossary**
22. **Part 22 — Questions Another AI Must Be Able to Answer**
23. **Part 23 — Presentation Preparation Reference (30s, 1m, 3m Overviews)**
24. **Part 24 — Quality Signoff & Auditor Attestation**

---

# PART 1 — PROJECT AUDIT & EMPIRICAL VERIFICATION STATUS

Before preparing this master dossier, a comprehensive source-code and empirical audit of the CIVILENS repository was conducted. Every technical claim in this document is confirmed by active Python modules, React components, SQLAlchemy ORM models, or verified automated tests.

### Audit Summary:
- **Backend Test Suite**: Exactly **244 passing tests** across 26 test files (`tests/`), including 16 Roboflow integration tests (`tests/test_roboflow_integration.py`).
- **Frontend Production Build**: Compiled cleanly via `tsc -b && vite build` in **327ms** with **0 TypeScript errors and 0 Vite warnings**.
- **Real-Browser Automation**: Verified end-to-end via headless Chrome automation (`scripts/verify_comparison_ui.py`) covering all 6 test scenarios across Citizen, Inspector, and Admin roles.
- **Relational Persistence**: Exactly **9 SQLAlchemy ORM tables** mapped and verified in SQLite WAL mode.
- **Active Deep Learning Checkpoints**:
  - `models/yolov8s_rdd2022.pt`: 11.14M parameters (SHA-256: `2cf3f6...`).
  - `models/taco_yolo11s.pt`: 9.43M parameters (SHA-256: `1b9c83...`).
- **External API Integrations**: Roboflow Serverless API (`https://serverless.roboflow.com`) with persistent SHA-256 caching (`data/cache/roboflow_predictions_cache.json`).
- **Geographic Boundary**: Hard-coded boundary checks (`app/modules/gis/bounds.py`, `frontend/src/config/geo.ts`) restricting complaints to Greater Mumbai and Navi Mumbai (`18.85` to `19.33` N, `72.75` to `73.18` E).

---

# PART 2 — PROJECT OVERVIEW & PROBLEM STATEMENT

### 1. Full Project Name and Meaning
**CIVILENS** is an acronym and portmanteau for **Civic Infrastructure Intelligence and Spatial Operations Lens**. It represents an intelligent, multimodal "lens" through which municipal operations centers can objectively observe, quantify, prioritize, and track civic infrastructure defects.

### 2. Introduction
CIVILENS is an explainable multimodal civic intelligence platform designed for municipal operations command centers. It converts unstructured citizen grievances (text and smartphone photos) into structured, mathematically prioritized, and auditable municipal interventions.

### 3. The Problem
Municipal public works and sanitation departments in developing urban centers operate under acute operational friction:
- **Textual Ambiguity**: Citizens file subjective complaints such as *"huge pothole near my house"* or *"smelly trash everywhere"*. Municipal staff have no objective way to determine whether a pothole is a minor 2-inch depression or a 10-inch axle-breaking crater.
- **Duplicate Ticket Flooding**: A single visible pothole on a major arterial corridor like the Western Express Highway generates dozens of repetitive complaints from commuters. Traditional portals treat each as an independent ticket, creating false workload spikes, dispatch redundancy, and administrative backlog.
- **Unverified Claims & Misfiling**: Traditional systems accept images as passive file attachments. They do not cross-check whether the attached photo matches the written complaint, leading to misrouted complaints and wasted field inspections.
- **Crude FIFO Triage**: Tickets are traditionally handled First-In, First-Out (FIFO) or sorted by arbitrary check-boxes. Dangerous defects near high-speed flyovers or school zones frequently sit unattended behind minor cosmetic issues.
- **Lack of Standardized Field Guidance**: Dispatched field crews lack immediate access to statutory engineering standards (such as MoRTH road repair specifications or CPCB solid waste rules), leading to sub-standard repairs that fail within weeks.

### 4. Project Motivation
The motivation behind CIVILENS is to build a scientifically rigorous, transparent, and ethically sound decision-support engine. Rather than replacing human municipal officers with an unreviewable "black box," CIVILENS provides explainable recommendations, transparent uncertainty metrics, and human-in-the-loop governance.

### 5. Main Objectives
1. Automatically detect, localize, and classify road damage and street litter from citizen photographs using deep convolutional neural networks.
2. Cross-validate citizen text claims against photographic evidence to identify misfilings without labeling citizens fraudulent.
3. Calculate an explainable, 6-factor additive priority score (0–100 points) based on physical urgency, visual severity, near-duplicate frequency, recency, and corridor hotspot status.
4. Cluster complaints geographically using Haversine DBSCAN to identify emerging infrastructure failure corridors.
5. Provide Municipal Officers with a Ward Operations Management workspace featuring statutory AI Field Guidance grounded in official government engineering standards.
6. Provide side-by-side benchmarking between local edge models and hosted cloud candidate models.

### 6. Target Users
- **Citizens**: Urban residents filing civic grievances, tracking remediation progress, and providing satisfaction feedback.
- **Municipal Officers / Ward Field Inspectors**: Ward engineers and triage supervisors who review prioritized queues, assign tasks to operational field teams, schedule repairs, and verify completion.
- **Municipal Administrators**: Executive officers who govern department routing rules, configure SLA response windows, manage field teams, and oversee system telemetry.

### 7. Geographic Scope
CIVILENS is configured for the **Greater Mumbai and Navi Mumbai** metropolitan areas under the operational model of the **Municipal Corporation of Greater Mumbai (MCGM / BMC)** and the **Navi Mumbai Municipal Corporation (NMMC)**.

### 8. The Two Primary Supported Categories (Scope Freeze)
Following faculty feedback, the platform's automated computer-vision perception is strictly frozen to **two well-developed primary use cases**:
1. **Potholes / Road Surface Damage**: Detection of potholes (`D40`), alligator fatigue cracking (`D20`), transverse cracks (`D10`), and longitudinal cracks (`D00`).
2. **Garbage Accumulation / Street Litter**: Multi-item detection of discarded packaging, plastic bottles, beverage cans, cartons, and roadside refuse.

*Broader civic categories (such as street flooding, water pipe bursts, and streetlight electrical faults) are handled via textual NLP and routed for human engineering inspection with zero synthetic bounding boxes.*

---

# PART 3 — PROBLEM STATEMENT AND SOLUTION MAPPING

| Existing Civic Grievance Problem | Why It Is Difficult to Manage | CIVILENS Feature Addressing It | Technology Involved | Expected Outcome |
|---|---|---|---|---|
| **Subjective Pothole Reporting** | Citizens describe defects vaguely without standard dimensions. | Deep Object Detection & Visual Severity Estimation | Ultralytics YOLOv8s fine-tuned on RDD2022 (`models/yolov8s_rdd2022.pt`) | Automated bounding box localization, D00–D40 classification, and defect area quantification. |
| **Street Litter & Waste Mismanagement** | Waste accumulation blocks storm drains and causes public health hazards. | Multi-Item Municipal Litter Detection | Ultralytics YOLO11s trained on TACO (`models/taco_yolo11s.pt`) | Multi-object segmentation across 9 waste categories with calibrated 0.45 confidence threshold. |
| **Crude Priority Triage** | First-In, First-Out queues neglect high-risk, life-threatening hazards. | Explainable 6-Factor Additive Priority Scoring | Mathematical Priority Engine (`app/modules/priority/engine.py`) | Authoritative 0–100 composite score escalating critical hazards to the top of the queue. |
| **Inaccurate Complaint Locations** | Citizens report vague landmarks or wrong postal addresses. | Browser GPS Detection & Interactive Map Picker | Browser Geolocation API + Leaflet GIS + Reverse Geocoding | Exact coordinate capture restricted to Mumbai/Navi Mumbai bounding box (`18.85–19.33` N, `72.75–73.18` E). |
| **Duplicate Ticket Flooding** | Multiple citizens report the same defect, creating redundant dispatches. | Spatiotemporal Near-Duplicate Deduplication | Geodesic Haversine ($250\text{m}$) + Jaccard Token Overlap | Groups near-duplicate reports into a single master ticket, amplifying friction score (+4 pts per duplicate). |
| **Infrastructure Corridors Overlooked** | Recurring failures along specific roads are treated as isolated events. | Hotspot Detection & Corridors Clustering | Haversine DBSCAN ($R=400\text{m}$, $\text{min\_samples}=2$) | Clusters incidents into spatial corridors (LOW, MODERATE, HIGH, SEVERE) with growth rate tracking. |
| **Mismatched / Erroneous Photo Evidence** | Citizens upload wrong images (e.g. trash photo for a road complaint). | Multimodal Text-Image Cross-Validation | CrossValidationEngine (`app/modules/cross_validation/validator.py`) | Identifies discrepancy (`INCONSISTENT`, 0.25 score) and routes for supervisory triage without calling citizens fraudulent. |
| **Sub-Standard Field Repairs** | Field crews use improper materials or skip essential compaction steps. | AI Field Guidance Grounded in Statutory Standards | GuidanceEngine (`app/services/guidance/`) + Knowledge Base | Synthesizes actionable instructions citing MoRTH Section 3004 and MCGM Monsoon SOPs. |
| **Lack of Operational Field Coordination** | Complaints sit unassigned; supervisors cannot track crew progress. | Ward Operations Management System | Command Center KPIs, Action Queue, Task Assignment | Enables officers to assign predefined teams, schedule work dates, log safety barricades, and review completion photos. |
| **"Phantom Repairs" & Closure Friction** | Contractors claim repair without proof; citizens complain tickets close prematurely. | Completion Proof & Citizen Reopen Workflow | UploadService + Citizen Portal Reopen & Feedback | Requires post-repair photo proof; allows citizens to rate satisfaction (1–5 stars) and reopen unresolved complaints. |

---

# PART 4 — COMPLETE SYSTEM ARCHITECTURE & DATA FLOW

CIVILENS is architected with a decoupled frontend, REST API service layer, modular AI inference pipelines, and persistent relational SQLite storage.

### 4.1 System Architecture Diagram (Mermaid)

```mermaid
graph TD
    subgraph Client Tier
        CP[Citizen Portal / Responsive Web]
        MO[Municipal Officer Command Center]
        AD[Admin Settings & Governance]
    end

    subgraph API Gateway & Security
        GW[FastAPI REST API /api/v1]
        SEC[Security: PBKDF2 Hashing & HMAC-SHA256 Tokens]
        GEO_VAL[Geographic Boundary Validator Lat 18.85-19.33]
        UPL[Image Upload Sanitizer Magic Bytes & Max 10MB]
    end

    subgraph Multimodal AI & Intelligence Pipeline
        NLP[Text NLP Grievance Classifier TF-IDF + Logistic Regression]
        ROAD_DET[Road Damage Detector YOLOv8s RDD2022]
        WASTE_DET[Waste & Litter Detector YOLO11s TACO]
        XVAL[Cross-Modal Consistency Matrix Text vs Vision]
        DEDUP[Near-Duplicate Deduplication Haversine + Jaccard]
        DBSCAN[Spatiotemporal Hotspots Haversine DBSCAN R=400m]
        PRIO[Explainable 6-Factor Priority Engine 0-100 pts]
        ROBO[Roboflow Serverless Adapter YOLO26 & RF-DETR]
        ROBO_CACHE[(Deterministic SHA-256 JSON Cache)]
    end

    subgraph Ward Operations & Guidance
        DISP[Department & SLA Dispatcher]
        OPS[Ward Operations: Teams, Schedules, Actions]
        GUIDE[AI Field Guidance Engine]
        KB[(Statutory Knowledge Base MoRTH, MCGM, CPCB)]
    end

    subgraph Data Persistence Tier
        DB[(Persistent SQLite Database WAL Mode)]
        FS[(Image Upload Storage /uploads)]
    end

    CP -->|Submit Grievance + Image| GW
    MO -->|Triage, Assign, Schedule, Close| GW
    AD -->|Govern Routing, Teams, Guidance| GW

    GW --> SEC
    GW --> GEO_VAL
    GW --> UPL

    UPL --> FS
    GW --> NLP
    GW --> ROAD_DET
    GW --> WASTE_DET
    ROAD_DET & WASTE_DET --> XVAL
    NLP --> XVAL

    ROAD_DET & WASTE_DET -.->|Optional Compare| ROBO
    ROBO <--> ROBO_CACHE

    GW --> DEDUP
    GW --> DBSCAN
    NLP & ROAD_DET & DEDUP & DBSCAN --> PRIO

    PRIO --> DISP
    DISP --> OPS
    OPS --> GUIDE
    GUIDE <--> KB

    OPS --> DB
    PRIO --> DB
    GW --> DB
```

---

### 4.2 Complaint Submission Sequence Diagram (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor Citizen
    participant UI as Citizen Portal (React)
    participant API as FastAPI Backend
    participant Geo as Geo Boundary Validator
    participant Upload as Upload Service
    participant AI as Pipeline Coordinator
    participant Vision as Local YOLO Detectors
    participant DB as SQLite Database

    Citizen->>UI: Clicks "Detect My Location" or picks point on map
    UI->>UI: Captures Lat/Lng via navigator.geolocation or Leaflet
    UI->>API: GET /api/v1/geo/reverse-geocode?lat=...&lng=...
    API-->>UI: Returns "Somaiya Vidyavihar, Vidyavihar East (N-Ward)"
    
    Citizen->>UI: Enters grievance text and attaches photo
    Citizen->>UI: Clicks "Submit Grievance"
    
    UI->>API: POST /api/v1/upload (multipart image)
    API->>Upload: Verify magic bytes, sanitize filename, write to disk
    Upload-->>API: Returns upload_id & file URL
    API-->>UI: Upload verified
    
    UI->>API: POST /api/v1/issues (text, location, upload_id, category)
    API->>Geo: Validate Lat/Lng within Mumbai/Navi Mumbai
    Geo-->>API: Coordinates Verified
    
    API->>AI: analyze_complaint(text, image_path, category)
    AI->>AI: Run NLP Classifier (TF-IDF + Logistic Regression)
    AI->>Vision: Run YOLOv8s (Road) or YOLO11s (Waste)
    Vision-->>AI: Detected Bounding Boxes & Confidence
    AI->>AI: Cross-Validate Text vs Vision Consistency
    AI->>AI: Run Haversine Deduplication & Hotspot Check
    AI->>AI: Compute 6-Factor Dynamic Priority Score (0–100)
    AI->>AI: Dispatch Department & SLA Hours
    
    AI->>DB: Persist IssueRecord & TimelineEvent
    DB-->>API: Issue Saved (e.g. CIVIC-2026-23363092)
    API-->>UI: HTTP 201 Created (Full Issue Dossier)
    UI-->>Citizen: Displays Tracking ID & Confirmation
```

---

### 4.3 AI Inference & Model Comparison Flow (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor Officer as Municipal Officer
    participant Drawer as Issue Detail Drawer
    participant API as FastAPI Backend
    participant Manager as Vision Pipeline Manager
    participant Local as Local PyTorch YOLO
    participant Roboflow as Roboflow Serverless API
    participant Cache as SHA-256 Cache

    Officer->>Drawer: Opens Complaint (e.g. CIVIC-2026-23363092)
    Drawer->>Drawer: Reads issue.metadata.visionComparison
    
    alt If Comparison already cached in Issue Metadata
        Drawer->>Drawer: Renders Vision Model Comparison UI immediately
    else If Comparison requested on-demand via Compare API
        Drawer->>API: POST /api/v1/vision/compare (image_path, category_hint)
        API->>Manager: compare_models(image_path, category_hint)
        
        Manager->>Local: Run Local YOLO (YOLOv8s RDD2022 or YOLO11s TACO)
        Local-->>Manager: Local Detections, Boxes, Latency (~50ms)
        
        Manager->>Cache: Check SHA-256 Image Hash
        alt Cache Hit
            Cache-->>Manager: Return Cached Hosted Predictions (0ms)
        else Cache Miss
            Manager->>Roboflow: HTTP POST /inference (potholes-krmk8/2 or garbage)
            Roboflow-->>Manager: Cloud Predictions & Latency (~650ms)
            Manager->>Cache: Save Response to Disk Cache
        end
        
        Manager-->>API: Aggregated Comparison Summary
        API-->>Drawer: HTTP 200 OK
    end
    
    Drawer->>Officer: Displays Side-by-Side Panels & Interactive Bounding Box Tabs
```

---

### 4.4 GIS Synchronization Sequence Diagram (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen / Inspector
    participant Frontend as Leaflet Tactical GIS Map
    participant API as FastAPI Backend
    participant DB as SQLite Database

    User->>Frontend: Navigates to Map View or Submits Issue
    Frontend->>API: GET /api/v1/gis/geojson
    API->>DB: SELECT * FROM issues WHERE status != 'ARCHIVED'
    DB-->>API: Returns list of 29 Active Records
    API->>API: Format as GeoJSON FeatureCollection
    API-->>Frontend: HTTP 200 OK (GeoJSON with Priority & Category properties)
    
    Frontend->>Frontend: Clear existing map layer
    Frontend->>Frontend: Plot CircleMarkers colored by Category (Indigo=Road, Emerald=Waste)
    Frontend->>Frontend: Attach Pulsing Ring to Critical Issues (Score >= 85)
    
    User->>Frontend: Clicks on Marker
    Frontend->>Frontend: Center and zoom map to coordinates
    Frontend->>Frontend: Open Issue Dossier Drawer with full record details
```

---

### 4.5 Role-Based Access Control (RBAC) Architecture (Mermaid)

```mermaid
graph TD
    subgraph Roles & Hierarchy
        C[Citizen Role Hierarchy = 1]
        I[Municipal Inspector Role Hierarchy = 2]
        A[Administrator Role Hierarchy = 3]
    end

    subgraph Security Layer
        AUTH[PBKDF2 Password Hash 100,000 Rounds + Salt]
        TOKEN[Signed HMAC-SHA256 Token 12h Expiration]
        GATE[Role Verification Dependencies require_citizen, require_inspector, require_admin]
    end

    subgraph Accessible Endpoints
        EP_C[Citizen Endpoints: File Grievance, View My Issues, Submit Feedback, Reopen Issue]
        EP_I[Inspector Endpoints: Command Center KPIs, Action Queue, Assign Task, Schedule, Action, Complete, View Guidance, View Model Comparison]
        EP_A[Admin Endpoints: User Management, CRUD Teams, Ward Configurations, Guidance Ingest & Allowlist, Demo Reset]
    end

    C --> AUTH
    I --> AUTH
    A --> AUTH
    AUTH --> TOKEN
    TOKEN --> GATE

    GATE -->|Role >= 1| EP_C
    GATE -->|Role >= 2| EP_I
    GATE -->|Role == 3| EP_A

    EP_I -.->|Inherits| EP_C
    EP_A -.->|Inherits| EP_I
    EP_A -.->|Inherits| EP_C
```

---

# PART 5 — USER ROLES AND FUNCTIONAL WORKFLOWS

CIVILENS implements three distinct operational roles enforced via cryptographic access tokens.

---

## 5.1 Citizen Experience

- **Account Management**: Self-registration and login via `POST /api/v1/auth/register` and `/api/v1/auth/login`. Default demo citizen: `citizen@civilens.org` (Name: Abhinay).
- **Location Capture**:
  - **Option A (GPS Detection)**: Uses the browser's native `navigator.geolocation` API to retrieve coordinates, which are reverse-geocoded to a human-readable street address via `/api/v1/geo/reverse-geocode`.
  - **Option B (Interactive Map Picker)**: Citizens can click on an interactive Leaflet map to pinpoint the exact location.
  - **Boundary Restriction**: Coordinates outside the Mumbai and Navi Mumbai metropolitan region are rejected immediately.
- **Image Upload**: Uploads photographic evidence securely through `/api/v1/upload`, where magic bytes are validated.
- **Tracking & Visibility**: Real-time status tracking (`Reported`, `Assigned`, `In Progress`, `Resolved`, `Reopened`).
- **Satisfaction Feedback & Reopen**: Citizens can submit 1–5 star ratings and comments. If a repair is unsatisfactory, citizens can reopen the complaint with a single click.
- **Security Boundary**: Citizens **never** see internal model diagnostics, Roboflow comparison panels, technical raw JSON metadata, or department dispatcher configuration.

---

## 5.2 Municipal Officer / Ward Inspector Experience

- **Inspector Command Center**:
  - 4 Real-time KPI Cards: Unassigned complaints, High-priority complaints, Work in progress, Complaints resolved this month.
  - Secondary Metrics Strip: Road vs Sanitation workload split, Ward-level complaint distribution.
- **My Action Queue**:
  - Triage feed with filter pills: `ALL`, `UNASSIGNED`, `IN_PROGRESS`, `HIGH_PRIORITY`, `RESOLVED`.
  - GlareHover cards displaying priority badges, category, composite score (0–100), complaint description, location, ward, consistency flag, and status.
- **Issue Detail Dossier**:
  - **Optical Evidence**: Shows bounding boxes, class labels, and confidence percentages.
  - **Vision Model Comparison**: Side-by-side inspection between Local YOLO and Roboflow Hosted Candidate.
  - **AI Field Guidance**: Statutory engineering recommendations (MoRTH / MCGM / CPCB).
  - **Operational Task Assignment**: Assigns complaint to predefined field teams (`Ward N Asphalt Patch Crew`, `Ward K Solid Waste Truck`), sets assigned officer, scheduled inspection date, and work instructions.
  - **Field Execution Actions**: Records temporary safety measures (hazard cones, barricades, warning tape), repeat collection cycles, and upload of post-repair photo proof with contractor ID.
  - **Closure & Reopening**: Resolves complaints or reopens them upon audit.
- **Boundary Note**: The full, separate "Resolution Center / Work-Order Lifecycle" page was removed from the Inspector sidebar navigation during refactoring; all inspection, guidance, and resolution workflows are housed within the **Issue Detail Drawer**.

---

## 5.3 Administrator Experience

- **User Governance**: Views all registered accounts and roles via `GET /api/v1/admin/users`.
- **Field Team Management**: Full CRUD operations on operational teams (`GET/POST/PATCH/DELETE /api/v1/admin/teams`).
- **Ward Configuration**: Manages ward boundaries, lead executive engineers, and team rosters (`/api/v1/admin/wards`).
- **Department Routing & SLA Engine**: Customizes department mappings, SLA hours, and emergency action protocols via `/api/v1/routing/config`.
- **Statutory Guidance Management**: Manages allowlisted research domains (`morth.nic.in`, `mcgm.gov.in`, `cpcb.nic.in`), approves documents, and ingests new specifications via `/api/v1/admin/guidance/*`.
- **Demonstration Reset**: Securely restores seed baseline complaints (`CIVIC-2026-001` through `006`) via `/api/v1/demo/reset`.

---

# PART 6 — ARTIFICIAL INTELLIGENCE & COMPUTER VISION PIPELINE

The computer-vision subsystem converts raw pixels into normalized, classified, and localized damage bounding boxes.

### 6.1 Conceptual Overview: How YOLO Works
YOLO (You Only Look Once) is a single-stage, anchor-free deep convolutional neural network. Unlike legacy two-stage detectors (e.g. Faster R-CNN) that first generate region proposals and then classify them, YOLO frames object detection as a single regression problem:
1. The input image is resized (e.g., $640 \times 640$ pixels) and passed through a convolutional backbone (e.g., modified CSPDarknet with C2f/C3k2 feature extractors and spatial pyramid pooling SPPF).
2. The network simultaneously predicts:
   - **Bounding Box Coordinates**: Center coordinates ($x, y$), width ($w$), and height ($h$).
   - **Objectness Confidence**: The probability that an object exists in that region.
   - **Class Probabilities**: The distribution across target classes (e.g., Pothole, Plastic Bottle).
3. Non-Maximum Suppression (NMS) eliminates redundant overlapping boxes using Intersection over Union (IoU) thresholding.

### 6.2 Key Machine Learning Terminology Explained
- **Object Detection vs. Classification**: Classification predicts *what* is in an image (one label for the entire image). Object Detection predicts *what* is in the image AND *where* it is located by drawing bounding boxes.
- **Bounding Box**: A rectangular coordinate boundary enclosing a detected defect. In CIVILENS, boxes are normalized to $[0.0, 1.0]$ in $[y_{\min}, x_{\min}, y_{\max}, x_{\max}]$ format.
- **Confidence Score**: A probability score ($0.00$ to $1.00$) representing the model's certainty that a defect exists within the bounding box.
- **Precision**: $\frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$. Measures what fraction of detected defects are real.
- **Recall**: $\frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$. Measures what fraction of actual street defects were successfully caught.
- **F1 Score**: The harmonic mean of precision and recall: $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$.
- **False Positive (FP)**: The model flags clean asphalt as a pothole or gravel as trash.
- **False Negative (FN)**: The model fails to detect an actual pothole or garbage pile.

---

### 6.3 Local Model 1: Road Damage Detector (`YOLOv8s RDD2022`)
- **Base Architecture**: Ultralytics YOLOv8 Small (`yolov8s`)
- **Model Checkpoint**: `models/yolov8s_rdd2022.pt` (11,137,148 parameters, ~11.14M)
- **Cryptographic Checksum**: `2cf3f60395de6591d8378294fc26b8d7c4ca8f227e455987b3713ce6eeeea119` (SHA-256)
- **File Size**: 22.53 MB
- **Dataset**: Crowdsensing-based Road Damage Detection Challenge 2022 (RDD2022), Sekilab / Maeda et al. (CC-BY-4.0).
- **Supported Classes**:
  - `0`: `D00` (Longitudinal Crack)
  - `1`: `D10` (Transverse Crack)
  - `2`: `D20` (Alligator Fatigue Crack)
  - `3`: `D40` (Pothole)
- **Operating Confidence**: `0.15` (calibrated for high sensitivity to hairline surface cracks).
- **Upstream Benchmark**: `0.4643 mAP@50` on RDD2022 official test split.

---

### 6.4 Local Model 2: Municipal Waste & Street Litter Detector (`YOLO11s TACO`)
- **Base Architecture**: Ultralytics **YOLO11 Small** (`yolo11s.yaml` with `C3k2` and `C2PSA` attention layers)
- **Model Checkpoint**: `models/taco_yolo11s.pt` (9,431,275 parameters, ~9.43M)
- **Cryptographic Checksum**: `1b9c8379aca95efa75ec1f6ac803cabd3ba531b7d4b3f459101bcfd3aaae95ef` (SHA-256)
- **File Size**: 19.19 MB (MIT License)
- **Dataset**: TACO (Trash Annotations in Context) municipal litter dataset (Proença & Simões, 2020).
- **Declared Classes (9 Classes)**: Plastic bag & wrapper, Cigarette, Bottle, Bottle cap, Can, Other plastic, Carton, Disposable cup, Other litter.
- **Operating Calibration**: Following Phase 10 empirical sweeps, operating confidence was raised from `0.20` to **`0.45`**, cutting False Positives by **54.8%** and boosting precision on held-out test data from 68.04% to **81.33%** while maintaining **70.52% recall**.

---

### 6.5 Roboflow Serverless Hosted Models (Experimental Candidates)

CIVILENS integrates the **Roboflow Serverless API** via `InferenceHTTPClient`:
1. **Pothole Model**:
   - Model ID: `potholes-krmk8/2`
   - Architecture: YOLO26 (Upstream Roboflow Train)
   - Primary Class: `Pothole` (Single class)
2. **Garbage Model**:
   - Model ID: `garbage_detection-wvzwv-n8vsv/1`
   - Architecture: RF-DETR Nano (Transformer-based object detection)
   - Primary Class: `garbage` (Single monolithic class)

#### Real-Browser Verification Results:
- Pothole Model: HTTP 200, one detection, **650.42 ms** latency, `cached: false`.
- Garbage Model: HTTP 200, one detection, **820.15 ms** latency, `cached: false`.
- Both requests executed over authentic citizen-submitted photographs.

#### Comparison: Local Baseline vs. Hosted Candidate

| Evaluation Dimension | Local Production Baseline | Roboflow Hosted Candidate | Architectural Decision |
|---|---|---|---|
| **Road Damage Models** | `models/yolov8s_rdd2022.pt` | `potholes-krmk8/2` (YOLO26) | **Local Retained**: Local detects cracks (`D00`, `D10`, `D20`) and potholes (`D40`). Hosted detects only potholes, missing 75% of road defect taxonomy. |
| **Waste Detection Models**| `models/taco_yolo11s.pt` | `garbage_detection-wvzwv-n8vsv/1` (RF-DETR) | **Local Retained**: Local outputs 9 distinct waste material classes. Hosted outputs a single generic `garbage` box. Local achieves +37.5% precision on street test split. |
| **Inference Latency** | **52.4 ms** (CPU PyTorch) | **650.4 ms – 820.2 ms** (Cloud Network) | **Local is ~12x faster**; zero cloud network latency. |
| **Operating Cost & Quota**| **100% Free & Unlimited** | Consumes monthly API plan credits | Local eliminates cloud billing and credit exhaustion risks. |
| **Citizen Data Privacy** | **100% Sovereign & Local** | Transmits images to US servers | Local protects citizen location privacy and meets municipal data residency policies. |
| **Operational Role** | **Authoritative Production** | **Benchmarking Candidate Only** | Local drives severity and priority scores. Hosted is strictly for side-by-side engineering comparison. |

---

# PART 7 — EXPLAINABLE SEVERITY & 6-FACTOR DYNAMIC PRIORITIZATION

CIVILENS avoids unreviewable "black box" priority scores. Instead, it computes an authoritative, additive 0–100 point score across 6 distinct risk components.

### 7.1 Authoritative 6-Factor Mathematical Formula

$$\text{Total Priority Score} = \min\Big(\max(0.0, \, U + T + V + F + R + L), \, 100.0\Big)$$

Where each component is bounded as follows:

1. **Urgency Points ($U \in [0.0, 20.0]$)**:
   $$U = \min(u \times 20.0, \, 20.0)$$
   Where $u \in [0.0, 1.0]$ is extracted by lexical hazard matching against critical keywords (*accident*, *death*, *injury*, *burst*, *live wire*, *open manhole*).
2. **Textual Severity Points ($T \in [0.0, 20.0]$)**:
   $$T = \min(t \times 20.0, \, 20.0)$$
   Where $t \in [0.0, 1.0]$ represents physical disruption magnitude extracted from complaint text.
3. **Visual Severity Points ($V \in [0.0, 20.0]$)**:
   If defect detected ($v > 0.0$):
   $$V = \min(v \times 20.0 \times \max(0.70, c), \, 20.0)$$
   Where $v$ is normalized bounding box surface area and $c$ is detector confidence. If no image or zero defects detected: $V = 0.0$.
4. **Related Reports Points ($F \in [0.0, 15.0]$)**:
   $$F = \min(3.0 + (f \times 4.0), \, 15.0)$$
   Where $f$ is the count of near-duplicate complaints within 250m. Amplifies public friction.
5. **Recency Points ($R \in [3.0, 10.0]$)**:
   Time elapsed since submission ($h$ hours):
   - $h \le 6.0\text{ hours} \implies R = 10.0$
   - $6.0 < h \le 24.0\text{ hours} \implies R = 8.0$
   - $24.0 < h \le 72.0\text{ hours} \implies R = 5.0$
   - $h > 72.0\text{ hours} \implies R = 3.0$
6. **Location Risk Points ($L \in [4.0, 15.0]$)**:
   $$L = \min(\text{base} + \min((r - 1) \times 2.0, \, 6.0), \, 15.0)$$
   Where $\text{base} = 9.0$ if the coordinates fall in a Haversine DBSCAN hotspot (otherwise $4.0$), and $r$ is historical recurrence count.

### 7.2 Priority Categorization Thresholds
- **CRITICAL**: $85.0 \le \text{Score} \le 100.0$
- **HIGH**: $70.0 \le \text{Score} < 85.0$
- **MEDIUM**: $40.0 \le \text{Score} < 70.0$
- **LOW**: $0.0 \le \text{Score} < 40.0$

### 7.3 Verified Worked Example (Incident `CIVIC-2026-23363092`)
- **Complaint**: *"Major fresh deep crater pothole breaking vehicle axles near Somaiya Vidyavihar arterial road."*
- **Urgency ($u = 0.45$)**: $0.45 \times 20.0 = \mathbf{9.0\text{ pts}}$
- **Text Severity ($t = 0.72$)**: $0.72 \times 20.0 = \mathbf{14.4\text{ pts}}$
- **Visual Severity ($v = 0.62$, $c = 0.9467$)**: $0.62 \times 20.0 \times 0.9467 = \mathbf{11.7\text{ pts}}$
- **Related Reports ($f = 3$ near duplicates)**: $\min(3.0 + 3 \times 4.0, 15.0) = \mathbf{15.0\text{ pts}}$
- **Recency ($h = 0.1\text{ hours}$)**: Fresh report $\le 6\text{h} = \mathbf{10.0\text{ pts}}$
- **Location Risk (Hotspot = True, Recurrence $r = 5$)**: $\min(9.0 + \min(4 \times 2.0, 6.0), 15.0) = \min(9.0 + 6.0, 15.0) = \mathbf{15.0\text{ pts}}$
- **Total Composite Priority Score**:
  $$\text{Total} = 9.0 + 14.4 + 11.7 + 15.0 + 10.0 + 15.0 = \mathbf{75.1} \implies \mathbf{HIGH}$$

---

# PART 8 — TACTICAL GIS, GEOLOCATION & GEOGRAPHIC BOUNDARIES

### 8.1 Geographic Bounding Box
CIVILENS strictly validates all spatial submissions against the **Mumbai and Navi Mumbai Metropolitan Region**:
- **Southern Latitude**: `18.85° N`
- **Northern Latitude**: `19.33° N`
- **Western Longitude**: `72.75° E`
- **Eastern Longitude**: `73.18° E`

Coordinates outside this bounding box are rejected with a clear operational message:
> *"CIVILENS currently supports complaints from Mumbai and Navi Mumbai only."*

### 8.2 Geolocation Capture & Reverse Geocoding
- **Browser Geolocation API**: Invoked via `navigator.geolocation.getCurrentPosition()`.
- **Reverse Geocoding**: Converts coordinates to human-readable street names via Nominatim OpenStreetMap with local offline dictionary fallback covering popular municipal junctions (Somaiya Vidyavihar, Kurla Station, Linking Road Bandra, Dadar TT Circle, Vashi Sector 17, etc.).
- **Map Picker**: Interactive Leaflet map picker allowing citizens to drag or click a pin to select coordinates.

### 8.3 Tactical GIS Map Architecture
The frontend features a tactical GIS map workspace adhering to the **Aurora Indigo** design system:
- **GIS Canvas Background**: `#10162A` (deep tactical midnight blue).
- **Marker Visual Hierarchy**:
  - Roads & Footpaths: Violet / Indigo markers (`#6457E8`).
  - Sanitation & Garbage: Emerald green markers (`#10B981`).
  - Critical Severity ($\ge 85$ pts): Animated pulsing red radar halo (`#EF4444`).
- **Synchronization**: Map data is fetched on-demand from `GET /api/v1/gis/geojson` and synchronized whenever an issue is submitted, triaged, or selected in the queue.

---

# PART 9 — MUNICIPAL WARD OPERATIONS & GRIEVANCE LIFECYCLE

CIVILENS tracks every complaint through a rigorous 14-step operational lifecycle:

1. **Grievance Registered**: Citizen submits text, coordinates, and photo proof.
2. **AI Multimodal Inference**: NLP classifies text; YOLO localizes visual defects.
3. **Cross-Modal Consistency**: Text claim is verified against detected visual objects.
4. **Spatiotemporal Correlation**: Geodesic distance checks identify duplicates and corridor hotspots.
5. **Priority Computed**: 6-factor additive score is assigned with human-readable rationale.
6. **Department Dispatch**: Routed to relevant municipal agency (e.g. `MCGM-ROADS`, `MCGM-SWM`).
7. **Inspector Triage**: Officer reviews the complaint in the Command Center queue.
8. **Statutory Guidance Review**: Officer consults MoRTH/MCGM guidelines in the Issue Dossier.
9. **Task Assignment**: Assigned to a predefined operational field team (e.g. `Ward N Asphalt Patch Crew`).
10. **Work Scheduling**: Inspection and repair date scheduled with specific shift notes.
11. **Temporary Field Action**: Crew records safety measures (cones, barricades).
12. **Work Completion**: Field team submits completion notes, contractor ID, and post-repair photo.
13. **Supervisory Closure**: Officer verifies repair and marks ticket `RESOLVED`.
14. **Citizen Feedback & Reopen**: Citizen rates resolution (1–5 stars) or reopens the ticket if defective.

---

# PART 10 — AI FIELD GUIDANCE & STATUTORY STANDARDS KNOWLEDGE BASE

A critical innovation in CIVILENS is the **AI Field Guidance** engine (`app/services/guidance/`). Rather than producing ungrounded LLM hallucinations, recommendations are synthesized from indexed official statutory specifications.

### 10.1 Indexed Statutory Knowledge Base
1. **MoRTH Specifications for Road and Bridge Works (Section 3004 / IRC:82-2023)**:
   - Work zone traffic control (50m/100m advance warning signs, Class-3 retro-reflective vests).
   - Rectangular vertical saw-cut cavity trimming into sound asphalt.
   - RS-1 rapid setting cationic bitumen tack coat ($0.25–0.30\text{ kg/m}^2$).
   - Compaction in lifts $\le 75\text{mm}$ using 500kg vibratory plate compactor to zero deflection.
2. **MCGM Standard Operating Procedure for Monsoon Pothole Filling**:
   - Mandatory proprietary polymer-modified Cold Mix Asphalt during monsoon/damp conditions.
   - Immediate escalation to Hydraulic Engineer / Storm Water Drain if water is bubbling from subgrade.
   - Geo-stamped before and after photograph requirement prior to ticket closure.
3. **CPCB Solid Waste Management Rules 2016 (Schedule II)**:
   - Mandatory segregation of organic wet waste, dry recyclables, and domestic hazardous items.
   - Personal Protective Equipment (heavy-duty nitrile gloves, puncture-resistant boots, N95 masks).
   - 0.5% sodium hypochlorite disinfectant spraying for biological waste spills.
4. **MPCB Bio-Medical & Hazardous Waste Protocol**:
   - Immediate hazardous escalation if syringes, chemical containers, or toxic waste are detected.

### 10.2 Officer Decision Support
Officers can click:
- **Accept**: Injects statutory steps directly into task assignment instructions.
- **Edit**: Allows customizing instructions while logging the justification.
- **Dismiss**: Clears the recommendation with a mandatory audit reason.

---

# PART 11 — DATASETS, TRAINING PROVENANCE & EMPIRICAL EXPERIMENTS

CIVILENS maintains strict separation between training datasets, validation splits, held-out test sets, and demonstration fixtures.

### 11.1 Dataset Inventory

| Dataset Name | Source & Organization | License | Total Samples | Split Structure | Purpose in CIVILENS |
|---|---|---|---|---|---|
| **RDD2022 (India Partition)** | Crowdsensing Road Damage Challenge (Sekilab / Maeda et al.) | CC-BY-4.0 | 200 balanced images | 100 Validation / 100 Held-Out Test | Evaluates D00, D10, D20, D40 road damage detection. |
| **TACO (Trash Annotations in Context)** | Pedro F. Proença & Pedro M. Simões | MIT License | 200 balanced images | 100 Validation / 100 Held-Out Test | Evaluates 9 municipal litter classes and hard-negative pavement alarms. |
| **NLP Grievance Corpus** | In-Memory Representative Municipal Corpus | MIT License | 27 training samples | 27 Train / 6 Held-Out Seed Issues | Trains TF-IDF + Logistic Regression category classifier (0% text overlap). |
| **Controlled Resolution Fixtures**| Curated Field Fixtures (`data/test_samples/`) | Internal Benchmark | 5 image pairs | 5 Controlled Test Cases | Evaluates before-and-after SSIM comparability and YOLO clearance. |

### 11.2 The Phase 10 Calibration Experiment
Prior to Phase 10, the waste detector operated at an uncalibrated threshold of `0.20`, producing false alarms against textured pavement. An extensive sweep across the validation split ($N=100$) established that raising the threshold to **`0.45`** achieved optimal performance:
- False Positives reduced by **54.8%** (from 62 down to 28).
- Precision improved from **68.04% to 81.33%** (+13.29 pp).
- Recall remained high at **70.52%**.
- Controlled fine-tuning trials on small candidate sets induced catastrophic forgetting (recall dropped to 58.38%), proving that retaining the original checkpoint with calibrated threshold `0.45` was scientifically superior.

---

# PART 12 — COMPREHENSIVE TECHNOLOGY STACK & JUSTIFICATIONS

| Layer | Technology | Version | Purpose in CIVILENS | Selection Justification |
|---|---|---|---|---|
| **Backend Framework** | **Python** | 3.10 – 3.13 | Core backend runtime | Broad ecosystem for machine learning, PyTorch, and geospatial algorithms. |
| **API Engine** | **FastAPI** | 1.0.0 | High-performance asynchronous REST API | Native async ASGI, automatic OpenAPI documentation, and strict Pydantic v2 validation. |
| **Server Engine** | **Uvicorn** | Latest | Asynchronous Server Gateway Interface (ASGI) | Production-grade concurrency for handling simultaneous citizen submissions. |
| **Frontend Framework** | **React** | 19.0.0 | Declarative Component UI | Robust component lifecycle, efficient DOM rendering, and strict role views. |
| **Type System** | **TypeScript** | 5.x | Strict frontend type contracts | Eliminates runtime interface errors between backend JSON models and frontend UI. |
| **Build Tool** | **Vite** | 6.x | Frontend build and HMR tool | Sub-second cold startup and instant hot module replacement. |
| **Deep Learning** | **Ultralytics YOLO** | 8.x / 11.x | Object detection neural networks | High-throughput anchor-free inference with native PyTorch weights. |
| **Deep Learning** | **PyTorch** | 2.x | Neural network compute engine | Industry standard for executing convolutional backbones and tensor operations. |
| **Machine Learning** | **Scikit-Learn** | 1.x | NLP classification & DBSCAN clustering | Lightweight, highly interpretable TF-IDF vectorization and Haversine spatial clustering. |
| **Computer Vision** | **OpenCV (`cv2`)** | 4.x | Image processing, SSIM, histograms | Structural similarity and 2D HSV color correlation for repair verification. |
| **Cloud Inference** | **Roboflow SDK** | Latest | Serverless hosted model candidate execution | Enables rigorous side-by-side benchmarking against cloud models. |
| **Database** | **SQLite 3** | 3.35+ | ACID relational database persistence | Zero-configuration, zero-network latency, persistent disk storage with WAL mode. |
| **ORM** | **SQLAlchemy** | 2.0 | Type-annotated relational mapping | Clean Mapped column schemas, transactional safety, and relational indexing. |
| **GIS Mapping** | **Leaflet / React-Leaflet** | Latest | Interactive tactical spatial GIS workspace | Lightweight, mobile-friendly interactive mapping without expensive Google Maps API billing. |
| **Styling** | **Tailwind CSS** | 4.x | Utility-first styling framework | Implements the high-trust Aurora Indigo design tokens consistently. |
| **Testing** | **Pytest & Selenium** | Latest | Automated unit, integration, and browser testing | Validates 244 backend test cases and 6 headless Chrome browser workflows. |

---

# PART 13 — COMPLETE REST API & RELATIONAL DATABASE REFERENCE

*(Refer to [`docs/CIVILENS_TECHNICAL_REFERENCE.md`](./CIVILENS_TECHNICAL_REFERENCE.md) for full endpoint request/response payloads and database schema definitions).*

---

# PART 14 — PROJECT SECURITY, CRYPTOGRAPHY & PRIVACY BOUNDARIES

1. **Password Hashing**: Passwords are never stored in plaintext. They are protected using **PBKDF2-HMAC-SHA256** with 100,000 iterations and a 16-byte cryptographically random salt (`os.urandom(16)`). Verification uses constant-time `hmac.compare_digest` to prevent timing attacks.
2. **Access Tokens**: Cryptographically signed access tokens using **HMAC-SHA256** with 12-hour expiration (`DEFAULT_TOKEN_TTL_HOURS = 12`). In production mode (`CIVILENS_ENV=production`), hardcoded development tokens are strictly forbidden.
3. **Upload Security**:
   - Magic byte header inspection via PIL verifies true file type (spoofed `.jpg` extensions containing executable shell code are rejected).
   - Maximum upload size strictly capped at 10MB.
   - Filenames are sanitized and converted to UUIDs to prevent directory traversal attacks (`../../etc/passwd`).
4. **Location Privacy**: GPS coordinates are captured with explicit user permission and stored only for valid municipal complaints.
5. **API Credential Protection**: Cloud API keys (e.g. `ROBOFLOW_API_KEY`) are stored in `.env`, never exposed to the frontend, and masked in all diagnostic logs (`NIae...0duw`).

---

# PART 15 — TESTING, VERIFICATION & REGRESSION TEST SUITE

CIVILENS maintains a zero-failure testing policy:
- **Total Passing Pytest Tests**: **244 / 244** (0 failures, 1 warning from starlette deprecation).
- **Execution Time**: ~30 seconds for full test suite.
- **Frontend Build**: `npm run build` succeeds in 327ms with 0 errors.
- **Headless Chrome Automation Suite (`scripts/verify_comparison_ui.py`)**:
  - Test 1 (Citizen Role): Verified that Model Comparison UI is 100% hidden.
  - Test 2 (Pothole Comparison): Verified baseline (`YOLOv8s RDD2022`), hosted (`potholes-krmk8/2`), latency (650ms), and bounding box tab switching.
  - Test 3 (Garbage Comparison): Verified baseline (`YOLO11s TACO`), hosted (`garbage_detection-wvzwv-n8vsv/1`), and RF-DETR Nano architecture.
  - Test 4 (Legacy Complaint): Verified quiet state message without fake data.
  - Test 5 (Failed Hosted Inference): Verified structured `AUTH_ERROR` alert without breaking local scoring.
  - Test 6 (Admin Role): Verified full comparison panel visibility.

---

# PART 16 — REPOSITORY STRUCTURE & FILE ORGANIZATION MAP

```
chiragwalaproj/
├── app/
│   ├── api/routes.py                     # All 48 REST API endpoints
│   ├── config.py                         # Environment variables and model configuration
│   ├── main.py                           # FastAPI application entry point and lifespan hooks
│   ├── core/
│   │   ├── pipeline.py                   # Master pipeline coordinator
│   │   ├── security.py                   # PBKDF2 hashing, HMAC tokens, RBAC gates
│   │   └── demo_store.py                 # In-memory store and SQLite demo repository facade
│   ├── db/
│   │   ├── database.py                   # SQLAlchemy engine, session maker, WAL configuration
│   │   ├── models.py                     # 9 SQLAlchemy persistent ORM table definitions
│   │   └── repository.py                 # SQLite transaction repository & seed management
│   ├── models/
│   │   ├── issue.py                      # Core Pydantic schemas (Issue, DynamicPriorityBreakdown)
│   │   └── field_guidance.py             # Field guidance schemas (Citations, Actions, Checklists)
│   ├── modules/
│   │   ├── cross_validation/validator.py # Text-image consistency verification
│   │   ├── evaluation/evaluator.py       # Classification evaluation metrics engine
│   │   ├── gis/                          # GIS mapper and boundary restriction (bounds.py)
│   │   ├── lifecycle/                    # SSIM scene comparability & OpenCV verification
│   │   ├── nlp/                          # TF-IDF classifier, deduplication, location parser
│   │   ├── priority/engine.py            # 6-factor additive dynamic priority calculation
│   │   ├── routing/dispatcher.py         # Configurable department routing & SLA actions
│   │   ├── spatiotemporal/               # Haversine DBSCAN hotspots and recurrence tracking
│   │   └── vision/                       # YOLO road & waste detectors, Roboflow adapter, manager
│   └── services/
│       ├── guidance/                     # Knowledge base, scraper, statutory guidance engine
│       └── upload_service.py             # Secure image upload verification and disk storage
├── data/
│   ├── civic_issues.db                   # Persistent SQLite database
│   ├── seed_issues.json                  # Baseline seed complaints (CIVIC-2026-001 to 006)
│   ├── cache/                            # Deterministic SHA-256 Roboflow prediction cache
│   ├── evaluation/                       # Evaluation manifests and held-out test datasets
│   └── test_samples/                     # Verified test fixture images (pothole, bottle, repair)
├── docs/                                 # Project documentation, guides, and model cards
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/                     # Login cards, role login forms, demo fill buttons
│   │   │   ├── common/                   # KpiCards, LocationPicker, PriorityGauge, Toast
│   │   │   ├── guidance/                 # AI Field Guidance section and document modal
│   │   │   ├── issues/                   # IssueDetailDrawer, VisionModelComparison, NewComplaintModal
│   │   │   ├── layout/                   # Sidebar navigation, TopBar application header
│   │   │   ├── map/                      # Tactical Leaflet GIS map workspace (CivicMap)
│   │   │   ├── portal/                   # Citizen Portal grievance filing and feedback view
│   │   │   └── views/                    # OverviewView (Command Center), MapView, AnalyticsView
│   │   ├── context/AuthContext.tsx       # Authentication context and role state management
│   │   ├── config/geo.ts                 # Mumbai & Navi Mumbai geographic bounds and landmarks
│   │   └── types/index.ts                # TypeScript data interfaces matching Pydantic models
│   └── package.json
├── models/                               # Local PyTorch checkpoints: yolov8s_rdd2022.pt, taco_yolo11s.pt
├── scripts/                              # Verification suites, evaluation sweep tools, diagnostic scripts
└── tests/                                # 26 automated Pytest test files (244 passing tests)
```

---

# PART 17 — REPRODUCIBLE SETUP, INSTALLATION & EXECUTION GUIDE

*(Refer to [`docs/SETUP_GUIDE.md`](./SETUP_GUIDE.md) and [`docs/CIVILENS_TECHNICAL_REFERENCE.md`](./CIVILENS_TECHNICAL_REFERENCE.md) for step-by-step commands).*

---

# PART 18 — LIVE ACADEMIC DEMONSTRATION WALKTHROUGH

*(Refer to [`docs/CIVILENS_DEMO_GUIDE.md`](./CIVILENS_DEMO_GUIDE.md) for the exact viva presentation script, dialogue, and 5-scenario live execution steps).*

---

# PART 19 — ARCHITECTURAL HISTORY & KEY ENGINEERING DECISIONS

1. **Why Scope was Frozen to Two Categories**: Early project phases explored flooding, streetlights, and traffic signals. Faculty feedback correctly identified that surface water reflections and night illumination cannot establish municipal pipe bursts or circuit breaks via standard computer vision. CIVILENS frozen perception strictly to Potholes and Garbage, where genuine PyTorch detectors operate reliably.
2. **Why Local YOLO Was Retained Over Roboflow Cloud**: Roboflow cloud models were evaluated as candidates. While functional, they exhibited 12x higher latency (~650ms vs ~50ms), single-class taxonomic collapse (missing road cracks and distinct waste materials), API credit costs, and citizen location privacy risks. Local YOLO models remain authoritative for production.
3. **Why the Resolution Center Page Was Removed**: The separate "Resolution Center" sidebar page created navigation redundancy. Municipal Officers manage the entire complaint lifecycle—from inspection to guidance, task assignment, and post-repair photographic closure—directly from the **Issue Detail Drawer**.
4. **Why Aurora Indigo Design Was Retained**: Civic operations workspaces require clean, high-contrast, high-trust visual ergonomics. Aurora Indigo uses a light workspace (`#F6F7FC`), pure-white cards (`#FFFFFF`), midnight-indigo navigation (`#13152E`), and restrained violet accents (`#6457E8`), avoiding dark "cyberpunk" dashboard antipatterns.

---

# PART 20 — KNOWN LIMITATIONS & FUTURE SCOPE

### 20.1 Current Verified Limitations
1. **Small Statistical NLP Split**: The textual classifier is trained on $N=27$ samples and evaluated against $N=6$ held-out seed issues. It demonstrates deterministic prototype mechanics but must not be claimed as municipal-scale NLP accuracy.
2. **Pavement Clutter in Waste Detection**: Local street waste precision is $81.33\%$ at conf $0.45$; complex gravel, broken asphalt, and fallen leaves can occasionally trigger false alarms, necessitating human supervisory review.
3. **SSIM Perspective Sensitivity**: OpenCV structural similarity verification requires comparable camera angles. Significant perspective shifts drop SSIM below threshold, safely falling back to manual review.
4. **Geographic Boundary**: Validated exclusively for Greater Mumbai and Navi Mumbai coordinates.

### 20.2 Realistic Future Scope
1. **Vernacular & Multi-Lingual NLP**: Expanding training data to include Marathi, Hindi, and Hinglish grievance idioms common in Mumbai.
2. **Edge Hardware Deployment**: Porting local YOLO models to NVIDIA Jetson edge devices mounted on municipal garbage collection trucks for passive automated road scanning.
3. **Live Municipal ERP Integration**: Developing bi-directional REST connectors to sync work orders directly with the BMC SAP / Civic Redressal ERP system.
4. **IoT Sensor Integration**: Connecting ultrasonic storm water depth sensors for ground-truth urban flooding detection.

---

# PART 21 — STUDENT-FRIENDLY TECHNICAL GLOSSARY

- **YOLO (You Only Look Once)**: A fast, single-stage deep learning algorithm that detects objects and draws bounding boxes in a single pass through a neural network.
- **Bounding Box**: A rectangular coordinate boundary enclosing a detected defect, normalized in CIVILENS to $[0.0, 1.0]$.
- **Confidence Score**: The probability ($0.00$ to $1.00$) that an object detection is real.
- **Precision vs. Recall**: Precision is "how many detected potholes are real potholes"; Recall is "how many of all actual potholes on the street did the model catch".
- **F1 Score**: The balanced harmonic mean between precision and recall.
- **Inference**: The process of running a trained neural network on a new image to generate predictions.
- **Hosted vs. Local Inference**: Local inference runs directly on the device/server CPU/GPU without internet. Hosted inference sends the image over the internet to a third-party cloud server (like Roboflow).
- **FastAPI**: A modern, high-performance Python web framework for building REST APIs with automatic documentation and validation.
- **DBSCAN (Density-Based Spatial Clustering)**: An unsupervised clustering algorithm that groups spatial coordinates that are closely packed together while marking outliers as noise.
- **Haversine Distance**: The angular geodesic distance between two points on the surface of a sphere given their latitude and longitude.
- **SSIM (Structural Similarity Index)**: An algorithm that measures the perceptual similarity between two images based on luminance, contrast, and structural texture.
- **RBAC (Role-Based Access Control)**: Restricting API endpoints and UI features based on authenticated user roles (Citizen, Inspector, Admin).
- **RAG / Grounded AI**: Providing an AI model with verified reference documents (such as MoRTH specifications) so its recommendations are factually grounded in official engineering standards.

---

# PART 22 — QUESTIONS ANOTHER AI MUST BE ABLE TO ANSWER

1. **What exactly does CIVILENS do?**
   - It is an explainable multimodal civic intelligence platform for municipal command centers that uses YOLO computer vision, NLP, and GIS to triage, prioritize, assign, and track road damage and street litter complaints.
2. **Why are only two categories supported for computer vision?**
   - Following faculty feedback, automated vision is frozen to Potholes/Road Damage (YOLOv8s RDD2022) and Municipal Waste (YOLO11s TACO) because ground-level smartphone photos reliably capture them. Categories like flooding and streetlights cannot be validated from surface photos and are routed for human review with zero synthetic boxes.
3. **How does the AI detect potholes?**
   - It runs an 11.14M parameter PyTorch YOLOv8s model trained on the multi-national RDD2022 dataset, detecting longitudinal cracks (`D00`), transverse cracks (`D10`), alligator cracks (`D20`), and potholes (`D40`).
4. **How does the AI detect garbage?**
   - It runs a 9.43M parameter YOLO11s model trained on the TACO taxonomy with spatial attention layers (`C2PSA`), detecting 9 distinct waste materials at a calibrated confidence threshold of 0.45.
5. **Why retain local YOLO models if Roboflow cloud API is integrated?**
   - Local YOLO runs 12x faster (~50ms vs ~650ms), detects multiple damage classes (Roboflow detects only single generic classes), costs zero API credits, and protects citizen location privacy by keeping image data on local infrastructure.
6. **How is priority calculated?**
   - Using an explainable 6-factor additive formula (0–100 points): Urgency (max 20), Text Severity (max 20), Visual Severity (max 20), Related Reports (max 15), Recency (max 10), and Location Risk / Hotspots (max 15).
7. **What happens if a citizen uploads a picture of a cat for a pothole complaint?**
   - The road detector finds 0 road defects; the cross-modal validator flags the complaint as `INCONSISTENT` (score 0.25) and routes it for manual supervisory triage. Crucially, it is never marked as "fraudulent".
8. **What is the geographic boundary of CIVILENS?**
   - Coordinates are strictly restricted to Greater Mumbai and Navi Mumbai (Lat 18.85–19.33, Lng 72.75–73.18).
9. **How many automated tests pass in the codebase?**
   - Exactly 244 backend Pytest tests pass, with 0 frontend TypeScript build errors, and all 6 headless Chrome browser automation tests passing.

---

# PART 23 — PRESENTATION PREPARATION REFERENCE

### 30-Second Elevator Pitch:
> *"CIVILENS is an explainable multimodal civic infrastructure intelligence platform designed for municipal command centers. Instead of treating citizen complaints as vague text and dumb photo attachments, CIVILENS uses specialized YOLO computer vision and NLP to localize physical defects, cross-validate evidence consistency, and calculate an authoritative 0–100 priority score. Operating within Greater Mumbai and Navi Mumbai, it empowers municipal officers to assign work orders to field crews with grounded engineering guidelines from MoRTH and BMC standard operating procedures."*

### 1-Minute Technical Overview:
> *"Traditional civic complaint portals suffer from subjective reporting, duplicate ticket flooding, and static FIFO queues that let dangerous road hazards sit unattended. CIVILENS solves this through multimodal artificial intelligence. When a citizen submits a complaint via GPS, our backend executes dual local neural networks: a YOLOv8s model fine-tuned on RDD2022 for road damage and a YOLO11s model trained on TACO for street litter. The system cross-validates text against vision, checks for duplicates using Haversine geodesic clustering, and calculates an explainable 6-component risk score. Municipal officers in the Command Center receive database-driven KPIs, dynamic triage queues, side-by-side cloud model benchmarking via Roboflow, and statutory AI Field Guidance citing official Ministry of Road Transport specifications."*

### 3-Minute Comprehensive Viva Overview:
> *(Deliver the 1-Minute overview, then elaborate on the three key pillars: 1. Ethical Cross-Modal Validation, 2. Local vs Hosted Model Benchmarking, and 3. Ward Operations Lifecycle with verified test evidence of 244 passing tests and zero synthetic bounding boxes).*

---

# PART 24 — QUALITY SIGNOFF & AUDITOR ATTESTATION

- **Codebase Audited**: `/Users/abby/chiragwalaproj`
- **Verification Status**: 244 / 244 Pytest tests passing; 0 TypeScript errors; 6 / 6 browser scenarios verified.
- **Truthful Disclosure**: All performance metrics, limitations, and operational boundaries have been disclosed with complete scientific integrity.
- **Signed by**: CIVILENS Automated Engineering Auditor (Antigravity AI)

