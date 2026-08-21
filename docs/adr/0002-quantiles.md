# ADR-0002: Quantile convention

**Status:** proposed · **Spec:** § 3.4 (reserved for v1.1)

## Context

Return-period losses are quantiles of a finite sample, and there are nine
recognised sample-quantile definitions (Hyndman & Fan). Defaults differ across
the implementations in scope:

| environment | default |
|---|---|
| NumPy `quantile` | linear interpolation (R-7) |
| Julia `Statistics.quantile` | R-7 |
| R `quantile` | R-7 |
| Excel `PERCENTILE.INC` | R-7 |
| Excel `PERCENTILE.EXC` | R-6 |
| various vendor tools | frequently order-statistic, no interpolation |

At a 1-in-250 return period on a 10,000-year simulation the quantile falls at
index 40 of the sorted losses. R-7 and R-6 differ there by an amount that is
small relative to the loss but not relative to a spread quoted in basis points.
Some ILS practice uses no interpolation at all and takes the 40th largest loss
directly, which is a third answer.

## Decision (proposed)

Mandate **R-7 / linear interpolation**, matching `PERCENTILE.INC` and the NumPy
and Julia defaults.

Additionally: require at least one case where R-6, R-7 and the plain order
statistic give three visibly different answers, so the corpus documents the size
of the disagreement rather than merely picking a side.

## Consequences

**Accepted.** R-7 is not what every vendor tool does, so conformant output will
differ from some commercial software. That difference becomes documented and
reproducible instead of mysterious — which is the more useful outcome, and
arguably the main deliverable of this repository for a practitioner audience.

**Excel.** Templates must use `PERCENTILE.INC` explicitly. `PERCENTILE` without
a suffix is the deprecated alias and must not be used, as its behaviour is
version-dependent.

**Open.** Whether the tail should instead be specified as an order statistic with
no interpolation, on the grounds that interpolating between two simulated years
invents a loss that no simulated year produced. This is a real argument and it
has not been settled. Resolve before v1.1 ships.
