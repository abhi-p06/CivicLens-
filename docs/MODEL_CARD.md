# CIVILENS — Model Cards & Machine Learning Provenance

This document specifies the architecture, training data provenance, evaluation benchmarks, and operational boundaries of machine learning models deployed in **CIVILENS**.

---

## Model 1: Road Damage Detector (RDD2022 YOLOv8s)

### 1.1 Architecture & Implementation
- **Base Architecture**: Ultralytics YOLOv8 Small (`yolov8s`)
- **Model Checkpoint**: `models/yolov8s_rdd2022.pt`
- **Parameter Count**: 11,137,148 parameters (~11.14M)
- **Layers**: Conv, C2f backbone/head, SPPF, Anchor-free Detect head (`nc=4`)
- **Cryptographic Checksum**: `2cf3f60395de6591d8378294fc26b8d7c4ca8f227e455987b3713ce6eeeea119` (SHA-256)
- **File Size**: 22.53 MB (22,533,347 bytes)
- **Inference Runtime**: PyTorch 2.x on CPU / CUDA

### 1.2 Training Data & Provenance
- **Dataset**: Crowdsensing-based Road Damage Detection Challenge 2022 (RDD2022), Sekilab / Maeda et al.
- **Geographic Coverage**: Multi-country dashcam surveillance (Japan, India, Czech Republic).
- **Upstream Repository**: Hugging Face `SreekarAditya/yolo-rdd2022-benchmark`
- **License**: CC-BY-4.0 (RDD2022 Consortium) / AGPL-3.0 (Ultralytics framework)

### 1.3 Supported Classes & Taxonomy
| Class ID | Code | Civic UI Label | Damage Description |
|---|---|---|---|
| `0` | `D00` | Longitudinal Crack | Parallel crack running along direction of traffic flow |
| `1` | `D10` | Transverse Crack | Perpendicular crack crossing traffic lanes |
| `2` | `D20` | Alligator Crack | Interconnected polygonal fatigue fissures (structural base failure) |
| `3` | `D40` | Pothole | Bowl-shaped road surface cavity with asphalt loss |

### 1.4 Benchmark vs. Local Evaluation
- **Upstream Published Benchmark**: `0.4643 mAP@50` on RDD2022 official test split (source: RDD2022 benchmark papers).
- **Local Functional Verification**: Evaluated across controlled test samples (`data/test_samples/`):
  - Localized potholes (`repair_pothole_before.jpg`) detected with confidence 0.36–0.94.
  - Alligator fissures (`alligator_crack.jpg`) detected with confidence 0.40–0.88.
  - Zero false-positive detections produced on clean asphalt (`clean_road.jpg`).
- **Normalized Coordinate Convention**: `[ymin, xmin, ymax, xmax]` normalized to `[0.0, 1.0]`.

### 1.5 Limitations & Domain Gaps
- Trained on vehicle-mounted cameras; extreme bird's-eye drone angles or extreme close-ups may degrade detection confidence.
- Wet pavement after heavy rain exhibits specular reflections that can lower crack detection recall.

---

## Model 2: Municipal Waste & Litter Detector (TACO YOLO11s)

### 2.1 Architecture & Implementation
- **Base Architecture**: Ultralytics **YOLO11 Small** (`yolo11s.yaml`)
- **Important Note on Architecture**: The checkpoint is an authentic **YOLO11s** model featuring modern `C3k2` and `C2PSA` (Point-wise Spatial Attention) layers, **not** YOLOv8.
- **Model Checkpoint**: `models/taco_yolo11s.pt` (*legacy alias `models/yolov8_waste.pt` maintained for backward compatibility*)
- **Parameter Count**: 9,431,275 parameters (~9.43M)
- **Cryptographic Checksum**: `1b9c8379aca95efa75ec1f6ac803cabd3ba531b7d4b3f459101bcfd3aaae95ef` (SHA-256)
- **File Size**: 19.19 MB (19,187,027 bytes)
- **License**: MIT License (declared by checkpoint creator) / AGPL-3.0 (Ultralytics framework)

