-- ============================================================================
-- VITA-DPG: Open Community Health & Triage Registry
-- File: 03_triggers.sql
-- Purpose: Clinical Early-Warning Triage Automation & DPG Privacy Audit Triggers
-- ============================================================================

SET search_path TO vita_health, public;

-- Trigger Function 1: Automated Clinical Acuity Calculation (Modified Early Warning)
-- Automatically escalates triage_level if vital signs breach safe physiological thresholds
CREATE OR REPLACE FUNCTION vita_health.fn_auto_calculate_triage()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.spo2_percent < 90 OR NEW.systolic_bp < 90 OR NEW.systolic_bp > 180 
       OR NEW.heart_rate_bpm > 130 OR NEW.heart_rate_bpm < 40 OR NEW.temperature_c >= 39.5 THEN
        NEW.triage_level := 'CRITICAL';
    ELSIF NEW.spo2_percent BETWEEN 90 AND 93 OR NEW.temperature_c >= 38.3 
       OR NEW.heart_rate_bpm BETWEEN 111 AND 130 OR NEW.systolic_bp BETWEEN 160 AND 180 THEN
        NEW.triage_level := 'URGENT';
    ELSIF NEW.temperature_c >= 37.6 OR NEW.heart_rate_bpm BETWEEN 101 AND 110 THEN
        NEW.triage_level := 'PRIORITY';
    ELSE
        NEW.triage_level := COALESCE(NEW.triage_level, 'ROUTINE');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_encounter_auto_triage ON vita_health.encounters;
CREATE TRIGGER trg_encounter_auto_triage
BEFORE INSERT OR UPDATE OF systolic_bp, diastolic_bp, heart_rate_bpm, temperature_c, spo2_percent
ON vita_health.encounters
FOR EACH ROW
EXECUTE FUNCTION vita_health.fn_auto_calculate_triage();

-- Trigger Function 2: Timestamp Maintenance on Persons
CREATE OR REPLACE FUNCTION vita_health.fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_persons_updated_at ON vita_health.persons;
CREATE TRIGGER trg_persons_updated_at
BEFORE UPDATE ON vita_health.persons
FOR EACH ROW
EXECUTE FUNCTION vita_health.fn_update_timestamp();

-- Trigger Function 3: DPG Indicator 9a - Mandatory Audit Trail on Clinical Encounters
CREATE OR REPLACE FUNCTION vita_health.fn_audit_clinical_encounter()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO vita_health.dpg_audit_log(table_name, operation, record_id, summary)
        VALUES ('encounters', 'INSERT', NEW.encounter_id, 
                'New triage encounter created for Patient #' || NEW.patient_id || ' [' || NEW.triage_level || ']');
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO vita_health.dpg_audit_log(table_name, operation, record_id, summary)
        VALUES ('encounters', 'UPDATE', NEW.encounter_id, 
                'Encounter #' || NEW.encounter_id || ' updated -> Status: ' || NEW.status || ', Triage: ' || NEW.triage_level);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO vita_health.dpg_audit_log(table_name, operation, record_id, summary)
        VALUES ('encounters', 'DELETE', OLD.encounter_id, 
                'Encounter #' || OLD.encounter_id || ' purged from registry');
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_encounters ON vita_health.encounters;
CREATE TRIGGER trg_audit_encounters
AFTER INSERT OR UPDATE OR DELETE ON vita_health.encounters
FOR EACH ROW
EXECUTE FUNCTION vita_health.fn_audit_clinical_encounter();