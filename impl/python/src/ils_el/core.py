"""Expected loss over a year loss table.

Implements spec SS 3.2 (summation) and SS 4.1 (expected loss).

Deliberately free of NumPy: the reference implementation should reduce a column
the way a reader of SS 4.1 would.
"""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Sequence
from pathlib import Path


def expected_loss(losses: Sequence[float], n_years: int | None = None) -> float:
    """Expected annual loss (spec SS 4.1).

    n_years defaults to len(losses). Passing it explicitly is required when the
    table omits zero-loss years, which the ELT form does; the YLT form in this
    case carries them.
    """
    n = len(losses) if n_years is None else n_years
    if n <= 0:
        raise ValueError("n_years must be positive")
    return sum(losses) / n


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
