from datetime import date
from typing import Dict, Any, Tuple, Optional
from src.models.base import ClinicalEntity


class Person(ClinicalEntity):
    """
    Base Class implementing Task 4 (Encapsulation via private attributes & @property)
    and Task 2 (Instance, Class, and Static methods).
    """
    _registry_count: int = 0

    def __init__(
        self,
        national_health_id: str,
        first_name: str,
        last_name: str,
        dob: date,
        gender: str,
        phone: str = ""
    ):
        self.__national_health_id = national_health_id.strip().upper()
        self.__first_name = first_name.strip()
        self.__last_name = last_name.strip()
        self.__dob = dob
        self.__gender = gender
        self.__phone = phone.strip()
        Person._increment_registry()

    # Task 4: Getters, Setters & @property decorators
    @property
    def national_health_id(self) -> str:
        return self.__national_health_id

    @property
    def full_name(self) -> str:
        return f"{self.__first_name} {self.__last_name}"

    @property
    def first_name(self) -> str:
        return self.__first_name

    @first_name.setter
    def first_name(self, value: str) -> None:
        if not value or len(value.strip()) < 2:
            raise ValueError("First name must contain at least 2 characters.")
        self.__first_name = value.strip()

    @property
    def last_name(self) -> str:
        return self.__last_name

    @last_name.setter
    def last_name(self, value: str) -> None:
        if not value or len(value.strip()) < 2:
            raise ValueError("Last name must contain at least 2 characters.")
        self.__last_name = value.strip()

    @property
    def gender(self) -> str:
        return self.__gender

    @property
    def phone(self) -> str:
        return self.__phone

    @phone.setter
    def phone(self, value: str) -> None:
        self.__phone = value.strip()

    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.__dob.year - (
            (today.month, today.day) < (self.__dob.month, self.__dob.day)
        )

    # Task 2: Class Method & Static Method
    @classmethod
    def _increment_registry(cls) -> None:
        cls._registry_count += 1

    @classmethod
    def total_instantiated(cls) -> int:
        return cls._registry_count

    @staticmethod
    def is_valid_health_id(health_id: str) -> bool:
        return bool(health_id and len(health_id.strip()) >= 5 and "-" in health_id)

    def get_summary_badge(self) -> str:
        return f"{self.full_name} [{self.__national_health_id}]"

    def validate_record(self) -> tuple[bool, str]:
        if not self.is_valid_health_id(self.__national_health_id):
            return False, "Health ID must follow format PREFIX-NUMBER (e.g., SL-PAT-9004)."
        return True, "Valid Person"

    def to_open_dict(self, anonymize: bool = False) -> Dict[str, Any]:
        return {
            "national_health_id": "REDACTED-PII" if anonymize else self.__national_health_id,
            "full_name": "ANONYMIZED" if anonymize else self.full_name,
            "age": self.age,
            "gender": self.__gender,
        }


# Task 5: Hierarchical Inheritance Branch A (Person -> Patient)
class Patient(Person):
    """Represents a care recipient with encapsulated blood type and allergy profile."""

    def __init__(
        self,
        national_health_id: str,
        first_name: str,
        last_name: str,
        dob: date,
        gender: str,
        blood_group: str,
        allergies: str = "None Recorded",
        emergency_contact: str = "",
        phone: str = "",
        patient_id: Optional[int] = None
    ):
        super().__init__(national_health_id, first_name, last_name, dob, gender, phone)
        self.__patient_id = patient_id
        self.__blood_group = blood_group
        self.__allergies = allergies or "None Recorded"
        self.__emergency_contact = emergency_contact

    @property
    def blood_group(self) -> str:
        return self.__blood_group

    @property
    def allergies(self) -> str:
        return self.__allergies

    @allergies.setter
    def allergies(self, value: str) -> None:
        self.__allergies = value.strip() or "None Recorded"

    # Task 5 & 6: Method Overriding using super()
    def get_summary_badge(self) -> str:
        base = super().get_summary_badge()
        return f"PATIENT: {base} | Blood: {self.__blood_group} | Allergies: {self.__allergies}"

    def to_open_dict(self, anonymize: bool = False) -> Dict[str, Any]:
        data = super().to_open_dict(anonymize=anonymize)
        data.update({
            "entity_type": "Patient",
            "blood_group": self.__blood_group,
            "allergies": self.__allergies,
        })
        return data


