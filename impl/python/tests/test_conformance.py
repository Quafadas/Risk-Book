"""Native harness. Reads the same case files as every other implementation.

Comparison logic is deliberately thin: the tolerance lives in the case data, so
no implementation can quietly adopt its own idea of 'close enough'
(spec SS 4.1).
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from ils_el.core import expected_loss, read_ylt

ROOT = Path(__file__).resolve().parents[3]
CASES = sorted((ROOT / "conformance" / "cases").rglob("*.json"))


def load(case_path: Path):
    case = json.loads(case_path.read_text(encoding="utf-8"))
    losses = read_ylt(ROOT / "conformance" / case["input"]["file"],
                      case["input"]["sha256"])
    return case, losses


def relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / abs(expected)


@pytest.mark.parametrize("case_path", CASES, ids=lambda p: p.stem)
def test_case(case_path: Path) -> None:
    case, losses = load(case_path)
    expected = float(Decimal(case["expected"]["exact_decimal"]))
    actual = expected_loss(losses, case["operation"]["n_years"])
    err = relative_error(actual, expected)
    assert err <= case["tolerance"]["rel"], (
        f"{case['id']}: got {actual!r}, want {expected!r} "
        f"({err:.3e} relative, tolerance {case['tolerance']['rel']:.0e})"
    )


@pytest.mark.parametrize("case_path", CASES, ids=lambda p: p.stem)
def test_row_count_matches_declaration(case_path: Path) -> None:
    case, losses = load(case_path)
    assert len(losses) == case["input"]["rows"]


@pytest.mark.parametrize("case_path", CASES, ids=lambda p: p.stem)
def test_tolerance_catches_a_real_error(case_path: Path) -> None:
    """The tolerance must still fail a wrong answer (spec SS 4.1).

    Dropping one loss-bearing year is the cheapest realistic mistake -- an
    off-by-one on the row range. If this ever passes, the tolerance has stopped
    discriminating and the case needs a tighter one.
    """
    case, losses = load(case_path)
    expected = float(Decimal(case["expected"]["exact_decimal"]))
    kept = list(losses)
    kept.remove(min(x for x in kept if x > 0))
    actual = expected_loss(kept, case["operation"]["n_years"])
    assert relative_error(actual, expected) > case["tolerance"]["rel"]


def test_rejects_bad_digest(tmp_path: Path) -> None:
    p = tmp_path / "ylt.csv"
    p.write_text("year,loss\n1,1.00\n")
    with pytest.raises(ValueError, match="digest mismatch"):
        read_ylt(p, "0" * 64)


def test_rejects_non_positive_n_years() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        expected_loss([1.0, 2.0], 0)
