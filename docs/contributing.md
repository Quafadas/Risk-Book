# Contributing

## Adding a case

1. Write the input table into `conformance/data/`.
2. Derive the golden value by a process **independent of every implementation in
   this repository** (spec § 4.1). Integer or rational arithmetic over the
   decimal text is the usual route. Do not run the Python implementation and
   record its output — that makes this a reference implementation with ports,
   not a specification.
3. Write the case JSON. `rationale` is mandatory and must say what the case is
   trying to break; six months from now the id alone will not tell you whether
   an edge case was deliberate or a typo.
4. Choose a relative tolerance (spec § 4.1). Wide enough that the difference
   between one language's standard sum and another's is not a failure, narrow
   enough that a real error still is. `el/mean-ylt-10k` uses `1e-9`: the four
   implementations sit within `5e-15` of the golden value, and dropping a single
   loss-bearing year would be `3e-7` off. The harnesses assert the second bound,
   so a tolerance that admits anything will not pass review by accident.
5. Declare it in `conformance/manifest.toml`, including any `unsupported` or
   `xfail` per implementation. A case that is neither run nor declared fails the
   build.
6. Run `just check` before `just test`.

## Changing an expected value or a tolerance

Either is a **breaking change to the specification** and needs a major version
bump (spec § 4.5). Golden values and their tolerances are the compatibility
surface. If an implementation disagrees with a golden value, the first
hypothesis is that the implementation is wrong; the second is that the spec is
ambiguous and needs a new section, not an edited number.

Widening a tolerance so that a failing implementation passes is the specific
move this rule exists to prevent. Fix the implementation, or if the tolerance
really was too tight, say so in the commit and bump the version.

## Adding an implementation

It must depend on nothing in `impl/` but the corpus (spec § 4.2). It must read
tolerances from the case file rather than hardcoding them. It keeps its own
build tool — do not attempt to unify the builds.

Use the platform's own array arithmetic (spec § 3.1). Do not hand-roll a
compensated accumulator to make your column match another implementation
exactly — the point is to show what the idiomatic code in each language does,
and the tolerance is there to absorb the difference.

## Editing an Excel template

Rebuild with `just build-excel` and commit the resulting workbook; CI fails if
the committed file does not match the builder. Reviewers read
`build_template.py`, not the zip.

`just check-excel` is the check CI runs. It compares the **formulas, cell values
and named ranges** of the committed workbook against a fresh build, and names
the first cells that differ. It deliberately does not compare the file's bytes:
an `.xlsx` is a zip of XML, and its bytes depend on the openpyxl version and on
the platform's deflate implementation, so a byte comparison reports differences
that have nothing to do with the workbook. Formatting — fonts, fills, column
widths — is cosmetic and is not compared either.

Named-range addresses are derived from the layout at build time. Never hardcode
them: a hardcoded address that drifts out of step produces a silently wrong
answer rather than an error. This has already happened once during development
and was caught only because a self-reference made LibreOffice emit `#VALUE!` —
had it landed on a merely wrong cell, the workbook would have recalculated
cleanly and reported a plausible number.

## Numerical discipline

Measure before hypothesising. Any claim in the spec or docs about how a method
behaves should be backed by a number produced by `tools/` or by a test, not by
reasoning about the code.
