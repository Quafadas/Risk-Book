# Glossary

Domain terms as this specification uses them, with the common alternative
readings noted. Where practitioners disagree, the disagreement is recorded
rather than resolved — that is the point of the corpus.

**Attachment point** — the loss level at which a layer begins to respond. Stated
either as ground-up loss or as loss net of underlying recoveries; the two differ
whenever inuring reinsurance is present. This specification will state which
basis each case uses (v1.1).

**Aggregate deductible (AAD)** — a retention applied to the sum of losses across
the period, as distinct from a per-occurrence deductible. Order of application
against per-occurrence terms is a live source of disagreement.

**Event Loss Table (ELT)** — events with losses and annual rates. Zero-loss years
are not represented, so the year count is a separate parameter. Contrast YLT.

**Expected loss (EL)** — the expected annual loss. In cat bond pricing "expected
loss" often means the expected loss *to the notes* expressed as a percentage of
principal, which is a different quantity from the expected loss to the subject
portfolio. This specification means the latter unless a case says otherwise.

**Exceedance probability (EP) curve** — the probability that loss exceeds a
given level. **OEP** is occurrence-based (largest single event in a year);
**AEP** is aggregate (total across the year). Conflating them is common and
material in the tail.

**Franchise deductible** — a threshold below which nothing is paid and above
which the loss is paid *in full*, as opposed to an ordinary deductible which is
subtracted. The discontinuity at the threshold is a natural test case.

**Hours clause** — the window within which losses are treated as one occurrence
(commonly 72 hours for windstorm, 168 for some perils). Implementations differ on
whether the window is anchored to the first loss, chosen to maximise recovery, or
selected by the cedent — a genuine commercial ambiguity, not a rounding question.

**Indexation clause** — adjusts attachment and limit by an inflation index. Some
formulations are circular (the indexed loss depends on the index, which depends
on the loss), which is why Excel needs iterative calculation enabled to model
them and code implementations need a defined fixed point.

**Reinstatement** — restoration of limit after a loss, usually for an additional
premium. "Pro rata as to time and amount" is standard wording and admits more
than one arithmetic reading, particularly on partial reinstatements straddling a
period boundary.

**Return period** — the reciprocal of an annual exceedance probability. A
"1-in-250 year loss" is the loss with a 0.4% annual exceedance probability. On a
finite simulation the value depends on the quantile convention (not yet
specified; reserved for v1.1), and at 10,000 years the 1-in-250 sits at index 40 — close
enough to the tail that interpolation choices are visible.

**Year Loss Table (YLT)** — simulated years, each carrying total loss to the
subject portfolio. Zero-loss years are present with a loss of zero, so the row
count equals the simulation length.
