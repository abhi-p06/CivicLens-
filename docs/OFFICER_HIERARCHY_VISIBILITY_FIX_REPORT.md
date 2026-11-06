# CIVILENS — Municipal Officer Hierarchy Visibility & RBAC Enforcement Report
**Author:** Google Antigravity Advanced Agentic Engineering Team  
**Date:** November 2026  
**Scope:** Resolving Officer Tree Visibility across Mumbai (BMC) and Navi Mumbai (NMMC) while Strictly Enforcing Jurisdiction-Based Mutation RBAC  
**Status:** ✅ Complete, Fully Verified & Production Ready  

---

## 1. Executive Summary

In previous iterations, when logged in as a **Municipal Officer (Inspector)**, the **Ward Hierarchy & Allocation** page displayed only Mumbai (BMC), completely omitting Navi Mumbai (NMMC). In contrast, central administrators saw the complete metropolitan hierarchy across both municipal authorities:
- **Mumbai $\rightarrow$ BMC $\rightarrow$ 7 Administrative Zones $\rightarrow$ 24 Administrative Wards $\rightarrow$ Sub-Wards $\rightarrow$ Localities**
- **Navi Mumbai $\rightarrow$ NMMC $\rightarrow$ 2 Administrative Zones $\rightarrow$ 8 Administrative Ward Offices $\rightarrow$ Sub-Wards $\rightarrow$ Localities**

