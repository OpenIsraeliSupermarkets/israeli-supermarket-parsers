#!/usr/bin/env python3
"""Fail-fast parse check: download then parse files until the first failure.

Expectation: every readable dump file parses and passes ``run_validation``.
Stops scheduling more files after the first parse or validation error.

Uses a fresh dump dir and scraper status path inside that dir, so leftover
``status_logs`` / daily-publish state cannot hide missing files.

Examples:
  python scripts/validate_parsing.py --parsers SHUFERSAL
  python scripts/validate_parsing.py --parsers SHUFERSAL,VICTORY_NEW_SOURCE
  python scripts/validate_parsing.py --per-engine
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import logging
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Any, AsyncGenerator, Dict, List, Optional

from il_supermarket_scarper import FileTypesFilters, ScarpingTask

from il_supermarket_parsers.engines.base import BaseFileConverter
from il_supermarket_parsers.parser_factory import ParserFactory
from il_supermarket_parsers.utils import DataLoader, DumpFile, Logger
from il_supermarket_parsers.utils.validation_utils import parse_file_via_csv

# Smallest files first so a stores/price failure does not wait on PRICE_FULL.
DEFAULT_TYPE_ORDER = (
    FileTypesFilters.STORE_FILE.name,
    FileTypesFilters.PRICE_FILE.name,
    FileTypesFilters.PROMO_FILE.name,
    FileTypesFilters.PRICE_FULL_FILE.name,
    FileTypesFilters.PROMO_FULL_FILE.name,
)


def engine_name(cls) -> str:
    """Most specific converter engine in the class MRO."""
    names = {base.__name__ for base in cls.__mro__}
    if "BigIdBranchesFileConverter" in names:
        return "BigIdBranchesFileConverter"
    if "BigIDFileConverter" in names:
        return "BigIDFileConverter"
    if "BaseFileConverter" in names:
        return "BaseFileConverter"
    return cls.__name__


def listed_factory_members() -> List[str]:
    """All ParserFactory members, including deprecated ones."""
    return ParserFactory.all_parsers_name()


def resolve_parsers(args: argparse.Namespace) -> List[str]:
    """Resolve which parsers to parse-check."""
    if args.parsers:
        return [name.strip() for name in args.parsers.split(",") if name.strip()]
    if args.all_listed:
        return listed_factory_members()
    if args.per_engine:
        by_engine: Dict[str, List[str]] = defaultdict(list)
        for name in listed_factory_members():
            cls = getattr(ParserFactory, name).value
            by_engine[engine_name(cls)].append(name)
        return [names[0] for _, names in sorted(by_engine.items())]
    raise SystemExit("Specify --per-engine, --all-listed, or --parsers")


def resolve_file_types(raw: Optional[str]) -> List[str]:
    """File types in fail-fast order. Default is every FileTypesFilters member."""
    allowed = FileTypesFilters.all_types()
    if not raw:
        return [name for name in DEFAULT_TYPE_ORDER if name in allowed]
    requested = [name.strip() for name in raw.split(",") if name.strip()]
    unknown = [name for name in requested if name not in allowed]
    if unknown:
        raise SystemExit(f"Unknown file types: {unknown}. Allowed: {allowed}")
    ordered = [name for name in DEFAULT_TYPE_ORDER if name in requested]
    leftover = [name for name in requested if name not in ordered]
    return ordered + leftover


def is_parse_ok(result: Dict[str, Any]) -> bool:
    """True when the file parsed and validated."""
    return bool(result.get("parsed"))


def is_empty_skip(result: Dict[str, Any]) -> bool:
    """True when the dump is zero-byte / unreadable (not a parser bug)."""
    return bool(result.get("skipped_empty"))


def _empty_summary() -> Dict[str, Any]:
    return {
        "parsed": 0,
        "failed": 0,
        "skipped_empty": 0,
        "stopped_on_failure": False,
    }


async def consume_until_failure(
    results: AsyncGenerator[Dict[str, Any], None],
) -> Dict[str, Any]:
    """Drain parse results; stop at the first parse/validation failure.

    Zero-byte files are skipped (counted, not failed).
    """
    summary = _empty_summary()
    async for result in results:
        if is_empty_skip(result):
            summary["skipped_empty"] += 1
            continue
        if is_parse_ok(result):
            summary["parsed"] += 1
            if summary["parsed"] % 25 == 0:
                print(f"    {summary['parsed']} ok...", flush=True)
            continue
        summary["failed"] = 1
        summary["stopped_on_failure"] = True
        summary["failed_file"] = result.get("file_name")
        summary["failed_file_type"] = result.get("file_type")
        summary["error"] = result.get("error")
        break
    return summary


def _base_result(dump_file: DumpFile) -> Dict[str, Any]:
    return {
        "file_name": dump_file.file_name,
        "file_type": dump_file.detected_filetype.name,
        "parsed": False,
        "skipped_empty": False,
        "row_count": 0,
        "error": None,
    }


async def parse_file(
    parser: BaseFileConverter, dump_file: DumpFile
) -> Dict[str, Any]:
    """Parse one dump file and run XML validation when rows are expected."""
    result = _base_result(dump_file)
    if not dump_file.is_expected_to_be_readable:
        result["skipped_empty"] = True
        return result
    try:
        df, csv_created, row_count = await parse_file_via_csv(parser, dump_file)
        result["row_count"] = row_count
        if dump_file.is_expected_to_have_records:
            if not csv_created or df is None or df.shape[0] == 0:
                result["error"] = "no rows parsed"
                return result
            parser.run_validation(df, dump_file)
        elif csv_created or row_count > 0:
            result["error"] = f"expected empty data, got {row_count} rows"
            return result
        result["parsed"] = True
    except (
        OSError,
        TypeError,
        ValueError,
        RuntimeError,
        KeyError,
        AssertionError,
        ET.ParseError,
    ) as exc:
        result["error"] = str(exc)
    return result


async def iter_parse_results(
    parser: BaseFileConverter, files: List[DumpFile]
) -> AsyncGenerator[Dict[str, Any], None]:
    """Yield parse results in file order (caller stops via consume)."""
    for dump_file in files:
        yield await parse_file(parser, dump_file)


def scrape_type(
    enum_name: str,
    dump_dir: str,
    status_dir: str,
    file_type: str,
    limit: Optional[int],
) -> None:
    """Download one file type into ``dump_dir`` with a throwaway status DB."""
    task = ScarpingTask(
        enabled_scrapers=[enum_name],
        files_types=[file_type],
        multiprocessing=1,
        output_configuration={
            "output_mode": "disk",
            "base_storage_path": dump_dir,
        },
        status_configuration={"database_type": "json", "base_path": status_dir},
    )
    task.start(limit=limit, when_date=datetime.datetime.now())
    task.join()


async def load_files(
    dump_dir: str, enum_name: str, file_type: str
) -> List[DumpFile]:
    """List dump files for one parser × file type."""
    files: List[DumpFile] = []
    async for dump_file in DataLoader(folder=dump_dir).load(
        enabled_scraper=[enum_name],
        files_types=[file_type],
    ):
        files.append(dump_file)
    return files


def _merge_type_summary(total: Dict[str, Any], part: Dict[str, Any]) -> None:
    total["parsed"] += part.get("parsed") or 0
    total["skipped_empty"] += part.get("skipped_empty") or 0
    if part.get("failed"):
        total["failed"] = 1
        total["stopped_on_failure"] = True
        total["failed_file"] = part.get("failed_file")
        total["failed_file_type"] = part.get("failed_file_type")
        total["error"] = part.get("error")


async def parse_one(
    enum_name: str, limit: Optional[int], file_types: List[str]
) -> Dict[str, Any]:
    """Scrape then parse one factory member until the first failure."""
    cls = getattr(ParserFactory, enum_name, None)
    row: Dict[str, Any] = {
        "parser": enum_name,
        "engine": None,
        "class": None,
        "limit": limit,
        "file_types": file_types,
        "parsed": 0,
        "failed": 0,
        "skipped_empty": 0,
        "pass": False,
        "stopped_on_failure": False,
    }
    if cls is None:
        row["error"] = f"Unknown parser {enum_name}"
        return row
    converter_cls = cls.value
    row["engine"] = engine_name(converter_cls)
    row["class"] = converter_cls.__name__
    parser = converter_cls()
    totals = _empty_summary()
    with tempfile.TemporaryDirectory(prefix=f"parse_{enum_name}_") as tmp:
        dump_dir = os.path.join(tmp, "dumps")
        status_dir = os.path.join(tmp, "status")
        os.makedirs(dump_dir, exist_ok=True)
        os.makedirs(status_dir, exist_ok=True)
        try:
            for file_type in file_types:
                print(f"    scraping {file_type}...", flush=True)
                scrape_type(enum_name, dump_dir, status_dir, file_type, limit)
                files = await load_files(dump_dir, enum_name, file_type)
                part = await consume_until_failure(iter_parse_results(parser, files))
                _merge_type_summary(totals, part)
                if totals["failed"]:
                    break
        except Exception as exc:  # pylint: disable=broad-exception-caught
            row["error"] = str(exc)
            return row
    row.update(totals)
    if row.get("failed"):
        row["pass"] = False
    elif row["parsed"] == 0:
        row["error"] = "no files parsed"
        row["pass"] = False
    else:
        row["pass"] = True
    return row


def _quiet_logs() -> None:
    level_name = os.environ.get("VALIDATE_LOG_LEVEL", "ERROR")
    level = getattr(logging, level_name.upper(), logging.ERROR)
    logging.getLogger("mylogger").setLevel(level)
    Logger.logger.setLevel(level)


async def run(
    parsers: List[str], limit: Optional[int], file_types: List[str]
) -> List[Dict[str, Any]]:
    """Parse-check each parser and return per-chain result rows."""
    _quiet_logs()
    results = []
    for name in parsers:
        print(f"Parsing {name}...", flush=True)
        row = await parse_one(name, limit, file_types)
        status = "PASS" if row.get("pass") else "FAIL"
        extra = ""
        if row.get("failed_file"):
            extra = (
                f" file={row['failed_file']}"
                f" type={row.get('failed_file_type')}"
                f" error={row.get('error')}"
            )
        elif row.get("error"):
            extra = f" error={row['error']}"
        skipped = row.get("skipped_empty") or 0
        skipped_extra = f" skipped_empty={skipped}" if skipped else ""
        print(
            f"  {status} engine={row.get('engine')} "
            f"parsed={row.get('parsed')} failed={row.get('failed')}"
            f"{skipped_extra}{extra}",
            flush=True,
        )
        results.append(row)
    return results


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for fail-fast parse validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--per-engine",
        action="store_true",
        help="One sample parser per converter engine (includes deprecated)",
    )
    group.add_argument(
        "--all-listed",
        action="store_true",
        help="Every ParserFactory member",
    )
    group.add_argument(
        "--parsers",
        help="Comma-separated ParserFactory names",
    )
    parser.add_argument(
        "--file-types",
        dest="file_types",
        help="Comma-separated FileTypesFilters names (default: all, small-first)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max files per type (default: all). Prefer all unless smoking.",
    )
    parser.add_argument(
        "--output",
        default="scripts/validation_parsing.json",
        help="JSON report path (default: scripts/validation_parsing.json)",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        default=True,
        help="Exit 1 if any parser failed (default)",
    )
    parser.add_argument(
        "--no-fail-on-error",
        action="store_false",
        dest="fail_on_error",
        help="Always exit 0 after writing the report",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Run parse checks, write JSON report, and exit non-zero on failures."""
    args = parse_args(argv)
    parsers = resolve_parsers(args)
    file_types = resolve_file_types(args.file_types)
    results = asyncio.run(run(parsers, args.limit, file_types))
    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)
    print(f"Wrote {args.output}", flush=True)

    failed = [row for row in results if not row.get("pass")]
    if args.fail_on_error and failed:
        print(f"{len(failed)} parser(s) failed parse check", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
