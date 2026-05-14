---
name: run-pylint
description: Run pylint on the Israeli supermarket parsers repo, locally or via Docker. Use when checking lint, running pylint, fixing lint errors, or mirroring the pylint CI step.
---

# Run pylint

## Fast path (use first)

```bash
pylint $(git ls-files '*.py') --disable=E0401,R0801,R0903,W0707,R0917,R0913 2>&1 | tee temp/pylint-run.txt
```

Disabled codes match `.github/workflows/pylint.yml` exactly.

---

## Docker path (mirrors `.github/workflows/pylint.yml`)

```bash
docker build -t erlichsefi/israeli-supermarket-parsers:lint --target lint .
mkdir -p temp
docker run --rm -v ./temp:/usr/src/app/temp erlichsefi/israeli-supermarket-parsers:lint 2>&1 | tee temp/pylint-run.txt
```

---

## Reading failures

Pylint output format: `module/file.py:line:col: Cxxx message`

Fix the flagged code, then re-run. The `ReadLints` tool also surfaces these inline after any edit.
