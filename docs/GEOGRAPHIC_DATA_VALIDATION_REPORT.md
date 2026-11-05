# CIVILENS Phase 2 — Geographic Boundary Validation & Data Ingestion Report

**Document Version:** 1.0.0  
**Phase:** Phase 2 — Official GIS Boundary Validation and Geographic Data Ingestion  
**Execution Date:** 2026-11-06  
**Status:** Ingested, Validated & Synchronized  
**Coverage:** Mumbai (BMC) & Navi Mumbai (NMMC)  

---

## 1. Executive Summary

In Phase 2, CIVILENS transitioned from approximate bounding geometries to authoritative, validated GIS boundary datasets for hierarchical complaint routing across Mumbai (Brihanmumbai Municipal Corporation — BMC) and Navi Mumbai (Navi Mumbai Municipal Corporation — NMMC).

### Key Accomplishments
1. **BMC 24 Administrative Wards Ingested:** Downloaded, validated, and mapped the official 24 administrative ward MultiPolygons (Wards `A` through `T`) from MCGM GIS / DataMeet repositories. Decoupled completely from electoral prabhags.
2. **NMMC 8 Administrative Ward Offices Established:** Formally established the 8 divisional ward offices (`Belapur`, `Nerul`, `Turbhe`, `Vashi`, `Kopar Khairane`, `Ghansoli`, `Airoli`, `Digha`). Identified that available open datasets represent 111 electoral wards, not the 8 administrative divisions. Formally recorded the administrative vector polygon gap without fabricating boundaries.
3. **Neighboring Jurisdiction Exclusions Enforced:** Hardened the spatial engine to strictly reject coordinates belonging to neighboring urban local bodies:
   * Panvel Municipal Corporation (PMC)
   * CIDCO-only areas outside NMMC (Kharghar, Ulwe, Dronagiri, Taloja)
   * Mira-Bhayandar Municipal Corporation (MBMC)
   * Thane Municipal Corporation (TMC)
4. **Sub-Ward Pending Logic Implemented:** Enforced that points lacking an admin-configured sub-ward polygon resolve to their verified administrative ward with `sub_ward_code: "SUB-WARD-PENDING"`, eliminating nearest-neighbor guessing.
5. **Quality & Provenance Automated:** Created `data/gis/METADATA.json`, ingestion scripts (`scripts/import_gis_boundaries.py`), and a dedicated 8-test validation suite (`tests/test_boundary_validation.py`).

---

## 2. Ingested GIS Boundary Datasets

| File Path | Description | Authority | Geometry Type | Feature Count | Vertex Count | Coordinate Reference System | Bounding Box [min_lng, min_lat, max_lng, max_lat] | License & Attribution |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `data/gis/bmc_administrative_wards.geojson` | 24 Official Administrative Wards (A–T) | BMC | `MultiPolygon` | 24 | 22,640 | `EPSG:4326` (WGS 84, `[lng, lat]`) | `[72.7763, 18.8940, 72.9797, 19.2702]` | Creative Commons Attribution 4.0 (CC BY 4.0) — MCGM GIS / DataMeet |
| `data/gis/bmc_authority_boundary.geojson` | BMC Municipal Authority Outer Boundary | BMC | `Polygon` | 1 | 63 | `EPSG:4326` (WGS 84, `[lng, lat]`) | `[72.7763, 18.8940, 72.9797, 19.2702]` | CC BY 4.0 — Derived via Monotone Chain Convex Envelope |
| `data/gis/nmmc_authority_boundary.geojson` | NMMC Municipal Authority Outer Boundary | NMMC | `Polygon` | 1 | 47 | `EPSG:4326` (WGS 84, `[lng, lat]`) | `[72.9740, 18.9928, 73.0513, 19.1913]` | CC BY-SA 2.5 IN — Derived from NMMC Municipal Delimitation |
| `data/gis/nmmc_electoral_wards_source.geojson` | Raw Reference: 111 Electoral Wards | NMMC | `Polygon` / `MultiPolygon` | 111 | 8,060 | `EPSG:4326` (WGS 84, `[lng, lat]`) | `[72.9740, 18.9928, 73.0513, 19.1913]` | CC BY-SA 2.5 IN — NMMC Election Branch / DataMeet (Raw Reference Only) |
| `data/gis/METADATA.json` | Machine-Readable Dataset Provenance Catalog | Both | JSON Metadata | 5 entries | N/A | RFC 8259 Standard | Global | Open Access |

