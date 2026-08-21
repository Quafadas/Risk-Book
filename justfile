# Task runner for a deliberately non-unified polyglot build.
# Each implementation keeps its own toolchain; this file is the only glue.

default: check test

# Corpus integrity gate -- run before anything else.
check:
    python3 tools/check_corpus.py
    python3 tools/check_independence.py

test: test-python test-scala test-julia test-excel

test-python:
    uv run --project impl/python pytest impl/python/tests -q

test-scala:
    cd impl/scala && ./mill test

test-julia:
    julia --project=impl/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'

test-excel: build-excel
    uv run --project impl/excel python impl/excel/runner.py

# The workbook is a build artifact of build_template.py, but it is committed --
# CI checks the two agree (spec SS 7.1).
build-excel:
    uv run --project impl/excel python impl/excel/build_template.py

# Regenerate the corpus and its golden values. Changing expected output is a
# breaking change to the spec (SS 6.5).
regen:
    python3 tools/generate_data.py

scorecard:
    python3 tools/scorecard.py

docs: scorecard
    mkdocs serve
