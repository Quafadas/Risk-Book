"""Expected loss over a year loss table.

Implements spec SS 3.1 (expected loss).

Uses NumPy, which is how a practitioner would actually reduce a loss column in
Python. An earlier draft avoided it on the grounds that the reference
implementation should not inherit a summation convention from a library the
other implementations cannot reproduce -- that mattered when the spec mandated a
summation convention and the tolerance was zero. It no longer does: implementations are
compared against the golden value within a relative tolerance, never against
each other, so each is free to be idiomatic.
"""

from __future__ import annotations

import hashlib
import io
from collections.abc import Sequence
from pathlib import Path

import numpy as np


def expected_loss(losses: Sequence[float] | np.ndarray,
                  n_years: int | None = None) -> float:
    """Expected annual loss (spec SS 3.1).

    n_years defaults to the row count. Passing it explicitly is required when
    the table omits zero-loss years, which the ELT form does; the YLT form in
    this case carries them.
    """
    values = np.asarray(losses, dtype=np.float64)        
    if n_years is None or n_years <= 0:
        raise ValueError("n_years must be positive")

    return float(values.sum() / n_years)


def read_ylt(path: str | Path, expected_sha256: str | None = None) -> np.ndarray:
    """Read the loss column of a YLT. Verifies the digest when one is supplied.

    The column is located by name from the header rather than by position, so a
    corpus file that grows a column does not silently shift the reading.
    """
    path = Path(path)
    raw = path.read_bytes()
    if expected_sha256 is not None:
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected_sha256:
            raise ValueError(
                f"digest mismatch for {path.name}: "
                f"expected {expected_sha256[:16]}..., got {actual[:16]}..."
            )

    text = raw.decode("utf-8")
    header = [h.strip() for h in text.splitlines()[0].split(",")]
    if "loss" not in header:
        raise ValueError(f"{path.name} has no 'loss' column: {header}")

    return np.loadtxt(
        io.StringIO(text),
        delimiter=",",
        skiprows=1,
        usecols=header.index("loss"),
        dtype=np.float64,
        ndmin=1,
    )