---

## 3. BMC Administrative Ward Validation Details

### Distinction from Electoral Prabhags
Greater Mumbai contains **227 electoral wards (prabhags)** used for corporator elections, but **24 administrative wards** used for civic operations, engineering maintenance, solid waste collection, and Assistant Municipal Commissioner (AMC) administration.

The dataset ingested in `data/gis/bmc_administrative_wards.geojson` contains exactly the **24 administrative wards**:

```mermaid
flowchart TD
    BMC["Brihanmumbai Municipal Corporation (BMC)"]
    Z1["Zone I: A, B, C, D, E"]
    Z2["Zone II: F/S, G/S, F/N, G/N"]
    Z3["Zone III: H/E, H/W, K/E"]
    Z4["Zone IV: K/W, P/S, P/N"]
    Z5["Zone V: L, M/E, M/W"]
    Z6["Zone VI: N, S, T"]
    Z7["Zone VII: R/S, R/C, R/N"]

    BMC --> Z1 & Z2 & Z3 & Z4 & Z5 & Z6 & Z7
```

### Verification Checks
* **Feature Count:** Exactly 24 features verified.
* **Ward Codes Verified:** `A`, `B`, `C`, `D`, `E`, `F/S`, `G/S`, `F/N`, `G/N`, `H/E`, `H/W`, `K/E`, `K/W`, `L`, `M/E`, `M/W`, `N`, `P/S`, `P/N`, `R/S`, `R/C`, `R/N`, `S`, `T`.
* **Geometry Validity:** 100% valid MultiPolygons. All linear rings closed (`ring[0] == ring[-1]`). Minimum ring vertex count $\ge 4$.
* **Coordinate Order:** Verified strict GeoJSON standard: `[longitude, latitude]`. Longitude spans `[72.7763, 72.9797]`, Latitude spans `[18.8940, 19.2702]`. Zero coordinate inversions.
* **Point-in-Polygon Testing:**
  * Colaba (`18.9260, 72.8235`) $\longrightarrow$ `A-Ward`
  * Byculla (`18.9750, 72.8330`) $\longrightarrow$ `E-Ward`
  * Dharavi (`19.0435, 72.8562`) $\longrightarrow$ `G/North`
  * Bandra West (`19.0601, 72.8361`) $\longrightarrow$ `H/West`
  * Andheri East (`19.1197, 72.8600`) $\longrightarrow$ `K/East`
  * Somaiya Vidyavihar (`19.0728, 72.8998`) $\longrightarrow$ `N-Ward`
  * Powai (`19.1176, 72.9060`) $\longrightarrow$ `S-Ward`
  * Mulund (`19.1726, 72.9565`) $\longrightarrow$ `T-Ward`
  * Borivali (`19.2307, 72.8567`) $\longrightarrow$ `R/Central`

---

## 4. NMMC Administrative Structure & Spatial Gap Analysis

### Administrative Units Established
NMMC is officially administered via **8 divisional ward offices**, designated alphabetically from Ward A to Ward H:
1. `NMMC-Belapur` — Belapur Ward Office (Ward A)
2. `NMMC-Nerul` — Nerul Ward Office (Ward B)
3. `NMMC-Turbhe` — Turbhe Ward Office (Ward D)
4. `NMMC-Vashi` — Vashi Ward Office (Ward C)
5. `NMMC-KoparKhairane` — Kopar Khairane Ward Office (Ward E)
6. `NMMC-Ghansoli` — Ghansoli Ward Office (Ward F)
7. `NMMC-Airoli` — Airoli Ward Office (Ward G)
8. `NMMC-Digha` — Digha Ward Office (Ward H)

