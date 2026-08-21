#!/usr/bin/env python3
"""Corpus integrity: schema, digests, golden-value agreement, spec coverage.

Runs before any implementation. A corpus error is not a conformance failure --
it means the question being asked is malformed.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tomllib
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "conformance" / "cases"
SPEC = ROOT / "spec" / "spec.md"
MANIFEST = ROOT / "conformance" / "manifest.toml"


def spec_sections() -> set[str]:
    text = SPEC.read_text(encoding="utf-8")
    return set(re.findall(r"^###?\s+(\d+(?:\.\d+)?)\s", text, re.MULTILINE))


def operations_prefix() -> str | None:
    """The number of the top-level "Operations" section, e.g. "3." for `## 3.`.

    Found by title rather than hardcoded. The operations section has been
    renumbered once already, and a hardcoded number silently turns this check
    from "every operation has a case" into "every subsection of whatever now
    sits at that number has a case".
    """
    text = SPEC.read_text(encoding="utf-8")
    m = re.search(r"^##\s+(\d+)\.\s+Operations\s*$", text, re.MULTILINE)
    return f"{m.group(1)}." if m else None


def main() -> int:
    errors: list[str] = []
    sections = spec_sections()
    manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    declared = set(manifest.get("cases", {}))
    found: set[str] = set()
    cited: set[str] = set()

    for path in sorted(CASES.rglob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        cid = case["id"]
        found.add(cid)
        cited.add(case["spec"])

        if path.relative_to(CASES).with_suffix("").as_posix() != cid:
            errors.append(f"{cid}: id does not match path {path.relative_to(ROOT)}")

        # Digest: the case must describe the data it actually points at.
        data = ROOT / "conformance" / case["input"]["file"]
        if not data.exists():
            errors.append(f"{cid}: input file missing: {case['input']['file']}")
        else:
            actual = hashlib.sha256(data.read_bytes()).hexdigest()
            if actual != case["input"]["sha256"]:
                errors.append(f"{cid}: digest mismatch on {case['input']['file']}")
            rows = len(data.read_text(encoding="utf-8").splitlines()) - 1
            if rows != case["input"]["rows"]:
                errors.append(f"{cid}: declares {case['input']['rows']} rows, file has {rows}")

        # The golden value must be a finite decimal number (spec SS 4.1).
        try:
            golden = Decimal(case["expected"]["exact_decimal"])
        except InvalidOperation:
            errors.append(f"{cid}: exact_decimal is not a decimal number")
        else:
            if not golden.is_finite():
                errors.append(f"{cid}: exact_decimal is not finite")

        # A tolerance that admits everything tests nothing (spec SS 4.1).
        if not 0 < case["tolerance"]["rel"] < 1e-3:
            errors.append(f"{cid}: tolerance.rel {case['tolerance']['rel']} outside (0, 1e-3)")

        if case["spec"] not in sections:
            errors.append(f"{cid}: cites spec SS {case['spec']}, which does not exist")

        if len(case.get("rationale", "")) < 40:
            errors.append(f"{cid}: rationale missing or too short (spec SS 4.4)")

    # Every case declared, every declaration real (spec SS 4.4: no silent skips).
    for missing in sorted(found - declared):
        errors.append(f"{missing}: present in corpus but absent from manifest.toml")
    for ghost in sorted(declared - found):
        errors.append(f"{ghost}: declared in manifest.toml but no such case")

    # Coverage: a normative operation section with no case is untested.
    prefix = operations_prefix()
    if prefix is None:
        errors.append('spec has no "## N. Operations" section; coverage unchecked')
    else:
        for sec in sorted(s for s in sections if s.startswith(prefix)):
            if sec not in cited:
                errors.append(f"spec SS {sec} has no case exercising it")

    if errors:
        print("Corpus errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"corpus: ok ({len(found)} case(s), {len(sections)} spec sections)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
