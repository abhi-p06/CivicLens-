# CIVILENS — Comprehensive Technical Reference

**Author**: CIVILENS Engineering Team  
**Scope**: Complete Technical Reference Manual for Backend, Frontend, APIs, Database Schemas, Computer Vision Pipelines, and System Configuration.  
**Platform Version**: 1.0.0 (API v1)  
**Target Environment**: Python 3.10–3.13, Node 18+, React 19, SQLite 3  

---

## 1. System Architecture Overview

CIVILENS is built on a clean three-tier architecture with modular service layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION TIER (FRONTEND)                    │
│  - React 19 / TypeScript 5.x / Vite 6.x                                │
│  - Tailwind CSS + "Aurora Indigo" Design System                        │
│  - Tactical Leaflet GIS Mapping Workspace                              │
│  - Framer Motion Orchestrated Micro-Interactions                       │
│  - State Management: React Context (AuthContext) + Component Hooks     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (JSON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION TIER (BACKEND)                      │
│  - FastAPI REST API Engine with ASGI Concurrency (uvicorn)             │
│  - Pydantic v2 Schema Validation and Strict Serialization              │
│  - Security: PBKDF2 Password Hashing & Expiring HMAC-SHA256 Tokens     │
│  - Pipeline Coordinator (`CivicIssueIntelligencePipeline`)             │
│  - Subsystems: Vision, NLP, Priority, GIS, Routing, Guidance           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ SQLAlchemy 2.0 ORM
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          DATA & INFERENCE TIER                         │
│  - Persistent SQLite Database (WAL mode, ACID-compliant)               │
│  - Local PyTorch / Ultralytics Inference (`models/`)                   │
│  - Roboflow Serverless API Client (`InferenceHTTPClient`)              │
│  - Local Disk Upload Storage (`uploads/`)                              │
│  - Deterministic SHA-256 JSON Cache (`data/cache/`)                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Complete REST API Reference (48 Endpoints)

All endpoints are prefixed with `/api/v1` unless noted otherwise.

### 2.1 Health & Diagnostics

#### `GET /api/v1/health`
- **Purpose**: System health monitoring and model status report.
- **Auth Required**: No (Public).
- **Required Role**: None.
- **Response**: `200 OK`
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-11-02T00:00:00Z",
    "subsystems": {
      "database": "connected",
      "vision_local_road": "loaded",
      "vision_local_waste": "loaded",
      "vision_roboflow_adapter": "ready",
      "nlp_classifier": "ready",
      "spatiotemporal": "ready"
    }
  }
  ```

---

### 2.2 Upload & Image Management

#### `POST /api/v1/upload`
- **Purpose**: Validates and stores citizen grievance photographs.
- **Auth Required**: Optional (Citizen can upload before logging in or while logged in).
- **Request**: `multipart/form-data` with `file: UploadFile`.
- **Validation**:
  - Magic bytes verified via PIL.
  - Allowed MIME types: `image/jpeg`, `image/png`, `image/webp`.
  - File size limit: `MAX_UPLOAD_SIZE_MB` (Default: 10MB).
  - Filename sanitization against path traversal (`../` stripped).
- **Response**: `201 Created`
  ```json
  {
    "upload_id": "2a178612-0bf4-4ea7-93ec-f011ce91232f",
    "filename": "2a178612-0bf4-4ea7-93ec-f011ce91232f.jpg",
    "content_type": "image/jpeg",
    "size_bytes": 145892,
    "url": "/api/v1/uploads/2a178612-0bf4-4ea7-93ec-f011ce91232f"
  }
  ```
- **Error Conditions**: `400 Bad Request` (corrupted image or spoofed extension), `413 Payload Too Large` (>10MB).

#### `GET /api/v1/uploads/{upload_id}`
- **Purpose**: Serves stored image files by immutable upload UUID.
- **Auth Required**: No (Public read-only for rendered UI evidence).
- **Response**: `FileResponse` with caching headers (`Cache-Control: public, max-age=86400`).

---

### 2.3 Authentication & User Management

#### `POST /api/v1/auth/login`
- **Purpose**: Authenticates Citizen, Inspector, or Admin users.
- **Request Body**:
  ```json
  {
    "username_or_email": "inspector@civilens.org",
    "password": "[MASKED]",
    "expected_role": "inspector"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 43200,
    "user": {
      "user_id": "INSP-MUMBAI-01",
      "name": "Abhinay",
      "email": "inspector@civilens.org",
      "role": "inspector"
    }
  }
  ```
- **Error Conditions**: `401 Unauthorized` (invalid password or mismatched expected role).

#### `POST /api/v1/auth/register`
- **Purpose**: Allows self-registration for Citizen accounts only.
- **Request Body**:
  ```json
  {
    "username": "abhinay_citizen",
    "email": "citizen@civilens.org",
    "password": "[MASKED]",
    "name": "Abhinay"
  }
  ```
- **Response**: `201 Created` with JWT access token.

#### `GET /api/v1/auth/me`
- **Purpose**: Retrieves currently authenticated user session.
- **Auth Required**: Yes (`Bearer <token>`).
- **Response**: `200 OK` with user details.

#### `POST /api/v1/auth/logout`
- **Purpose**: Logs out the active user session.
- **Auth Required**: Yes.
- **Response**: `200 OK` (`{"message": "Logged out successfully"}`).

#### `GET /api/v1/admin/users`
- **Purpose**: Lists registered users across the platform.
- **Auth Required**: Yes (`ADMIN` role required).
- **Response**: `200 OK` with array of user records (passwords/salts excluded).

---

### 2.4 Analysis & Vision Inference

#### `POST /api/v1/analyze`
- **Purpose**: Runs preliminary AI pipeline without persisting the issue (interactive playground).
- **Request Body**: `IssueCreate` schema.
- **Response**: Full AI assessment breakdown (NLP prediction, YOLO detections, priority score).

#### `POST /api/v1/vision/compare`
- **Purpose**: Executes explicit side-by-side computer-vision inference between Local YOLO Baseline and Roboflow Hosted Candidate.
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN` role required).
- **Request Body**:
  ```json
  {
    "image_path": "uploads/2a178612-0bf4-4ea7-93ec-f011ce91232f.jpg",
    "category_hint": "Roads & Footpaths"
  }
  ```
