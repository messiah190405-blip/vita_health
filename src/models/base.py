from abc import ABC, abstractmethod
from typing import Dict, Any


class ClinicalEntity(ABC):
    """
    Task 6: Abstract Base Class (ABC) enforcing a strict polymorphic contract
    across all domain objects and guaranteeing DPG Indicator 6 (Open Data Extraction).
    """

    @abstractmethod
    def get_summary_badge(self) -> str:
        """Polymorphic display string tailored to each clinical subclass."""
        pass

    @abstractmethod
    def validate_record(self) -> tuple[bool, str]:
        """Polymorphic domain validation rules."""
        pass

    @abstractmethod
    def to_open_dict(self, anonymize: bool = False) -> Dict[str, Any]:
        """DPG Indicator 6 & 9a: Non-proprietary dictionary serialization with PII redaction."""
        pass