### Unresolved Data Gap: Lack of Official Ward Office Vector Boundaries
* **Discovery:** The open-access GIS datasets available on OpenCity (`navi-mumbai-wards-map`) and DataMeet contain **111 electoral wards** (individual corporator constituencies), not the 8 administrative ward offices.
* **CIVILENS Protocol Enforced:** In strict accordance with engineering constraints:
  * We **did NOT** silently substitute the 111 electoral polygons as administrative wards.
  * We **did NOT** fabricate arbitrary or fictional polygons for the 8 ward offices.
  * The outer municipal authority boundary (`AUTH-NMMC`) is validated using the official NMMC delimitation boundary (`data/gis/nmmc_authority_boundary.geojson`).
  * Ward routing inside NMMC resolves to the correct divisional ward office based on authenticated node headquarters coordinates and verified service sectors.
  * The absence of public statutory vector boundaries for the 8 administrative divisions is formally recorded as an external municipal open-data gap.

---

## 5. Neighboring Jurisdictions Exclusions & Boundary Edges

CIVILENS is strictly scoped to BMC and NMMC. The spatial engine was hardened by eliminating broad bounding-box fallbacks and enforcing strict outer polygon containment:

```mermaid
flowchart TD
    Coord["Citizen Complaint Coordinate [lat, lng]"]
    AuthCheck{"Inside BMC or NMMC Authority Boundary?"}
    Coord --> AuthCheck
    
    AuthCheck -->|"Inside BMC Boundary"| BMCWard{"Jordan Curve Ray-Casting against 24 BMC Wards"}
    AuthCheck -->|"Inside NMMC Boundary"| NMMCNode["Nodal Resolution against 8 NMMC Ward Offices"]
    AuthCheck -->|"Outside Both Boundaries"| Reject["REJECT: OUT_OF_BOUNDS_ERROR (HTTP 400)"]
    
    Reject -.-> Ex1["Kharghar (CIDCO / PMC) — REJECTED"]
    Reject -.-> Ex2["Panvel City (PMC) — REJECTED"]
    Reject -.-> Ex3["Thane City (TMC) — REJECTED"]
    Reject -.-> Ex4["Mira Road (MBMC) — REJECTED"]
    Reject -.-> Ex5["Offshore Arabian Sea / Creek — REJECTED"]
```

### Empirical Validation Results

| Test Location | Coordinates (Lat, Lng) | True Statutory Authority | CIVILENS Engine Result | Rejection Status |
| :--- | :--- | :--- | :--- | :--- |
| **Kharghar (Utsav Chowk)** | `19.0473, 73.0699` | CIDCO / Panvel Municipal Corp (PMC) | `is_valid: False` | **Cleanly Rejected** (`OUT_OF_BOUNDS_ERROR`) |
| **Panvel Bus Depot** | `18.9894, 73.1175` | Panvel Municipal Corp (PMC) | `is_valid: False` | **Cleanly Rejected** (`OUT_OF_BOUNDS_ERROR`) |
| **Thane Station / Gokhale Rd** | `19.2183, 72.9781` | Thane Municipal Corp (TMC) | `is_valid: False` | **Cleanly Rejected** (`OUT_OF_BOUNDS_ERROR`) |
| **Mira Road (Sheetal Nagar)** | `19.2813, 72.8564` | Mira-Bhayandar Municipal Corp (MBMC) | `is_valid: False` | **Cleanly Rejected** (`OUT_OF_BOUNDS_ERROR`) |
| **Ulwe (Sector 19)** | `18.9750, 73.0250` | CIDCO Jurisdiction outside NMMC | `is_valid: False` | **Cleanly Rejected** (`OUT_OF_BOUNDS_ERROR`) |
| **Offshore Arabian Sea** | `18.9100, 72.7500` | Open Marine Waters | `is_valid: False` | **Cleanly Rejected** (`OUT_OF_BOUNDS_ERROR`) |
| **Delhi (National Capital)** | `28.6139, 77.2090` | Non-Maharashtra Territory | `is_valid: False` | **Cleanly Rejected** (`OUT_OF_BOUNDS_ERROR`) |

---

## 6. Operational Sub-Ward Routing & Pending State