- **Response**: `200 OK` containing `VisionComparisonData` payload (counts, models, boxes, latency, cache state).

---

### 2.5 Grievance Management & Lifecycle

#### `POST /api/v1/issues`
- **Purpose**: Creates, analyzes, prioritizes, and persists a new civic complaint.
- **Auth Required**: Optional (Citizen portal).
- **Request Body**: `IssueCreate`
  ```json
  {
    "complaintText": "Deep pothole crater near school gate causing bike skidding.",
    "location": "Somaiya Vidyavihar Main Gate, Vidyavihar East",
    "latitude": 19.0728,
    "longitude": 72.8998,
    "location_method": "gps",
    "uploadId": "2a178612-0bf4-4ea7-93ec-f011ce91232f",
    "category": "Roads & Footpaths",
    "ward": "N-Ward"
  }
  ```
- **Validation**: Lat/Lng validated within Mumbai/Navi Mumbai bounding box (`[18.85, 19.33]`, `[72.75, 73.18]`).
- **Response**: `201 Created` with full `Issue` object including calculated priority, visual detections, and department routing.

#### `GET /api/v1/issues`
- **Purpose**: Lists all issues with optional filtering.
- **Auth Required**: No (Inspector / Admin filterable).
- **Query Parameters**:
  - `category`: Filter by `IssueCategory`.
  - `priority`: Filter by `PriorityLevel` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
  - `status`: Filter by `IssueStatus` (`OPEN`, `IN_PROGRESS`, `RESOLVED`, etc.).
  - `hotspot_only`: Boolean flag.
- **Response**: `200 OK` with array of `Issue` objects.

#### `GET /api/v1/issues/my`
- **Purpose**: Retrieves complaints submitted by the authenticated citizen.
- **Auth Required**: Yes (`CITIZEN` role).
- **Response**: `200 OK` with citizen's issues.

