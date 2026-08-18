"""
validator.py
Calculates the Sentinel Health Score and enforces the Trust Gate safety check.

Scoring Formula:
    sentinel_score = completeness_ratio × validity_ratio × 100
    where:
        completeness_ratio = present_fields / expected_fields
        validity_ratio     = valid_fields / present_fields   (0 if no fields present)

Trust Gate Tiers:
    GREEN  (≥ green_threshold)  — Data is reliable, safe to pass downstream.
    AMBER  (≥ amber_threshold)  — Partially degraded, use with caution.
    RED    (< amber_threshold)  — Unreliable, trigger self-healing flow.
"""

import logging
from typing import Any, Dict, List, NamedTuple, Tuple, Type, Union

logger = logging.getLogger(__name__)

# Type alias: a single type or a tuple of types accepted for a schema field.
SchemaType = Union[Type, Tuple[Type, ...]]


class ValidationResult(NamedTuple):
    """Structured result returned by ``SentinelValidator.validate_data()``."""
    score: float
    status: str          # "GREEN" | "AMBER" | "RED"
    failed_fields: List[str]


class SentinelValidator:
    """
    Validates scraped data against an expected schema contract and produces
    a Sentinel Health Score with a tri-tier Trust Gate status.
    """

    def __init__(
        self,
        expected_schema: Dict[str, SchemaType],
        *,
        green_threshold: float = 80.0,
        amber_threshold: float = 50.0,
    ) -> None:
        """
        Args:
            expected_schema:  Mapping of field names → expected Python type(s).
                              Example: ``{"title": str, "price": (int, float)}``
            green_threshold:  Minimum score for GREEN status.
            amber_threshold:  Minimum score for AMBER status.

        Raises:
            ValueError: If thresholds are logically inconsistent.
        """
        if green_threshold <= amber_threshold:
            raise ValueError(
                f"green_threshold ({green_threshold}) must be strictly greater "
                f"than amber_threshold ({amber_threshold})."
            )
        self.expected_schema = expected_schema
        self.green_threshold = green_threshold
        self.amber_threshold = amber_threshold

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_valid_type(value: Any, expected_type: SchemaType) -> bool:
        """
        Check whether *value* matches *expected_type*, with an explicit
        guard against Python's ``bool ⊂ int`` quirk.

        ``bool`` is rejected when ``int`` or ``float`` is expected because
        scraped data should never legitimately be a bare ``True``/``False``
        when a numeric value is expected.
        """
        if isinstance(value, bool):
            # bool is a subclass of int in Python — reject unless the
            # schema explicitly lists bool as an accepted type.
            if expected_type is bool:
                return True
            if isinstance(expected_type, tuple) and bool in expected_type:
                return True
            return False

        # isinstance() handles both single types and tuples natively.
        return isinstance(value, expected_type)

    @staticmethod
    def _is_present(value: Any) -> bool:
        """
        A field is considered *present* if it is not ``None`` and, for
        strings, not empty or whitespace-only.
        """
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_data(self, scraped_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate *scraped_data* against the expected schema.

        Args:
            scraped_data: Field→value pairs extracted by the scraper.

        Returns:
            A ``ValidationResult(score, status, failed_fields)``.

        Raises:
            TypeError: If *scraped_data* is not a ``dict``.
        """
        if not isinstance(scraped_data, dict):
            raise TypeError(
                f"scraped_data must be a dict, got {type(scraped_data).__name__}"
            )

        total_expected: int = len(self.expected_schema)
        if total_expected == 0:
            logger.debug("Empty schema contract — trivially valid.")
            return ValidationResult(score=100.0, status="GREEN", failed_fields=[])

        present_count: int = 0
        valid_count: int = 0
        failed_fields: List[str] = []

        for field, expected_type in self.expected_schema.items():
            value = scraped_data.get(field)

            # --- Presence check (None, empty string, whitespace-only) ---
            if not self._is_present(value):
                failed_fields.append(f"{field}: Missing or empty")
                continue

            present_count += 1

            # --- Type validation ---
            if self._is_valid_type(value, expected_type):
                valid_count += 1
            else:
                actual_type = type(value).__name__
                if isinstance(expected_type, tuple):
                    expected_str = "/".join(t.__name__ for t in expected_type)
                else:
                    expected_str = expected_type.__name__
                failed_fields.append(
                    f"{field}: Expected {expected_str}, got {actual_type}"
                )

        # --- Score Calculation ---
        completeness_ratio: float = present_count / total_expected
        validity_ratio: float = (valid_count / present_count) if present_count > 0 else 0.0
        sentinel_score: float = round(completeness_ratio * validity_ratio * 100, 2)

        # --- Trust Gate (tri-tier) ---
        if sentinel_score >= self.green_threshold:
            status = "GREEN"
        elif sentinel_score >= self.amber_threshold:
            status = "AMBER"
        else:
            status = "RED"

        logger.info(
            "Sentinel Score: %.2f%% | Status: %s | Failures: %d",
            sentinel_score, status, len(failed_fields),
        )

        return ValidationResult(
            score=sentinel_score, status=status, failed_fields=failed_fields
        )
