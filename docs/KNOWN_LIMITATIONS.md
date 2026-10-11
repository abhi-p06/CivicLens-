# CIVILENS — Known Limitations & Operational Boundaries

This document formally details the known technical, scientific, and empirical limitations of the **CIVILENS** platform. 

CIVILENS is designed as an **academic demonstration and prototype advisory engine**, not an autonomous civic enforcement system. All algorithmic outputs are subject to the boundaries described below.

---

## 1. Small NLP Training and Evaluation Split (N=27 Train, N=6 Held-Out)

### Provenance & Split
- **Training Corpus**: The textual category classifier is trained on an in-memory corpus of **27 representative municipal grievance samples** across **5 supported categories** (`app/modules/nlp/classifier.py`): Roads & Footpaths (6), Sanitation & Garbage (6), Water Supply & Drainage (6), Electricity & Streetlights (5), Traffic & Public Safety (4).
- **Held-Out Evaluation Set**: The model is evaluated against **6 held-out seed complaints** (`data/seed_issues.json`, `CIVIC-2026-001` through `CIVIC-2026-006`).
- **Data Split Integrity**: There is strictly **0% text overlap** between training samples and held-out evaluation records (enforced by automated test `tests/test_evaluation_provenance.py`). Training examples are never re-used as evaluation data.

### Impact & Operational Scope
- While the classifier demonstrates reliable routing on standard civic phrasing across its 5 supported categories, it lacks statistical coverage for:
  - Regional languages and transliterated vernaculars (e.g., Marathi, Hindi, or Hinglish idioms common in Mumbai).
  - Highly convoluted, composite, or multi-department grievances (e.g. *"garbage dumped into a waterlogged pothole causing traffic jam"*).
  - Sarcastic or indirect citizen feedback.
- The current empirical evaluation results reflect small-sample demonstration performance ($N=27$ train, $N=6$ test) and **must never be claimed as municipal-scale NLP accuracy**.

---

## 2. Low Precision in Local Waste Detection (27.3% Precision on N=5 Samples)

### Limitation
In held-out local evaluation using 5 annotated street images (`data/evaluation/waste_detection_eval_manifest.json`), the **YOLO11s TACO Waste Detector** achieved:
- **Recall@50**: `100.0%` (detected all true waste items)
- **Precision@50**: `27.3%` (16 false positives vs. 6 true positives)
- **F1-Score@50**: `42.9%`

### Domain Gap Analysis
- The underlying TACO dataset was compiled largely in parks, beaches, and clean suburban settings with high foreground-background contrast.
- In contrast, real municipal street surveillance features asphalt aggregate, broken curb stones, fallen leaves, mud clods, and uneven shadow patterns that the model frequently mistakes for discarded plastic packaging, cans, or bottle caps.
- **Operational Rule**: Upstream benchmark metrics (e.g. `mAP50 = 0.311`, `mAP50-95 = 0.234`) represent clean benchmark conditions and must **never** be cited as CIVILENS's locally measured street performance. A conservative confidence threshold (`0.20`) and multimodal validation are enforced.

---

## 3. Limited Controlled Resolution-Verification Benchmark (N=5 Fixture Pairs)

### Limitation
The computer-vision resolution verification subsystem (`OpenCV SSIM` + dual YOLO delta analysis) was benchmarked on **5 controlled before-and-after image pairs**:
- 2 successfully cleared pothole repairs.
- 1 defective repair where the pothole remained unpatched.
- 1 incompatible scene angle (viewpoint shift).
- 1 corrupted image test.

### Operational Caveat
- In controlled conditions, the pipeline correctly distinguishes repaired road patches from active potholes.
- However, real-world field verification involves uncontrolled camera angles, variable lighting (day vs. night), different smartphone focal lengths, and wet weather.
- Under significant perspective changes, structural similarity (SSIM) falls below threshold, triggering the **`REQUIRES MANUAL VERIFICATION`** fallback. Autonomous closure without human inspector review is strictly avoided.

---

## 4. Unsupported Visual Categories

### Limitation
CIVILENS currently possesses validated ground-level computer-vision object detectors for only two visual categories:
1. **Road Surface Damage** (Potholes, cracks via RDD2022 YOLOv8s).
2. **Municipal Waste & Litter** (Packaging debris, bottles, cans via TACO YOLO11s).

### Unvalidated Categories
- **Street Flooding & Waterlogging**: Explicitly unsupported. Public datasets are satellite/aerial; surface water cannot verify pipe rupture.
- **Streetlight & Electrical Failures**: No automated detector; classified via text NLP.
- **Traffic Signal Failures**: No automated detector; routed via text NLP.
- **Encroachments & Unauthorized Construction**: No automated detector.

All unvalidated categories default to **`MANUAL REVIEW`** with **zero synthetic bounding boxes**.

---

## 5. Demonstration Data vs. Field-Validated Municipal Evidence

### Limitation
The default database includes seed records (`CIVIC-2026-001` through `CIVIC-2026-006`) and curated test images (`data/test_samples/`) designed to reliably demonstrate:
- Spatial clustering (DBSCAN).
- Near-duplicate ticket grouping.
- Historical corridor recurrence.
- Scene comparability and resolution deltas.

These demonstration assets illustrate algorithmic mechanics. They do not constitute empirical field surveys of a live municipal jurisdiction.

---

## 6. Mandatory Human-in-the-Loop Supervisory Review

### Architectural Policy
CIVILENS enforces a strict **human-in-the-loop governance model**:
1. **No Automatic Citizen Penalization**: Discrepant evidence between complaint text and photos is flagged as `INCONSISTENT` for supervisory review, but **never** marked as "fake" or "fraudulent".
2. **Inspector Authority Required**: Status changes to `IN PROGRESS` or `RESOLVED` require authenticated municipal credentials. Client-supplied inspector IDs are strictly ignored in favor of server-authenticated identities.
3. **Admin Authority for Routing**: Department dispatch rules and SLA configurations can only be altered by authenticated administrators.
4. **Advisory Scoring**: The 0–100 priority score serves as an operational advisory metric to assist dispatchers, not an unreviewable automated decision.

---

## 7. Discrepancy Between 6 Routing Categories and 5 Trained Classifier Classes

### Limitation
The platform's municipal dispatch engine (`app/modules/routing/dispatcher.py`) supports **6 active departmental routing domains**:
1. `Roads & Footpaths` (`MCGM-ROADS`)
2. `Sanitation & Garbage` (`MCGM-SWM`)
3. `Water Supply & Drainage` (`MCGM-HED`)
4. `Electricity & Streetlights` (`BEST-ELEC`)
5. `Storm Water & Drainage` (`MCGM-SWD`)
6. `Traffic & Public Safety` (`MTP-TRANSIT`)

However, the statistical NLP training corpus (`CIVIC_TRAINING_CORPUS`) contains only **5 categories** across 27 samples. `Storm Water & Drainage` (`IssueCategory.STORM_WATER`) has **zero (0) training examples**.

### Handling & Operational Honesty
- **No False ML Claims**: Complaints routed to `Storm Water & Drainage` via keywords (*"nullah"*, *"culvert"*, *"stormwater"*) are marked with `classificationMode: "demo_fallback"`—never `real_ml`.
- **Administrative Flexibility**: Administrators can dynamically modify SLA hours, emergency actions, and department codes for `Storm Water & Drainage` via `/api/v1/routing/config` even though dedicated statistical ML classification is not trained for this category.
- **Vision Handling**: Like generic water complaints, visual evidence for storm water drainage routes to `FloodingDetector`, resulting in zero synthetic bounding boxes and an unvalidated/manual-review status.