#### `GET /api/v1/issues/{issue_id}`
- **Purpose**: Retrieves a single issue by ID.
- **Response**: `200 OK` with `Issue` object.

#### `PATCH /api/v1/issues/{issue_id}/status`
- **Purpose**: Updates complaint status.
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).
- **Request Body**: `{"status": "ACTION IN PROGRESS"}`.
- **Response**: `200 OK` with updated `Issue`.

---

### 2.6 Municipal Operations & Ward Management

#### `GET /api/v1/operations/kpis`
- **Purpose**: Calculates database-driven operational KPIs for the Command Center.
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).
- **Response**: `200 OK`
  ```json
  {
    "unassigned_count": 5,
    "high_priority_count": 11,
    "work_in_progress_count": 8,
    "resolved_this_month_count": 14,
    "road_workload_count": 18,
    "sanitation_workload_count": 11,
    "total_active_count": 29,
    "ward_distribution": {"N-Ward": 12, "L-Ward": 8, "G/North": 9}
  }
  ```

#### `POST /api/v1/issues/{issue_id}/assign`
- **Purpose**: Assigns complaint to a department and operational field team.
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).
- **Request Body**: `TaskAssignRequest` (department, team_id, team_name, assigned_officer, priority, instructions).
- **Response**: `200 OK`.

#### `POST /api/v1/issues/{issue_id}/schedule`
- **Purpose**: Schedules inspection or repair date for an issue.
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).
- **Request Body**: `ScheduleRequest` (`scheduled_date`, `shift`, `notes`).
- **Response**: `200 OK`.

#### `POST /api/v1/issues/{issue_id}/action`
- **Purpose**: Records field progress actions (temporary safety measures, repeat waste pickups).
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).
- **Request Body**: `ActionRequest` (temporary_measures, repeat_collection, action_notes).
- **Response**: `200 OK`.

#### `POST /api/v1/issues/{issue_id}/complete`
- **Purpose**: Submits completion details, notes, and post-action photograph proof.
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).
- **Request Body**: `CompleteRequest` (completion_notes, contractor_id, completion_upload_id).
- **Response**: `200 OK` (transitions status to `AWAITING CONFIRMATION` or `RESOLVED`).

#### `POST /api/v1/issues/{issue_id}/reopen`
- **Purpose**: Reopens an unresolved or unsatisfactory complaint.
- **Auth Required**: Yes (`CITIZEN`, `INSPECTOR`, or `ADMIN`).
- **Request Body**: `ReopenRequest` (`reopen_reason`, `target_status: "REOPENED"`).
- **Response**: `200 OK`.

#### `POST /api/v1/issues/{issue_id}/feedback`
- **Purpose**: Records citizen rating and resolution feedback.
- **Auth Required**: Yes (`CITIZEN`).
- **Request Body**: `FeedbackRequest` (`rating: 1-5`, `comments`, `satisfied: bool`).
- **Response**: `200 OK`.

---

### 2.7 Field Teams & Ward Configurations

#### `GET /api/v1/teams`
- **Purpose**: Lists operational teams (filtered by category if provided).
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).

#### `POST /api/v1/admin/teams`
- **Purpose**: Creates a new municipal field team.
- **Auth Required**: Yes (`ADMIN`).

#### `PATCH /api/v1/admin/teams/{team_id}`
- **Purpose**: Updates team details or availability status (`AVAILABLE`, `DEPLOYED`, `OFF_DUTY`).
- **Auth Required**: Yes (`ADMIN`).

#### `DELETE /api/v1/admin/teams/{team_id}`
- **Purpose**: Deletes a field team record.
- **Auth Required**: Yes (`ADMIN`).

#### `GET /api/v1/admin/wards`
- **Purpose**: Lists all municipal ward configurations.
- **Auth Required**: Yes (`ADMIN`).

#### `PATCH /api/v1/admin/wards/{ward_code}`
- **Purpose**: Updates ward lead officer and active team allocations.
- **Auth Required**: Yes (`ADMIN`).

---

### 2.8 Computer Vision Verification (Backend Archive)

