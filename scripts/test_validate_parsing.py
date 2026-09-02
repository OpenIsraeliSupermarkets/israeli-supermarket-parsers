"""Unit tests for fail-fast parse validation helpers."""

import unittest

from il_supermarket_parsers.engines.base import BaseFileConverter
from il_supermarket_parsers.engines.big_id import BigIDFileConverter
from il_supermarket_parsers.engines.branches import BigIdBranchesFileConverter

from scripts.validate_parsing import (
    consume_until_failure,
    engine_name,
    is_empty_skip,
    is_parse_ok,
    resolve_file_types,
)


def _ok(name: str, file_type: str = "PRICE_FILE") -> dict:
    """Successful parse result."""
    return {
        "file_name": name,
        "file_type": file_type,
        "parsed": True,
        "skipped_empty": False,
        "row_count": 3,
        "error": None,
    }


def _fail(name: str, error: str, file_type: str = "PRICE_FILE") -> dict:
    """Failed parse result."""
    return {
        "file_name": name,
        "file_type": file_type,
        "parsed": False,
        "skipped_empty": False,
        "row_count": 0,
        "error": error,
    }


def _empty(name: str) -> dict:
    """Zero-byte skip result."""
    return {
        "file_name": name,
        "file_type": "PRICE_FILE",
        "parsed": False,
        "skipped_empty": True,
        "row_count": 0,
        "error": None,
    }


class TestParseHelpers(unittest.IsolatedAsyncioTestCase):
    """Fail-fast contract for validate_parsing."""

    def test_is_parse_ok_requires_parsed(self):
        """Unreadable skips and errors are not a successful parse."""
        self.assertTrue(is_parse_ok(_ok("a")))
        self.assertFalse(is_parse_ok(_fail("a", "columns chainid missing")))
        self.assertFalse(is_parse_ok(_empty("a")))
        self.assertTrue(is_empty_skip(_empty("a")))
        self.assertFalse(is_empty_skip(_fail("a", "id missing")))

    def test_engine_name_picks_most_specific(self):
        """Branches beats BigID beats Base."""
        self.assertEqual(
            engine_name(BigIdBranchesFileConverter), "BigIdBranchesFileConverter"
        )
        self.assertEqual(engine_name(BigIDFileConverter), "BigIDFileConverter")
        self.assertEqual(engine_name(BaseFileConverter), "BaseFileConverter")

    def test_resolve_file_types_orders_small_first(self):
        """PRICE_FULL is parsed after STORE even if requested first."""
        ordered = resolve_file_types("PRICE_FULL_FILE,STORE_FILE")
        self.assertEqual(ordered, ["STORE_FILE", "PRICE_FULL_FILE"])

    async def test_consume_stops_on_first_failure(self):
        """Later files must not be pulled after the first failed result."""
        pulled = []

        async def results():
            items = (
                _ok("one"),
                _ok("two"),
                _fail("three", "columns chainid missing"),
                _ok("four"),
            )
            for item in items:
                pulled.append(item["file_name"])
                yield item

        summary = await consume_until_failure(results())
        self.assertEqual(summary["parsed"], 2)
        self.assertEqual(summary["failed"], 1)
        self.assertTrue(summary["stopped_on_failure"])
        self.assertEqual(summary["failed_file"], "three")
        self.assertEqual(summary["error"], "columns chainid missing")
        self.assertEqual(pulled, ["one", "two", "three"])

    async def test_consume_skips_empty(self):
        """Zero-byte dumps do not fail-fast the chain."""
        pulled = []

        async def results():
            items = (_ok("one"), _empty("blank.xml"), _ok("three"))
            for item in items:
                pulled.append(item["file_name"])
                yield item

        summary = await consume_until_failure(results())
        self.assertEqual(summary["parsed"], 2)
        self.assertEqual(summary["skipped_empty"], 1)
        self.assertEqual(summary["failed"], 0)
        self.assertFalse(summary["stopped_on_failure"])
        self.assertEqual(pulled, ["one", "blank.xml", "three"])

    async def test_consume_all_ok(self):
        """A full successful drain reports no failure."""

        async def results():
            yield _ok("one")
            yield _ok("two")

        summary = await consume_until_failure(results())
        self.assertEqual(summary["parsed"], 2)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["skipped_empty"], 0)
        self.assertFalse(summary["stopped_on_failure"])


if __name__ == "__main__":
    unittest.main()
