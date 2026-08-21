# Contributing

## Adding a case

1. Write the input table into `conformance/data/`.
2. Derive the golden value by a process **independent of every implementation in
   this repository** (spec § 6.1). Integer or rational arithmetic over the
   decimal text is the usual route. Do not run the Python implementation and
   record its output — that makes this a reference implementation with ports,
   not a specification.
3. Write the case JSON. `rationale` is mandatory and must say what the case is
   trying to break; six months from now the id alone will not tell you whether
   an edge case was deliberate or a typo.
4. Declare it in `conformance/manifest.toml`, including any `unsupported` or
   `xfail` per implementation. A case that is neither run nor declared fails the
   build.
5. Run `just check` before `just test`.

## Changing an expected value

This is a **breaking change to the specification** and needs a major version
bump (spec § 6.5). Golden values are the compatibility surface. If an
implementation disagrees with a golden value, the first hypothesis is that the
implementation is wrong; the second is that the spec is ambiguous and needs a
new section, not an edited number.

## Adding an implementation

It must depend on nothing in `impl/` but the corpus (spec § 6.2). It must read
tolerances from the case file rather than hardcoding them. It keeps its own
build tool — do not attempt to unify the builds.

## Editing an Excel template

Rebuild with `just build-excel` and commit the resulting workbook; CI fails if
the committed file does not match the builder. Reviewers read
`build_template.py`, not the zip.

Named-range addresses are derived from the layout at build time. Never hardcode
them: a hardcoded address that drifts out of step produces a silently wrong
answer rather than an error. This has already happened once during development
and was caught only because a self-reference made LibreOffice emit `#VALUE!` —
had it landed on a merely wrong cell, the workbook would have recalculated
cleanly and reported a plausible number.

## Numerical discipline

Measure before hypothesising. Every claim in the spec about how a method behaves
is backed by a number produced by `tools/`, not by reasoning about the code.