#### `POST /api/v1/issues/{issue_id}/verify`
- **Purpose**: Computes OpenCV SSIM and YOLO clearance between before/after repair photos.
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).
- **Request Body**: `{"resolutionUploadId": "uuid", "inspectorRemarks": "..."}`.
- **Response**: `200 OK` containing `ResolutionEvidence` (SSIM, color correlation, clearance status).

#### `GET /api/v1/issues/{issue_id}/verifications`
- **Purpose**: Retrieves audit history of all verification attempts on an issue.

---

### 2.9 GIS, Geolocation & Spatiotemporal Telemetry

#### `GET /api/v1/gis/geojson`
- **Purpose**: Exports active complaints formatted as a standard GeoJSON FeatureCollection.
- **Auth Required**: No (Public GIS view).

#### `GET /api/v1/gis/map`
- **Purpose**: Retrieves structured map points with marker icons, priority colors, and cluster IDs.
- **Auth Required**: No.

#### `GET /api/v1/geo/bounds`
- **Purpose**: Returns configured geographic boundaries for Mumbai & Navi Mumbai.
- **Response**:
  ```json
  {
    "region": "Mumbai & Navi Mumbai",
    "min_lat": 18.85,
    "max_lat": 19.33,
    "min_lng": 72.75,
    "max_lng": 73.18
  }
  ```

#### `GET /api/v1/geo/reverse-geocode`
- **Purpose**: Converts GPS latitude/longitude into a readable Mumbai street address.
- **Query Parameters**: `lat`, `lng`.
- **Response**: `{"address": "Somaiya Vidyavihar, Vidyavihar East, Mumbai", "ward": "N-Ward"}`.

#### `GET /api/v1/geo/search`
- **Purpose**: Autocomplete search for Mumbai localities, landmarks, and transit junctions.
- **Query Parameters**: `q` (query string).
- **Response**: Array of matching landmarks with latitude, longitude, and ward code.

#### `GET /api/v1/hotspots`
- **Purpose**: Computes and returns Haversine DBSCAN hotspot clusters ($R=400\text{m}$).

#### `GET /api/v1/recurring`
- **Purpose**: Lists locations experiencing recurring grievances over 30-day windows.

#### `GET /api/v1/routing/config`
- **Purpose**: Returns active department routing mappings, SLAs, and emergency actions.

#### `POST /api/v1/routing/config`
- **Purpose**: Updates department routing rules and SLA configurations.
- **Auth Required**: Yes (`ADMIN` role required).

#### `GET /api/v1/evaluation/metrics`
- **Purpose**: Computes live precision, recall, F1, and confusion matrix across database records.

#### `POST /api/v1/demo/reset`
- **Purpose**: Resets database to seed baseline complaints (`CIVIC-2026-001` through `006`).
- **Auth Required**: Yes (`ADMIN` role).

---

### 2.10 AI Field Guidance & Knowledge Base

#### `GET /api/v1/issues/{issue_id}/guidance`
- **Purpose**: Retrieves grounded statutory field guidance for an issue.
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).
- **Response**: `FieldGuidanceResult` (citations, precautions, actions, checklists).

#### `POST /api/v1/issues/{issue_id}/guidance/regenerate`
- **Purpose**: Forces re-synthesis of field guidance bypassing cache.
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).

#### `POST /api/v1/issues/{issue_id}/guidance/decision`
- **Purpose**: Records officer decision on an action recommendation (Accept, Edit, Dismiss).
- **Auth Required**: Yes (`INSPECTOR` or `ADMIN`).
- **Request Body**: `GuidanceDecisionRequest` (`item_id`, `decision`, `edited_text`, `reason`).

#### `GET /api/v1/guidance/documents/{doc_id}`
- **Purpose**: Retrieves full text, sections, and metadata of an indexed statutory guideline.

#### `GET /api/v1/admin/guidance/sources`
- **Purpose**: Lists registered government research domains (MoRTH, MCGM, CPCB, etc.).
- **Auth Required**: Yes (`ADMIN`).

