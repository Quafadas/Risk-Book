#!/usr/bin/env python3
"""Build the Excel template for case el/mean-ylt-10k.

The workbook IS the implementation: the harness writes inputs into named ranges
and reads named outputs back. Formulas are laid out cell by cell rather than as
one nested expression, so a divergence can be traced to a step (spec SS 7.3).

Three strategies are computed side by side, because the interesting question is
not whether Excel can average a column but whether it can implement the
summation convention in SS 3.2 at all:

  EL_SUM         =SUM(range)/n            -- Excel's own accumulation
  EL_AVERAGE     =AVERAGE(range)          -- may differ from the above
  EL_COMPENSATED  Neumaier via two helper columns, 20k cells

The third is the one under test. It is also the one most likely to be defeated
by Excel's cosmetic rounding, which zeroes results of subtractions between
nearly equal operands -- exactly the term Neumaier depends on.
"""

from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.workbook.defined_name import DefinedName

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "conformance" / "data" / "ylt-10k.csv"
OUT = Path(__file__).resolve().parent / "templates" / "el_mean.xlsx"

BLUE = Font(name="Arial", color="0000FF")          # input
BLACK = Font(name="Arial")                          # formula
BOLD = Font(name="Arial", bold=True)
YELLOW = PatternFill("solid", fgColor="FFFF00")     # key output
NUM = "#,##0.000000"


def main() -> None:
    with CSV_PATH.open() as fh:
        losses = [r["loss"] for r in csv.DictReader(fh)]
    n = len(losses)
    last = n + 1  # data occupies rows 2..n+1

    wb = Workbook()

    # ---- YLT sheet: data plus the Neumaier accumulator -------------------
    ws = wb.active
    ws.title = "YLT"
    for col, head in enumerate(
        ["year", "loss", "S (running sum)", "c (compensation)"], start=1
    ):
        cell = ws.cell(row=1, column=col, value=head)
        cell.font = BOLD
    ws.freeze_panes = "A2"

    for i, loss in enumerate(losses, start=2):
        ws.cell(row=i, column=1, value=i - 1).font = BLACK
        c = ws.cell(row=i, column=2, value=float(loss))
        c.font = BLUE
        c.number_format = "#,##0.00"

    # Seed row: S0 = 0, c0 = 0 are implicit, so row 2 is written out longhand.
    ws["C2"] = "=B2"
    ws["D2"] = "=IF(ABS(0)>=ABS(B2),(0-C2)+B2,(B2-C2)+0)"
    for r in range(3, last + 1):
        ws[f"C{r}"] = f"=C{r-1}+B{r}"
        ws[f"D{r}"] = (
            f"=D{r-1}+IF(ABS(C{r-1})>=ABS(B{r}),"
            f"(C{r-1}-C{r})+B{r},"
            f"(B{r}-C{r})+C{r-1})"
        )
    for r in range(2, last + 1):
        ws.cell(row=r, column=3).number_format = NUM
        ws.cell(row=r, column=4).number_format = "0.00E+00"

    ws.column_dimensions["A"].width = 8
    for col in "BCD":
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
        ("SUM_LOSSES", "calc", f"=SUM(YLT!B2:B{last})", "Excel's own accumulation order"),
        ("COUNT_ROWS", "calc", f"=COUNT(YLT!B2:B{last})", "Guards an off-by-one in the range"),
        ("S_FINAL", "calc", f"=YLT!C{last}", "Neumaier running sum, final row"),
        ("C_FINAL", "calc", f"=YLT!D{last}", "Neumaier compensation, final row"),
        ("SUM_COMPENSATED", "calc", "={S_FINAL}+{C_FINAL}", "Spec SS 3.2 total"),
        ("Outputs", "head", None, None),
        ("EL_SUM", "out", "={SUM_LOSSES}/{N_YEARS}", "SUM(range) / n"),
        ("EL_AVERAGE", "out", f"=AVERAGE(YLT!B2:B{last})", "AVERAGE(range)"),
        ("EL_COMPENSATED", "out", "={SUM_COMPENSATED}/{N_YEARS}", "Spec SS 4.1 -- the value under test"),
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

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({n} rows, ~{2 * n} helper formulas)")


if __name__ == "__main__":
    main()