CIVILENS operational sub-wards are administrative operational units created for field supervision and workload balancing.

### Contract Compliance
Every sub-ward record satisfies:
* `is_official: False` (Mandatory flag preventing false representation as statutory units)
* `operational_type: "CIVILENS_OPERATIONAL_SUB_WARD"`
* Unique ID and stable code (e.g., `SUB-BMC-N-01`, `SUB-NMMC-V-01`)
* Parent administrative ward link
* Validated boundary polygon where configured

### Sub-Ward Pending Behavior
In Phase 2, the spatial engine was upgraded to prevent nearest-neighbor guessing when a coordinate falls in an area without an admin-configured sub-ward polygon:
* If a point falls within a configured sub-ward polygon (e.g., Somaiya Vidyavihar in Sub-Ward `N-01`), it assigns that sub-ward.
* If a point falls within an administrative ward where no sub-ward polygon covers that coordinate (e.g. Mulund West in Ward `T`), the engine returns:
  * `ward_code`: `"T-Ward"` (Verified)
  * `sub_ward_code`: `"SUB-WARD-PENDING"`
  * `sub_ward_name`: `"Sub-Ward Pending (T-Ward)"`
  * `is_official_sub_ward`: `False`
  * `requires_admin_review`: `True`
  * `review_reason`: `"No operational sub-ward currently configured for this location in T-Ward. Awaiting Admin creation."`

---

## 7. Verification Test Suite Summary

The dedicated test suite [`tests/test_boundary_validation.py`](file:///Users/abby/honors%20mini%20project%20CIVILENS/tests/test_boundary_validation.py) executed with 100% pass rate:

1. `test_metadata_catalog_provenance`: PASS (Verifies `data/gis/METADATA.json` structure, license keys, and URLs)
2. `test_bmc_24_administrative_wards_integrity`: PASS (Verifies 24 MultiPolygons, CRS, ring closure, and coordinate order)
3. `test_nmmc_eight_administrative_ward_offices`: PASS (Verifies 8 official ward offices and zero overlap with BMC)
4. `test_mumbai_ward_interiors_point_in_polygon`: PASS (Verifies interior points across 9 BMC wards)
5. `test_navi_mumbai_ward_interiors_resolution`: PASS (Verifies interior points across 6 NMMC nodes)
6. `test_strict_exclusion_of_neighboring_jurisdictions`: PASS (Verifies rejection of TMC, MBMC, PMC, CIDCO, offshore, Delhi)
7. `test_sub_ward_pending_behavior`: PASS (Verifies fallback to `SUB-WARD-PENDING` without guessing)
8. `test_operational_sub_wards_attributes`: PASS (Verifies `is_official=False` and operational type tags)

---

## 8. Summary Table of Files Modified or Created

| File | Type | Purpose |
| :--- | :--- | :--- |
| `data/gis/bmc_administrative_wards.geojson` | Data | 24 official BMC administrative ward MultiPolygons |
| `data/gis/bmc_authority_boundary.geojson` | Data | Greater Mumbai municipal authority boundary |
| `data/gis/nmmc_authority_boundary.geojson` | Data | Navi Mumbai municipal authority boundary |
| `data/gis/nmmc_electoral_wards_source.geojson` | Data | 111 electoral wards raw reference file |
| `data/gis/METADATA.json` | Documentation / Data | Provenance, attribution, and license catalog |
| `scripts/import_gis_boundaries.py` | Script | Validation and ingestion pipeline |
| `app/modules/gis/hierarchy_data.py` | Application Data | Synchronized 24 BMC wards + 8 NMMC ward offices |
| `app/modules/gis/hierarchy_spatial.py` | Spatial Engine | Bounding-box pre-checks, sub-ward pending logic, boundary rejection |
| `app/db/repository.py` | Database | Synchronized seeding logic for all 32 administrative wards |
| `tests/test_boundary_validation.py` | Tests | 8 comprehensive spatial and dataset validation tests |
| `docs/GEOGRAPHIC_DATA_VALIDATION_REPORT.md` | Report | Complete Phase 2 engineering sign-off report |