#### `PATCH /api/v1/admin/guidance/sources/{source_id}`
- **Purpose**: Updates allowlist status or active state of a guidance source.
- **Auth Required**: Yes (`ADMIN`).

#### `GET /api/v1/admin/guidance/documents`
- **Purpose**: Lists indexed statutory documents.
- **Auth Required**: Yes (`ADMIN`).

#### `PATCH /api/v1/admin/guidance/documents/{doc_id}`
- **Purpose**: Approves or updates document status (`CURRENT`, `DRAFT`, `SUPERSEDED`).
- **Auth Required**: Yes (`ADMIN`).

#### `POST /api/v1/admin/guidance/ingest`
- **Purpose**: Ingests new official document from an allowlisted government URL.
- **Auth Required**: Yes (`ADMIN`).

---

## 3. Database Schema Reference (9 Relational Tables)

Persistent SQLite database located at `data/civic_issues.db` (or `data/civilens_presentation.db` in presentation mode).

### Table 1: `issues`
| Column Name | SQLite Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | Unique complaint ID (e.g. `CIVIC-2026-23363092`) |
| `complaint_text` | `TEXT` | `NOT NULL` | Citizen grievance narrative text |
| `category` | `VARCHAR(64)` | `NOT NULL, INDEX` | Civic category (`Roads & Footpaths`, `Sanitation & Garbage`, etc.) |
| `urgency` | `FLOAT` | `NOT NULL, DEFAULT 0.0` | NLP lexical urgency score (0.0 to 1.0) |
| `severity` | `FLOAT` | `NOT NULL, DEFAULT 0.0` | NLP physical disruption severity (0.0 to 1.0) |
| `location` | `VARCHAR(255)` | `NOT NULL, INDEX` | Landmark or locality address |
| `latitude` | `FLOAT` | `NOT NULL, INDEX` | Geocoded latitude coordinate |
| `longitude` | `FLOAT` | `NOT NULL, INDEX` | Geocoded longitude coordinate |
| `ward` | `VARCHAR(64)` | `NULLABLE, INDEX` | Municipal administrative ward (e.g. `N-Ward`, `H/West`) |
| `timestamp` | `VARCHAR(64)` | `NOT NULL, INDEX` | ISO 8601 creation timestamp |
| `duplicate_group` | `VARCHAR(64)` | `NULLABLE` | Near-duplicate cluster identifier |
| `is_duplicate` | `BOOLEAN` | `NOT NULL, DEFAULT 0` | Near-duplicate flag |
| `near_duplicate_count` | `INTEGER` | `NOT NULL, DEFAULT 0` | Number of related reports in proximity |
| `visual_detection` | `VARCHAR(128)` | `NULLABLE` | Primary computer-vision label |
| `visual_confidence` | `FLOAT` | `NOT NULL, DEFAULT 0.0` | Detector confidence score (0.0 to 1.0) |
| `visual_severity` | `FLOAT` | `NOT NULL, DEFAULT 0.0` | Normalized defect surface area (0.0 to 1.0) |
| `evidence_consistency`| `FLOAT` | `NOT NULL, DEFAULT 0.0` | Multimodal consistency score (0.0 to 1.0) |
| `consistency_level` | `VARCHAR(64)` | `NOT NULL` | `CONSISTENT`, `INCONSISTENT`, `MANUAL REVIEW` |
| `consistency_flag` | `VARCHAR(64)` | `NOT NULL` | UI badge text |
| `recurrence` | `INTEGER` | `NOT NULL, DEFAULT 1` | Historical report recurrence count |
| `is_hotspot` | `BOOLEAN` | `NOT NULL, DEFAULT 0` | Flagged as Haversine DBSCAN hotspot |
| `hotspot_cluster_id`| `VARCHAR(64)` | `NULLABLE` | Hotspot cluster identifier |
| `priority_score` | `FLOAT` | `NOT NULL, INDEX` | Composite 6-factor score (0.0 to 100.0) |
| `priority_level` | `VARCHAR(32)` | `NOT NULL, INDEX` | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `department` | `VARCHAR(128)` | `NOT NULL, INDEX` | Assigned municipal agency |
| `recommended_action`| `TEXT` | `NOT NULL` | Statutory operational instruction |
| `sla_hours` | `INTEGER` | `NOT NULL, DEFAULT 72`| Maximum resolution SLA timeframe |
| `citizen_id` | `VARCHAR(64)` | `NULLABLE, INDEX` | Submitting citizen account ID |
| `status` | `VARCHAR(32)` | `NOT NULL, INDEX` | `OPEN`, `ASSIGNED`, `IN PROGRESS`, `RESOLVED`, etc. |
| `data_json` | `TEXT` | `NOT NULL` | Full Pydantic Issue JSON payload (preserves metadata, guidance, timeline) |
| `created_at` | `DATETIME` | `NOT NULL` | Record creation timestamp |
| `updated_at` | `DATETIME` | `NOT NULL` | Record update timestamp |