### 2.2 Training Data & Provenance
- **Dataset**: TACO (Trash Annotations in Context) municipal litter dataset (Proença & Simões, 2020).
- **Source Repository**: Hugging Face `fabiocigaina/TACO-yolo11s`
- **Declared Classes**: 9 municipal waste categories:
  - `0`: Plastic bag & wrapper (`Plastic Waste / Wrapper`)
  - `1`: Cigarette (`Litter Debris`)
  - `2`: Bottle (`Bottle / Container`)
  - `3`: Bottle cap (`Bottle Cap / Small Plastic`)
  - `4`: Can (`Metal Can Debris`)
  - `5`: Other plastic (`Plastic Scrap`)
  - `6`: Carton (`Discarded Carton / Box`)
  - `7`: Cup (`Disposable Cup`)
  - `8`: Other (`Solid Waste / Litter`)

### 2.3 Benchmark vs. Local Evaluation
- **Upstream Published Benchmark**: `mAP50 = 0.311`, `mAP50-95 = 0.234` on TACO validation set at 120 epochs (source: Hugging Face repository `fabiocigaina/TACO-yolo11s`).
- **Local Held-Out Evaluation (N=5 Annotated Street Samples)**:
  - Dataset Manifest: `data/evaluation/waste_detection_eval_manifest.json`
  - **Image Presence Accuracy**: `100.0%`
  - **Precision@50**: `27.3%`
  - **Recall@50**: `100.0%`
  - **F1-Score@50**: `42.9%`
  - **True Positives (IoU ≥ 0.50)**: `6`
  - **False Positives**: `16`
  - **False Negatives**: `0`

### 2.4 Domain Gap & Operational Limitations
- **Critical Finding**: While recall on visible trash is very high (100%), precision in local street evaluation is low (27.3%) due to frequent false detections against textured pavement, gravel, and urban shadows.
- **Operational Strategy**:
  - The detection confidence threshold is calibrated to `0.20`.
  - Used in conjunction with textual NLP classification to avoid false-positive municipal dispatches.
  - The upstream benchmark mAP is **never** presented as local accuracy.

---

## Subsystem 3: Street Flooding & Waterlogging (Explicitly Unsupported)

### 3.1 Status
- **Operational Status**: **OPERATIONALLY UNVALIDATED / EXPLICITLY UNSUPPORTED**
- **Detector Implementation**: `FloodingDetector` in `app/modules/vision/flooding_detector.py`
- **Synthetic Bounding Boxes**: **Zero (0)**. Under no circumstances does CIVILENS fabricate synthetic bounding boxes or fake confidence scores.

### 3.2 Technical & Domain Provenance Analysis
1. Public computer-vision flood models are primarily trained on satellite SAR (Synthetic Aperture Radar) or high-altitude aerial imagery. They do not generalize to street-level CCTV or citizen smartphone photos.
2. Ground-level street wetness or puddles from normal rain do not establish subsurface municipal water pipe bursts or sewer overflows.
3. Automated object bounding boxes cannot reliably segment variable water reflection boundaries without severe false-alarm rates.

### 3.3 Routing Policy
- Complaints reported under `Water Supply & Drainage` or citing flooding are routed to **MANUAL REVIEW** with an explicit explanatory note:
  > *"Inspection pending: Photographic evidence cannot confirm subsurface municipal water pipe rupture or source of leakage. Routed for field engineer pressure inspection."*
- Text urgency and textual severity are fully evaluated, allowing high-priority flooding issues to be escalated based on human grievance reports without bogus vision detections.

---

## Subsystem 4: Text NLP Classifier (TF-IDF + Scikit-Learn)

### 4.1 Architecture & Implementation
- **Pipeline Architecture**: Scikit-Learn `Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words="english")), ("clf", LogisticRegression(C=5.0, max_iter=200, random_state=42))])`
- **Training Corpus**: In-memory dataset of exactly **27 representative municipal grievance samples** (`CIVIC_TRAINING_CORPUS` in `app/modules/nlp/classifier.py`).
- **Supported Categories (5 categories represented in training)**:
  1. `Roads & Footpaths` (`IssueCategory.ROAD_DAMAGE`): 6 samples
  2. `Sanitation & Garbage` (`IssueCategory.SANITATION`): 6 samples
  3. `Water Supply & Drainage` (`IssueCategory.WATER_SUPPLY`): 6 samples
  4. `Electricity & Streetlights` (`IssueCategory.ELECTRICAL`): 5 samples
  5. `Traffic & Public Safety` (`IssueCategory.TRAFFIC_SAFETY`): 4 samples
