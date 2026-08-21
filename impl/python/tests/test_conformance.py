"""Native harness. Reads the same case files as every other implementation.

Comparison logic is deliberately thin: the tolerance lives in the case data, so
no implementation can quietly adopt its own idea of 'close enough' (spec SS 6.2).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from ils_el.core import compensated_sum, expected_loss, read_ylt

ROOT = Path(__file__).resolve().parents[3]
CASES = sorted((ROOT / "conformance" / "cases").rglob("*.json"))


def load(case_path: Path):
    case = json.loads(case_path.read_text())
    losses = read_ylt(ROOT / "conformance" / case["input"]["file"],
                      case["input"]["sha256"])
    return case, losses


def ulp_error(actual: float, expected: float) -> float:
    if actual == expected:
        return 0.0
    return abs(actual - expected) / math.ulp(expected)


@pytest.mark.parametrize("case_path", CASES, ids=lambda p: p.stem)
def test_case(case_path: Path) -> None:
    case, losses = load(case_path)
    expected = float.fromhex(case["expected"]["binary64_hex"])
    actual = expected_loss(losses, case["operation"]["n_years"])
    budget = case["tolerance"]["compensated"]["ulp"]
    assert ulp_error(actual, expected) <= budget, (
        f"{case['id']}: got {actual.hex()}, want {case['expected']['binary64_hex']}"
    )


@pytest.mark.parametrize("case_path", CASES, ids=lambda p: p.stem)
def test_exact_decimal_agrees_with_hex(case_path: Path) -> None:
    """The two golden forms must denote the same number (spec SS 6.1)."""
    case = json.loads(case_path.read_text())
    from decimal import Decimal
    assert float(Decimal(case["expected"]["exact_decimal"])) == \
        float.fromhex(case["expected"]["binary64_hex"])


def test_naive_summation_is_rejected() -> None:
    """Guards the reason SS 3.2 exists.

    If this ever passes, the corpus has stopped discriminating between
    summation strategies and the case needs strengthening, not deleting.
    """
    case, losses = load(ROOT / "conformance" / "cases" / "el" / "mean-ylt-10k.json")
    expected = float.fromhex(case["expected"]["binary64_hex"])
    naive = 0.0
    for x in losses:
        naive += x
    assert ulp_error(naive / case["operation"]["n_years"], expected) > 1.0


def test_compensated_sum_handles_dominant_year() -> None:
    """Neumaier over Kahan: correction must survive a large addend (SS 3.2)."""
    assert compensated_sum([1.0, 1e100, 1.0, -1e100]) == 2.0


def test_rejects_bad_digest(tmp_path: Path) -> None:
    p = tmp_path / "ylt.csv"
    p.write_text("year,loss\n1,1.00\n")
    with pytest.raises(ValueError, match="digest mismatch"):
        read_ylt(p, "0" * 64)
