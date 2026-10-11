# CIVILENS — AURORA INDIGO DESIGN SYSTEM SPECIFICATION

## 1. Product Identity & Purpose

- **Product Name**: CIVILENS
- **Sub-Brand / Domain**: Civic Infrastructure Intelligence
- **Platform Capability**: AI-powered civic issue intelligence system analyzing municipal complaints, validating multimodal visual evidence (YOLOv8 + NLP), calculating risk-aware explainable priorities, detecting spatiotemporal clusters (DBSCAN), and verifying physical resolution lifecycle workflows.
- **Design Concept**: **AURORA INDIGO** — A clean, high-trust civic intelligence system combining midnight-indigo navigational structure, pure-white editorial cards with thin neutral borders, purposeful violet primary actions with restrained gradients, and a tactical GIS map workspace.

---

## 2. Visual Architecture & Surface Contrast

The application strictly employs a **tri-surface visual architecture**:
1. **Main Canvas / Workspace**: Light, calm, high-legibility canvas (`#F6F7FC`).
2. **Primary Application Cards & Panels**: Pure white (`#FFFFFF`) with subtle neutral borders (`#E4E7F1`) and soft shadows (`shadow-xs` / `shadow-sm`).
3. **Muted Secondary Surfaces**: Soft lavender-tinted neutral (`#F0F2F9`) for secondary strips, table headers, and neutral badges.
4. **Left Navigation Sidebar**: Midnight indigo (`#13152E`) with subtle item hovers (`#212348`) and violet linear gradient active states (`linear-gradient(100deg, #3A326F, #29264F)`).
5. **Tactical GIS Map Workspace**: Deep midnight slate (`#10162A`) integrated into the otherwise light workspace, providing crisp contrast for semantic incident markers, DBSCAN clusters, and priority heatmaps.

> **CRITICAL RULE**: Do not recolor the entire application dark. The main workspace is **LIGHT** (`#F6F7FC`). The sidebar is **MIDNIGHT INDIGO** (`#13152E`). The map canvas is **DARK** (`#10162A`).

---

## 3. Aurora Indigo Color Tokens

| Token Name | Hex Value | Semantic Role & UI Application |
| :--- | :--- | :--- |
| **Canvas** | `#F6F7FC` | Global application workspace background |
| **Card / Surface** | `#FFFFFF` | Primary card panels, KPI cards, modal bodies, top bar |
| **Muted Surface** | `#F0F2F9` | Secondary metrics strip, quiet table headers, subtle container backgrounds |
| **Primary Text** | `#11162A` | Primary headings, titles, active labels, body copy |
| **Secondary Text**| `#65708B` | Subtitles, descriptive text, timestamps, secondary metadata |
| **Borders** | `#E4E7F1` | Structural borders for cards, dividers, top bar bottom border |
| **Sidebar BG** | `#13152E` | Persistent left sidebar background |
| **Sidebar Hover**| `#212348` | Hover state for sidebar navigation items |
| **Sidebar Active**| `linear-gradient(100deg, #3A326F, #29264F)` | Active navigation link container gradient |
| **Primary Action**| `#6457E8` | Primary button actions, active tabs, focus accents |
| **Primary Hover** | `#5145CF` | Hover state for primary action buttons |
| **Secondary Accent**| `#8B5CF6` | Active sidebar indicator line, secondary badges, radar highlights |
| **Informational Blue**| `#3B82F6` | Informational status badges, telemetry notes |
| **Critical** | `#EF4444` | Critical priority badge, emergency alert indicators, acute collision hazards |
| **High Priority** | `#F97316` | High priority badge, acute garbage/water hazard indicators |
| **Medium Priority**| `#EAB308` | Medium priority badge, municipal warnings |
| **Resolved / Success**| `#10B981` | Resolved status, verified inspection badge, online engine status |
| **Map Background**| `#10162A` | Tactical GIS map base canvas with restrained geographic details |

---

## 4. Typography Scale & Specifications

- **Primary Font Family**: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `'Segoe UI'`, `Roboto`, sans-serif.
- **Technical Monospace Family**: `'JetBrains Mono'`, `ui-monospace`, `monospace` (strictly reserved for GPS coordinates, work order IDs like `CIVIC-2026-001`, SLA hours, and raw confidence scores).

### Hierarchy & Scale

