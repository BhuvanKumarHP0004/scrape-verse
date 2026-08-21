"""
main_validation_test.py
Local stress-test runner for the SentinelValidator and BrightDataClient.

Runs 8 deterministic edge-case scenarios against the validator and prints
a clear PASS / FAIL verdict for each, with a final summary.

Usage:
    python main_validation_test.py
"""

import sys
import logging
from typing import Any, Dict, List, Optional, Tuple

from validator import SentinelValidator, ValidationResult
from bright_scraper import BrightDataClient, ConfigurationError

# ---------------------------------------------------------------------------
# Logging — keep output clean; only show WARNING+ from library code
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s | %(name)s | %(message)s",
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run_test(
    test_num: int,
    title: str,
    validator: SentinelValidator,
    data: Dict[str, Any],
    *,
    expected_status: str,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    expected_failure_count: Optional[int] = None,
) -> bool:
    """
    Run a single validation test and print a PASS/FAIL verdict.

    Returns True if the test passed.
    """
    separator = "=" * 60
    print(f"\n{separator}")
    print(f"  TEST {test_num}: {title}")
    print(separator)
    print(f"  Input data : {data}")

    result: ValidationResult = validator.validate_data(data)

    print(f"  Score       : {result.score}%")
    print(f"  Status      : {result.status}")
    print(f"  Failures    : {result.failed_fields if result.failed_fields else 'None'}")

    # --- Assertions ---
    passed = True
    reasons: List[str] = []

    if result.status != expected_status:
        passed = False
        reasons.append(f"status={result.status}, expected={expected_status}")

    if min_score is not None and result.score < min_score:
        passed = False
        reasons.append(f"score={result.score} < min={min_score}")

    if max_score is not None and result.score > max_score:
        passed = False
        reasons.append(f"score={result.score} > max={max_score}")

    if expected_failure_count is not None and len(result.failed_fields) != expected_failure_count:
        passed = False
        reasons.append(
            f"failure_count={len(result.failed_fields)}, expected={expected_failure_count}"
        )

    verdict = "✅ PASS" if passed else "❌ FAIL"
    print(f"  Verdict     : {verdict}")
    if reasons:
        for r in reasons:
            print(f"    ↳ {r}")

    return passed


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------

