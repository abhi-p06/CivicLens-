# CIVILENS — Hierarchy Tree Repair & Role-Based Scoping Report

## 1. Executive Summary

This report documents the diagnosis, root-cause analysis, engineering remediation, and visual verification for the **Ward Hierarchy & Crew Allocation** module in CIVILENS.

### Initial Observed Failures
1. The page displayed `"2 Cities • 0 Authorities"`.
2. The City & Administrative Tree was empty.
3. The UI displayed `"No administrative entities match \"\""` even when the search field was blank.
4. The jurisdiction details panel remained unpopulated and never loaded any entity.
5. Role-based scoping was missing on the hierarchy endpoint.

---

## 2. Root Cause Analysis

### Root Cause 1: SQLite Schema Column Drift (`HTTP 500`)
- **Location**: `app/db/models.py` vs `app/db/database.py`
- **Mechanism**: `IssueRecord` defined `supervisor_name = Column(String(128), nullable=True)`. However, `issue_cols` in `init_db()` in `app/db/database.py` omitted `supervisor_name` from its migration list.
- **Impact**: Any join or query against `IssueRecord` during `demo_store.get_hierarchy_tree()` crashed with:
  `sqlite3.OperationalError: no such column: issues.supervisor_name`, returning `HTTP 500 Internal Server Error`.

### Root Cause 2: Missing Properties on Backend Tree Nodes (`TypeError`)
- **Location**: `app/db/repository.py` lines 2637–2743
- **Mechanism**: The backend dictionary builders for `auth_node`, `zone_node`, `ward_node`, `sub_node`, and `loc_node` provided `id`, `label`, `code`, and `type`, but completely omitted `name` and `level`.
- **Impact**: In `WardHierarchyAllocationView.tsx`, the search filter executed `node.name.toLowerCase()`. When `node.name` was `undefined`, JavaScript threw an unhandled TypeError, terminating tree rendering.

### Root Cause 3: Frontend Error Swallowing & Hardcoded Counter
- **Location**: `frontend/src/components/views/WardHierarchyAllocationView.tsx`
- **Mechanism**:
  1. When `loadTree()` threw an error, `setError` was called, but the JSX rendering block checked only `loading ? ... : filteredTree.length === 0 ? "No administrative entities match \"\""`. It completely ignored the `error` state.
  2. The city root containers (`Mumbai` and `Navi Mumbai`) were hardcoded even if the backend returned 0 authorities or failed, causing the counter to show `"2 Cities • 0 Authorities"`.

### Root Cause 4: Missing RBAC Scoping & Empty-Branch Pruning
- **Location**: `app/api/routes.py` and `app/db/repository.py`
- **Mechanism**: `GET /api/v1/hierarchy/tree` did not inject `current_user`. Citizens were not barred with HTTP 403, and Municipal Officers (Inspectors) were not scoped to their assigned jurisdiction (`N-Ward`). Furthermore, filtering by `ward_code` failed to prune empty zones and authorities.

---

## 3. Engineering Remediation

### 3.1 Database Migration & Integrity
- **Updated `app/db/database.py`**: Added `("supervisor_name", "VARCHAR(128)")` to the idempotent column upgrade loop in `init_db()`.
- Verified that `data/civic_issues.db` contains 2 authorities (BMC & NMMC), 9 zones, 32 wards (24 BMC + 8 NMMC), 14 sub-wards, 14 localities, and 35 civic complaints.

### 3.2 Backend Hierarchy Tree Enhancement (`app/db/repository.py`)
- Attached required contract fields to every node level:
  - `name`: Human-readable name matching statutory records.
  - `level`: Explicit hierarchy rank (`authority`, `zone`, `ward`, `sub_ward`, `locality`).
  - `supervisor` / `supervisor_name`: Assigned supervisor for sub-wards and wards.
  - `department`: Responsible department (e.g., Solid Waste, Roads & Potholes).
  - `office_address`: Statutory municipal office address for administrative wards.
- **Intelligent Branch Pruning**:
  - When filtering by `ward_code` or `sub_ward_id`, zones with 0 matching wards are excluded.
  - Authorities with 0 matching zones are excluded.
  - Prevents empty ghost branches when scoping to a specific ward.

