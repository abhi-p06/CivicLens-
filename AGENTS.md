# AGENTS.md — CIVILENS DESIGN CONSTRAINTS & DEVELOPMENT GUIDELINES

This document establishes the **mandatory rules and architectural boundaries** for all AI coding agents working on the CIVILENS repository.

---

## 1. Core Mandate: Adherence to DESIGN_SYSTEM.md

All frontend work must strictly implement and maintain the visual language defined in [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md).
- **Product Identity**: CIVILENS (Civic Infrastructure Intelligence).
- **Design Philosophy**: **AURORA INDIGO** — A clean, high-trust civic operations workspace combining midnight-indigo navigational structure, pure-white cards with thin neutral borders, purposeful violet primary actions with restrained gradients, and a tactical GIS map workspace.
- **Do NOT invent alternate designs**. Do NOT revert the application to an all-black terminal, cybersecurity SOC console, or neon cyberpunk dashboard.

---

## 2. Fixed Design Tokens (Never Deviate)

Agents must use these exact CSS variables and semantic tokens:
- `--app-bg`: `#F6F7FC` (Main application workspace canvas — **MUST BE LIGHT**)
- `--surface`: `#FFFFFF` (Primary cards, panels, modals — **PURE WHITE**)
- `--surface-muted`: `#F0F2F9` (Secondary metrics strip and subtle containers)
- `--sidebar-bg`: `#13152E` (Left sidebar navigation — **MIDNIGHT INDIGO**)
- `--sidebar-hover`: `#212348` (Sidebar item hover)
- `--sidebar-active`: `linear-gradient(100deg, #3A326F, #29264F)` (Sidebar active gradient)
- `--text-primary`: `#11162A` (Headings, active labels, body text)
- `--text-secondary`: `#65708B` (Muted metadata, subtitles, timestamps)
- `--border`: `#E4E7F1` (Structural card borders, dividers)
- `--accent`: `#6457E8` (Primary violet action and focus indicator)
- `--accent-hover`: `#5145CF` (Action hover state)
- `--accent-secondary`: `#8B5CF6` (Secondary accent / sidebar active indicator)
- `--critical`: `#EF4444`
- `--high`: `#F97316`
- `--medium`: `#EAB308`
- `--low`: `#3B82F6`
- `--success`: `#10B981`
- **GIS Map Base**: `#10162A` (The GIS workspace uses its own dark midnight canvas with restrained geographic details).

---

## 3. Mandatory Desktop Layout Rules (Reference: 1600 × 900)

1. **Sidebar Dimensions & State**:
   - Expanded width: **256px**.
   - Collapsed width: **72px**.
   - **Default State**: MUST default to **EXPANDED** on desktop viewports. Full labels must be immediately visible without requiring manual user toggling.
2. **Top Application Bar**:
   - Fixed height: **56px** (`h-14`).
   - Background: Pure white (`#FFFFFF`) with bottom border (`#E4E7F1`).
   - Breadcrumb navigation on left, search trigger in center, ward/demo controls on right.
   - **NO duplicate headings**: The main page title must NOT be repeated in the top bar.
3. **Main Content Stage**:
   - Workspace padding: **24px** (`p-6`).
   - Single row of **four equal-width KPI cards** with **34–38px** `CountUp` numbers.
   - Quiet **secondary metrics strip** below KPI cards.
   - Two-column grid split:
     - **Left Column (55%)**: Tactical Spatial GIS Map (Dark canvas, layer controls, expand button).
     - **Right Column (45%)**: Priority Incident Queue (Featured Aceternity `CardSpotlight` for top critical issue, scrollable feed for subsequent issues with full descriptions readable).
   - Card spacing: **14px – 18px** gap.

---

## 4. Component Usage & Library Contracts

- **shadcn/ui**:
  - Always use actual shadcn/ui primitives: `Sidebar`, `Command`, `Dialog`, `Tooltip`, `DropdownMenu`, `Tabs`.
  - Stored in `frontend/src/components/ui/`.
- **React Bits**:
  - `CountUp`: Used for numerical KPI counters and percentage reveals.
  - `AnimatedContent`: Used for entry choreography of sections.
  - `FadeContent`: Used for unblur/opacity transitions of sequential AI results.
  - Stored in `frontend/src/components/reactbits/`.
- **Aceternity UI**:
  - `CardSpotlight`: Used **selectively** on the #1 critical risk focus element in the incident queue. Do not spam spotlights across every card.
  - Stored in `frontend/src/components/aceternity/`.
- **Motion for React (`framer-motion`)**:
  - Use real motion props and `layoutId` for the active navigation indicator, drawer slide-in, priority gauge progress, and pipeline reveals.
  - Always respect `useCivicMotion()` / `prefers-reduced-motion`.

---

## 5. Architectural Separation & Backend Integrity

1. **Backend & Models are FROZEN**:
   - Do NOT redesign, replace, or break the Python/FastAPI backend (`app/main.py`, `app/api/routes.py`, `app/core/pipeline.py`).
   - ML models (scikit-learn TF-IDF classifier, YOLOv8 vision inference, DBSCAN spatial clustering, deterministic priority calculations, SSIM resolution verification) are active and functional.
2. **Data & APIs are REAL**:
   - Do not replace real backend APIs with fake or hardcoded mock datasets.
   - When deterministic demo mode is active, maintain the `Demo Mode` indicator clearly.

---

## 6. Stacking Hierarchy & Z-Index Layering

Under no circumstances should the GIS map canvas render over modals, dialogs, or drawers.
- Map Canvas: `isolation: isolate; z-index: 0`
- TopBar: `z-index: 100`
- Sidebar: `z-index: 200`
- Floating HUD Controls: `z-index: 400`
- Issue Detail Drawer: `z-index: 8000`
- Modal Backdrops / Overlays: `z-index: 9000`
- Modal Dialog Contents: `z-index: 9001`
- Toasts: `z-index: 9999`
- Tooltips: `z-index: 10000`
- All modal dialogs must use Radix `<DialogPortal>` or `<Portal>` attached to `document.body`.

---

## 7. Strict Prohibitions (Antipattern Checklist)

- ❌ DO NOT make the entire application background dark.
- ❌ DO NOT add glowing borders, neon accents, or glassmorphic blurs everywhere.
- ❌ DO NOT use tiny all-caps monospaced fonts outside technical metadata.
- ❌ DO NOT shrink the priority queue column to fit small cards; incident text must be fully readable.
- ❌ DO NOT allow the desktop sidebar to default to collapsed icon-only mode.
- ❌ DO NOT duplicate page headings.
- ❌ DO NOT create unused placeholder components or simulate features without real implementation.

---

## 8. Verification Protocol for All Changes

Before completing any task involving UI or layout:
1. Run `npm run build` in `frontend/` to ensure 0 TypeScript or Vite build errors.
2. Run visual validation at `1600 × 900` and `1280 × 800` via Chrome headless CDP.
3. Verify that the desktop sidebar is expanded, KPI counters animate, the map and queue are balanced (55%/45%), and modal dialogs render above the map.