This task resolved the root cause of the missing Navi Mumbai branch, unified the underlying tree ingestion across roles, and achieved strict separation between **read visibility** (metropolitan situational awareness across Greater Mumbai and Navi Mumbai) and **operational write authority** (strictly restricted to the officer's assigned administrative jurisdiction).

---

## 2. Root Cause Analysis

### A. Backend Pruning of Non-Assigned Authorities
In `app/api/routes.py` (`get_hierarchy_tree`), the endpoint previously intercepted requests from users with `role == "inspector"` and explicitly hardcoded:
```python
# PREVIOUS BEHAVIOR (ROOT CAUSE):
if current_user and current_user.role == "inspector":
    oj = demo_store.get_officer_jurisdiction(current_user.user_id)
    if oj and oj.get("ward_code"):
        authority = "BMC"  # <--- HARDCODED BMC ONLY
        ward = oj["ward_code"]
```
Because `authority="BMC"` was supplied to `demo_store.get_hierarchy_tree()`, the database query pruned all records belonging to Navi Mumbai (`AUTH-NMMC`), returning exclusively BMC and excluding NMMC entirely.

### B. Confusing Visibility with Permission
The architecture conflated *jurisdiction visibility* with *operational authority*. Because municipal officers should only manage complaints in their assigned ward (e.g. `N-Ward` or `Belapur`), the API mistakenly restricted the entire geographical reference tree. In municipal governance, field supervisors require metropolitan situational awareness (seeing neighboring wards, boundary intersections, and overall city progress) without possessing operational mutation rights in external wards.

---

## 3. Architecture & Implementation Changes

### 3.1 Backend: Unified Tree API with Granular Mutation RBAC

1. **Unified Hierarchy Tree (`GET /api/v1/hierarchy/tree`)**:
   - Both **Administrator** and **Municipal Officer (Inspector)** accounts now receive the complete hierarchy covering:
     - 2 Cities: Mumbai & Navi Mumbai
     - 2 Authorities: BMC (24 wards) & NMMC (8 ward offices)
     - 9 Zones & 32 Administrative Wards
   - Citizens remain strictly barred (`HTTP 403 Forbidden`).

2. **Dedicated Jurisdiction Discovery (`GET /api/v1/hierarchy/jurisdiction/me`)**:
   - Returns the authenticated officer's exact operational assignment (`authority_id`, `ward_code`, `sub_ward_id`, `jurisdiction_level`).
   - For `INSP-MUMBAI-01`: `AUTH-BMC`, `N-Ward`, `SUB-BMC-N-01`.
   - For `INSP-NMMC-01`: `AUTH-NMMC`, `NMMC-Belapur`, `SUB-NMMC-B-01`.

3. **Multi-Authority Officer Seeding (`app/db/repository.py` & `security.py`)**:
   - Seeded both BMC Inspector (`INSP-MUMBAI-01`, `inspector@civilens.org`) and NMMC Inspector (`INSP-NMMC-01`, `inspector.nmmc@civilens.org`).
   - Added corresponding demo tokens and JWT issuance for both jurisdictions.

4. **Hardened Backend Mutation RBAC**:
   - **Task Assignment (`POST /api/v1/issues/{id}/assign`)**: `check_inspector_jurisdiction()` enforces that an officer can only assign crews to complaints inside their authorized ward. Cross-ward and cross-authority operations return `HTTP 403 Forbidden`.
   - **Jurisdiction Correction (`PATCH /api/v1/issues/{id}/jurisdiction`)**: Inspectors cannot transfer complaints across authorities (e.g. BMC to NMMC).
   - **Administrative Mutations (`POST/PATCH/DELETE /api/v1/hierarchy/sub-wards`, `/api/v1/admin/teams`, `/api/v1/hierarchy/supervisors/assign`)**: Gated exclusively to `current_user = Depends(require_admin)` returning `HTTP 403 Forbidden` for officers.

---

### 3.2 Frontend: Aurora Indigo Tree Presentation & Operational Scope Gating

1. **Dynamic Node Permission Tagging**:
   - When loading the tree in `WardHierarchyAllocationView.tsx`, the client fetches `api.hierarchy.getMyJurisdiction()` and tags every tree node recursively:
     - `is_authorized`: `true` if node matches the officer's ward/sub-ward.
     - `is_readonly`: `true` if node is outside their authorized scope.
     - `has_authorized_descendant`: `true` for ancestor zones/authorities containing the officer's ward.
   - For Administrators: `is_authorized = true` and `is_readonly = false` for all nodes.

2. **Automated Ward Focus on Load**:
   - When an Officer opens the view, the application automatically locates and selects their assigned ward (e.g. `N-Ward` or `NMMC-Belapur`) in the details panel, expanding all necessary parent nodes.

3. **Visual Distinction in Tree Navigation**:
   - **Authorized Working Area**: Marked with emerald shield badge (`Authorized Working Area`), emerald border, and highlighted active background.
   - **Read-Only Jurisdiction**: Marked with slate lock badge (`Read-Only`), allowing instant inspection without accidental editing.
   - **Active Zone Containers**: Marked with violet badge (`Contains Active Ward`).

4. **Inspector Notice & Quick Jump Header**:
   - Replaced old generic notice with an Aurora Indigo status strip:
     > **Metropolitan Administrative Tree (Mumbai BMC + Navi Mumbai NMMC)**  
     > Full visibility is enabled across all 24 BMC wards and 8 NMMC ward offices. Operational actions are active strictly within your authorized working jurisdiction (e.g. `N-Ward`), while external entities remain read-only.
   - Includes a quick-jump shortcut: `Go to My Ward ({ward_code})`.

5. **Details Panel Permission Guard**:
   - **Authorized Node Selected**: Displays green `Authorized Working Jurisdiction (ACTIVE SCOPE)` banner confirming active dispatch rights.
   - **Unauthorized Node Selected**: Displays neutral `Read-Only Jurisdiction (Outside Authorized Scope)` banner clearly explaining that metropolitan situational awareness is enabled, but mutations are locked.
   - Operational buttons (`Manage Crews`, `Assign Lead`, `New Sub-Ward`, `Edit Sub-Ward`) are hidden for non-admins and replaced with read-only indicators.

6. **Cross-Authority Tree Search**:
   - The tree search dynamically filters and auto-expands matching entities across both Mumbai and Navi Mumbai (e.g., searching "Belapur" expands South Navi Mumbai; searching "N-Ward" expands Mumbai Zone VI).

---

## 4. Verification & Testing

### 4.1 Pytest Automated RBAC Suite (`tests/test_hierarchy_tree_rbac.py`)
```
tests/test_hierarchy_tree_rbac.py ........ [100%]
============================== 8 passed in 1.71s ==============================
```
- ✅ `test_hierarchy_tree_unauthenticated_public`: Tree contains BMC & NMMC.
- ✅ `test_hierarchy_tree_admin_role`: Admin sees BMC (24 wards) & NMMC (8 wards).
- ✅ `test_hierarchy_tree_officer_mumbai_sees_both_authorities`: BMC officer sees BMC (24 wards) & NMMC (8 wards).
- ✅ `test_hierarchy_tree_officer_nmmc_sees_both_authorities`: NMMC officer sees BMC (24 wards) & NMMC (8 wards).
- ✅ `test_hierarchy_tree_citizen_forbidden`: Citizen blocked with 403 Forbidden.
- ✅ `test_hierarchy_tree_filter_by_ward`: Query param filtering behaves deterministically.
- ✅ `test_officer_jurisdiction_me_endpoint`: Returns assigned operational ward.
- ✅ `test_backend_rbac_officer_cannot_mutate_unauthorized_jurisdictions`:
  - BMC officer blocked from assigning tasks on NMMC complaints (403).
  - NMMC officer blocked from assigning tasks on BMC complaints (403).
  - Officer blocked from moving complaint to foreign authority (403).
  - Officer blocked from creating sub-wards, teams, or supervisor assignments (403).

### 4.2 Frontend Production Build
```
> frontend@0.0.0 build
> tsc -b && vite build
✓ 2423 modules transformed.
dist/index.html                     0.83 kB
dist/assets/index-BF57N-aG.css    112.06 kB
dist/assets/index-DXfMv24O.js   1,187.87 kB
✓ built in 366ms (0 TypeScript / Vite errors)
```

### 4.3 Headless Browser Visual Evidence (1600×900 & 1280×800)

| Screenshot Artifact | Description |
|---|---|
| `officer_hierarchy_admin_1600x900.png` | Admin view displaying 2 Cities, 2 Authorities, full BMC + NMMC tree with administrative configuration actions. |
| `officer_hierarchy_bmc_officer_1600x900.png` | BMC Officer (`INSP-MUMBAI-01`) view displaying BOTH Mumbai and Navi Mumbai, with N-Ward auto-selected and highlighted as Authorized Working Area. |
| `officer_hierarchy_bmc_officer_1280x800.png` | BMC Officer view at responsive 1280×800 viewport adhering to Aurora Indigo layout standards. |
| `officer_hierarchy_search_belapur_nmmc.png` | Cross-authority search query "Belapur" expanding Navi Mumbai NMMC nodes smoothly for a BMC officer. |
| `officer_hierarchy_bmc_viewing_unauthorized_belapur.png` | BMC Officer selecting Belapur (NMMC): Details panel displays "Read-Only Jurisdiction (Outside Authorized Scope)" with locked controls. |
| `officer_hierarchy_nmmc_officer_1600x900.png` | NMMC Officer (`INSP-NMMC-01`) view displaying BOTH Mumbai and Navi Mumbai, with Belapur auto-selected as Authorized Working Area. |

---

## 5. Conclusion
The Municipal Officer Ward Hierarchy is now 100% consistent with the Administrator view across both Greater Mumbai (BMC) and Navi Mumbai (NMMC). Regional visibility has been decoupled from operational mutations, ensuring municipal officers have complete situational awareness across both municipal corporations while strictly safeguarding jurisdiction boundaries on both the frontend and the FastAPI backend.