| Level | Size | Weight | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Main Page Heading** | `32px – 36px` | Bold (`700`) | `1.2` | Primary page heading (e.g. `Civic Intelligence`) |
| **Section Heading** | `19px – 22px` | Semibold (`600`) | `1.3` | Panel titles (e.g. `Tactical Spatial Map`, `Priority Incident Queue`) |
| **Incident Title / Subhead**| `16px – 17px`| Semibold (`600`) | `1.4` | Incident category, modal header, card title |
| **Body Text** | `14px – 15px` | Regular (`400`) / Medium (`500`) | `1.5` | Citizen complaint descriptions, card descriptions |
| **Navigation Items** | `14px` | Medium (`500`) | `1.4` | Expanded sidebar menu links, top bar breadcrumbs |
| **Secondary Metadata** | `12px – 13px` | Regular (`400`) / Medium (`500`) | `1.4` | Ward tags, timestamps, secondary strip metrics |
| **KPI Primary Numbers** | `34px – 38px` | Bold (`700`) | `1.1` | Main numeric counter values (`CountUp`), tabular numbers |

> **PROHIBITION**: Do NOT use uppercase monospaced typography throughout the application. All uppercase text must be limited to micro status tags (e.g. `CRITICAL`, `HIGH`, `OPEN`).

---

## 5. Desktop Layout Rules (Reference: 1600 × 900)

- **Reference Target Viewport**: `1600 × 900` pixels (with responsive scalability down to `1280 × 800`).
- **Sidebar Width (Expanded)**: `256px` fixed width on desktop viewports.
- **Sidebar Width (Collapsed)**: `72px` with centered icon tooltips.
- **Desktop Sidebar State**: **Defaults to EXPANDED (`256px`)**, ensuring full text labels are immediately readable.
- **Top Application Bar**: `56px` fixed height (`h-14`), border-bottom `#E4E7F1`, background `#FFFFFF`.
- **Main Workspace Padding**: `24px` (`p-6`).
- **Card Spacing / Grid Gaps**: `14px – 18px` gap between major layout cards (`gap-4` / `gap-4.5`).

### Command Center Composition (Definitive Content Order)
1. **Top Application Bar (56px)**:
   - Sticky `h-14` header with scroll-reactive shadow/background transition.
   - Left: Contextual breadcrumb (`Operations > Command Center`) and active incident count.
   - Center: Command Palette search trigger (`⌘K`).
   - Right: Ward selector, Motion animation toggle, Demo mode indicator, and primary action (`+ New Complaint` in `#6457E8`).
   - Never duplicates the main page heading.
2. **Page Header Row**:
   - Left: Main heading (`Civic Intelligence`, 32–36px bold, `#11162A`) + descriptive subtitle (14–15px, `#65708B`).
   - Right: Real-time system health indicator (`Inference Engine Online`) + primary action button (`Analyze an Issue`).
3. **KPI Card Row**:
   - Single 4-column row (`grid grid-cols-4 gap-4`).
   - Equal-width white cards with `#E4E7F1` borders: **Total Issues**, **High Priority**, **Unreported Issues**, **Active Hotspots**.
   - Metric values: 34–38px bold tabular numbers with animated `CountUp`.
4. **Secondary Metrics Strip**:
   - Quiet horizontal strip below KPI cards (`bg-[#F0F2F9]`, border `#E4E7F1`, 12–13px text, `#65708B`).
   - Displays recurring chronic sites, pending resolutions, vision precision rate, and SLA dispatch window.