### Table 2: `users`
| Column Name | SQLite Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | User ID (e.g. `CITIZEN-001`, `INSP-MUMBAI-01`) |
| `username` | `VARCHAR(64)` | `UNIQUE, NOT NULL` | Login username |
| `email` | `VARCHAR(128)` | `UNIQUE, NOT NULL` | Official email address |
| `name` | `VARCHAR(128)` | `NOT NULL` | Display name (e.g. `Abhinay`) |
| `password_hash` | `VARCHAR(256)` | `NOT NULL` | PBKDF2-HMAC-SHA256 hash (100,000 iterations) |
| `salt` | `VARCHAR(64)` | `NOT NULL` | 16-byte random cryptographic salt (hex-encoded) |
| `role` | `VARCHAR(32)` | `NOT NULL, INDEX` | `citizen`, `inspector`, `admin` |
| `is_active` | `BOOLEAN` | `NOT NULL, DEFAULT 1`| Active status flag |
| `created_at` | `DATETIME` | `NOT NULL` | Creation timestamp |

### Table 3: `operational_teams`
| Column Name | SQLite Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | Team ID (e.g. `TEAM-RDS-N01`, `TEAM-SWM-K01`) |
| `name` | `VARCHAR(128)` | `NOT NULL` | Team name (e.g. `Ward N Asphalt Patch Crew`) |
| `department` | `VARCHAR(128)` | `NOT NULL` | Municipal department |
| `category` | `VARCHAR(64)` | `NOT NULL` | Supported issue category |
| `status` | `VARCHAR(32)` | `NOT NULL, DEFAULT 'AVAILABLE'` | `AVAILABLE`, `DEPLOYED`, `OFF_DUTY` |
| `ward` | `VARCHAR(64)` | `NOT NULL, DEFAULT 'ALL'` | Assigned operational ward |
| `contact_lead` | `VARCHAR(128)` | `NOT NULL` | Duty supervisor name |
| `active_tasks_count`| `INTEGER` | `NOT NULL, DEFAULT 0` | Current active work order count |
| `created_at` | `DATETIME` | `NOT NULL` | Creation timestamp |
| `updated_at` | `DATETIME` | `NOT NULL` | Update timestamp |

### Table 4: `ward_configs`
| Column Name | SQLite Data Type | Constraints | Description |
|---|---|---|---|
| `ward_code` | `VARCHAR(64)` | `PRIMARY KEY` | Ward code (e.g. `N-Ward`, `L-Ward`, `G/North`) |
| `ward_name` | `VARCHAR(128)` | `NOT NULL` | Full ward name (e.g. `Vidyavihar / Ghatkopar`) |
| `lead_officer` | `VARCHAR(128)` | `NOT NULL` | Ward executive engineer / inspector name |
| `active_teams` | `TEXT` | `NOT NULL` | JSON array of assigned team IDs |
| `updated_at` | `DATETIME` | `NOT NULL` | Update timestamp |

