-- ============================================================================
-- VITA-DPG: Open Community Health & Triage Registry
-- File: 04_procedures.sql
-- Purpose: Atomic Stored Procedures for Patient Intake, Vitals Update & Discharge
-- ============================================================================

SET search_path TO vita_health, public;

-- Procedure 1: Register Patient + Initial Triage Encounter Atomically
CREATE OR REPLACE PROCEDURE vita_health.sp_admit_new_patient_encounter(
    p_health_id VARCHAR,
    p_first_name VARCHAR,
    p_last_name VARCHAR,
    p_dob DATE,
    p_gender VARCHAR,
    p_phone VARCHAR,
    p_blood_group VARCHAR,
    p_allergies TEXT,
    p_emergency_contact VARCHAR,
    p_staff_id INTEGER,
    p_facility_id INTEGER,
    p_complaint TEXT,
    p_sys_bp INTEGER,
    p_dia_bp INTEGER,
    p_hr INTEGER,
    p_temp NUMERIC,
    p_spo2 INTEGER,
    p_notes TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_person_id INTEGER;
    v_patient_id INTEGER;
BEGIN
    -- Upsert Person record
    INSERT INTO vita_health.persons (national_health_id, first_name, last_name, date_of_birth, gender, phone_number)
    VALUES (p_health_id, p_first_name, p_last_name, p_dob, p_gender, p_phone)
    ON CONFLICT (national_health_id) DO UPDATE
        SET phone_number = EXCLUDED.phone_number
    RETURNING person_id INTO v_person_id;

    -- Upsert Patient record
    INSERT INTO vita_health.patients (person_id, blood_group, allergies, emergency_contact)
    VALUES (v_person_id, p_blood_group, COALESCE(NULLIF(p_allergies, ''), 'None Recorded'), p_emergency_contact)
    ON CONFLICT (person_id) DO UPDATE
        SET allergies = EXCLUDED.allergies,
            emergency_contact = EXCLUDED.emergency_contact
    RETURNING patient_id INTO v_patient_id;

    -- Insert Encounter (Trigger automatically computes triage_level & writes audit log)
    INSERT INTO vita_health.encounters (
        patient_id, staff_id, facility_id, chief_complaint,
        systolic_bp, diastolic_bp, heart_rate_bpm, temperature_c, spo2_percent, clinical_notes
    )
    VALUES (
        v_patient_id, p_staff_id, p_facility_id, p_complaint,
        p_sys_bp, p_dia_bp, p_hr, p_temp, p_spo2, p_notes
    );
END;
$$;

-- Procedure 2: Update Patient Vitals & Clinical Notes
CREATE OR REPLACE PROCEDURE vita_health.sp_update_encounter_vitals(
    p_encounter_id INTEGER,
    p_sys_bp INTEGER,
    p_dia_bp INTEGER,
    p_hr INTEGER,
    p_temp NUMERIC,
    p_spo2 INTEGER,
    p_notes TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE vita_health.encounters
    SET systolic_bp = p_sys_bp,
        diastolic_bp = p_dia_bp,
        heart_rate_bpm = p_hr,
        temperature_c = p_temp,
        spo2_percent = p_spo2,
        clinical_notes = p_notes
    WHERE encounter_id = p_encounter_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Encounter ID % does not exist.', p_encounter_id;
    END IF;
END;
$$;

-- Procedure 3: Discharge or Refer Patient
CREATE OR REPLACE PROCEDURE vita_health.sp_discharge_encounter(
    p_encounter_id INTEGER,
    p_final_status VARCHAR,
    p_discharge_summary TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE vita_health.encounters
    SET status = p_final_status,
        clinical_notes = COALESCE(clinical_notes, '') || E'\n[DISCHARGE NOTE]: ' || p_discharge_summary,
        discharged_at = NOW()
    WHERE encounter_id = p_encounter_id;
END;
$$;