# ILS Risk Conformance Suite

A language-neutral **specification** and **test corpus** for insurance-linked
securities risk calculations, with independent implementations in Python, Scala,
Julia and Excel.

The specification is the product. The implementations are evidence that it is
implementable in each language and should provide some sense of the relative readability of each..

## Why

Two desks can compute the same expected loss from the same loss table and get
different numbers. Usually the cause is not a modelling disagreement but an
unstated convention — summation order, quantile interpolation, tie-breaking,
whether a running total is carried down a column. These are invisible in code
review and rarely written down.

This repository writes them down, and then tests four independent
implementations against them.

Each implementation uses its own language's standard arithmetic, so the four do
not produce byte-identical answers. Each case declares a relative tolerance wide
enough to cover that and narrow enough to catch a real error, and every
implementation is measured against an independently derived golden value rather
than against the others.

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
impl/python/          reference implementation (python / uv)
impl/scala/           independent implementation (scala / Mill)
impl/julia/           independent implementation (Julia / Pkg)
impl/excel/           template workbooks + harness
tools/                corpus checks, golden-value derivation, scorecard
```