### Table 5: `uploads`
| Column Name | SQLite Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | Upload UUID |
| `filename` | `VARCHAR(255)` | `NOT NULL` | Stored disk filename |
| `content_type` | `VARCHAR(64)` | `NOT NULL` | Validated MIME type (`image/jpeg`, etc.) |
| `size_bytes` | `INTEGER` | `NOT NULL` | File size in bytes |
| `original_filename`| `VARCHAR(255)` | `NULLABLE` | Uploaded client filename |
| `issue_id` | `VARCHAR(64)` | `NULLABLE, INDEX` | Associated issue ID |
| `created_at` | `DATETIME` | `NOT NULL` | Timestamp |

### Table 6: `guidance_sources`
| Column Name | SQLite Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | Source ID (e.g. `SRC-MORTH-01`) |
| `name` | `VARCHAR(128)` | `NOT NULL` | Government authority name |
| `domain` | `VARCHAR(128)` | `UNIQUE, NOT NULL` | Allowlisted domain (e.g. `morth.nic.in`) |
| `base_url` | `VARCHAR(255)` | `NOT NULL` | Base URL |
| `category` | `VARCHAR(64)` | `NOT NULL` | Target domain (`Roads & Footpaths`, `Sanitation`) |
| `is_active` | `BOOLEAN` | `NOT NULL, DEFAULT 1`| Active research flag |
| `is_allowlisted` | `BOOLEAN` | `NOT NULL, DEFAULT 1`| Strict SSRF protection allowlist |
| `last_status` | `VARCHAR(32)` | `NOT NULL` | Retrieval status (`HEALTHY`, `NEVER_RUN`) |
| `updated_at` | `DATETIME` | `NOT NULL` | Update timestamp |

### Table 7: `guidance_documents`
| Column Name | SQLite Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | Document ID (e.g. `DOC-MORTH-3004`) |
| `source_id` | `VARCHAR(64)` | `NOT NULL, INDEX` | Foreign key referencing `guidance_sources.id` |
| `source_domain` | `VARCHAR(128)` | `NOT NULL` | Allowlisted domain |
| `source_org` | `VARCHAR(128)` | `NOT NULL` | Authoritative organization |
| `title` | `VARCHAR(255)` | `NOT NULL` | Document title |
| `url` | `VARCHAR(512)` | `NOT NULL` | Official source URL |
| `publication_date`| `VARCHAR(32)` | `NOT NULL` | Official release date |
| `document_version`| `VARCHAR(64)` | `NOT NULL` | Version identifier (e.g. `IRC:82-2023`) |
| `document_status` | `VARCHAR(32)` | `NOT NULL, INDEX` | `CURRENT`, `DRAFT`, `SUPERSEDED` |
| `applicable_category`| `VARCHAR(64)`| `NOT NULL, INDEX` | Applicable civic issue category |
| `file_hash` | `VARCHAR(64)` | `NOT NULL, INDEX` | SHA-256 integrity hash of document text |
| `raw_text` | `TEXT` | `NOT NULL` | Cleaned statutory text |
| `summary` | `TEXT` | `NOT NULL` | Executive summary of guidelines |
| `sections_json` | `TEXT` | `NOT NULL` | JSON array of indexed statutory clauses |
| `is_approved` | `BOOLEAN` | `NOT NULL, DEFAULT 1`| Administrator approval flag |

### Table 8: `routing_configs`
| Column Name | SQLite Data Type | Constraints | Description |
|---|---|---|---|
| `category` | `VARCHAR(64)` | `PRIMARY KEY` | Civic issue category name |
| `department` | `VARCHAR(128)` | `NOT NULL` | Assigned municipal department |
| `code` | `VARCHAR(64)` | `NOT NULL` | Department code (e.g. `MCGM-ROADS`) |
| `config_json` | `TEXT` | `NOT NULL` | Serialized SLA actions by priority level |
| `updated_at` | `DATETIME` | `NOT NULL` | Timestamp |

