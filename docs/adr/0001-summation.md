# ADR-0001: Summation convention

**Status:** accepted (spec v1.0) · **Spec:** § 3.2

## Context

Every calculation in this specification reduces a loss column to a total at some
point. Floating-point addition is not associative, so the order of accumulation
changes the result. The divergence is small, invisible in code review, and
compounds through anything built on top of it.

Measured on the v1.0 reference YLT (10,000 years), against the exact mean derived
by integer arithmetic:

| method | error |
|---|---|
| naive left fold | 13.4 ulp |
| naive fold, sorted ascending | 2.4 ulp |
| pairwise (NumPy, `Base.sum`) | exact |
| Kahan / Neumaier | exact |
| `math.fsum` | exact |

The candidates were: leave it unspecified and set a loose tolerance; mandate
pairwise; mandate compensated summation; or mandate exact rational arithmetic.

## Decision

Mandate **Neumaier compensated summation**, with a tolerance of **0 ulp**.

Neumaier rather than classic Kahan because the correction term is selected on the
relative magnitude of accumulator and addend. Kahan's variant loses the
correction when a single addend exceeds the running total — which is exactly what
a large loss year is.

## Consequences

**Accepted.** Roughly ten lines of explicit code in each implementation instead
of a one-line call to a standard library sum. Some loss of throughput relative to
a vectorised sum; irrelevant at corpus scale, potentially relevant at production
scale, where an implementation may use a faster method provided it still passes.

**Gained.** A zero-ulp tolerance, which means the corpus can distinguish a real
disagreement from noise. Under a loose tolerance every method above passes and
the case tests nothing.

**Rejected — mandate pairwise.** It is exact on this input, but the result
depends on the blocking factor, which is a library implementation detail, not a
specification. Three languages would agree by coincidence rather than by
construction, and the coincidence would break silently on a different input.

**Rejected — exact rational arithmetic.** Correct and unimplementable in Excel.
Excel is in scope precisely because it is what counterparties use.

**Note.** Julia's `Base.sum` and LibreOffice's `=SUM()` both hit the golden value
here. Neither is thereby conformant: § 3.2 requires the method, not the answer.
The Julia test suite records this coincidence explicitly so that a future
divergence is read as expected rather than as a regression.

## Revisiting

If a future case shows Neumaier itself diverging from the exact result — likely
once catastrophic single-event losses sit alongside near-zero attritional years
across many more simulation years — the options are exact accumulation into a
wide integer, or a per-case tolerance above zero. Prefer the former; a nonzero
tolerance on a deterministic calculation is a standing invitation to drift.
