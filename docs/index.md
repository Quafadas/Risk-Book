# ILS Risk Conformance Suite

A language-neutral **specification** and **test corpus** for insurance-linked
securities risk calculations, with independent implementations in Python, Scala,
Julia and Excel.

The specification is the product. The implementations are evidence that it is
implementable, and the disagreements between them are the findings.

## Why

Two desks can compute the same expected loss from the same loss table and get
different numbers. Usually the cause is not a modelling disagreement but an
unstated convention — summation order, quantile interpolation, tie-breaking,
whether a running total is carried down a column. These are invisible in code
review and rarely written down.

This repository writes them down, and then tests four independent
implementations against them.

## The first finding

Case `el/mean-ylt-10k` reduces a 10,000-year loss table to a single number.
Measured against the exact mean, derived by integer arithmetic:

| method | error |
|---|---|
| Neumaier compensated summation (spec § 3.2) | exact |
| pairwise summation (NumPy, `Base.sum`) | exact *on this input* |
| `=SUM(range)` in LibreOffice | exact |
| **naive left fold** (Scala `Array.sum`, a `for` loop) | **13.4 ulp** |
| naive fold, input sorted ascending | 2.4 ulp |
| **running-total column in a spreadsheet** | **13.4 ulp** |

The last row is the one that matters in practice. `=SUM()` is well-behaved, but
hand-built layer models overwhelmingly carry a running total down a helper
column — and that accumulates the full naive error. At 10,000 years the
divergence is in the twelfth significant figure and nobody notices. The
mechanism does not improve with more years.

See [Results](results.md) for the current scorecard.

## Scope

In scope: the deterministic contract mechanics — layer attachment and
exhaustion, franchise and aggregate deductibles, reinstatements and
reinstatement premium, indexation, hours clauses, and EP curve construction from
a fixed ELT or YLT. All pure functions of tabular input.

Out of scope: catastrophe model construction, hazard simulation, vendor model
calibration.

At v1.0 only expected loss is specified. The scope above is the roadmap, not the
current contents.

## Structure

```
spec/spec.md          normative specification -- section numbers are a public API
conformance/cases/    the corpus: one JSON file per case
conformance/data/     input tables, digest-pinned
conformance/manifest.toml   tiers, capabilities, xfails
impl/python/          reference implementation (uv)
impl/scala/           independent implementation (Mill)
impl/julia/           independent implementation (Pkg)
impl/excel/           template workbooks + harness
tools/                corpus checks, golden-value derivation, scorecard
```
