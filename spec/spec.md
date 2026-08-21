# ILS Risk Conformance Specification

**Version 1.0** · Status: draft

Section numbers are a public interface. Cases, manifests and issue reports cite
them. Sections are **never renumbered**; superseded sections are marked
deprecated and retained.

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be interpreted
as in RFC 2119.

---

## 1. Scope

This specification defines a set of deterministic calculations over catastrophe
loss tables, together with a corpus of test cases and expected results. An
implementation conforms at version *v* if it produces every expected result for
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

**Event Loss Table (ELT)** — a table of events, each carrying a loss and an
annual rate of occurrence. Zero-loss years are *not* represented; the year count
is a separate parameter. (Reserved for v1.1; no cases at v1.0.)

**Expected Loss (EL)** — the expected annual loss to the subject portfolio,
expressed in the currency and scale declared by the case input.

**ulp** — unit in the last place: the distance between a binary64 value and the
next representable value of greater magnitude.

## 3. Numeric conventions

### 3.1 Input encoding

Loss values MUST be transported as decimal text. Every value in the corpus is
quantised to two decimal places, so each is exactly representable as a decimal
and every conforming parser recovers a bit-identical binary64.

Implementations MUST parse with a correctly-rounded decimal-to-binary64 routine.
The standard library routine of every language in this repository satisfies this;
hand-rolled parsers generally do not.

All arithmetic is IEEE 754 binary64. Extended-precision accumulation (x87 80-bit,
FMA contraction) MUST NOT be relied upon, as it is not portable.

### 3.2 Summation

Where this specification requires a sum over a loss column, implementations MUST
use **Neumaier compensated summation**:

```
total = 0, comp = 0
for each x:
    t = total + x
    comp += (|total| >= |x|) ? (total - t) + x
                             : (x - t) + total
    total = t
return total + comp
```

Neumaier's variant is required, not classic Kahan: the correction term is
selected on the relative magnitude of accumulator and addend, which keeps it
correct when a single large loss year exceeds the running total — the
characteristic shape of a catastrophe YLT.

Implementations MUST NOT substitute a naive accumulation. On the v1.0 reference
YLT a naive left fold lands **13.4 ulp** from the exact mean; naive accumulation
over the same data sorted ascending lands 2.4 ulp away. Pairwise summation
(NumPy's `sum`, Julia's `Base.sum`) happens to agree with the exact result on
this input, but agreement by coincidence is not conformance.

> **Rationale.** Summation order is the single most common source of
> irreproducibility between implementations of the same loss calculation, and it
> is invisible in code review. Fixing the convention at the base of the
> specification means every later section inherits a reproducible total.
> See ADR-0001.

### 3.3 Ordering

Where this specification requires a sort, the sort MUST be stable and ties MUST
be broken by ascending row index of the input table. (Reserved for v1.1;
no cases at v1.0.)

### 3.4 Quantiles

Reserved for v1.1. Implementations MUST NOT assume a default; the convention
will be named explicitly. See ADR-0002 for the choice under consideration
(R-7 / linear interpolation, matching `PERCENTILE.INC` and NumPy's default).

## 4. Operations

### 4.1 Expected loss

Given a YLT column of losses `L` of length *m*, and a declared simulation length
`n`:

```
EL = compensated_sum(L) / n
```

`n` MUST be taken from the case's `operation.n_years` and MUST NOT be inferred
from the row count. For a YLT the two coincide, and implementations SHOULD
assert that they do; for an ELT (v1.1) they do not.

`n` MUST be positive. Implementations MUST signal an error rather than returning
a non-finite value.

---

## 5. Reserved

Sections 5.1–5.9 are reserved for layer mechanics (attachment, exhaustion,
franchise, aggregate deductible, reinstatements, indexation, hours clause) at
v1.1 and later.

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
implementation in this repository. For v1.0 the losses are quantised to cents,
so the sum is an exact integer and the mean is an exact decimal; the golden
value is obtained by integer arithmetic (`tools/generate_data.py`). No
floating-point summation participates in its derivation.

> This is the rule that keeps the repository a specification rather than a
> reference implementation with ports. If expected outputs were generated by the
> Python implementation, a bug in Python would silently become the standard.

### 6.2 Implementation independence

Implementations MUST NOT depend on one another, directly or transitively. They
share the corpus and nothing else.

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

### 6.5 Versioning

Cases carry `since`. Implementations declare a target spec version. Adding cases
at a later version MUST NOT retroactively invalidate an implementation that
conforms at an earlier one.

Changing the expected output of an existing case is a **breaking change** to the
specification and requires a major version increment. Golden values are the
compatibility surface.

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
`excel`. LibreOffice is a different implementation of Excel semantics. A claim
about Excel requires the fidelity job (§ 7.5).

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

### 7.4 Observed divergence at v1.0

Measured under LibreOffice on case `el/mean-ylt-10k`:

| strategy | ulp error |
|---|---|
| `=SUM(range)/n` | 0 |
| `=AVERAGE(range)` | 0 |
| Neumaier via helper columns (§ 3.2) | 0 |
| running-total helper column, taken alone | **13.4** |

`=SUM()` is not a naive left fold and is exact on this input. A **running-total
column** — the layout hand-built layer models overwhelmingly use — accumulates
the full naive error. The compensation term survives; cosmetic rounding does not
destroy it.

This is the first substantive finding of the corpus and the reason spreadsheet
implementations are in scope.

### 7.5 Fidelity

A claim that a template conforms *under Excel* requires a run on licensed Excel
via COM automation. This runs on a schedule rather than per commit, and asserts
agreement with the LibreOffice column. Divergence between the two engines is
itself a reportable finding.

---

## 8. Changelog

**1.0** — initial release. §§ 1–4.1, 6, 7. One case: `el/mean-ylt-10k`.
