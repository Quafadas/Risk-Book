#!/usr/bin/env python3
"""Build the Excel template for case el/mean-ylt-10k.

The workbook IS the implementation: the harness writes inputs into named ranges
and reads named outputs back. Formulas are laid out cell by cell rather than as
one nested expression, so a divergence can be traced to a step (spec SS 7.3).

Three strategies are computed side by side, because the interesting question is
not whether a spreadsheet can average a column but whether the ways a modeller
might do it agree (spec SS 7.3):

  EL_SUM       =SUM(range)/n     -- the value under test (spec SS 3.2)
  EL_AVERAGE   =AVERAGE(range)   -- the obvious alternative
  EL_RUNNING   running total carried down a helper column

The third is reported, not a candidate. It is the layout hand-built layer models
overwhelmingly use, so it is worth showing a reader whether it agrees.
"""

from __future__ import annotations

import csv
import datetime
import re
import shutil
import zipfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.workbook.defined_name import DefinedName

# The workbook is a build artifact but it is committed, and CI compares a
# rebuild against the committed bytes (spec SS 7.1). That only works if the
# build is reproducible, so every timestamp in the container is pinned. The
# epoch is arbitrary; the DOS time format zip uses cannot represent anything
# before 1980.
FIXED_TIMESTAMP = datetime.datetime(1980, 1, 1, 0, 0, 0)
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "conformance" / "data" / "ylt-10k.csv"
OUT = Path(__file__).resolve().parent / "templates" / "el_mean.xlsx"

BLUE = Font(name="Arial", color="0000FF")          # input
BLACK = Font(name="Arial")                          # formula
BOLD = Font(name="Arial", bold=True)
YELLOW = PatternFill("solid", fgColor="FFFF00")     # key output
NUM = "#,##0.000000"


def normalise(path: Path) -> None:
    """Repack the container so the build is byte-reproducible.

    Two sources of wall-clock drift have to go, or a rebuild never matches the
    committed workbook and the CI staleness check (spec SS 7.1) is noise:

    * every zip entry carries an mtime;
    * openpyxl rewrites `dcterms:modified` in docProps/core.xml during `save()`,
      so pinning it on the Workbook beforehand has no effect.
    """
    stamp = FIXED_TIMESTAMP.strftime("%Y-%m-%dT%H:%M:%SZ")
    tmp = path.with_suffix(".xlsx.tmp")
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(
        tmp, "w", zipfile.ZIP_DEFLATED
    ) as dst:
        for name in sorted(src.namelist()):
            payload = src.read(name)
            if name == "docProps/core.xml":
                payload = re.sub(
                    rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:)",
                    rb"\g<1>" + stamp.encode() + rb"\g<2>",
                    payload,
                )
            info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            dst.writestr(info, payload)
    shutil.move(tmp, path)


def main() -> None:
    with CSV_PATH.open() as fh:
        losses = [r["loss"] for r in csv.DictReader(fh)]
    n = len(losses)
    last = n + 1  # data occupies rows 2..n+1

    wb = Workbook()

    # ---- YLT sheet: data plus the running-total diagnostic ---------------
    ws = wb.active
    ws.title = "YLT"
    for col, head in enumerate(["year", "loss", "S (running sum)"], start=1):
        ws.cell(row=1, column=col, value=head).font = BOLD
    ws.freeze_panes = "A2"

    for i, loss in enumerate(losses, start=2):
        ws.cell(row=i, column=1, value=i - 1).font = BLACK
        c = ws.cell(row=i, column=2, value=float(loss))
        c.font = BLUE
        c.number_format = "#,##0.00"

    ws["C2"] = "=B2"
    for r in range(3, last + 1):
        ws[f"C{r}"] = f"=C{r-1}+B{r}"
    for r in range(2, last + 1):
        ws.cell(row=r, column=3).number_format = NUM

    ws.column_dimensions["A"].width = 8
    for col in "BC":
        ws.column_dimensions[col].width = 22

    # ---- Calc sheet: named inputs and outputs ----------------------------
    cs = wb.create_sheet("Calc")
    cs["A1"] = "ILS conformance -- case el/mean-ylt-10k"
    cs["A1"].font = Font(name="Arial", bold=True, size=13)
    cs["A2"] = "Blue = harness input. Yellow = harness output. Black = formula."
    cs["A2"].font = Font(name="Arial", italic=True, size=9)

    # (label, kind, formula_or_value, note). Addresses are captured as the
    # rows are written -- hardcoding them is how the named ranges drift out of
    # step with the layout, which is a silent wrong-answer bug, not a crash.
    layout = [
        ("Inputs", "head", None, None),
        ("N_YEARS", "input", n, "Written by the harness from case.operation.n_years"),
        ("FIRST_ROW", "input", 2, "First data row on sheet YLT"),
        ("LAST_ROW", "input", last, "Last data row on sheet YLT"),
        ("Intermediates", "head", None, None),
        ("SUM_LOSSES", "calc", f"=SUM(YLT!B2:B{last})", "The spreadsheet's own accumulation"),
        ("COUNT_ROWS", "calc", f"=COUNT(YLT!B2:B{last})", "Guards an off-by-one in the range"),
        ("S_FINAL", "calc", f"=YLT!C{last}", "Running total, final row"),
        ("Outputs", "head", None, None),
        ("EL_SUM", "out", "={SUM_LOSSES}/{N_YEARS}", "Spec SS 4.1 -- the value under test"),
        ("EL_AVERAGE", "out", f"=AVERAGE(YLT!B2:B{last})", "AVERAGE(range)"),
        ("EL_RUNNING", "out", "={S_FINAL}/{N_YEARS}", "Reported: running-total column (SS 7.3)"),
    ]

    addr: dict[str, str] = {}
    r = 4
    for label, kind, value, note in layout:
        if kind == "head":
            cs.cell(row=r, column=1, value=label).font = BOLD
            r += 1
            continue
        addr[label] = f"B{r}"
        cs.cell(row=r, column=1, value=label).font = Font(name="Arial")
        # Formulas reference earlier outputs by label, resolved here, so a
        # layout change cannot leave a dangling reference behind.
        resolved = value.format(**addr) if isinstance(value, str) else value
        cell = cs.cell(row=r, column=2, value=resolved)
        cell.number_format = NUM
        cell.font = BLUE if kind == "input" else BLACK
        if kind == "out":
            cell.fill = YELLOW
        note_cell = cs.cell(row=r, column=3, value=note)
        note_cell.font = Font(name="Arial", size=9, color="666666")
        note_cell.alignment = Alignment(horizontal="left")
        r += 1

    cs.column_dimensions["A"].width = 20
    cs.column_dimensions["B"].width = 24
    cs.column_dimensions["C"].width = 52

    # ---- Named ranges: the harness contract ------------------------------
    for name, ref in addr.items():
        wb.defined_names.add(DefinedName(name, attr_text=f"Calc!${ref[0]}${ref[1:]}"))

    # Fixed document timestamps. The committed workbook is compared against a
    # rebuild byte for byte (spec SS 7.1); openpyxl would otherwise stamp
    # docProps/core.xml with the wall clock and make every comparison fail.
    wb.properties.created = FIXED_TIMESTAMP
    wb.properties.modified = FIXED_TIMESTAMP
    wb.properties.creator = "build_template.py"
    wb.properties.lastModifiedBy = "build_template.py"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    normalise(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({n} rows, {n} helper formulas)")


if __name__ == "__main__":
    main()