### Table 9: `verification_history` (Backend Audit Trail)
| Column Name | SQLite Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | Verification event ID |
| `issue_id` | `VARCHAR(64)` | `NOT NULL, INDEX` | Issue ID |
| `inspector_id` | `VARCHAR(64)` | `NOT NULL` | Authenticated inspector ID |
| `status` | `VARCHAR(64)` | `NOT NULL` | Verification verdict (`LIKELY RESOLVED`) |
| `confidence` | `FLOAT` | `NOT NULL` | Confidence metric |
| `verification_method`| `VARCHAR(128)`| `NOT NULL` | Method (`yolo_before_after_comparison`) |
| `scene_comparable`| `BOOLEAN` | `NOT NULL` | SSIM scene comparability flag |
| `data_json` | `TEXT` | `NOT NULL` | Detailed SSIM/HSV/YOLO metrics payload |
| `created_at` | `DATETIME` | `NOT NULL` | Event timestamp |

---

## 4. Environment Variables Reference

| Variable Name | Type | Default Value | Purpose & Production Constraint |
|---|---|---|---|
| `CIVILENS_ENV` | `string` | `development` | Operating mode (`development` or `production`). |
| `CIVILENS_PORT` | `integer`| `8000` | FastAPI HTTP port. |
| `CIVILENS_DB_PATH` | `string` | `data/civic_issues.db` | Path to persistent SQLite database. |
| `CIVILENS_PRESENTATION_MODE` | `boolean` | `false` | When `true`, disables auto-seeding for clean presentations. |
| `CIVILENS_SEED_COMPLAINTS` | `boolean` | `true` | Seeds baseline issues on startup if DB is empty. |
| `CIVILENS_UPLOAD_DIR` | `string` | `uploads` | Image upload directory. |
| `MAX_UPLOAD_SIZE_MB` | `integer`| `10` | Maximum allowed image upload size. |
| `CIVILENS_ALLOWED_ORIGINS` | `string` | `http://localhost:5173,...` | Allowed CORS origins (wildcards with credentials forbidden). |
| `CIVILENS_AUTH_SECRET_KEY` | `string` | `dev-insecure-secret...` | HMAC-SHA256 signing secret for access tokens. |
| `CIVILENS_ALLOW_DEV_TOKENS` | `boolean` | `true` | Permits demo tokens in development. **Must be false in prod.** |
| `CIVILENS_GEO_MIN_LAT` | `float` | `18.85` | Southern latitude boundary (Mumbai Region). |
| `CIVILENS_GEO_MAX_LAT` | `float` | `19.33` | Northern latitude boundary (Mumbai Region). |
| `CIVILENS_GEO_MIN_LNG` | `float` | `72.75` | Western longitude boundary (Mumbai Region). |
| `CIVILENS_GEO_MAX_LNG` | `float` | `73.18` | Eastern longitude boundary (Navi Mumbai Region). |
| `ENABLE_YOLO_INFERENCE` | `boolean` | `true` | Toggles PyTorch deep learning inference. |
| `YOLO_MODEL_PATH` | `string` | `models/yolov8s_rdd2022.pt` | Path to local road damage model checkpoint. |
| `WASTE_MODEL_PATH` | `string` | `models/taco_yolo11s.pt` | Path to local waste model checkpoint. |
| `YOLO_CONFIDENCE_THRESHOLD` | `float` | `0.15` | Operating confidence threshold for road detector. |
| `WASTE_CONFIDENCE_THRESHOLD` | `float` | `0.45` | Operating confidence threshold for waste detector. |
| `YOLO_DEVICE` | `string` | `cpu` | PyTorch compute device (`cpu`, `cuda`, `mps`). |
| `ROBOFLOW_API_KEY` | `string` | `[MASKED]` | Private serverless API key for Roboflow inference. |
| `ROBOFLOW_API_URL` | `string` | `https://serverless.roboflow.com` | Base endpoint for hosted model execution. |
| `ROBOFLOW_POTHOLE_MODEL_ID` | `string` | `potholes-krmk8/2` | Hosted candidate pothole model ID (YOLO26). |
| `ROBOFLOW_GARBAGE_MODEL_ID` | `string` | `garbage_detection-wvzwv-n8vsv/1` | Hosted candidate garbage model ID (RF-DETR Nano). |
| `ROBOFLOW_CACHE_ENABLED` | `boolean` | `true` | Toggles persistent SHA-256 disk caching. |
| `ROBOFLOW_TIMEOUT_SEC` | `float` | `15.0` | Network timeout for external cloud inference calls. |

