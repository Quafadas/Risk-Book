# ILS Risk Conformance Specification

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be interpreted
as in RFC 2119.

## 1. Scope

This specification defines a set of deterministic calculations over together with a corpus of test cases and expected results over some common risk metrics. 
An implementation conforms at version *v* if it produces every expected result for
every case marked `since <= v` that it does not declare unsupported.

The specification covers the **contract mechanics** of ILS risk measurement —
calculations that are pure functions of tabular input. It does not cover
catastrophe model construction, hazard simulation, or vendor model calibration.

**Non-goal: agreement with any particular vendor.** Where market practice
diverges, this specification picks one convention, states it, and documents the
alternatives. The value of the corpus is that the divergences become visible and
reproducible, not that they are resolved.

## 2. Definitions

**Year Loss Table (YLT)** — a table of simulated years, each carrying the total
loss to the subject portfolio in that year. Years with no loss are present with
a loss of zero. The number of rows is the simulation length.

e.g. 
| Year | Loss |
| --- |--- |
| 1 | 10 |
| 3 | 20 |

**Event Loss Table (ELT)** — a table of events, each carrying a loss.
| Year | Day | Loss |
| --- |--- |--- |
| 1 | 1 | 10 |
| 3 |  1 | 20 |
| 3 |  2 | 20 |


**ulp** — unit in the last place: the distance between a binary64 value and the
next representable value of greater magnitude.

## 4. Operations

### 4.1 Expected loss

Given a YLT column of losses `L` of length *m*, and a declared number of simulation periods
`n`, the obvious definition of EL:

```
EL = sum(L) / n
```

`n` MUST be taken from the case's `operation.n_years` and MUST NOT be inferred
from the row count. 

`n` MUST be positive. Implementations MUST signal an error rather than returning
a non-finite value.

---

## 6. The corpus

### 6.1 Golden values

Every case carries its expected result in two forms, which MUST denote the same
number:

- `exact_decimal` — the exact result as decimal text.
- `binary64_hex` — the correctly-rounded binary64, as a C99 hex float literal.

Comparison is performed against `binary64_hex`. Hex float is used because it is
exact, compact, and parseable by every language in this repository
(`float.fromhex`, `Double.parseDouble`, `parse(Float64, ...)`). It is **not**
parseable by Excel, which is why spreadsheet implementations are compared
against `exact_decimal` under a relative tolerance instead.

Golden values MUST be derived by a documented process that is independent of any
implementation in this repository. The weakness of this concept is, in general inaccuracy in floating point arithmetic. That is beyond the scope of what we're trying to solve. 

Each test sets out tolerances within which we accept a pass. 

### 6.2 Implementation independence

Implementations MUST NOT depend on one another, directly or transitively. They
share the test corpus and nothing else.

This constrains harnesses as well as libraries. The Excel harness is written in
Python; it MUST NOT import from `impl/python`. CI enforces this
(`tools/check_independence.py`).

Tolerances MUST be read from the case file. An implementation MUST NOT hardcode
a tolerance in its test code, so that no implementation can adopt its own notion
of "close enough".

### 6.3 Result envelope

A black-box runner MUST emit a single JSON object per case:

```json
{
  "case": "el/mean-ylt-10k",
  "impl": "python",
  "spec_version": "1.0",
  "value": 5493015.493994,
  "binary64_hex": "0x1.4f445df9d9903p+22"
}
```

### 6.4 Case status

The manifest records, per implementation:

- **pass** / **fail** — as measured.
- **unsupported** — a structural limit of the platform. Not a defect.
- **xfail** — a known, documented disagreement, with a spec citation.

Silent skips are prohibited. A case that is neither run nor declared is a
manifest error and MUST fail the build.

---

## 7. Spreadsheet implementations

### 7.1 Form

A spreadsheet implementation is a **fixed template workbook per case family**,
with named ranges for inputs and outputs. The harness writes inputs into the
named input ranges, forces recalculation, and reads the named output ranges.

The formulas in the workbook are the implementation. A workbook generated
per-run by the harness tests the generator, not the spreadsheet, and does not
conform.

### 7.2 Recalculation and cached values

An `.xlsx` stores both the formula (`<f>`) and the last computed value (`<v>`).
Reading cached values without recalculating is permitted **only** when the
workbook's inputs are those of the case and a provenance record accompanies it
recording the engine, version, refresh timestamp, and digests of the input cells
and formulas. A digest mismatch MUST fail the run as *stale*, distinctly from
*wrong*.

Results obtained under LibreOffice MUST be reported as `libreoffice`, not as
`excel`. LibreOffice is a different implementation of Excel semantics. 

Templates MUST NOT use volatile functions (`NOW`, `TODAY`, `RAND`, `OFFSET`,
`INDIRECT`), which recalculate on load and defeat cached-value provenance.
`OFFSET` and `INDIRECT` are additionally prohibited because they obscure the
dependency graph.

### 7.3 Legibility

Templates MUST expose intermediate calculations cell by cell rather than as a
single nested expression, so that a divergence can be attributed to a step
without reverse-engineering a formula.

Named-range addresses MUST be derived from the layout at build time, not
hardcoded. A hardcoded address that drifts out of step with the layout produces
a silently wrong answer rather than an error.
