# CIVILENS — Executive Summary

**Project Name**: CIVILENS (Civic Infrastructure Intelligence Platform)  
**Domain**: Multimodal Artificial Intelligence, Computer Vision, Spatiotemporal GIS, Civic Tech  
**Target Jurisdiction**: Greater Mumbai & Navi Mumbai Municipal Operational Model  
**Tech Stack**: Python 3.10–3.13, FastAPI, React 19, TypeScript, Vite, SQLite, PyTorch, Ultralytics YOLO, Scikit-Learn  
**Authoritative Scope Freeze**: Two Core Civic Domains — Potholes/Road Damage and Municipal Waste/Street Litter  
**Status**: Academic Research Prototype & Operations Management Platform (Fully Implemented & Verified)

---

## 1. Executive Overview

Rapid urbanization has placed severe operational burdens on municipal corporations. Traditional civic grievance redressal platforms (e.g., standard citizen mobile apps, web portals, municipal hotlines) encounter systemic friction:
- **Vague Grievance Descriptions**: Citizens submit subjective complaints (*"road broken"*, *"smells terrible"*) without standardized defect measurements.
- **Duplicate Ticket Flooding**: A single visible pothole on an arterial corridor triggers dozens of repetitive complaints, overwhelming dispatch queues and distorting municipal statistics.
- **Unverified Photographic Evidence**: Traditional portals treat photos as passive file attachments, failing to verify whether the image actually depicts the reported issue or an entirely different problem.
- **Crude First-In, First-Out (FIFO) Triage**: Complaints are logged linearly or placed into broad low/medium/high buckets based on self-reported checkboxes, leaving life-threatening road craters unattended behind routine cosmetic complaints.
- **Lack of Operational Field Guidance**: Field teams are dispatched without standardized repair protocols, safety precautions, or statutory equipment specifications.

**CIVILENS** addresses these systemic challenges by transforming citizen-reported grievances into structured, objectively prioritized, and operationally actionable municipal interventions. The system combines deep convolutional neural networks, Natural Language Processing (NLP), spatiotemporal clustering, and an explainable mathematical priority engine within a tactical Geographic Information System (GIS) workspace.

---

## 2. The Complete CIVILENS Concept

CIVILENS operates as a closed-loop civic intelligence lifecycle:

$$\text{Citizen Report} \longrightarrow \text{AI Multimodal Triage} \longrightarrow \text{Dynamic Risk Scoring} \longrightarrow \text{GIS Tactical Mapping} \longrightarrow \text{Field Operations} \longrightarrow \text{Citizen Feedback}$$

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           1. CITIZEN SUBMISSION PORTAL                         │
│  - GPS Location Detection (Browser Geolocation API) & Interactive Map Picker    │
│  - Strict Boundary Validation (Mumbai & Navi Mumbai: Lat 18.85-19.33, Lng 72.75-73.18) │
│  - Secure Image Upload (Magic bytes validation, JPEG/PNG/WEBP, Max 10MB)       │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                        2. MULTIMODAL AI INTELLIGENCE ENGINE                    │
│  - Vision Baseline: YOLOv8s RDD2022 (Road Damage) & YOLO11s TACO (Waste)       │
│  - Experimental Candidate: Roboflow Serverless API (YOLO26 & RF-DETR Nano)     │
│  - Text NLP: Scikit-Learn TF-IDF + Logistic Regression (Urgency & Severity)    │
│  - Cross-Validation: Text-Image Consistency Matrix (CONSISTENT / INCONSISTENT) │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                      3. EXPLAINABLE RISK-AWARE PRIORITIZATION                  │
│  - Authoritative 6-Factor Additive Priority Formula (0–100 Points)             │
│  - Spatiotemporal Clustering: Haversine DBSCAN (R=400m) & Token Deduplication  │
│  - Automated Department Routing (Roads, SWM, HED, BEST, SWD, Transit)          │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                    4. MUNICIPAL WARD OPERATIONS COMMAND CENTER                 │
│  - Real-Time Command Center KPIs & Priority Incident Queue (Action Filters)     │
│  - Interactive Issue Dossier with Task Assignment & Predefined Field Teams     │
│  - Grounded AI Field Guidance (Statutory Specifications: MoRTH, MCGM, CPCB)    │
│  - Progress Tracking, Completion Proof Upload, Reopen Workflow, & Rating       │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Two Core Civic Focus Domains

Following academic faculty guidance, CIVILENS strictly freezes its computer-vision perception to **two core infrastructure categories**:

1. **Potholes and Road Surface Damage**:
   - **Local Production Model**: `YOLOv8s RDD2022` (11.14M parameters, CC-BY-4.0).
   - **Classes Detected**: `D00` (Longitudinal Crack), `D10` (Transverse Crack), `D20` (Alligator Fatigue Fissure), `D40` (Pothole).
   - **Operating Confidence**: `0.15` (high sensitivity for early fissure detection).
2. **Garbage Accumulation and Street Litter**:
   - **Local Production Model**: `YOLO11s TACO` (9.43M parameters, MIT License).
   - **Classes Detected**: 9 municipal waste categories (Plastic bags/wrappers, Bottles, Bottle caps, Cans, Cartons, Cups, Cigarettes, Other plastic, Other litter).
   - **Calibrated Operating Confidence**: `0.45` (demonstrating **81.33% precision** and **70.52% recall** on held-out test data).

*Broader categories (such as street flooding, streetlights, and traffic signals) are categorized exclusively via text NLP and routed for human engineering review with zero synthetic bounding boxes.*

---

