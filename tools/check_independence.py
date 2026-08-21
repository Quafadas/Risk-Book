#!/usr/bin/env python3
"""Enforce spec SS 6.2: implementations share the corpus and nothing else.

The Excel harness is written in Python, which makes it one careless import away
from becoming a wrapper around the reference implementation. Agreement between
the two columns would then mean nothing. This is cheap insurance.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "impl"

# Any import naming another implementation's package.
FORBIDDEN = re.compile(
    r"^\s*(?:from|import)\s+(ils_el\b|impl\.|\.\.python)", re.MULTILINE
)


def main() -> int:
    failures: list[str] = []
    for path in sorted((IMPL / "excel").rglob("*.py")):
        for m in FORBIDDEN.finditer(path.read_text()):
            line = path.read_text()[: m.start()].count("\n") + 1
            failures.append(f"{path.relative_to(ROOT)}:{line}: {m.group(0).strip()}")

    if failures:
        print("Implementation independence violated (spec SS 6.2):", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(
            "\nThe Excel harness drives a spreadsheet; it must not borrow the\n"
            "reference implementation. See spec SS 6.2.",
            file=sys.stderr,
        )
        return 1

    print("independence: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
