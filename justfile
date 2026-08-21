# Task runner for a deliberately non-unified polyglot build.
# Each implementation keeps its own toolchain; this file is the only glue.

MILL_VERSION := "1.1.8"

default: check test

# Corpus integrity gate -- run before anything else.
check:
    python3 tools/check_corpus.py
    python3 tools/check_independence.py

test: test-python test-scala test-julia test-excel

test-python:
    uv run --project impl/python pytest impl/python/tests -q

test-scala: bootstrap-scala
    cd impl/scala && ./mill test

test-julia:
    julia --project=impl/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'

test-excel: build-excel
    uv run --project impl/excel python impl/excel/runner.py

# Mill ships as a per-version launcher script, which is gitignored rather than
# committed. Version must match the //| mill-version: header in build.mill and
# the bootstrap step in .github/workflows/ci.yml.
bootstrap-scala:
    #!/usr/bin/env bash
    set -euo pipefail
    cd impl/scala
    if [ ! -x mill ]; then
        curl -fsSL -o mill \
          "https://repo1.maven.org/maven2/com/lihaoyi/mill-dist/{{MILL_VERSION}}/mill-dist-{{MILL_VERSION}}-mill.sh"
        chmod +x mill
    fi

# The workbook is a build artifact of build_template.py, but it is committed --
# CI checks the two agree (spec SS 7.1). The build is byte-reproducible, so a
# rebuild on an unchanged corpus leaves the worktree clean.
build-excel:
    uv run --project impl/excel python impl/excel/build_template.py

# Regenerate the corpus and its golden values. Changing expected output, or
# widening a tolerance, is a breaking change to the spec (SS 6.5).
regen:
    uv run --with numpy python tools/generate_data.py

scorecard:
    python3 tools/scorecard.py

docs: scorecard
    mkdocs serve
