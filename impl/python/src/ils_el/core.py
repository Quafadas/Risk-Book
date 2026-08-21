"""Expected loss over a year loss table.

Implements spec SS 3.2 (summation) and SS 4.1 (expected loss). Deliberately free
of NumPy: the reference implementation must not inherit a summation convention
from a library that the other implementations cannot reproduce.
"""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Iterable, Sequence
from pathlib import Path


def compensated_sum(values: Iterable[float]) -> float:
    """Neumaier compensated summation (spec SS 3.2).

    Neumaier's variant, not classic Kahan: the correction term is selected on
    the relative magnitude of accumulator and addend, which keeps it correct
    when a single large loss year dominates the partial sum -- exactly the
    shape of a catastrophe YLT.
    """
    total = 0.0
    comp = 0.0
    for x in values:
        t = total + x
        if abs(total) >= abs(x):
            comp += (total - t) + x
        else:
            comp += (x - t) + total
        total = t
    return total + comp


def expected_loss(losses: Sequence[float], n_years: int | None = None) -> float:
    """Expected annual loss (spec SS 4.1).

    n_years defaults to len(losses). Passing it explicitly is required when the
    table omits zero-loss years, which the ELT form does; the YLT form in this
    case carries them.
    """
    n = len(losses) if n_years is None else n_years
    if n <= 0:
        raise ValueError("n_years must be positive")
    return compensated_sum(losses) / n


def read_ylt(path: str | Path, expected_sha256: str | None = None) -> list[float]:
    """Read a two-column YLT. Verifies the digest when one is supplied."""
    path = Path(path)
    raw = path.read_bytes()
    if expected_sha256 is not None:
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected_sha256:
            raise ValueError(
                f"digest mismatch for {path.name}: "
                f"expected {expected_sha256[:16]}..., got {actual[:16]}..."
            )
    rows = csv.DictReader(raw.decode("utf-8").splitlines())
    return [float(r["loss"]) for r in rows]