def run_all_tests() -> bool:
    """Execute all validation test scenarios. Returns True if all pass."""

    # Standard schema used by most tests
    schema = {
        "title": str,
        "price": (int, float),
        "rating": (int, float),
        "availability": str,
    }
    validator = SentinelValidator(expected_schema=schema)

    results: List[bool] = []

    # ------------------------------------------------------------------
    # TEST 1: All fields present and valid → GREEN
    # ------------------------------------------------------------------
    results.append(_run_test(
        1,
        "Healthy Page — All Fields Present & Valid",
        validator,
        {
            "title": "Quantum AI Development Board",
            "price": 129.99,
            "rating": 4.8,
            "availability": "In Stock",
        },
        expected_status="GREEN",
        min_score=100.0,
        max_score=100.0,
        expected_failure_count=0,
    ))

    # ------------------------------------------------------------------
    # TEST 2: Broken page — missing price, corrupted rating → AMBER
    #   completeness = 3/4 (price missing), validity = 2/3 (rating wrong type)
    #   score = 3/4 × 2/3 × 100 = 50.0%  →  AMBER (degraded but partial data)
    # ------------------------------------------------------------------
    results.append(_run_test(
        2,
        "Broken Page — Missing Price, Corrupted Rating (Site Redesign)",
        validator,
        {
            "title": "Quantum AI Development Board",
            "price": None,
            "rating": "Error 404 Layout Shift",
            "availability": "In Stock",
        },
        expected_status="AMBER",
        min_score=50.0,
        max_score=50.0,
        expected_failure_count=2,
    ))

    # ------------------------------------------------------------------
    # TEST 3: Completely empty input → RED (0%)
    # ------------------------------------------------------------------
    results.append(_run_test(
        3,
        "Empty Input — No Fields At All",
        validator,
        {},
        expected_status="RED",
        min_score=0.0,
        max_score=0.0,
        expected_failure_count=4,
    ))

    # ------------------------------------------------------------------
    # TEST 4: All fields present but every type is wrong → RED
    # ------------------------------------------------------------------
    results.append(_run_test(
        4,
        "All Present, All Wrong Types",
        validator,
        {
            "title": 99999,
            "price": "not-a-number",
            "rating": [4, 5],
            "availability": 42,
        },
        expected_status="RED",
        min_score=0.0,
        max_score=0.0,
        expected_failure_count=4,
    ))

    # ------------------------------------------------------------------
    # TEST 5: Whitespace-only strings treated as missing → RED
    # ------------------------------------------------------------------
    results.append(_run_test(
        5,
        "Whitespace-Only Strings — Should Be Treated As Missing",
        validator,
        {
            "title": "   ",
            "price": 29.99,
            "rating": 3.5,
            "availability": "\t\n",
        },
        expected_status="AMBER",
        min_score=50.0,
        max_score=50.0,
        expected_failure_count=2,
    ))

    # ------------------------------------------------------------------
    # TEST 6: Boolean masquerading as int → type failure
    # ------------------------------------------------------------------
    results.append(_run_test(
        6,
        "Boolean-as-Integer — bool ⊂ int Guard",
        validator,
        {
            "title": "Valid Title",
            "price": True,           # bool, not int
            "rating": False,         # bool, not float
            "availability": "In Stock",
        },
        expected_status="AMBER",
        min_score=50.0,
        max_score=50.0,
        expected_failure_count=2,
    ))

    # ------------------------------------------------------------------
    # TEST 7: Extra unexpected fields (schema tolerance) → GREEN
    #   Validator should ignore fields NOT in the schema.
    # ------------------------------------------------------------------
    results.append(_run_test(
        7,
        "Extra Fields — Schema Should Only Check Expected Keys",
        validator,
        {
            "title": "Quantum AI Development Board",
            "price": 129.99,
            "rating": 4.8,
            "availability": "In Stock",
            "color": "Midnight Blue",       # extra
            "manufacturer": "NovaTech",     # extra
        },
        expected_status="GREEN",
        min_score=100.0,
        max_score=100.0,
        expected_failure_count=0,
    ))

    # ------------------------------------------------------------------
    # TEST 8: Empty schema contract → trivially GREEN (100%)
    # ------------------------------------------------------------------
    empty_validator = SentinelValidator(expected_schema={})
    results.append(_run_test(
        8,
        "Empty Schema — No Expectations, Trivially Valid",
        empty_validator,
        {"any_field": "any_value"},
        expected_status="GREEN",
        min_score=100.0,
        max_score=100.0,
        expected_failure_count=0,
    ))

    # ------------------------------------------------------------------
    # Bonus: BrightDataClient credential guard
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("  TEST 9: BrightDataClient — Missing Credentials Guard")
    print("=" * 60)

    bonus_passed = False
    try:
        # Should raise ConfigurationError because no env vars are set
        _client = BrightDataClient(api_token="", collector_id="")
        print("  ❌ FAIL — No exception raised for empty credentials.")
    except ConfigurationError as exc:
        print(f"  ConfigurationError raised correctly: {exc}")
        print("  Verdict     : ✅ PASS")
        bonus_passed = True
    except Exception as exc:
        print(f"  ❌ FAIL — Wrong exception type: {type(exc).__name__}: {exc}")

    results.append(bonus_passed)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n{'=' * 60}")
    print(f"  SUMMARY: {passed}/{total} tests passed", end="")
    if failed:
        print(f"  ({failed} FAILED)")
    else:
        print("  — ALL CLEAR ✅")
    print("=" * 60)

    return all(results)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