- **Urgency Extraction**: Lexical hazard analyzer mapping critical keywords (`accident`, `death`, `injury`, `burst`, `live wire`, `open manhole`), high-priority cues (`dangerous`, `hazard`, `flooding`, `sparking`), and moderate cues (`broken`, `stench`, `pothole`).
- **Text Severity Extraction**: Rule-based physical impairment scoring (0.0–1.0) evaluated from infrastructural disruption claims.

### 4.2 Evaluation Provenance & Data Split
- **Held-Out Test Data**: Exactly **6 held-out seed issues** (`CIVIC-2026-001` through `CIVIC-2026-006` in `data/seed_issues.json`).
- **Data Leakage & Overlap**: Strictly **0% text overlap** between the 27 training samples and the 6 held-out evaluation complaints (verified by automated regression test `tests/test_evaluation_provenance.py`).
- **Evaluation Metrics & Denominators**:
  - Dynamically computed via `GET /api/v1/evaluation/metrics`.
  - Classification accuracy, macro/weighted precision, recall, and F1 are computed across active database records ($N=6$ at baseline seed state).
  - Calculated strictly via Scikit-Learn `accuracy_score`, `precision_score`, `recall_score`, and `f1_score` — zero fabricated metrics.
- **Academic Scope & Statistical Limitation**: This corpus demonstrates prototype mechanics and deterministic pipeline integration. These small samples **must never be claimed as municipal-scale statistical accuracy**.

### 4.3 Sixth Routing Category (Storm Water & Drainage) Boundary
- **Administrative Routing Domain**: The platform defines 6 configurable municipal departments in `department_dispatcher` (`get_default_routing_config()`), including `Storm Water & Drainage` (`IssueCategory.STORM_WATER` routed to `Storm Water Drains Department (SWD)` / `MCGM-SWD`).
- **Absence of Dedicated ML Training Samples**: The trained TF-IDF + Logistic Regression model (`_pipeline`) does NOT contain dedicated training samples for `IssueCategory.STORM_WATER`. It has exactly 5 trained classes.
- **Honest Fallback Handling**: Unseen citizen complaints containing explicit storm water drainage terminology (e.g., *"nullah"*, *"culvert"*, *"stormwater"*) produce ML confidence <0.25 across the 5 trained classes and drop to deterministic keyword fallback (`mode="demo_fallback"`). They are routed directly to `Storm Water Drains Department (SWD)` without falsely claiming `real_ml` inference.

---

## Model 4: Roboflow Hosted Pothole Detector (Experimental Candidate)

### 4.1 Architecture & Implementation
- **Provider**: Roboflow Serverless Hosted API
- **Model ID**: `potholes-krmk8/2`
- **Architecture**: YOLO26 Object Detection (Upstream Roboflow Train)
- **Deployment Mode**: Optional comparison candidate via `InferenceHTTPClient` (`inference-sdk`)
- **Primary Supported Class**: `Pothole` (Single class)

