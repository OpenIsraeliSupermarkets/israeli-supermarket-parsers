#!/usr/bin/env bash
# Scrape every chain, then parse and verify each file. Run from the repo root.
#   scripts/live_scrape_verify.sh [NUM_SAMPLES] [extra pytest args, e.g. -k Shufersal]
# NUM_SAMPLES = files per chain and file type (default: all of them).
# SKIPPED tests (-rs) downloaded nothing, so they were not verified.
NUM_SAMPLES="${1:-all}"; [ "$#" -gt 0 ] && shift
[ "$NUM_SAMPLES" = all ] && NUM_SAMPLES=1000000
NUM_SAMPLES="$NUM_SAMPLES" python -m pytest il_supermarket_parsers/parsers/tests/test_all.py \
  -n 4 -q -rfs --tb=short "$@"