# Task 5: Hierarchical Inheritance Branch B (Person -> Clinician)
class Clinician(Person):
    """Represents licensed medical personnel."""

    def __init__(
        self,
        national_health_id: str,
        first_name: str,
        last_name: str,
        dob: date,
        gender: str,
        license_number: str,
        role_title: str,
        specialization: str = "General Practice",
        staff_id: Optional[int] = None
    ):
        super().__init__(national_health_id, first_name, last_name, dob, gender)
        self.__staff_id = staff_id
        self.__license_number = license_number
        self.__role_title = role_title
        self.__specialization = specialization

    @property
    def staff_id(self) -> Optional[int]:
        return self.__staff_id

    @property
    def role_title(self) -> str:
        return self.__role_title

    def get_summary_badge(self) -> str:
        return f"CLINICIAN: {self.full_name} ({self.__role_title} - {self.__specialization})"

    def to_open_dict(self, anonymize: bool = False) -> Dict[str, Any]:
        data = super().to_open_dict(anonymize=anonymize)
        data.update({
            "entity_type": "Clinician",
            "role_title": self.__role_title,
            "specialization": self.__specialization,
        })
        return data


# Task 5: Single Inheritance (ClinicalEntity -> ClinicalEncounter)
class ClinicalEncounter(ClinicalEntity):
    """
    Encapsulates physiological vitals and computes clinical acuity scores.
    Uses immutable tuples (Task 3 Extra Credit) for physiological reference bounds.
    """
    SAFE_SPO2_RANGE: Tuple[int, int] = (94, 100)
    SAFE_SYS_BP_RANGE: Tuple[int, int] = (90, 140)

    def __init__(
        self,
        encounter_id: int,
        patient_name: str,
        health_id: str,
        age_years: int,
        gender: str,
        blood_group: str,
        allergies: str,
        chief_complaint: str,
        systolic_bp: int,
        diastolic_bp: int,
        heart_rate_bpm: int,
        temperature_c: float,
        spo2_percent: int,
        triage_level: str,
        status: str,
        attending_clinician: str,
        facility_name: str,
        admitted_time: str,
        clinical_notes: str = ""
    ):
        self.encounter_id = encounter_id
        self.patient_name = patient_name
        self.health_id = health_id
        self.age_years = age_years
        self.gender = gender
        self.blood_group = blood_group
        self.allergies = allergies
        self.chief_complaint = chief_complaint
        self.__systolic_bp = systolic_bp
        self.__diastolic_bp = diastolic_bp
        self.__heart_rate_bpm = heart_rate_bpm
        self.__temperature_c = float(temperature_c)
        self.__spo2_percent = spo2_percent
        self.triage_level = triage_level
        self.status = status
        self.attending_clinician = attending_clinician
        self.facility_name = facility_name
        self.admitted_time = admitted_time
        self.clinical_notes = clinical_notes or ""

    @property
    def vitals_tuple(self) -> Tuple[int, int, int, float, int]:
        """Task 3 Extra Credit: Immutable tuple snapshot of vital signs."""
        return (
            self.__systolic_bp,
            self.__diastolic_bp,
            self.__heart_rate_bpm,
            self.__temperature_c,
            self.__spo2_percent,
        )

    @property
    def systolic_bp(self) -> int:
        return self.__systolic_bp

    @property
    def diastolic_bp(self) -> int:
        return self.__diastolic_bp

    @property
    def heart_rate_bpm(self) -> int:
        return self.__heart_rate_bpm

    @property
    def temperature_c(self) -> float:
        return self.__temperature_c

    @property
    def spo2_percent(self) -> int:
        return self.__spo2_percent

    def get_summary_badge(self) -> str:
        return f"[{self.triage_level}] #{self.encounter_id} {self.patient_name} — SpO2 {self.__spo2_percent}% | BP {self.__systolic_bp}/{self.__diastolic_bp}"

    def validate_record(self) -> tuple[bool, str]:
        if not (40 <= self.__systolic_bp <= 300):
            return False, "Systolic BP out of physiological bounds (40–300 mmHg)."
        if not (50 <= self.__spo2_percent <= 100):
            return False, "SpO2 must be between 50% and 100%."
        return True, "Valid Clinical Encounter"

    def to_open_dict(self, anonymize: bool = False) -> Dict[str, Any]:
        return {
            "encounter_id": self.encounter_id,
            "patient_name": "REDACTED" if anonymize else self.patient_name,
            "national_health_id": "REDACTED" if anonymize else self.health_id,
            "age_years": self.age_years,
            "gender": self.gender,
            "triage_level": self.triage_level,
            "systolic_bp": self.__systolic_bp,
            "diastolic_bp": self.__diastolic_bp,
            "heart_rate_bpm": self.__heart_rate_bpm,
            "temperature_c": self.__temperature_c,
            "spo2_percent": self.__spo2_percent,
            "status": self.status,
            "facility": self.facility_name,
            "admitted_time": self.admitted_time,
        }