### 4.2 Upstream Publisher Claims vs. Local Held-Out Benchmark
- **Upstream Publisher Claims** (Jayden's Workspace, Universe Roboflow):
  - mAP@50: **91.2%**
  - Precision: **89.1%**
  - Recall: **85.9%**
- **CIVILENS Controlled Held-Out Evaluation** (`scripts/evaluate_roboflow_candidates.py` on held-out road test split, $N=10$):
  - **Local Validation Verification**: Achieved **94.6% confidence** on clear, localized close-up test pothole (`repair_pothole_before.jpg`).
  - **Held-Out Test Set (Complex Street Scenarios)**:
    - Precision: **0.0%**
    - Recall: **0.0%** (0 True Positives, 5 False Negatives)
    - F1-Score: **0.0%**
    - mAP@50: **0.0%**
  - *Comparison with Local Production Model (`models/yolov8s_rdd2022.pt`)*:
    - Local Precision: **25.0%**, Recall: **20.0%**, F1: **22.2%**, mAP@50: **20.0%** on same difficult test split.
- **Taxonomic & Domain Limitations**:
  - The hosted model predicts strictly a single class (`Pothole`). It possesses **zero capability** for longitudinal cracks (`D00`), transverse cracks (`D10`), or structural alligator fatigue cracking (`D20`).
  - The model fails to generalize to distant, oblique-angle, or shadowed potholes prevalent in Indian municipal dashcam imagery.

### 4.3 Operational Latency, Quota & Privacy Boundaries
- **Average Inference Latency**: **615.6 ms** (cloud round-trip + inference) vs. **218.9 ms** for local PyTorch on CPU (~2.8x slower).
- **Quota & Credit Protection**: Roboflow serverless calls consume monthly API plan credits. Deduplicated with SHA-256 caching (`data/cache/roboflow_predictions_cache.json`).
- **Data Privacy & Sovereign Boundary**: Image payloads are transmitted over public HTTPS to third-party US cloud infrastructure. For civic grievance platforms requiring data residency compliance (e.g. municipal privacy directives), unencrypted cloud forwarding without citizen consent is prohibited.
- **Production Status**: **REJECTED FOR PRODUCTION DEPLOYMENT**. Retained strictly as optional side-by-side comparison tooling via `POST /api/v1/vision/compare`.

---

## Model 5: Roboflow Hosted Municipal Garbage Detector (Experimental Candidate)

### 5.1 Architecture & Implementation
- **Provider**: Roboflow Serverless Hosted API
- **Model ID**: `garbage_detection-wvzwv-n8vsv/1`
- **Architecture**: RF-DETR Nano (Transformer-based object detection)
- **Deployment Mode**: Optional comparison candidate via `InferenceHTTPClient` (`inference-sdk`)
- **Primary Supported Class**: `garbage` (Broad monolithic class)

### 5.2 Upstream Publisher Claims vs. Local Held-Out Benchmark
- **Upstream Publisher Claims** (Sahil's Workspace, Universe Roboflow):
  - mAP@50: **91.8%**
  - Precision: **93.4%**
  - Recall: **88.9%**
- **CIVILENS Controlled Held-Out Evaluation** (`scripts/evaluate_roboflow_candidates.py` on held-out waste test split, $N=10$, IoU $\ge 0.50$):
  - **Hosted Model (`RF-DETR Nano`)**:
    - Precision: **50.0%** (2 TP, 2 FP)
    - Recall: **28.6%** (2 TP, 5 FN)
    - F1-Score: **36.4%**
    - mAP@50: **14.4%**
    - mAP@50-95: **7.2%**
  - **Local Production Model (`models/taco_yolo11s.pt`)**:
    - Precision: **87.5%** (7 TP, 1 FP)
    - Recall: **100.0%** (7 TP, 0 FN)
    - F1-Score: **93.3%**
    - mAP@50: **100.0%**
    - mAP@50-95: **68.9%**
- **Taxonomic & Domain Limitations**:
  - The hosted RF-DETR Nano model outputs only a generic `garbage` bounding box, losing all granular material taxonomy.
  - In contrast, the local TACO YOLO11s model accurately segments 9 distinct civic waste categories (`Plastic bag`, `Bottle`, `Can`, `Carton`, etc.), enabling targeted waste-management dispatch.

### 5.3 Operational Latency, Quota & Privacy Boundaries
- **Average Inference Latency**: **728.0 ms** vs. **93.7 ms** for local YOLO11s on CPU (~7.8x slower).
- **Quota & Credit Protection**: Monitored and cached deterministically using image SHA-256 digests.
- **Production Status**: **REJECTED FOR PRODUCTION DEPLOYMENT**. Local TACO YOLO11s demonstrates superior precision (+37.5%), superior recall (+71.4%), 8x faster execution, and zero external network/cloud dependencies.
