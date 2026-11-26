import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from src.models.entities import ClinicalEncounter

load_dotenv()


class SupabaseHealthRepository:
    """
    Task 7: PostgreSQL persistence layer interfacing with Supabase views,
    triggers, and stored procedures using psycopg2.
    """

    def __init__(self) -> None:
        self.db_url = os.getenv("SUPABASE_DB_URL", "").strip()
        if not self.db_url:
            raise RuntimeError(
                "Missing SUPABASE_DB_URL in .env file. Copy your Session Pooler URI from Supabase."
            )

    def _connect(self):
        return psycopg2.connect(self.db_url, sslmode="require", cursor_factory=RealDictCursor)

    def fetch_triage_board(self) -> List[ClinicalEncounter]:
        sql = "SELECT * FROM vita_health.vw_active_triage_board;"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return [
                ClinicalEncounter(
                    encounter_id=r["encounter_id"],
                    patient_name=r["patient_name"],
                    health_id=r["national_health_id"],
                    age_years=r["age_years"],
                    gender=r["gender"],
                    blood_group=r["blood_group"],
                    allergies=r["allergies"],
                    chief_complaint=r["chief_complaint"],
                    systolic_bp=r["systolic_bp"],
                    diastolic_bp=r["diastolic_bp"],
                    heart_rate_bpm=r["heart_rate_bpm"],
                    temperature_c=float(r["temperature_c"]),
                    spo2_percent=r["spo2_percent"],
                    triage_level=r["triage_level"],
                    status=r["status"],
                    attending_clinician=r["attending_clinician"],
                    facility_name=r["facility_name"],
                    admitted_time=r["admitted_time"],
                    clinical_notes=r["clinical_notes"] or "",
                )
                for r in rows
            ]

    def fetch_clinicians(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT cs.staff_id, p.first_name || ' ' || p.last_name || ' (' || cs.role_title || ')' AS label
            FROM vita_health.clinical_staff cs
            JOIN vita_health.persons p ON cs.person_id = p.person_id
            WHERE cs.on_duty = TRUE ORDER BY cs.staff_id;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return list(cur.fetchall())

    def fetch_facilities(self) -> List[Dict[str, Any]]:
        sql = "SELECT facility_id, facility_name FROM vita_health.facilities WHERE is_active = TRUE ORDER BY facility_id;"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return list(cur.fetchall())

    def fetch_audit_logs(self, limit: int = 25) -> List[Dict[str, Any]]:
        sql = """
            SELECT audit_id, operation, record_id, summary, TO_CHAR(logged_at, 'YYYY-MM-DD HH24:MI:SS') AS logged_at
            FROM vita_health.dpg_audit_log
            ORDER BY audit_id DESC LIMIT %s;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (limit,))
            return list(cur.fetchall())

    def admit_patient_via_procedure(self, payload: Dict[str, Any]) -> None:
        sql = """
            CALL vita_health.sp_admit_new_patient_encounter(
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
        """
        params = (
            payload["health_id"],
            payload["first_name"],
            payload["last_name"],
            payload["dob"],
            payload["gender"],
            payload["phone"],
            payload["blood_group"],
            payload["allergies"],
            payload["emergency_contact"],
            payload["staff_id"],
            payload["facility_id"],
            payload["complaint"],
            payload["sys_bp"],
            payload["dia_bp"],
            payload["hr"],
            payload["temp"],
            payload["spo2"],
            payload["notes"],
        )
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()

    def update_vitals_via_procedure(
        self, encounter_id: int, sys_bp: int, dia_bp: int, hr: int, temp: float, spo2: int, notes: str
    ) -> None:
        sql = "CALL vita_health.sp_update_encounter_vitals(%s, %s, %s, %s, %s, %s, %s);"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (encounter_id, sys_bp, dia_bp, hr, temp, spo2, notes))
            conn.commit()

    def discharge_via_procedure(self, encounter_id: int, status: str, summary: str) -> None:
        sql = "CALL vita_health.sp_discharge_encounter(%s, %s, %s);"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (encounter_id, status, summary))
            conn.commit()

    def delete_encounter(self, encounter_id: int) -> None:
        sql = "DELETE FROM vita_health.encounters WHERE encounter_id = %s;"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (encounter_id,))
            conn.commit() 

    def fetch_facility_metrics(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT facility_id, facility_code, facility_name, district,
                   bed_capacity, active_patients, critical_cases, occupancy_pct
            FROM vita_health.vw_facility_metrics
            ORDER BY facility_id;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return list(cur.fetchall())

    def refer_encounter_via_procedure(
        self, encounter_id: int, target_facility_id: int, reason: str
    ) -> None:
        sql = "CALL vita_health.sp_refer_encounter(%s, %s, %s);"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (encounter_id, target_facility_id, reason))
            conn.commit() 

    def fetch_prescriptions_for_encounter(self, encounter_id: int) -> List[Dict[str, Any]]:
        sql = """
            SELECT prescription_id, medication_name, dosage, frequency, duration_days, dispensed,
                   TO_CHAR(prescribed_at, 'YYYY-MM-DD HH24:MI') AS prescribed_at
            FROM vita_health.prescriptions
            WHERE encounter_id = %s
            ORDER BY prescription_id DESC;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (encounter_id,))
            return list(cur.fetchall())

    def add_prescription_via_procedure(
        self, encounter_id: int, med_name: str, dosage: str, frequency: str, days: int
    ) -> None:
        sql = "CALL vita_health.sp_add_prescription(%s, %s, %s, %s, %s);"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (encounter_id, med_name, dosage, frequency, days))
            conn.commit()

    def toggle_prescription_dispensed(self, prescription_id: int, dispensed: bool) -> None:
        sql = "UPDATE vita_health.prescriptions SET dispensed = %s WHERE prescription_id = %s;"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (dispensed, prescription_id))
            conn.commit()

    def fetch_lab_orders_for_encounter(self, encounter_id: int) -> List[Dict[str, Any]]:
        sql = """
            SELECT lab_order_id, test_name, specimen_type, result_summary, status,
                   TO_CHAR(ordered_at, 'YYYY-MM-DD HH24:MI') AS ordered_at
            FROM vita_health.lab_orders
            WHERE encounter_id = %s
            ORDER BY lab_order_id DESC;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (encounter_id,))
            return list(cur.fetchall())

    def add_lab_order_via_procedure(
        self, encounter_id: int, test_name: str, specimen_type: str
    ) -> None:
        sql = "CALL vita_health.sp_add_lab_order(%s, %s, %s);"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (encounter_id, test_name, specimen_type))
            conn.commit()

    def update_lab_order_status(self, lab_order_id: int, status: str, result_summary: str) -> None:
        sql = """
            UPDATE vita_health.lab_orders
            SET status = %s, result_summary = %s
            WHERE lab_order_id = %s;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (status, result_summary, lab_order_id))
            conn.commit() 

    def fetch_vitals_history(self, encounter_id: int) -> List[Dict[str, Any]]:
        sql = """
            SELECT history_id, systolic_bp, diastolic_bp, heart_rate_bpm,
                   temperature_c, spo2_percent, triage_level,
                   TO_CHAR(recorded_at, 'YYYY-MM-DD HH24:MI') AS recorded_at
            FROM vita_health.vitals_history
            WHERE encounter_id = %s
            ORDER BY history_id DESC;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (encounter_id,))
            return list(cur.fetchall())

    def fetch_patient_id_for_encounter(self, encounter_id: int) -> Optional[int]:
        sql = "SELECT patient_id FROM vita_health.encounters WHERE encounter_id = %s;"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (encounter_id,))
            row = cur.fetchone()
            return row["patient_id"] if row else None

    def fetch_immunizations_for_patient(self, patient_id: int) -> List[Dict[str, Any]]:
        sql = """
            SELECT immunization_id, vaccine_name, dose_number, administered_by,
                   TO_CHAR(administered_on, 'YYYY-MM-DD') AS administered_on,
                   COALESCE(TO_CHAR(next_due_date, 'YYYY-MM-DD'), '—') AS next_due_date
            FROM vita_health.immunizations
            WHERE patient_id = %s
            ORDER BY immunization_id DESC;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (patient_id,))
            return list(cur.fetchall())

    def record_immunization_via_procedure(
        self,
        patient_id: int,
        vaccine_name: str,
        dose_number: int,
        administered_by: str,
        next_due_date: Optional[str],
    ) -> None:
        sql = "CALL vita_health.sp_record_immunization(%s, %s, %s, %s, %s);"
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (patient_id, vaccine_name, dose_number, administered_by, next_due_date))
            conn.commit()

    def _resolve_db_uri(self) -> str:
        for attr in ("dsn", "database_url", "connection_string", "db_url", "uri"):
            val = getattr(self, attr, None)
            if isinstance(val, str) and val.strip():
                return val.strip()

        for env_key in ("DATABASE_URL", "SUPABASE_DB_URL", "VITA_HEALTH_DB_URL"):
            val = os.getenv(env_key)
            if val and val.strip():
                return val.strip()

        raise RuntimeError(
            "No database connection string found on SupabaseHealthRepository or in environment "
            "(DATABASE_URL / SUPABASE_DB_URL)."
        )


    def authenticate_clinician(self, identifier: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticates a clinician by badge_code or email against vita_health.authenticate_clinician."""
        sql = """
            SELECT
                staff_id,
                full_name,
                role_title,
                badge_code,
                email,
                facility_id,
                label,
                last_login_at
            FROM vita_health.authenticate_clinician(%s, %s);
        """
        uri = self._resolve_db_uri()
        with psycopg2.connect(uri, options="-c search_path=vita_health,extensions,public") as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (identifier.strip(), password))
                row = cur.fetchone()
                conn.commit()
                if not row:
                    return None
                return {
                    "staff_id": row[0],
                    "full_name": row[1],
                    "role_title": row[2],
                    "badge_code": row[3],
                    "email": row[4],
                    "facility_id": row[5],
                    "label": row[6],
                    "last_login_at": str(row[7]) if row[7] else None,
                }