-- ============================================================================
-- VITA-DPG: Open Community Health & Triage Registry
-- File: 02_views.sql
-- Purpose: Analytical & Operational Views for PyQt6 Live Tables & DPG Exports
-- ============================================================================

SET search_path TO vita_health, public;

-- View 1: Live Triage & Patient Roster (Joins Persons, Patients, Staff, Encounters)
CREATE OR REPLACE VIEW vita_health.vw_active_triage_board AS
SELECT 
    e.encounter_id,
    p.patient_id,
    per.national_health_id,
    (per.first_name || ' ' || per.last_name) AS patient_name,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, per.date_of_birth))::INT AS age_years,
    per.gender,
    p.blood_group,
    p.allergies,
    e.chief_complaint,
    e.systolic_bp,
    e.diastolic_bp,
    (e.systolic_bp || '/' || e.diastolic_bp || ' mmHg') AS blood_pressure,
    e.heart_rate_bpm,
    e.temperature_c,
    e.spo2_percent,
    e.triage_level,
    e.status,
    (sper.first_name || ' ' || sper.last_name || ' (' || cs.role_title || ')') AS attending_clinician,
    f.facility_name,
    TO_CHAR(e.admitted_at, 'YYYY-MM-DD HH24:MI') AS admitted_time,
    e.clinical_notes
FROM vita_health.encounters e
JOIN vita_health.patients p ON e.patient_id = p.patient_id
JOIN vita_health.persons per ON p.person_id = per.person_id
JOIN vita_health.clinical_staff cs ON e.staff_id = cs.staff_id
JOIN vita_health.persons sper ON cs.person_id = sper.person_id
JOIN vita_health.facilities f ON e.facility_id = f.facility_id
ORDER BY 
    CASE e.triage_level
        WHEN 'CRITICAL' THEN 1
        WHEN 'URGENT' THEN 2
        WHEN 'PRIORITY' THEN 3
        ELSE 4
    END,
    e.admitted_at DESC;

-- View 2: DPG Indicator 6 - Anonymized Non-PII Public Health Surveillance Export
-- Strips all PII (names, national IDs, phone numbers) for safe open-data CSV/JSON export
CREATE OR REPLACE VIEW vita_health.vw_dpg_anonymized_surveillance AS
SELECT 
    e.encounter_id AS case_reference,
    f.district,
    f.facility_name,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, per.date_of_birth))::INT AS patient_age,
    per.gender,
    e.triage_level,
    e.systolic_bp,
    e.diastolic_bp,
    e.heart_rate_bpm,
    e.temperature_c,
    e.spo2_percent,
    e.status,
    DATE(e.admitted_at) AS encounter_date
FROM vita_health.encounters e
JOIN vita_health.patients p ON e.patient_id = p.patient_id
JOIN vita_health.persons per ON p.person_id = per.person_id
JOIN vita_health.facilities f ON e.facility_id = f.facility_id;

-- View 3: Facility Capacity & Triage Load Summary
CREATE OR REPLACE VIEW vita_health.vw_facility_metrics AS
SELECT 
    f.facility_id,
    f.facility_code,
    f.facility_name,
    f.district,
    f.bed_capacity,
    COUNT(e.encounter_id) FILTER (WHERE e.status = 'ACTIVE') AS active_patients,
    COUNT(e.encounter_id) FILTER (WHERE e.status = 'ACTIVE' AND e.triage_level = 'CRITICAL') AS critical_cases,
    ROUND(
        (COUNT(e.encounter_id) FILTER (WHERE e.status = 'ACTIVE')::NUMERIC / NULLIF(f.bed_capacity, 0)) * 100, 
        1
    ) AS occupancy_pct
FROM vita_health.facilities f
LEFT JOIN vita_health.encounters e ON f.facility_id = e.facility_id
GROUP BY f.facility_id, f.facility_code, f.facility_name, f.district, f.bed_capacity;