5. **Geospatial Intelligence Map & Priority Queue (55% / 45% Split)**:
   - First screen at 1600 × 900 presents header, KPIs, strip, and the majority of the map and priority queue.
   - **Left Panel (55% width)**: Tactical Spatial GIS Map.
     - Dark canvas (`#10162A`) with subtle street details and pulsing incident pins.
     - Floating layer controls (`Markers`, `Clusters`, `Hotspots`, `Heatmap`) and expand button.
     - Smooth camera `flyTo` tracking on selected incident coordinates.
   - **Right Panel (45% width)**: Priority Incident Queue.
     - Section title + incident counter (`Top 4 of N`).
     - Featured Risk Element: Aceternity UI `CardSpotlight` highlighting the #1 critical risk issue with a subtle `#6457E8` cursor spotlight.
     - Scrollable Incident Feed: Sequential cards (#2 to #5), each with priority badge, category, full complaint text readable, ward, priority score, and verification badge.
     - Selecting an issue smoothly focuses the map and opens the **Issue Detail Drawer**.
6. **AI Insights Section (Below the fold)**:
   - Surfaces real calculated patterns from the active repository ground truth:
     - DBSCAN Spatial Cluster Density anomaly
     - Multimodal Cosine Text–YOLOv8 optical verification rate
     - Chronic Infrastructure Recurrence fatigue pattern
     - Department SLA Dispatch Load directives
7. **Recent Activity Timeline (Below the fold, 7 columns)**:
   - Chronological vertical timeline of citizen grievances and automated sensor detections.
   - Node status markers, timestamps, category tags, complaint excerpts, and interactive inspection triggers.
8. **Issue Category Trends & Analytical Breakdown (Below the fold, 5 columns)**:
   - Real data category distribution bars with average risk scores.
   - Multi-factor risk spectrum bins (Low, Moderate, High, Critical).
   - Direct link to complete evaluation benchmarks.

---

## 6. Component Specifications & Design Tokens

### A. Surface & Card Design
- **Background**: `#FFFFFF` pure white.
- **Border**: `1px solid #E4E7F1`.
- **Border Radius**: `16px` (`rounded-2xl`) for cards, `12px` (`rounded-xl`) for sub-cards and pills.
- **Shadows**: Clean, soft elevation:
  - `shadow-xs`: `0 1px 2px 0 rgba(17, 22, 42, 0.04)`
  - `shadow-sm`: `0 1px 3px 0 rgba(17, 22, 42, 0.06), 0 1px 2px -1px rgba(17, 22, 42, 0.04)`
  - `shadow-md`: `0 4px 6px -1px rgba(17, 22, 42, 0.07), 0 2px 4px -2px rgba(17, 22, 42, 0.04)`

### B. shadcn/ui Primitives
- **Sidebar** ([`src/components/ui/sidebar.tsx`](file:///Users/abby/chiragwalaproj/frontend/src/components/ui/sidebar.tsx)):
  - Built with `SidebarProvider`, `Sidebar`, `SidebarHeader`, `SidebarContent`, `SidebarMenu`, `SidebarMenuButton`, `SidebarFooter`, `SidebarTrigger`.
  - Background `#13152E`, item hover `#212348`, active state `linear-gradient(100deg, #3A326F, #29264F)`.
  - Active indicator: `#8B5CF6` line via `layoutId="sidebarActiveIndicator"`.
- **Command Dialog** ([`src/components/ui/command.tsx`](file:///Users/abby/chiragwalaproj/frontend/src/components/ui/command.tsx)):
  - Centered modal with search input, keyboard navigation, `#F0F2F9` header, `#FFFFFF` body.
- **Dialog & Modals**:
  - Attached to `document.body` via Radix `<DialogPortal>`.
  - Clean `#FFFFFF` card container with `#F0F2F9` header and `#E4E7F1` dividers.

### C. React Bits Integration
- **CountUp** ([`src/components/reactbits/CountUp.tsx`](file:///Users/abby/chiragwalaproj/frontend/src/components/reactbits/CountUp.tsx)): Easing counter applied to all primary KPI cards and progress reveals.
- **AnimatedContent** ([`src/components/reactbits/AnimatedContent.tsx`](file:///Users/abby/chiragwalaproj/frontend/src/components/reactbits/AnimatedContent.tsx)): Choreographed entrance animations (`distance={16}`).
- **FadeContent** ([`src/components/reactbits/FadeContent.tsx`](file:///Users/abby/chiragwalaproj/frontend/src/components/reactbits/FadeContent.tsx)): Sequential unblur and opacity reveals for AI pipeline results.
- **GlareHover** ([`src/components/reactbits/GlareHover.tsx`](file:///Users/abby/chiragwalaproj/frontend/src/components/reactbits/GlareHover.tsx)): Interactive cursor glare reflection (`glareColor="rgba(100, 87, 232, 0.16)"`) applied selectively to the #1 featured AI Insight Card.

### D. Aceternity UI Integration
- **CardSpotlight** ([`src/components/aceternity/CardSpotlight.tsx`](file:///Users/abby/chiragwalaproj/frontend/src/components/aceternity/CardSpotlight.tsx)):
  - Applied selectively to the #1 critical risk item in the Priority Incident Queue.
  - Subtle violet cursor illumination (`#6457E8`, `radius={240}`).

### E. Motion for React & Scroll System
- **Initial Page Entrance (<1.4s)**:
  - Header rises and fades in smoothly (`y: -10 &rarr; 0`).
  - KPI cards reveal with a 60ms stagger, triggering numerical `CountUp`.
  - Secondary strip appears sequentially.
  - 55% GIS Map and 45% Priority Queue reveal in sequence with small card stagger.
- **Internal Scroll Progress Indicator**:
  - Thin 2.5px violet line (`#6457E8` &rarr; `#8B5CF6`) sticky at the top of the workspace.
  - Tracks internal container scroll via `useScroll({ container: containerRef })` smoothed with `useSpring`.
  - Automatically hidden when content is not scrollable.
- **Subtle Header Parallax**:
  - Low-contrast Mumbai civic skyline SVG decorative layer linked to scroll via `useTransform(scrollY, [0, 260], [0, -12])`.
  - Text titles, badges, and controls remain stationary at `relative z-10`.
- **Scroll-Triggered Section Reveals**:
  - AI Insights, Recent Activity timeline, and Category trends reveal using `whileInView` and `viewport={{ once: true, margin: '-40px' }}`.
  - 12–18px upward reveal with 350–450ms duration and 50–70ms stagger.
- **Accessibility (`prefers-reduced-motion`)**:
  - Integrated via `useCivicMotion()` context and UI toggle button.
  - Immediately zeroes transforms (`y: 0`), eliminates delays, and preserves instant feedback when reduced motion is requested.

---

## 7. Stacking Context & Z-Index Layering

- **Map Container**: `isolation: isolate; z-index: 0;`
- **Top Application Bar**: `z-index: 100`
- **Sidebar**: `z-index: 200`
- **Floating Map HUD Controls**: `z-index: 400`
- **Issue Detail Drawer**: `z-index: 8000`
- **Modal Backdrops (`DialogOverlay`, `Portal`)**: `z-index: 9000`
- **Modal Dialog Content (`DialogContent`, `Portal`)**: `z-index: 9001`
- **Toasts**: `z-index: 9999`
- **Tooltips**: `z-index: 10000`

---

## 8. Prohibited Design Patterns

1. ❌ **NO all-black backgrounds** for the workspace. Main workspace is `#F6F7FC`.
2. ❌ **NO cyan or neon borders** on components.
3. ❌ **NO excessive glassmorphism** or opaque blurry surfaces covering content.
4. ❌ **NO wall of tiny uppercase labels**; use sentence-cased readable typography.
5. ❌ **NO duplicate page headings** across top bar and content stage.
6. ❌ **NO map canvas rendering above dialogs, modals, or drawers**.
7. ❌ **NO desktop sidebar defaulting to collapsed icon-only state**. Desktop defaults to expanded (256px).

---

## 9. Signature AI Analysis Experience Specification

The **Analyze Issue** interaction is the signature demonstration moment of CIVILENS:

### A. Ten-Stage Cognitive Pipeline Workflow
1. **Complaint received**: Ingestion signature verification & payload validation.
2. **NLP classification**: Category, urgency & semantic intent extraction.
3. **Location extraction**: GIS geocoding, landmark indexing & administrative ward resolution.
4. **Duplicate detection**: Spatial proximity (Haversine) & TF-IDF semantic vector cosine matching.
5. **YOLO vision analysis**: YOLOv8 optical defect detection, confidence estimation & bounding box verification.
6. **Text–image cross-validation**: Multimodal cosine alignment & consistency classification (`CONSISTENT`, `INCONSISTENT`, `MANUAL REVIEW`).
7. **Hotspot and recurrence analysis**: Haversine DBSCAN spatiotemporal cluster membership & chronic recurrence index.
8. **Risk-aware priority**: Multi-factor explainable 0–100 priority score calculation.
9. **Department routing**: Municipal department SLA assignment & field dispatch determination.
10. **Results ready**: Synthesized municipal dispatch intelligence dossier.

### B. Active & Completed Stage Choreography
- **Active Processing Stage**:
  - Highlight: Subtle `#6457E8` violet highlight ring (`ring-2 ring-[#6457E8]/25`), elevated shadow.
  - Moving Progress Indicator: Animated gradient laser scan line across the card header.
  - Pipeline Connecting Line: Continuous horizontal progress track connecting all 10 nodes, filling with violet `#6457E8` and emerald `#10B981`.
  - Clear Processing Label: Dedicated status banner displaying the exact active processing step (e.g. `Extracting tokens & semantic classification intent...`).
- **Completed Stages**:
  - Retain complete verified state with green `#10B981` `COMPLETE` pill badge and preserved empirical result cards.

### C. Sequential Result Reveal (Dossier)
Revealed in exact ordered sequence following stage completion:
1. **Category**: Name, confidence & NLP classification match.
2. **Urgency**: Percentage with animated `CountUp`.
3. **Severity**: Percentage with animated `CountUp`.
4. **Location**: Geocoded landmark, GPS coordinates & administrative ward.
5. **Evidence Consistency**: Multimodal alignment verdict & cosine score.
6. **Dynamic Priority Score**: Real animated `PriorityGauge` reaching real computed score + breakdown vectors.
7. **Department**: Assigned municipal department & response SLA.
8. **Recommended Action**: Official dispatch directive & field repair protocol.

### D. Presentation Controls
- **Replay**: Re-runs the staged presentation using the current analysis results.
- **Skip Animation**: Immediately bypasses presentation delays to show all stages completed and the full dossier, without bypassing actual backend analysis or fabricating results.
- **Reset Demo**: Clears intake inputs and returns to a clean form ready for new complaints.
- **Deterministic Demo Mode Cadence**: 4–7 second sequence (~5.35s total) with honest real-time wait states when executing live inference.