### 3.3 Strict RBAC Jurisdiction Enforcement (`app/api/routes.py`)
- Injected `current_user: Optional[AuthenticatedUser] = Depends(get_current_user)` into `GET /api/v1/hierarchy/tree`:
  - **Citizen**: Immediately rejected with `HTTP 403 Forbidden` (`"Citizens are not authorized to access administrative hierarchy management."`).
  - **Municipal Officer (Inspector)**: Queries `demo_store.get_officer_jurisdiction(current_user.user_id)`. If unassigned, returns `[]`. If assigned (e.g. `INSP-MUMBAI-01` $\rightarrow$ `N-Ward`), scopes strictly to `authority_code="BMC"`, `ward_code="N-Ward"`.
  - **Administrator / Unauthenticated Legacy**: Returns the complete Mumbai (BMC) and Navi Mumbai (NMMC) hierarchy (32 administrative units).

### 3.4 Frontend Tree & State Resilience (`WardHierarchyAllocationView.tsx` & `api.ts`)
- **Authenticated Headers**: Updated `api.hierarchy.getTree()` in `frontend/src/services/api.ts` to pass `Authorization: Bearer <token>`.
- **Dynamic City Containers**: Only render City roots (`Mumbai`, `Navi Mumbai`) if they contain child authorities.
- **Responsive Header Counter**: Displays `{treeData.length} Cities • {rawAuthorities.length} Authorities`.
- **Explicit Error & Empty States**:
  - Displays red warning banner with `"Retry Loading"` button on API failure.
  - Displays amber jurisdiction notice if an inspector has no assigned jurisdiction: `"No administrative jurisdiction has been assigned to this account. Please contact an administrator."`
- **Recursive Search Filtering**:
  - Safe null-coalescing on `(node.name || node.label || '')`.
  - If a parent node matches (`BMC`, `N-Ward`), all its child sub-wards and beats remain visible.
  - If a child node matches, ancestors are preserved so the navigational path remains intact.
  - Automatically expands matching branches on user keystroke.
- **Default Selection**: Automatically selects the first available ward/authority on load to populate the details panel, KPI cards, and preview Leaflet GIS map without requiring manual user clicking.

---

## 4. Verification & Testing

### 4.1 Automated Backend Pytest Suite
Created `tests/test_hierarchy_tree_rbac.py` covering:
1. `test_hierarchy_tree_unauthenticated_public`: 2 authorities, all 9 zones, all 32 wards.
2. `test_hierarchy_tree_admin_role`: Admin sees BMC (24 wards) + NMMC (8 wards).
3. `test_hierarchy_tree_inspector_with_jurisdiction`: Officer `INSP-MUMBAI-01` sees ONLY BMC $\rightarrow$ Zone VI $\rightarrow$ N-Ward (0 NMMC, 0 other BMC wards).
4. `test_hierarchy_tree_inspector_without_jurisdiction`: Unassigned officer receives `[]`.
5. `test_hierarchy_tree_citizen_forbidden`: Citizen returns `HTTP 403 Forbidden`.
6. `test_hierarchy_tree_filter_by_ward`: Pruning leaves only matching ward branch.

**Test Run Outcome**:
- `tests/test_hierarchy_tree_rbac.py`: **6 passed**
- Full test suite: **296 passed, 0 failures in 35.59s**.

### 4.2 Frontend Build
- Executed `npm run build` in `frontend/`:
  `✓ built in 358ms` with **0 TypeScript and Vite compilation errors**.

### 4.3 Visual CDP Browser Automation Validation
Captured high-resolution screenshots:
1. `hierarchy_fix_admin_1600x900.png`: Full administrator tree at 1600x900 showing `"2 Cities • 2 Authorities"`, expanded BMC Zone I, E-Ward selected, Leaflet preview map rendering E-Ward polygon boundary in violet.
2. `hierarchy_fix_admin_1280x800.png`: Responsive validation at 1280x800 confirming sidebar and 55%/45% layout balance.
3. `hierarchy_fix_search_nward.png`: Search query `"N-Ward"` showing auto-expanded Mumbai $\rightarrow$ Zone VI $\rightarrow$ N-Ward with 3 CIVILENS operational sub-wards and locality beats.
4. `hierarchy_fix_inspector_scoped.png`: Municipal Officer view logged in as Inspector Abhinay showing `"1 City • 1 Authority"`, officer jurisdiction alert banner, and strict scoping to Zone VI N-Ward.

