-- ============================================================================
-- VITA-DPG: Open Community Health & Triage Registry
-- File: 01_schema_tables.sql
-- Purpose: Normalized (3NF) Schema, Tables, Constraints & Indexes for Supabase
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS vita_health;
SET search_path TO vita_health, public;

-- 1. Health Facilities (Clinics / Community Health Posts)
CREATE TABLE IF NOT EXISTS vita_health.facilities (
    facility_id SERIAL PRIMARY KEY,
    facility_code VARCHAR(20) UNIQUE NOT NULL,
    facility_name VARCHAR(120) NOT NULL,
    district VARCHAR(80) NOT NULL,
    bed_capacity INTEGER NOT NULL CHECK (bed_capacity >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Base Persons Registry (Demonstrates Relational Supertype for Inheritance)
CREATE TABLE IF NOT EXISTS vita_health.persons (
    person_id SERIAL PRIMARY KEY,
    national_health_id VARCHAR(32) UNIQUE NOT NULL,
    first_name VARCHAR(60) NOT NULL,
    last_name VARCHAR(60) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('Female', 'Male', 'Non-Binary', 'Prefer Not to Say')),
    phone_number VARCHAR(25),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Clinical Staff (Subtype 1: Doctors, Nurses, Community Health Officers)
CREATE TABLE IF NOT EXISTS vita_health.clinical_staff (
    staff_id SERIAL PRIMARY KEY,
    person_id INTEGER UNIQUE NOT NULL REFERENCES vita_health.persons(person_id) ON DELETE CASCADE,
    facility_id INTEGER NOT NULL REFERENCES vita_health.facilities(facility_id) ON DELETE RESTRICT,
    license_number VARCHAR(40) UNIQUE NOT NULL,
    role_title VARCHAR(50) NOT NULL CHECK (role_title IN ('Physician', 'Registered Nurse', 'Community Health Officer', 'Pharmacist')),
    specialization VARCHAR(80) NOT NULL DEFAULT 'General Practice',
    on_duty BOOLEAN NOT NULL DEFAULT TRUE
);

-- 4. Patients (Subtype 2: Registered Care Recipients)
CREATE TABLE IF NOT EXISTS vita_health.patients (
    patient_id SERIAL PRIMARY KEY,
    person_id INTEGER UNIQUE NOT NULL REFERENCES vita_health.persons(person_id) ON DELETE CASCADE,
    blood_group VARCHAR(5) NOT NULL CHECK (blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'UNK')),
    allergies TEXT DEFAULT 'None Recorded',
    chronic_conditions TEXT DEFAULT 'None',
    emergency_contact VARCHAR(100) NOT NULL,
    consent_granted BOOLEAN NOT NULL DEFAULT TRUE
);

-- 5. Clinical Encounters & Triage Visits
CREATE TABLE IF NOT EXISTS vita_health.encounters (
    encounter_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES vita_health.patients(patient_id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES vita_health.clinical_staff(staff_id) ON DELETE RESTRICT,
    facility_id INTEGER NOT NULL REFERENCES vita_health.facilities(facility_id) ON DELETE RESTRICT,
    chief_complaint TEXT NOT NULL,
    systolic_bp INTEGER NOT NULL CHECK (systolic_bp BETWEEN 40 AND 300),
    diastolic_bp INTEGER NOT NULL CHECK (diastolic_bp BETWEEN 20 AND 200),
    heart_rate_bpm INTEGER NOT NULL CHECK (heart_rate_bpm BETWEEN 20 AND 250),
    temperature_c NUMERIC(4,1) NOT NULL CHECK (temperature_c BETWEEN 30.0 AND 44.0),
    spo2_percent INTEGER NOT NULL CHECK (spo2_percent BETWEEN 50 AND 100),
    triage_level VARCHAR(20) NOT NULL DEFAULT 'ROUTINE' CHECK (triage_level IN ('CRITICAL', 'URGENT', 'PRIORITY', 'ROUTINE')),
    clinical_notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DISCHARGED', 'REFERRED')),
    admitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    discharged_at TIMESTAMPTZ
);

-- 6. DPG Indicator 9a: Immutable Privacy & Access Audit Log ("Do No Harm by Design")
CREATE TABLE IF NOT EXISTS vita_health.dpg_audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(60) NOT NULL,
    operation VARCHAR(15) NOT NULL,
    record_id INTEGER NOT NULL,
    changed_by TEXT NOT NULL DEFAULT CURRENT_USER,
    summary TEXT NOT NULL,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_encounters_status ON vita_health.encounters(status);
CREATE INDEX IF NOT EXISTS idx_encounters_triage ON vita_health.encounters(triage_level);
CREATE INDEX IF NOT EXISTS idx_persons_health_id ON vita_health.persons(national_health_id);