---
name: is-parsing-complete
description: Parse every downloaded Israeli supermarket XML file and stop on the first parse or validation failure. Second-tier check after run-pytest (sampled live tests). Use when verifying files actually parse, diagnosing XML shape drift, list_key/id_field mismatches, or after a pytest PASS/SKIP.
disable-model-invocation: true
---

# Parse / Validate Supermarket Files

## Core principle

**Pytest sampling ≠ parse completeness.**

`run-pytest` downloads **10 files per type** (`NUM_SAMPLES=10`). A SKIPPED live-source test validated nothing (source unreachable / bot-protected).

This skill downloads into a **fresh dump dir** and runs `parser.read()` + `run_validation()` on each file. Expectation:

every readable file **parses and matches the XML** (row counts, id field, roots, unused keys)

Stop at the **first** parse or validation failure. Do not keep parsing the rest of the chain.

**Exception — empty files:** `is_expected_to_be_readable=False` (zero-byte) is skipped (`skipped_empty`) and does not fail-fast. Tiny files that are not expected to have records must parse to **zero rows**.

## When to use

| Use this skill | Use `run-pytest` / `fix-supermarket-parser` instead |
|---|---|
| Prove every file (or every type) parses | Fast sampled CI (`NUM_SAMPLES=10`) |
| `columns chainid missing`, `id missing`, element count mismatch | Diagnose and patch `parsers/<chain>.py` |
| After pytest PASS/SKIP, prove files parse | Unit/offline layout tests |
| Exhaustive check without patching `test_case.py` `limit = None` | Never commit `limit = None` |

Run pytest first when both matter. A pytest PASS with a parse FAIL is still a real bug. A SKIPPED pytest is **not** a PASS.

## Do not confuse with sampled CI

CI and `run-pytest` cap downloads at 10 files. That skip is **by design** — not proof the rest parse.

This check uses a **fresh dump dir** and a scraper status path inside that dir, so daily-publish / leftover `status_logs` cannot hide missing files. Do **not** reuse a production dump or status JSON.

Do **not** patch `il_supermarket_parsers/parsers/tests/test_case.py` to set `limit = None`. Use this helper instead.

## Agent workflow

1. Resolve `ParserFactory` names (user list, or one sample per engine).
2. Run the helper (it instantiates via `ParserFactory.<NAME>.value`; scrape uses the matching `ScraperFactory` name):

```bash
python scripts/validate_parsing.py --parsers SHUFERSAL
python scripts/validate_parsing.py --parsers SHUFERSAL,VICTORY_NEW_SOURCE
python scripts/validate_parsing.py --per-engine
python scripts/validate_parsing.py --all-listed --output scripts/validation_parsing.json
```

3. Default is **all files, all types**, fail-fast. File types run small-first (`STORE`, `PRICE`, `PROMO`, then `*_FULL`). Use `--limit N` or `--file-types PRICE_FILE` only when the user asks for a cheaper smoke.
4. On **FAIL**: record `failed_file`, `failed_file_type`, `error`, how many succeeded before the stop. Stay on that chain; follow **fix-supermarket-parser** (inspect the XML, fix converter config, keep the old shape).
5. On **PASS**: `failed=0` and `parsed > 0` (optional `skipped_empty > 0` is OK).

## Checklist

- [ ] Fresh dump dir (no leftover `status_logs` skip)
- [ ] Real `parser.read()` + `run_validation()` (not pytest sample-only)
- [ ] Stopped on first parse/validation failure (empty-file skips continue)
- [ ] `parsed > 0` and `failed == 0` (PASS)
- [ ] First failure includes filename + file type + error (FAIL)

## Common issues

| Symptom | Likely cause |
|---|---|
| `columns chainid missing` / empty DataFrame | Wrong `list_key` — see fix-supermarket-parser |
| `id <x> missing from <columns>` | Wrong `id_field` |
| `element count mismatch` | Need `SubRootedXmlDataFrameConverter` or ignore wrapper |
| First file fails, rest not tried | Expected — fail-fast |
| `skipped_empty` | Zero-byte dump; not a parser bug |
| `no files parsed` | Scrape returned nothing; geo / source down — not a silent PASS |
| Pytest SKIPPED, this FAIL | Source reachable now, or XML drifted — treat as a real parser bug |
| Pytest PASS, this FAIL | Sample of 10 missed the bad file/type |
