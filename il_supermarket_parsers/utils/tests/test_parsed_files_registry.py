"""Parsed-file registry on ParserStatus and the re-download diff."""

import datetime
import json
import os
import tempfile
import unittest

from il_supermarket_scarper import FileTypesFilters
from il_supermarket_scarper.utils.databases import JsonDataBase

from il_supermarket_parsers.utils.loading_utils import DumpFile
from il_supermarket_parsers.utils.status import (
    ParserStatus,
    ParserStatusOutput,
    files_to_download,
)


def _dump_file(file_name: str, content: bytes = b"<Root/>") -> DumpFile:
    return DumpFile(
        store_folder="Shufersal",
        file_name=file_name,
        prefix_file_name=file_name.split("-")[0],
        extracted_store_number="001",
        extracted_chain_id="7290027600007",
        extracted_date=datetime.datetime(2025, 1, 1),
        detected_filetype=FileTypesFilters.PRICE_FILE,
        file_content=content,
    )


class TestParsedFilesRegistry(unittest.TestCase):
    """processed and skipped are recorded; failed is not."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.db = JsonDataBase("shufersal_price_file", base_path=self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _load(self) -> ParserStatusOutput:
        path = os.path.join(self._tmp.name, "shufersal_price_file.json")
        with open(path, "r", encoding="utf-8") as handle:
            return ParserStatusOutput(**json.load(handle))

    def _run(self, status: ParserStatus, outcomes: dict) -> None:
        status.on_parsing_start(
            limit=None, enabled_file_types="PRICE_FILE", enabled_scraper="SHUFERSAL"
        )
        for name, outcome in outcomes.items():
            dump = _dump_file(name)
            if outcome == "skipped":
                status.register_skipped_file(dump)
                continue
            status.registered_file_to_process(dump)
            if outcome == "processed":
                status.register_processed_file(dump, row_count=3)
            else:
                status.register_failed_file(dump, 0, ValueError("bad"), "trace")

    def test_registry_records_processed_and_skipped_only(self) -> None:
        """A failed file stays out of parsed_files so it can be re-requested."""
        status = ParserStatus(self.db)
        self._run(
            status,
            {
                "Price7290027600007-001-202501010000.xml": "processed",
                "Price7290027600007-002-202501010000.xml": "skipped",
                "Price7290027600007-003-202501010000.xml": "failed",
            },
        )

        expected = {
            "Price7290027600007-001-202501010000.xml",
            "Price7290027600007-002-202501010000.xml",
        }
        self.assertEqual(status.parsed_file_names(), expected)
        output = self._load()
        self.assertEqual(output.parsed_file_names(), expected)
        rows = {row.file_name: row for row in output.parsed_files}
        self.assertEqual(
            rows["Price7290027600007-001-202501010000.xml"].row_count, 3
        )
        self.assertIsNone(rows["Price7290027600007-002-202501010000.xml"].row_count)
        self.assertTrue(output.validate_file_status())

    def test_reparse_in_later_task_is_valid(self) -> None:
        """Failed in one run, parsed after a forced re-download in the next."""
        name = "Price7290027600007-003-202501010000.xml"
        self._run(ParserStatus(self.db), {name: "failed"})
        self._run(ParserStatus(self.db), {name: "processed"})

        output = self._load()
        self.assertEqual(output.parsed_file_names(), {name})
        self.assertTrue(output.validate_file_status())

    def test_duplicate_within_one_task_is_still_invalid(self) -> None:
        """Scoping by task keeps the per-run duplicate check."""
        name = "Price7290027600007-001-202501010000.xml"
        status = ParserStatus(self.db)
        self._run(status, {name: "processed"})
        status.register_processed_file(_dump_file(name), row_count=3)

        self.assertFalse(self._load().validate_file_status())

    def test_status_without_registry_still_loads(self) -> None:
        """Status JSON written before parsed_files existed stays valid."""
        output = ParserStatusOutput(global_status=[], events=[])
        self.assertEqual(output.parsed_files, [])
        self.assertTrue(output.validate_file_status())


class TestFilesToDownload(unittest.TestCase):
    """downloaded minus parsed, compared on normalized names."""

    def test_diff_ignores_extensions_and_null(self) -> None:
        downloaded = [
            "Price7290027600007-001-202501010000.xml",
            "PriceNULL7290027600007-002-202501010000.gz",
            "Promo7290027600007-001-202501010000.xml",
        ]
        parsed = [
            "Price7290027600007-001-202501010000",
            "Price7290027600007-002-202501010000.xml",
        ]
        self.assertEqual(
            files_to_download(downloaded, parsed),
            ["Promo7290027600007-001-202501010000"],
        )

    def test_nothing_missing(self) -> None:
        self.assertEqual(files_to_download(["Stores1-1.xml"], ["Stores1-1.xml"]), [])
        self.assertEqual(files_to_download([], []), [])


if __name__ == "__main__":
    unittest.main()
