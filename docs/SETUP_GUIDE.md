# CIVILENS — Local Setup & Reproducible Execution Guide

This document describes the reproducible startup process for the **CIVILENS** civic issue intelligence platform on macOS and Linux systems.

---

## 1. Prerequisites and Supported Versions

| Runtime / Tool | Supported Version | Verification Command |
|---|---|---|
| **Python** | `3.10` – `3.13` (tested on `3.13.13`) | `python3 --version` |
| **Node.js** | `v18.x` – `v22.x` (tested on `v22.x`) | `node -v` |
| **npm** | `v9.x` – `v10.x` | `npm -v` |
| **SQLite3** | `3.35+` (included in Python standard library) | `sqlite3 --version` |
| **Git** | `2.30+` | `git --version` |

---

## 2. Backend Dependency Installation

From the repository root:

```bash
# 1. (Recommended) Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Upgrade pip and wheel
pip install --upgrade pip setuptools wheel

# 3. Install required Python packages
pip install -r requirements.txt
```

Core backend libraries include:
- `fastapi` & `uvicorn` (REST API engine)
- `ultralytics` & `torch` (YOLO computer vision inference)
- `scikit-learn` & `numpy` (NLP TF-IDF classifier and DBSCAN spatial clustering)
- `sqlalchemy` (SQLite ORM and persistence)
- `opencv-python` & `pillow` (SSIM structural similarity & image processing)
- `pytest` & `httpx` (Automated testing suite)

---

## 3. Frontend Dependency Installation

```bash
# Navigate to the frontend directory
cd frontend

# Install exact npm dependencies
npm install

# Return to repository root
cd ..
```

---

## 4. Environment Variables and Configuration

Copy the example environment configuration:

```bash
cp .env.example .env
```

Key environment settings:

| Variable | Default Value | Purpose |
|---|---|---|
| `CIVILENS_ENV` | `development` | Operating mode (`development` or `production`) |
| `CIVILENS_PORT` | `8000` | FastAPI server listening port |
| `CIVILENS_DB_PATH` | `data/civic_issues.db` | Persistent SQLite database file |
| `CIVILENS_DEMO_MODE` | `true` | Enables deterministic demonstration helpers & reset |
| `YOLO_MODEL_PATH` | `models/yolov8s_rdd2022.pt` | Road damage detector checkpoint |
| `WASTE_MODEL_PATH` | `models/taco_yolo11s.pt` | Municipal waste detector checkpoint |
| `CIVILENS_ALLOW_DEV_TOKENS` | `true` | Permits demo tokens in development mode |
| `CIVILENS_ALLOWED_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins (never wildcard with credentials) |

> **Security Note**: In `production` mode (`CIVILENS_ENV=production`), development tokens are strictly disabled. Real API keys (`CIVILENS_ADMIN_API_KEY` and `CIVILENS_INSPECTOR_API_KEY`) must be supplied.

---

## 5. Model Checkpoint Installation and Verification

CIVILENS requires two PyTorch/Ultralytics model checkpoints in the `models/` directory:

1. **`models/yolov8s_rdd2022.pt`** (Road Damage Detection — RDD2022 taxonomy, CC-BY-4.0)
   - SHA-256: `2cf3f60395de6591d8378294fc26b8d7c4ca8f227e455987b3713ce6eeeea119`
2. **`models/taco_yolo11s.pt`** (Municipal Waste Detection — TACO taxonomy, MIT License)
   - SHA-256: `1b9c8379aca95efa75ec1f6ac803cabd3ba531b7d4b3f459101bcfd3aaae95ef`
   - *Legacy alias `models/yolov8_waste.pt` is maintained for backward compatibility.*

To verify or download missing checkpoints automatically:

```bash
python scripts/download_vision_models.py
```

The script verifies cryptographic SHA-256 digests. If valid weights exist locally, no redundant downloads occur.

---

## 6. Database Initialization

The SQLite database at `data/civic_issues.db` is initialized automatically when the application starts via FastAPI lifecycle hooks.
If the database file does not exist, the server creates the schema and seeds baseline municipal records from `data/seed_issues.json`.

To force a clean baseline re-initialization manually:

```bash
# Optional: remove existing database file to trigger clean seed
rm -f data/civic_issues.db
```

---

## 7. Starting the FastAPI Backend

```bash
# From repository root
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`

---

## 8. Starting the React/Vite Frontend

In a separate terminal window:

```bash
cd frontend
npm run dev
```

- Web Application: `http://localhost:5173`
- The Vite dev server proxies API calls to `http://localhost:8000`.

---

## 9. Running the Test Suites

### Backend Test Suite
```bash
# Run complete test suite (168 tests)
pytest -v

# Run with concise summary
pytest -q
```

### Vision and Security Integrity Tests
```bash
pytest -v tests/test_release_vision_integrity.py
pytest -v tests/test_release_security_gate.py
```

### Full System Smoke Test
```bash
python scripts/smoke_test_api.py
```

### Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 10. Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `Port 8000 already in use` | Another process is bound to port 8000 | Find process: `lsof -i :8000` and kill it: `kill -9 <PID>` |
| `Port 5173 already in use` | Previous Vite server still running | Kill process: `lsof -i :5173` or Vite will offer port 5174 |
| `Weights file not found on disk` | Missing `.pt` checkpoint | Run `python scripts/download_vision_models.py` |
| `database is locked` | Concurrent write lock in SQLite | Ensure old background server processes are terminated |
| `HTTP 401 Unauthorized` on status update | Missing or invalid auth token | Pass header `Authorization: Bearer demo-inspector-token` (in dev) |
| `HTTP 403 Forbidden` on routing update | Inspector token used on admin route | Pass header `Authorization: Bearer demo-admin-token` |
| `Unreadable image file` (HTTP 400/422) | Invalid image format or corrupted bytes | Upload valid JPEG, PNG, or WebP under 10 MB |
