---
name: run-pytest
description: Run the pytest suite for the Israeli supermarket parsers repo, locally or via Docker. Use when running tests, checking test output, or verifying a specific chain passes. Covers fast path and Docker path. For exhaustive parse completeness, use is-parsing-complete instead of NUM_SAMPLES=None.
---

# Run pytest

## Fast path (use first)

```bash
mkdir -p temp
python -m pytest il_supermarket_parsers/parsers/tests/test_all.py -vv -n auto 2>&1 | tee temp/pytest-run.txt
```

- `-n auto` — pytest-xdist picks worker count from `os.cpu_count()`.
- Output lands in `temp/` (same mount CI uses).

### Run a single chain

```bash
python -m pytest il_supermarket_parsers/parsers/tests/test_all.py -vv -k "<ChainName>" 2>&1 | tee temp/pytest-run.txt
```

---

## Docker path (use when fast path passes but CI still fails)

Mirrors `.github/workflows/test-suite.yml` exactly:

```bash
docker build -t erlichsefi/israeli-supermarket-parsers:test --target test .
mkdir -p temp
docker run --rm -v ./temp:/usr/src/app/temp erlichsefi/israeli-supermarket-parsers:test 2>&1 | tee temp/pytest-run.txt
```

Inside the image, `CMD` uses `-n 2`; only the local fast path above uses `-n auto`.

---

## Exhaustive mode (new source or uncertain parser)

Pytest PASS with `NUM_SAMPLES=10` is **not** proof every file parses. A SKIPPED live-source test validated nothing.

Do **not** patch `test_case.py` to set `limit = None` (that times out CI if committed). Use
[is-parsing-complete](../is-parsing-complete/SKILL.md)
(`scripts/validate_parsing.py`): fresh dump dir, all files, **stops on the first parse or validation failure**.

```bash
python scripts/validate_parsing.py --parsers <ChainName>
python scripts/validate_parsing.py --parsers <ChainName> --limit 1
```

---

## Scan for failures

```bash
grep -E "^FAILED|ERROR" temp/pytest-run.txt
```

Each failure line: `FAILED test_all.py::ChainTestCase::test_name`.
