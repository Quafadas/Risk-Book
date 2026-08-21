#!/usr/bin/env python3
"""Generate the YLT for case el/mean-ylt-10k and derive its golden value.

Provenance, not implementation. The committed CSV is the source of truth; this
script exists so the corpus can be regenerated and audited, and is NOT part of
any conformance implementation.

The golden value is derived by EXACT INTEGER ARITHMETIC over the decimal text of
the CSV. It is not produced by NumPy, or by any floating-point summation, so no
implementation's rounding behaviour can become the standard by accident
(spec SS 4.1).
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "conformance" / "data" / "ylt-10k.csv"
CASE = ROOT / "conformance" / "cases" / "el" / "mean-ylt-10k.json"

N_YEARS = 10_000
SEED = 20260821
P_ZERO = 0.62          # share of simulated years with no qualifying loss
LN_MU = 15.5           # of ln(loss) for non-zero years
LN_SIGMA = 1.4


def generate() -> list[Decimal]:
    rng = np.random.Generator(np.random.PCG64(SEED))
    has_loss = rng.random(N_YEARS) >= P_ZERO
    raw = rng.lognormal(LN_MU, LN_SIGMA, N_YEARS) * has_loss
    # Quantise to cents so the decimal text is the exact value, and every
    # conforming parser recovers bit-identical binary64 inputs (spec SS 3.1).
    return [Decimal(int(round(x * 100))).scaleb(-2) for x in raw]


def main() -> None:
    losses = generate()

    CSV.parent.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", newline="\n", encoding="utf-8") as fh:
        fh.write("year,loss\n")
        for i, v in enumerate(losses, start=1):
            fh.write(f"{i},{v:.2f}\n")

    text = CSV.read_bytes()
    sha = hashlib.sha256(text).hexdigest()

    # --- exact golden -------------------------------------------------------
    # Sum of cents is an integer; n is an integer; so the mean is an exact
    # decimal with at most 6 fractional digits. No rounding occurs here.
    cents = sum(int(v.scaleb(2)) for v in losses)
    exact_mean = Fraction(cents, 100 * N_YEARS)
    assert exact_mean.denominator in (1, 2, 4, 5, 8, 10, 16, 20, 25, 40, 50,
                                      80, 100, 125, 200, 250, 400, 500, 625,
                                      1000, 1250, 2000, 2500, 5000, 10000,
                                      12500, 20000, 25000, 50000, 100000,
                                      125000, 250000, 500000, 1000000)
    exact_dec = (Decimal(cents) / Decimal(100 * N_YEARS)).normalize()
    nearest = float(exact_mean)          # correctly rounded, via Fraction

    case = {
        "id": "el/mean-ylt-10k",
        "spec": "3.1",
        "since": "1.0",
        "rationale": (
            "Smallest possible end-to-end case: parse a 10k-row YLT and reduce "
            "it to a single number. Exists to exercise the whole path -- read "
            "decimal text, sum a column, divide by a declared period count -- "
            "before any layer structure is put on top of it."
        ),
        "input": {
            "kind": "ylt",
            "file": "data/ylt-10k.csv",
            "sha256": sha,
            "rows": N_YEARS,
            "columns": ["year", "loss"],
            "currency": "USD",
            "scale": 1,
        },
        "operation": {"name": "expected_loss", "n_years": N_YEARS},
        "expected": {"exact_decimal": str(exact_dec)},
        # Wide enough to cover the difference between one standard summation
        # and another (measured: at most 5e-15 relative on this input), narrow
        # enough that a real error still fails -- dropping a single loss-bearing
        # year moves the mean by 3e-7 relative (spec SS 4.1).
        "tolerance": {"rel": 1e-9},
    }
    CASE.parent.mkdir(parents=True, exist_ok=True)
    CASE.write_text(json.dumps(case, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"wrote {CSV.relative_to(ROOT)}  sha256={sha[:16]}...")
    print(f"exact mean  = {exact_dec}")
    print(f"binary64    = {nearest!r}")
    print(f"zero years  = {sum(1 for v in losses if v == 0)}")
    print(f"max loss    = {max(losses)}")


if __name__ == "__main__":
    main()
