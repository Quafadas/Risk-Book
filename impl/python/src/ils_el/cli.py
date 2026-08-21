"""Black-box runner: emits the result envelope defined in spec SS 6.3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ils_el.core import expected_loss, read_ylt


def main() -> int:
    ap = argparse.ArgumentParser(prog="ils-el")
    ap.add_argument("case", type=Path, help="path to a conformance case JSON")
    args = ap.parse_args()

    case = json.loads(args.case.read_text(encoding="utf-8"))
    root = args.case.resolve().parents[2]
    losses = read_ylt(root / case["input"]["file"], case["input"]["sha256"])
    value = expected_loss(losses, case["operation"]["n_years"])

    print(json.dumps([{
        "case": case["id"],
        "impl": "python",
        "spec_version": "1.0",
        "value": value,
    }], indent=2))
    return 0
