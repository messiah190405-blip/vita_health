-- ============================================================================
-- VITA-DPG: Prescriptions & Diagnostic Lab Orders Extension
-- File: 07_prescriptions_and_labs.sql
-- ============================================================================

SET search_path TO vita_health, public;

CREATE TABLE IF NOT EXISTS vita_health.prescriptions (
    prescription_id SERIAL PRIMARY KEY,
    encounter_id INTEGER NOT NULL REFERENCES vita_health.encounters(encounter_id) ON DELETE CASCADE,
    medication_name VARCHAR(120) NOT NULL,
    dosage VARCHAR(60) NOT NULL,
    frequency VARCHAR(60) NOT NULL,
    duration_days INTEGER NOT NULL DEFAULT 5 CHECK (duration_days BETWEEN 1 AND 365),
    dispensed BOOLEAN NOT NULL DEFAULT FALSE,
    prescribed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vita_health.lab_orders (
    lab_order_id SERIAL PRIMARY KEY,
    encounter_id INTEGER NOT NULL REFERENCES vita_health.encounters(encounter_id) ON DELETE CASCADE,
    test_name VARCHAR(100) NOT NULL,
    specimen_type VARCHAR(50) NOT NULL DEFAULT 'Blood',
    result_summary VARCHAR(160) DEFAULT 'Awaiting result',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED', 'FLAGGED')),
    ordered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE PROCEDURE vita_health.sp_add_prescription(
    p_encounter_id INTEGER,
    p_medication_name VARCHAR,
    p_dosage VARCHAR,
    p_frequency VARCHAR,
    p_duration_days INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO vita_health.prescriptions (
        encounter_id, medication_name, dosage, frequency, duration_days
    )
    VALUES (
        p_encounter_id, p_medication_name, p_dosage, p_frequency, p_duration_days
    );

    INSERT INTO vita_health.dpg_audit_log(table_name, operation, record_id, summary)
    VALUES (
        'prescriptions', 'INSERT', p_encounter_id,
        'Prescribed ' || p_medication_name || ' (' || p_dosage || ') for Encounter #' || p_encounter_id
    );
END;
$$;

CREATE OR REPLACE PROCEDURE vita_health.sp_add_lab_order(
    p_encounter_id INTEGER,
    p_test_name VARCHAR,
    p_specimen_type VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO vita_health.lab_orders (
        encounter_id, test_name, specimen_type
    )
    VALUES (
        p_encounter_id, p_test_name, p_specimen_type
    );

    INSERT INTO vita_health.dpg_audit_log(table_name, operation, record_id, summary)
    VALUES (
        'lab_orders', 'INSERT', p_encounter_id,
        'Ordered lab [' || p_test_name || '] for Encounter #' || p_encounter_id
    );
END;
$$;