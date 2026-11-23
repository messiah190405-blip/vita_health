-- ============================================================================
-- VITA-DPG: Longitudinal Vitals History & Immunization Registry
-- File: 08_vitals_history_and_immunizations.sql
-- ============================================================================

SET search_path TO vita_health, public;

CREATE TABLE IF NOT EXISTS vita_health.vitals_history (
    history_id SERIAL PRIMARY KEY,
    encounter_id INTEGER NOT NULL REFERENCES vita_health.encounters(encounter_id) ON DELETE CASCADE,
    systolic_bp INTEGER NOT NULL,
    diastolic_bp INTEGER NOT NULL,
    heart_rate_bpm INTEGER NOT NULL,
    temperature_c NUMERIC(4,1) NOT NULL,
    spo2_percent INTEGER NOT NULL,
    triage_level VARCHAR(20) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vita_health.immunizations (
    immunization_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES vita_health.patients(patient_id) ON DELETE CASCADE,
    vaccine_name VARCHAR(100) NOT NULL,
    dose_number INTEGER NOT NULL DEFAULT 1 CHECK (dose_number >= 1),
    administered_by VARCHAR(100) NOT NULL,
    administered_on DATE NOT NULL DEFAULT CURRENT_DATE,
    next_due_date DATE
);

-- Automatically snapshot vitals whenever an encounter is inserted or updated
CREATE OR REPLACE FUNCTION vita_health.fn_snapshot_vitals()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO vita_health.vitals_history (
        encounter_id, systolic_bp, diastolic_bp, heart_rate_bpm,
        temperature_c, spo2_percent, triage_level
    )
    VALUES (
        NEW.encounter_id, NEW.systolic_bp, NEW.diastolic_bp, NEW.heart_rate_bpm,
        NEW.temperature_c, NEW.spo2_percent, NEW.triage_level
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_snapshot_vitals ON vita_health.encounters;
CREATE TRIGGER trg_snapshot_vitals
AFTER INSERT OR UPDATE OF systolic_bp, diastolic_bp, heart_rate_bpm, temperature_c, spo2_percent, triage_level
ON vita_health.encounters
FOR EACH ROW
EXECUTE FUNCTION vita_health.fn_snapshot_vitals();

CREATE OR REPLACE PROCEDURE vita_health.sp_record_immunization(
    p_patient_id INTEGER,
    p_vaccine_name VARCHAR,
    p_dose_number INTEGER,
    p_administered_by VARCHAR,
    p_next_due_date DATE
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO vita_health.immunizations (
        patient_id, vaccine_name, dose_number, administered_by, next_due_date
    )
    VALUES (
        p_patient_id, p_vaccine_name, p_dose_number, p_administered_by, p_next_due_date
    );

    INSERT INTO vita_health.dpg_audit_log(table_name, operation, record_id, summary)
    VALUES (
        'immunizations', 'INSERT', p_patient_id,
        'Administered ' || p_vaccine_name || ' (Dose ' || p_dose_number || ') to Patient #' || p_patient_id
    );
END;
$$;