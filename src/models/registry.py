from typing import Dict, List, Tuple, Optional
from src.models.entities import ClinicalEncounter


class InMemoryTriageRegistry:
    """
    Task 3: Manages domain objects in memory using Lists, Dictionaries,
    and Immutable Tuples (extra credit) for O(1) lookup and instant UI filtering.
    """

    # Immutable Tuple of allowed triage severity tiers (Task 3 Extra Credit)
    TRIAGE_TIERS: Tuple[str, ...] = ("ALL", "CRITICAL", "URGENT", "PRIORITY", "ROUTINE")

    def __init__(self) -> None:
        self._encounters_list: List[ClinicalEncounter] = []
        self._encounters_by_id: Dict[int, ClinicalEncounter] = {}

    def sync_all(self, encounters: List[ClinicalEncounter]) -> None:
        self._encounters_list = list(encounters)
        self._encounters_by_id = {enc.encounter_id: enc for enc in encounters}

    def add_record(self, encounter: ClinicalEncounter) -> None:
        self._encounters_list.append(encounter)
        self._encounters_by_id[encounter.encounter_id] = encounter

    def update_record(self, encounter: ClinicalEncounter) -> None:
        if encounter.encounter_id in self._encounters_by_id:
            self._encounters_by_id[encounter.encounter_id] = encounter
            for idx, item in enumerate(self._encounters_list):
                if item.encounter_id == encounter.encounter_id:
                    self._encounters_list[idx] = encounter
                    break

    def delete_record(self, encounter_id: int) -> bool:
        if encounter_id in self._encounters_by_id:
            del self._encounters_by_id[encounter_id]
            self._encounters_list = [
                e for e in self._encounters_list if e.encounter_id != encounter_id
            ]
            return True
        return False

    def get_by_id(self, encounter_id: int) -> Optional[ClinicalEncounter]:
        return self._encounters_by_id.get(encounter_id)

    def filter_records(
        self, query: str = "", triage_filter: str = "ALL", active_only: bool = True
    ) -> List[ClinicalEncounter]:
        q = query.strip().lower()
        results: List[ClinicalEncounter] = []
        for enc in self._encounters_list:
            if active_only and enc.status != "ACTIVE":
                continue
            if triage_filter != "ALL" and enc.triage_level != triage_filter:
                continue
            if q and (
                q not in enc.patient_name.lower()
                and q not in enc.health_id.lower()
                and q not in enc.chief_complaint.lower()
            ):
                continue
            results.append(enc)
        return results

    def get_kpi_snapshot(self) -> Tuple[int, int, int, float]:
        """Returns immutable tuple: (active_count, critical_count, urgent_count, avg_spo2)."""
        active = [e for e in self._encounters_list if e.status == "ACTIVE"]
        critical = sum(1 for e in active if e.triage_level == "CRITICAL")
        urgent = sum(1 for e in active if e.triage_level == "URGENT")
        avg_spo2 = round(sum(e.spo2_percent for e in active) / len(active), 1) if active else 0.0
        return (len(active), critical, urgent, avg_spo2)