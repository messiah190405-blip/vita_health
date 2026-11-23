-- ============================================================================
-- VITA-DPG: Open Community Health & Triage Registry
-- File: 05_seed_data.sql
-- Purpose: Initial Seed Data for Immediate Testing
-- ============================================================================

SET search_path TO vita_health, public;

INSERT INTO vita_health.facilities (facility_code, facility_name, district, bed_capacity) VALUES
('FAC-WA-01', 'Connaught Community Triage Unit', 'Western Area Urban', 45),
('FAC-WA-02', 'Lumley District Polyclinic', 'Western Area Urban', 30),
('FAC-BO-01', 'Bo Regional Maternal & Child Post', 'Bo District', 60)
ON CONFLICT (facility_code) DO NOTHING;

-- Seed Clinicians
INSERT INTO vita_health.persons (national_health_id, first_name, last_name, date_of_birth, gender, phone_number) VALUES
('SL-MED-1001', 'Aminata', 'Kamara', '1986-04-12', 'Female', '+232-76-555101'),
('SL-MED-1002', 'Mohamed', 'Sesay', '1990-09-23', 'Male', '+232-77-555202')
ON CONFLICT (national_health_id) DO NOTHING;

INSERT INTO vita_health.clinical_staff (person_id, facility_id, license_number, role_title, specialization)
SELECT person_id, 1, 'SLMDC-8841', 'Physician', 'Emergency & Internal Medicine'
FROM vita_health.persons WHERE national_health_id = 'SL-MED-1001'
ON CONFLICT (license_number) DO NOTHING;

INSERT INTO vita_health.clinical_staff (person_id, facility_id, license_number, role_title, specialization)
SELECT person_id, 1, 'SLNB-4419', 'Registered Nurse', 'Triage & Critical Care'
FROM vita_health.persons WHERE national_health_id = 'SL-MED-1002'
ON CONFLICT (license_number) DO NOTHING;

-- Seed Sample Encounters via Stored Procedure
CALL vita_health.sp_admit_new_patient_encounter(
    'SL-PAT-9001', 'Mariama', 'Koroma', '1994-07-18', 'Female', '+232-78-112233',
    'O+', 'Penicillin', 'Ibrahim Koroma (+232-76-998877)',
    1, 1, 'Acute febrile illness, severe headache, dizziness',
    98, 62, 118, 39.6, 94, 'RDT Malaria pending; IV paracetamol initiated.'
);

CALL vita_health.sp_admit_new_patient_encounter(
    'SL-PAT-9002', 'Samuel', 'Conteh', '1968-11-03', 'Male', '+232-30-445566',
    'A+', 'None Recorded', 'Grace Conteh (+232-30-445567)',
    1, 1, 'Shortness of breath and chest tightness',
    186, 112, 126, 37.1, 88, 'Hypertensive urgency + hypoxia. Oxygen therapy started.'
);

CALL vita_health.sp_admit_new_patient_encounter(
    'SL-PAT-9003', 'Fatmata', 'Bangura', '2001-02-25', 'Female', '+232-79-334455',
    'B+', 'Sulfa drugs', 'Zainab Bangura (+232-79-334456)',
    2, 1, 'Routine antenatal follow-up and mild fatigue',
    116, 74, 78, 36.8, 99, 'Vitals stable; iron/folate supplementation reviewed.'
);