## 4. Key Architectural Innovations

### 1. Multimodal Text–Image Cross-Validation
Traditional platforms accept attachments blindly. CIVILENS cross-validates citizen text claims against visual detections:
- **Consistent**: Text cites road damage; computer vision detects a pothole $\to$ **`CONSISTENT`** (Score: 0.96).
- **Discrepant**: Citizen reports a severe pothole but attaches a photograph of a discarded plastic bottle $\to$ **`INCONSISTENT`** (Score: 0.25).
- **Ethical Safeguard**: The system **never labels the citizen fraudulent**. It flags the record for manual supervisory triage with transparent reasoning.

### 2. Authoritative 6-Factor Explainable Priority Scoring
Rather than opaque "black-box" predictions or crude low/medium/high checkboxes, CIVILENS calculates an exact, mathematically transparent composite priority score (0–100 points):

$$\text{Total Priority (0–100)} = U + T + V + F + R + L$$

Where:
- $\text{Urgency } (U)$: Max **20 pts** (Immediate physical hazard to life, safety, or transit).
- $\text{Text Severity } (T)$: Max **20 pts** (Reported infrastructural disruption magnitude).
- $\text{Visual Severity } (V)$: Max **20 pts** (Defect surface area modulated by detector confidence).
- $\text{Related Reports } (F)$: Max **15 pts** (Public friction amplification from near-duplicates).
- $\text{Recency } (R)$: Max **10 pts** (Time decay: $\le 6\text{h} \to 10\text{pts}$, $\le 24\text{h} \to 8\text{pts}$, $\le 72\text{h} \to 5\text{pts}$, $> 72\text{h} \to 3\text{pts}$).
- $\text{Location Risk } (L)$: Max **15 pts** (Municipal hotspot corridor base of 9 pts plus recurrence bonus).

### 3. Local Production Baseline vs. Hosted Roboflow Candidate Comparison
CIVILENS integrates the **Roboflow Serverless Hosted API** (`potholes-krmk8/2` for road damage and `garbage_detection-wvzwv-n8vsv/1` for sanitation). However, empirical evaluation revealed critical domain limitations in the hosted candidates (e.g., loss of material taxonomy, inability to detect road cracks, and 3x–8x higher latency). Consequently, CIVILENS maintains a strict architectural policy:
- **Local Models Remain Authoritative**: Local YOLO models exclusively drive production severity and priority scores.
- **Hosted Models as Benchmarking Candidates**: Hosted predictions are displayed in a dedicated side-by-side **Vision Model Comparison** drawer view for engineering evaluation without impacting production dispatching.
- **Credit Quota Protection**: Calls are deterministically cached using SHA-256 image digests, preventing redundant cloud credit consumption.

### 4. AI Field Guidance Grounded in Official Statutory Standards
Municipal officers in the Issue Dossier receive practical, context-aware field recommendations synthesized from official specifications:
- **MoRTH Section 3004 / IRC:82-2023**: Standard Specifications for Road and Bridge Works (traffic control, vertical saw-cut trimming, cationic tack coat, mechanical compaction).
- **MCGM Monsoon SOP**: BMC guidelines for cold mix asphalt and sub-base moisture checks.
- **CPCB Solid Waste Management Rules 2016 (Schedule II)**: Mandatory waste handling, segregation, and PPE precautions.
- **Officer Decision Workflow**: Officers can accept recommendations (injecting them into work order instructions), edit them, or dismiss them.

### 5. Ward Operations Management System
The Municipal Officer workspace features:
- **Inspector Command Center**: Real-time database KPIs (Unassigned, High Priority, In Progress, Monthly Resolutions, Road vs Sanitation split, Ward distribution).
- **My Action Queue**: Filterable grievance list (`ALL`, `UNASSIGNED`, `IN_PROGRESS`, `HIGH_PRIORITY`, `RESOLVED`).
- **Comprehensive Issue Dossier**: Task assignment to predefined field teams, scheduling inspection dates, recording temporary safety actions, uploading geo-tagged completion photographs, and processing citizen feedback.

---

## 5. Verification & Codebase Integrity

| Verification Gate | Target Requirement | Measured Result | Status |
|---|---|---|---|
| **Backend Unit & Integration Suite** | Comprehensive subsystem coverage | **244 / 244 tests passing** (0 failures) | **PASSED** |
| **Roboflow Integration Suite** | Hosted API, caching, error handling | **16 / 16 tests passing** | **PASSED** |
| **Frontend Production Build** | TypeScript & Vite compilation | **0 errors, 0 warnings** (built in 327ms) | **PASSED** |
| **Real-Browser Automation (Headless Chrome)** | End-to-end verification across Citizen, Inspector, and Admin | **All 6 browser test scenarios passed** | **PASSED** |
| **Persistent SQLite Storage** | Relational integrity and WAL mode | **9 tables fully mapped and verified** | **PASSED** |

---

## 6. Scientific Honesty & Deployment Boundaries

1. **Academic Demonstration Status**: CIVILENS is an academic research prototype and decision-support tool. It is not currently deployed across live MCGM municipal municipal servers.
2. **Human-in-the-Loop Governance**: The system provides decision support; all status changes, task assignments, and closures require authenticated human officer action.
3. **No Fabricated Data**: Metrics, bounding boxes, and citations represent genuine algorithm execution. No synthetic bounding boxes are generated for unsupported categories.
4. **Geographic Scope**: Validated exclusively for the **Greater Mumbai and Navi Mumbai** metropolitan areas (Latitude 18.85–19.33, Longitude 72.75–73.18).

