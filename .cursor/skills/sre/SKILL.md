---
name: sre
description: Run CI tests locally for the Israeli supermarket parsers repo and fix any failures. Use when the user asks to run CI, run tests, check if tests pass, fix CI failures, or fix broken tests in this repo.
---

# Run CI and Fix

CI runs pytest inside Docker (`--target test`). Mirror that locally, then fix any failures using the parser-fix workflow.

## Workflow

```
- [ ] 1. Run tests (fast path or Docker)
- [ ] 2. Identify failing tests from output
- [ ] 3. Fix each failure (see fix-supermarket-parser skill)
- [ ] 4. Re-run until all pass
```

---

## Step 1: Run tests

**Fast path (no Docker — use this first):**

Parallelism: use `-n auto` so pytest-xdist picks a worker count from the host (`os.cpu_count()`). Override with `-n N` if you need a fixed number.

Log path: write under the repo’s `temp/` directory (same as CI’s `./temp` mount), not a hardcoded `/tmp`, so paths work across machines and sandboxes.

```bash
mkdir -p temp
python -m pytest il_supermarket_parsers/parsers/tests/test_all.py -vv -n auto 2>&1 | tee temp/pytest-run.txt
```

**Exact CI path (Docker — use when fast path passes but CI still fails):**

```bash
docker build -t erlichsefi/israeli-supermarket-parsers:test --target test .
mkdir -p temp
docker run --rm -v ./temp:/usr/src/app/temp erlichsefi/israeli-supermarket-parsers:test 2>&1 | tee temp/pytest-run.txt
```

The Docker run command matches exactly what `.github/workflows/test-suite.yml` does.

Inside the image, `Dockerfile` `CMD` still runs pytest with `-n 2`; only the **local fast path** above uses `-n auto` to match your machine.

---

## Step 1b: Run pylint (mirrors `.github/workflows/pylint.yml`)

**Fast path:**

```bash
pylint $(git ls-files '*.py') --disable=E0401,R0801,R0903,W0707,R0917,R0913 2>&1 | tee /tmp/pylint-run.txt
```

**Exact CI path (Docker `lint` target):**

```bash
docker build -t erlichsefi/israeli-supermarket-parsers:lint --target lint .
mkdir -p temp
docker run --rm -v ./temp:/usr/src/app/temp erlichsefi/israeli-supermarket-parsers:lint 2>&1 | tee /tmp/pylint-run.txt
```

Pylint failures show as `your-module/file.py:line:col: Cxxx message`. Fix the flagged code, then re-run. The `ReadLints` tool also surfaces these after any edit.

---

## Step 2: Identify failures

Scan the output for `FAILED` lines:

```bash
grep -E "^FAILED|ERROR" temp/pytest-run.txt
```

Each line is in the form `FAILED test_all.py::ChainTestCase::test_name`.

---

## Step 3: Fix failures

For each failing test, apply the **fix-supermarket-parser** skill (`.cursor/skills/fix-supermarket-parser/SKILL.md`).

Quick summary of that workflow:
1. Run the single failing test to capture the error + the downloaded XML path.
2. Inspect the XML to find `list_key`, `id_field`, `roots`.
3. Update **only** `il_supermarket_parsers/parsers/<chain>.py`.
4. Re-run the single test, then the full chain test class.

Common error → fix mapping:

| Error | Fix |
|-------|-----|
| `columns chainid missing` + empty DataFrame | Wrong `list_key` |
| `id <x> missing from <columns>` | Wrong `id_field` |
| `element count mismatch` | Use `SubRootedXmlDataFrameConverter` or add wrapper to `ignore_column` |
| `list_key element was not found` | `list_key` tag absent; check XML for the actual wrapper tag |

---

## Step 4: Verify

After all individual fixes:

```bash
python -m pytest il_supermarket_parsers/parsers/tests/test_all.py -vv -n auto
```

All tests must pass before the work is done. Run `ReadLints` on every edited `parsers/<chain>.py`.
