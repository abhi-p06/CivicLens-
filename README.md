# CIVILENS — Civic Infrastructure Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%20|%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6.x-646CFF.svg)](https://vitejs.dev/)
[![Tests](https://img.shields.io/badge/Tests-168%20passing-brightgreen.svg)](./tests)
[![Design](https://img.shields.io/badge/Design%20System-Aurora%20Indigo-6457E8.svg)](./DESIGN_SYSTEM.md)

**CIVILENS** is an explainable multimodal civic intelligence platform designed for municipal operations centers. It combines NLP complaint classification, computer-vision defect localization (road damage & waste accumulation), spatial corridor clustering (Haversine DBSCAN), explainable 6-factor composite priority scoring, and computer-vision-based resolution verification.

---

## Key Capabilities

1. **Multimodal Civic Vision**: Genuine PyTorch inference across supported municipal defect domains:
   - **Road Surface Damage**: Potholes (`D40`) and cracks (`D00`, `D10`, `D20`) via `YOLOv8s RDD2022` (11.14M params).
   - **Sanitation & Waste**: Packaging debris, bottles, cans, and cartons via `YOLO11s TACO` (9.43M params).
   - **Unsupported Categories (Flooding)**: Explicitly reported as unvalidated with zero synthetic detections; routed honestly to human engineering review.
2. **Multimodal Evidence Consistency**: Cross-validates citizen text claims against computer-vision detections; detects category discrepancies and routes for supervisory review without labeling citizen reports "fake".
3. **Explainable 6-Factor Priority Scoring**: Exact mathematical composite scoring (0–100 pts) summing:
   $$\text{Priority} = \text{Urgency (20)} + \text{Text Severity (20)} + \text{Visual Severity (20)} + \text{Related Reports (15)} + \text{Recency (10)} + \text{Location Risk (15)}$$
4. **Spatiotemporal GIS Hotspots**: Algorithmic spatial clustering using Haversine DBSCAN ($R=300\text{m}$) over municipal coordinates (Mumbai default).
5. **Computer-Vision Resolution Verification**: Structural similarity (`OpenCV SSIM`), color histogram correlation, and dual-YOLO defect clearance verifying physical repair evidence before issue closure.
6. **Role-Based Security & Governance**: Strict permission gates separating Citizen, Inspector, and Admin roles. Server-authenticated identities override client-supplied IDs; dev tokens are strictly disabled in production.
7. **Aurora Indigo Interface**: Clean, high-trust civic operations workspace adhering to [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md) and [`AGENTS.md`](./AGENTS.md).

---

## Quickstart

### 1. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify or download model checkpoints
python scripts/download_vision_models.py

# Start FastAPI server (Port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
# In a new terminal window
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## Running Verification & Smoke Tests

```bash
# 1. Run complete pytest suite (168 tests)
pytest -v

# 2. Run end-to-end API smoke test (10 checkpoints)
python scripts/smoke_test_api.py

# 3. Verify frontend production build
cd frontend && npm run build
```

---

## Documentation Pack

- 📖 **[Local Setup Guide](docs/SETUP_GUIDE.md)**: Prerequisites, dependency installation, model verification, environment configuration, and troubleshooting.
- 🎓 **[Academic Demo Guide](docs/DEMO_GUIDE.md)**: Step-by-step presentation script covering the 7 core demonstration scenarios.
- 🧠 **[Model Card & Provenance](docs/MODEL_CARD.md)**: Model architectures, parameters, checkpoint hashes, licenses, upstream benchmarks vs. local metrics, and domain gaps.
- ⚠️ **[Known Limitations](docs/KNOWN_LIMITATIONS.md)**: Small NLP evaluation corpus, waste detection street precision, resolution benchmark size, and human-in-the-loop policies.
- 🎨 **[Design System Specification](DESIGN_SYSTEM.md)**: Aurora Indigo color tokens, typography, component rules, and GIS map styling.
- 🛡️ **[Agent Development Boundaries](AGENTS.md)**: Architectural boundaries, stacking z-indexes, and design prohibitions.

---

## Repository Structure

```
chiragwalaproj/
├── app/
│   ├── api/routes.py              # FastAPI REST endpoints
│   ├── config.py                  # Environment and model paths
│   ├── core/                      # Pipeline coordinator, security, demo store
│   ├── db/                        # SQLite ORM models and repository
│   ├── models/issue.py            # Pydantic schemas and enums
│   └── modules/                   # Subsystems: NLP, Vision, Priority, Spatiotemporal, Routing
├── data/
│   ├── civic_issues.db            # Persistent SQLite database
│   ├── seed_issues.json           # Baseline demo seed data
│   ├── evaluation/                # Model manifests & evaluation test datasets
│   └── test_samples/              # Validated visual test fixture images
├── docs/                          # Setup guide, demo guide, model cards, limitations
├── frontend/                      # React 19 + Vite + TypeScript application
├── models/                        # Checkpoints: yolov8s_rdd2022.pt, taco_yolo11s.pt
├── scripts/                       # Model downloaders, smoke test, evaluation scripts
├── tests/                         # Pytest automated test suites (168 passing tests)
├── requirements.txt               # Backend dependencies
└── DESIGN_SYSTEM.md               # Aurora Indigo UI specification
```

---

## License

- Platform Code: MIT License
- RDD2022 Checkpoint: CC-BY-4.0 (Sekilab / Maeda et al.)
- TACO Checkpoint: MIT License (fabiocigaina / TACO Consortium)
- Ultralytics Framework: AGPL-3.0
