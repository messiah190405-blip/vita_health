# VITA HEALTH — Clinical Triage & Care Management Workstation

[![License: MIT](https://img.shields.io/badge/License-MIT-241810.svg)](LICENSE.md)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3B291D.svg)](https://www.python.org/)
[![UI Framework: PyQt6](https://img.shields.io/badge/UI-PyQt6-5A3E2B.svg)](https://pypi.org/project/PyQt6/)
[![Backend: Supabase PostgreSQL](https://img.shields.io/badge/Backend-Supabase%20PostgreSQL-2E1F15.svg)](https://supabase.com/)

**VITA HEALTH** is a desktop clinical triage and care-coordination workstation engineered in Python with **PyQt6** and backed by a **Supabase PostgreSQL** database (`vita_health` schema). Designed for rapid triage visibility, atomic encounter admissions, multi-tabbed clinical inspection, facility capacity monitoring, immutable audit logging, and privacy-aware data export (`CSV` and `JSON`), it combines a lineless glassmorphic desktop interface with non-blocking background database synchronization.

---

## Table of Contents

1. [System Architecture & Design Philosophy](#system-architecture--design-philosophy)
2. [Core Functional Modules & Clinical Workflows](#core-functional-modules--clinical-workflows)
3. [Database Architecture, Schemas & Supabase Setup](#database-architecture-schemas--supabase-setup)
4. [User Interface, Custom Widgets & Theme System](#user-interface-custom-widgets--theme-system)
5. [Keyboard Shortcuts & Navigation Ergonomics](#keyboard-shortcuts--navigation-ergonomics)
6. [Data Export, Privacy & Audit Controls](#data-export-privacy--audit-controls)
7. [Repository Layout & Module Responsibilities](#repository-layout--module-responsibilities)
8. [Installation, Configuration & Running the App](#installation-configuration--running-the-app)
9. [Troubleshooting Guide for Collaborators & Users](#troubleshooting-guide-for-collaborators--users)
10. [Clinical Governance & Academic Scope](#clinical-governance--academic-scope)
11. [License](#license)

---

## System Architecture & Design Philosophy

VITA HEALTH structures the application into decoupled layers so that database latency, large encounter queues, and visual polish do not degrade desktop responsiveness:

```text
+-------------------------------------------------------------------+
|                   Presentation Layer (PyQt6)                      |
|  VitaHealthMainWindow | BackdropPageStack | GlassCardFrame        |
|  GlassTableWidget (Lineless) | ClinicianProfileSwitcher | Drawer  |
+---------------------------------+---------------------------------+
                                  | signals / slots & AsyncTaskWorker
                                  v
+-------------------------------------------------------------------+
|             Client Registry & State Layer (In-Memory)             |
|  InMemoryTriageRegistry | ClinicalEncounter | Live Filters & KPIs |
+---------------------------------+---------------------------------+
                                  | repository calls
                                  v
+-------------------------------------------------------------------+
|          Data Access & Persistence Layer (Supabase PostgreSQL)    |
|  SupabaseHealthRepository | database: postgres | schema: vita_health|
+-------------------------------------------------------------------+
```

* **Presentation Layer (`src/ui/main_window.py`, `src/ui/theme.py`):** Builds `VitaHealthMainWindow` with a fixed left navigation rail, a central `BackdropPageStack` (`QStackedWidget`) rendering a darkened `src/img/pamp.jpg` backdrop, a fixed-height toast status bar, and an animated slide-over **Encounter Inspector** drawer.
* **Domain & Registry Layer (`src/models/entities.py`, `src/models/registry.py`):** Models records via `ClinicalEncounter` and stores synchronized records in `InMemoryTriageRegistry` to provide instant search, acuity filtering, active/all toggling, and KPI calculations without redundant round-trips.
* **Data Access & Concurrency Layer (`src/database/db_manager.py` & `AsyncTaskWorker`):** Centralizes PostgreSQL operations inside `SupabaseHealthRepository` and runs I/O-bound tasks on `QThread` workers (`AsyncTaskWorker`) with automatic cleanup and error surfacing.

---

## Core Functional Modules & Clinical Workflows

### 1. Left Navigation Rail & Persistent Controls
* **Brand Header (`VITA HEALTH · Clinical Triage & Care OS`):** Displays the workstation mark, application title, and clinical suite subtitle.
* **Primary Page Navigation (`Triage Command`, `Patient Intake`, `Facilities & Audit`):** Switches the active page in the center stack and automatically refreshes facility and audit telemetry when opening **Facilities & Audit**.
* **Clinical Care Standards Card:** Documents key platform characteristics: open-source **MIT** licensing, **CSV & JSON** export formats, and **PII Redaction + Audit** safeguards.
* **On-Duty Profile Switcher (`ClinicianProfileSwitcher`):** Displays a cream initials medallion with a live shift status dot, clinician name, role/shift label, and profile position counter (`1/N`). Clicking cycles through available clinicians, emits `profileSelected`, syncs the selection with the clinician selector on **Patient Intake**, and posts a toast confirmation.
* **Bottom Toast Bar:** Surfaces transient status updates for syncs, admissions, vitals updates, referrals, discharges, deletions, exports, and profile changes before returning to the ready state.

### 2. Triage Command (Page Index `0`)
The central command view for monitoring active encounters and launching clinical actions:
* **Sync Live Data (`AsyncTaskWorker`):** Concurrently retrieves encounters, facilities, and clinicians through `SupabaseHealthRepository`, updates `InMemoryTriageRegistry`, refreshes dropdowns and KPI cards, re-renders the triage table, and animates `ArcSpinner` while active.
* **KPI Summary Cards:**
  * **Active Encounters:** Total active encounters in the registry.
  * **Critical Acuity:** Count of encounters classified as `CRITICAL`.
  * **Urgent Queue:** Count of encounters classified as `URGENT`.
  * **Cohort Mean SpO₂:** Mean blood oxygen saturation percentage across tracked records.
* **Search, Acuity Filter Pills & Active Toggle:**
  * **Search Field (`Ctrl+K`):** Filters live by patient name, National Health ID, or chief complaint.
  * **Triage Tier Pills:** Capsule filter controls for `ALL`, `CRITICAL`, `URGENT`, `PRIORITY`, and `ROUTINE` (driven by `InMemoryTriageRegistry.TRIAGE_TIERS`).
  * **Active Only Checkbox (`ActiveCheckBox`):** Filters to active encounters when checked or includes inactive/discharged records when unchecked.
* **Live Triage Table (`GlassTableWidget`):** Displays `ID`, `Acuity` (color-coded pill/cell highlight), `Status`, `Patient`, `Health ID`, `Age/Sex`, `Chief Complaint`, `BP (mmHg)`, `HR / Temp`, and `SpO₂`. Clicking a row opens the **Encounter Inspector** drawer for that encounter.
* **Export CSV / Export JSON:** Exports the currently filtered encounter set in CSV or JSON format after prompting whether to anonymize PII.

### 3. Patient Intake & Automated Triage (Page Index `1`)
Designed for registering patients, recording baseline physiological observations, previewing acuity, and executing atomic admissions:
* **Live Acuity Preview Badge:** Watches changes to **SpO₂**, **Systolic BP**, **Heart Rate**, and **Temperature** in real time and previews `CRITICAL`, `URGENT`, `PRIORITY`, or `ROUTINE` severity before submission.
* **Patient Demographics & Clinical Fields:**
  * **Required Fields:** `National Health ID`, `First Name`, and `Chief Complaint` (validated prior to submission; `Emergency Contact` and `Last Name` also support standard intake entry with safe fallbacks where applicable).
  * **Additional Patient & Encounter Fields:** `Date of Birth`, `Gender`, `Phone`, `Blood Group`, `Allergies`, `Facility`, `Clinician`, `Diastolic BP`, `Heart Rate (bpm)`, `Temperature (°C)`, `SpO₂ (%)`, and `Clinical Notes`.
* **Atomic Admission Execution:** Calls `admit_patient_via_procedure` via `SupabaseHealthRepository`, clears intake inputs on success, switches back to **Triage Command**, and triggers a live sync.

### 4. Facilities & Audit (Page Index `2`)
Provides operational capacity metrics and an immutable audit log of encounter activity:
* **Reload Telemetry:** Asynchronously fetches facility metrics and audit logs while displaying `ArcSpinner` and a loading status label.
* **Facility Capacity Table:** Displays `Facility`, `District`, `Beds`, `Active`, `Critical`, and an embedded `Occupancy %` progress bar (`QProgressBar`) for each facility.
* **Immutable Encounter Audit Log:**
  * **Audit Search Box:** Filters cached audit records in real time by `Audit ID`, `Operation`, `Record ID`, `Event Summary`, or `Timestamp (UTC)`.
  * **Audit Log Table:** Displays `Audit ID`, `Operation`, `Record ID`, `Event Summary`, and `Timestamp (UTC)`.

### 5. Slide-Over Encounter Inspector Drawer
Clicking any row in **Triage Command** animates open the right-hand inspector drawer (`420px` width) with four tabs:

| Tab | Capabilities & Repository Interactions |
| :--- | :--- |
| **Vitals** | Edit and save vital signs (`Systolic BP`, `Diastolic BP`, `Heart Rate`, `Temp (°C)`, `SpO₂ (%)`) and `Notes` via `update_vitals_via_procedure`; refer the encounter to a target facility with a reason via `refer_encounter_via_procedure`; discharge via `discharge_via_procedure`; or delete/audit via `delete_encounter` (with confirmation). |
| **Rx** | Issue prescriptions (`medication_name`, `dosage`, `frequency`, duration in days) via `add_prescription_via_procedure`; click any prescription row to toggle its `dispensed` status (`YES` / `NO`) via `toggle_prescription_dispensed`. |
| **Labs** | Order lab tests (`test_name` and specimen type: `Blood`, `Urine`, `Sputum`, `Swab`) via `add_lab_order_via_procedure`; click any lab order row to cycle status (`PENDING` $\rightarrow$ `COMPLETED` $\rightarrow$ `FLAGGED`) via `update_lab_order_status`. |
| **Trend & Vax** | View chronological **Vitals Snapshot History** (`Time`, `Acuity`, `BP / SpO₂`) via `fetch_vitals_history`; log patient immunizations (`vaccine_name`, `dose_number`) attributed to the active on-duty clinician via `record_immunization_via_procedure`. |

---

## Database Architecture, Schemas & Supabase Setup

### Why `vita_health` Schema + `search_path` Instead of `CREATE DATABASE`
On Supabase, each project provisions a managed `postgres` database. Rather than issuing `CREATE DATABASE` statements in the SQL Editor (which creates a separate database outside the project's default `postgres` database/Table Editor context), VITA HEALTH organizes its objects inside a dedicated **`vita_health` schema**:

```sql
CREATE SCHEMA IF NOT EXISTS vita_health;
SET search_path TO vita_health, public;
```

* **Database:** `postgres`
* **Schema:** `vita_health`
* **Search Path:** `vita_health, public` — ensures unqualified object lookups resolve in `vita_health` first and fall back to `public` when needed.
* **Viewing Tables in Supabase Dashboard:** In **Table Editor** (or **Database → Tables**), switch the schema selector dropdown from `public` to `vita_health` to inspect tables created inside `vita_health`.
* **Row-Level Security (RLS):** During local development and troubleshooting with direct PostgreSQL connections, RLS can be kept disabled. Before exposing data to untrusted clients or public Supabase APIs (`anon` / `authenticated`), enable RLS and define explicit policies tailored to your access model.

---

## User Interface, Custom Widgets & Theme System

The UI pairs `NOIR_ESPRESSO_CREAM_QSS` (`src/ui/theme.py`) with custom `QPainter`-drawn widgets in `src/ui/main_window.py`:

* **`ClinicianProfileSwitcher`:** Custom-painted profile card in the navigation rail featuring an initials medallion, live shift indicator dot, clinician name, role/shift label, index indicator (`1/N`), and click-to-cycle profile switching.
* **`PillFilterButton`:** Custom rounded capsule filter button (`radius = height / 2`) for `ALL`, `CRITICAL`, `URGENT`, `PRIORITY`, and `ROUTINE`.
* **`ActiveCheckBox`:** Custom checkbox rendering a cream box with a crisp dark espresso checkmark when checked and a dark translucent box with a cream outline when unchecked.
* **`GlassTableWidget`:** Custom glassmorphic table configured with `setFrameShape(QFrame.Shape.NoFrame)`, `setShowGrid(False)`, `setFocusPolicy(Qt.FocusPolicy.NoFocus)`, rounded clipping mask, and borderless QSS rules (`border: none`, `gridline-color: transparent`) so no gridlines, header lines, or cell border strokes appear.
* **Box-Free Chevron Controls (`ChevronComboBox`, `ChevronDateEdit`, `ChevronSpinBox`, `ChevronDoubleSpinBox`):** Hide native spinner/drop-down boxes and paint clean stroke chevrons with click-to-increment/decrement hit zones on numeric spin boxes.
* **`ArcSpinner`:** Smoothly animated rotating arc indicator shown during asynchronous sync and telemetry operations.

---

## Keyboard Shortcuts & Navigation Ergonomics

| Shortcut / Action | Behavior |
| :--- | :--- |
| `Ctrl+K` | Focuses the triage board search input (`search_input`). |
| `Esc` | Closes the slide-over **Encounter Inspector** drawer. |
| `Return` / `Enter` (in Intake text fields) | Advances focus sequentially to the next intake form field. |
| Click Row (Triage Table) | Loads encounter details and opens the **Encounter Inspector** drawer. |
| Click Row (Rx / Labs Table) | Toggles prescription dispensing or cycles lab order status. |
| Click `ClinicianProfileSwitcher` | Cycles to the next on-duty clinician profile and syncs intake selection. |

---

## Data Export, Privacy & Audit Controls

* **Interactive PII Anonymization:** Clicking **Export CSV** or **Export JSON** on **Triage Command** first checks whether any records match the active filters. If matches exist, it prompts whether to anonymize PII (such as patient names and National Health IDs) via `ClinicalEncounter.to_open_dict(anonymize=...)` before opening the save dialog.
* **Audit Trail:** Encounter mutations and deletions are recorded in the audit log and viewable on the **Facilities & Audit** page with live search filtering.

---

## Repository Layout & Module Responsibilities

```text
vita-health/
├── src/
│   ├── main.py                  # Initializes SupabaseHealthRepository & launches VitaHealthMainWindow
│   ├── database/
│   │   └── db_manager.py        # SupabaseHealthRepository (queries, procedures, vitals, Rx, labs, vax, audit)
│   ├── models/
│   │   ├── entities.py          # ClinicalEncounter domain model & export serialization
│   │   └── registry.py          # InMemoryTriageRegistry (filtering, KPI snapshot, acuity tiers)
│   ├── ui/
│   │   ├── main_window.py       # VitaHealthMainWindow, custom QPainter widgets & async workflows
│   │   └── theme.py             # NOIR_ESPRESSO_CREAM_QSS stylesheet
│   └── img/
│       └── pamp.jpg             # Backdrop artwork rendered by BackdropPageStack
├── README.md                    # Project documentation
└── LICENSE.md                   # MIT License
```

---

## Installation, Configuration & Running the App

### 1. Environment Setup
Ensure you have **Python 3.10+** installed, then create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
```

Install dependencies (PyQt6 and your PostgreSQL driver/client packages):

```bash
pip install PyQt6 psycopg[binary]
```

### 2. Supabase Schema & Connection String Setup
1. In your Supabase project's **SQL Editor**, ensure the `vita_health` schema and required tables/views/procedures are created and set `search_path` to `vita_health, public`.
2. In the Supabase dashboard, open **Connect** (or **Project Settings → Database**), copy your PostgreSQL connection URI for database `postgres`, and replace `[YOUR-PASSWORD]` with your database password.
3. Configure your application environment/repository connection string so `SupabaseHealthRepository` connects to `postgres` with `search_path` set to `vita_health, public` (for example via connection options `-c search_path=vita_health,public` or session setup).

### 3. Launch the Workstation

```bash
python -m src.main
```

---

## Troubleshooting Guide for Collaborators & Users

* **"No tables in schema — The 'public' schema doesn't have any tables":** Your tables were created in `vita_health`. Open **Table Editor** and switch the schema selector dropdown from `public` to `vita_health`.
* **Query returned "No rows returned" when checking `vita_health` tables:** Confirm that your `CREATE TABLE` script was actually executed (not just saved or partially highlighted) and check the SQL Editor output for any prior statement errors.
* **App fails to find tables or procedures:** Verify that your connection string points to the `postgres` database in the intended Supabase project and that `search_path` includes `vita_health, public`.
* **Network/IPv6 connectivity issues from desktop environments:** If a direct connection URI fails due to network/IPv6 routing, use the **Transaction pooler** or **Session pooler** URI provided in Supabase's **Connect** panel.

---

## Clinical Governance & Academic Scope

**VITA HEALTH** is developed as an academic and engineering clinical workflow & triage management workstation. While it models realistic clinical triage tiers, vitals tracking, referrals, prescriptions, lab orders, immunizations, audit trails, and PII-aware exports, it is **not** a regulated medical device and should not be used as a standalone clinical diagnostic or life-safety decision system without formal clinical validation and regulatory approval.

---

## License

This project is distributed under the **MIT License**. See [LICENSE.md](LICENSE.md) for details.