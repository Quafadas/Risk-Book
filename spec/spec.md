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
loss tables, together with a corpus of test cases and expected results over some
common risk metrics. An implementation conforms at version *v* if it produces
every expected result, within the declared tolerance, for every case marked
`since <= v` that it does not declare unsupported.

The specification covers the **contract mechanics** of ILS risk measurement —
the parts that are arithmetic on a table, where two correct implementations
should agree. It does not cover catastrophe model construction, hazard
simulation or vendor model calibration.

At v1.0 only expected loss is specified. The remaining mechanics — layer
attachment and exhaustion, franchise and aggregate deductibles, reinstatements,
indexation, hours clauses, EP curves — are the roadmap, not the contents.

## 2. Definitions

**Year Loss Table (YLT)** — a table of simulated years, each carrying the total
loss to the subject portfolio in that year. Years with no loss are present with
a loss of zero. The number of rows is the simulation length.

e.g.

| Year | Loss |
| --- | --- |
| 1 | 10 |
| 2 | 0 |
| 3 | 20 |

**Event Loss Table (ELT)** — a table of events, each carrying a loss. Years with
no loss are *not* represented, so the year count is a separate parameter.
(Reserved for v1.1; no cases at v1.0.)

| Year | Day | Loss |
| --- | --- | --- |
| 1 | 1 | 10 |
| 3 | 1 | 20 |
| 3 | 2 | 20 |

**Expected Loss (EL)** — the expected annual loss to the subject portfolio,
expressed in the currency and scale declared by the case input.

## 3. Numeric conventions

### 3.1 Input encoding

Loss values MUST be transported as decimal text. Every value in the corpus is
quantised to two decimal places, so each is exactly representable as a decimal
and every conforming parser recovers the same value.

Implementations SHOULD parse with their standard library's
decimal-to-floating-point routine. All arithmetic is IEEE 754 binary64.

### 3.2 Summation

Where this specification requires a sum over a loss column, implementations
SHOULD use the standard summation facility of their language or platform —
`sum` in Python and Julia, `.sum` in Scala, `=SUM(range)` in a spreadsheet. No
accumulation order is mandated.

Floating-point addition is not associative, so implementations will not agree to
the last bit. Each case declares a tolerance (§ 6.1) wide enough to cover that
and narrow enough to catch a real error. Implementations are compared against
the golden value, never against each other.

### 3.3 Ordering

Where this specification requires a sort, the sort MUST be stable and ties MUST
be broken by ascending row index of the input table. (Reserved for v1.1;
no cases at v1.0.)

### 3.4 Quantiles

Reserved for v1.1. Implementations MUST NOT assume a default; the convention
will be named explicitly. The candidate is R-7 / linear interpolation, which
matches `PERCENTILE.INC` and the NumPy and Julia defaults. Excel's
`PERCENTILE.EXC` is R-6 and gives a different answer; some vendor tools use no
interpolation at all and take the order statistic directly, giving a third.

## 4. Operations

### 4.1 Expected loss

Given a YLT column of losses `L`, and a declared number of simulation
periods `n`:

```
EL = sum(L) / n
```

where `sum` is a standard summation per § 3.2.

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

### 6.1 Golden values and tolerance

Each case declares its expected result as `exact_decimal`: the mathematically
exact value, as decimal text. Implementations parse it with their standard
decimal-to-binary64 routine (§ 3.1).

Each case also declares a **relative tolerance**. An implementation conforms on
a case when

```
|actual - expected| / |expected| <= tolerance.rel
```

The tolerance lives in the case data and MUST NOT be held by an implementation:
no implementation gets its own view of "close enough". It is set when the case is
authored, wide enough to cover the difference between one standard summation and
another, and narrow enough that a genuine error — the wrong column, an
off-by-one on the row range — still fails.

Golden values MUST be derived by a documented process that is independent of any
implementation in this repository. For v1.0 the losses are quantised to cents,
so the sum is an exact integer and the mean an exact decimal; the golden value is
obtained by integer arithmetic (`tools/generate_data.py`).

> This is the rule that keeps the repository a specification rather than a
> reference implementation with ports. If expected outputs were generated by the
> Python implementation, a bug in Python would silently become the standard.

### 6.2 Implementation independence

Implementations MUST NOT depend on one another, directly or transitively. They
share the test corpus and nothing else.

This constrains harnesses as well as libraries. The Excel harness is written in
Python; it MUST NOT import from `impl/python`. CI enforces this
(`tools/check_independence.py`).

### 6.3 Result envelope

A black-box runner MUST emit, for each case, a JSON object of the form:

```json
{
  "case": "el/mean-ylt-10k",
  "impl": "python",
  "spec_version": "1.0",
  "value": 5493015.493994
}
```

A runner invoked over several cases MUST emit a JSON array of such objects. A
runner MAY add further keys; consumers MUST ignore keys they do not recognise.

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

Changing the expected output of an existing case, or widening its tolerance, is
a **breaking change** to the specification and requires a major version
increment. Golden values and their tolerances are the compatibility surface.

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

Results obtained under LibreOffice MUST be reported with `engine` set to
`libreoffice`. LibreOffice is a different implementation of Excel semantics; a
claim about Excel requires a run on licensed Excel.

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

A template MAY compute the same quantity more than one way and report each
result, where the alternatives are what practitioners actually build. The v1.0
template reports `=SUM(range)/n`, `=AVERAGE(range)`, and a running total carried
down a helper column. The first is the value under test; the others are reported
so that a reader can see whether the layout they use agrees.

---

## 8. Changelog

**1.0** — initial release. §§ 1–4.1, 6, 7. One case: `el/mean-ylt-10k`.
