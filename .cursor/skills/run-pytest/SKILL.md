---
name: run-pytest
description: Run the pytest suite for the Israeli supermarket parsers repo, locally or via Docker. Use when running tests, checking test output, or verifying a specific chain passes. Covers fast path, Docker path, and exhaustive (unlimited samples) mode.
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

By default each test downloads **10 sample files** (`NUM_SAMPLES=10`). To fetch every file from a source, temporarily patch `il_supermarket_parsers/parsers/tests/test_case.py` lines 106-109:

**Before:**
```python
try:
    self.limit = int(os.environ.get("NUM_SAMPLES", 10))
except ValueError:
    self.limit = 10
```

**After:**
```python
self.limit = None
```

Then run only the affected chain:

```bash
python -m pytest il_supermarket_parsers/parsers/tests/test_all.py -vv -k "<ChainName>" 2>&1 | tee temp/pytest-run-full.txt
```

**Revert before committing** — `limit = None` causes CI to download unbounded data and time out.

---

## Scan for failures

```bash
grep -E "^FAILED|ERROR" temp/pytest-run.txt
```

Each failure line: `FAILED test_all.py::ChainTestCase::test_name`.
