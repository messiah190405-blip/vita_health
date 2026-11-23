-- ============================================================================
-- VITA-DPG: Enterprise Referral & Facility Telemetry Extensions
-- File: 06_enterprise_referrals.sql
-- ============================================================================

SET search_path TO vita_health, public;

CREATE OR REPLACE PROCEDURE vita_health.sp_refer_encounter(
    p_encounter_id INTEGER,
    p_target_facility_id INTEGER,
    p_referral_reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_target_name VARCHAR(120);
BEGIN
    SELECT facility_name INTO v_target_name
    FROM vita_health.facilities
    WHERE facility_id = p_target_facility_id;

    IF v_target_name IS NULL THEN
        RAISE EXCEPTION 'Target facility % not found.', p_target_facility_id;
    END IF;

    UPDATE vita_health.encounters
    SET facility_id = p_target_facility_id,
        status = 'REFERRED',
        clinical_notes = COALESCE(clinical_notes, '') ||
            E'\n[REFERRED -> ' || v_target_name || ']: ' || p_referral_reason
    WHERE encounter_id = p_encounter_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Encounter ID % does not exist.', p_encounter_id;
    END IF;
END;
$$;