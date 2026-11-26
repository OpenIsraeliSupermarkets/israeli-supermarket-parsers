"""A dump parsed before, same name and same content, is not parsed again (#154).

A killed run leaves its dumps on disk; the next run finds them again. Their
rows are already in the CSV, so parsing them again would append a second copy.
"""

import json
import os
import tempfile
import unittest

from il_supermarket_scarper.utils import DumpFolderNames
from il_supermarket_scarper.utils.databases import JsonDataBase

from il_supermarket_parsers.raw_parsing_pipeline import RawParsingPipeline
from il_supermarket_parsers.utils.data_loaders.data_loader import DataLoader
from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)
from il_supermarket_parsers.utils.status.parser_status import ParserStatus
from il_supermarket_parsers.utils.status.parser_status_contract import (
    ParserStatusOutput,
)

SCRAPER = "SHUFERSAL"
STORE_FOLDER = DumpFolderNames.SHUFERSAL.value
PRICEFULL_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290027600007</ChainId>
  <SubChainId>1</SubChainId>
  <StoreId>001</StoreId>
  <BikoretNo>0</BikoretNo>
  <Items>
    <Item>
      <ItemCode>1001</ItemCode>
      <ItemType>0</ItemType>
      <ItemName>Milk 3%</ItemName>
      <ItemPrice>6.90</ItemPrice>
    </Item>
    <Item>
      <ItemCode>1002</ItemCode>
      <ItemType>0</ItemType>
      <ItemName>Bread</ItemName>
      <ItemPrice>5.50</ItemPrice>
    </Item>
  </Items>
</Root>
"""


def _write_xml(folder: str, filename: str, content: str) -> None:
    with open(os.path.join(folder, filename), "w", encoding="utf-8") as handle:
        handle.write(content)


def _build_pipeline(root: str, output_dir: str, status_dir: str, file_type: str):
    """A RawParsingPipeline for SHUFERSAL over *root*, as the task wires it."""
    return RawParsingPipeline(
        data_loader=DataLoader(root),
        output_writer=CSVOutputWriter(
            output_folder=output_dir,
            csv_file_name=f"{file_type.lower()}_{SCRAPER.lower()}",
        ),
        parser_status=ParserStatus(
            JsonDataBase(f"{SCRAPER}_{file_type}".lower(), base_path=status_dir)
        ),
    )


def _validate_status_file(status_dir: str) -> None:
    """Every status JSON keeps a coherent per-file lifecycle."""
    for name in os.listdir(status_dir):
        if name.endswith(".json"):
            with open(os.path.join(status_dir, name), "r", encoding="utf-8") as handle:
                assert ParserStatusOutput(**json.load(handle)).validate_file_status()


FILE_TYPE = "PRICE_FULL_FILE"
FILE_NAME = "PriceFull7290027600007-001-20250101.xml"


class TestAlreadyParsed(unittest.IsolatedAsyncioTestCase):
    """Two runs over the same dump folder, as after a killed scrape."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = os.path.join(self._tmp.name, "dumps")
        self.output_dir = os.path.join(self._tmp.name, "outputs")
        self.status_dir = os.path.join(self._tmp.name, "status")
        self.store_dir = os.path.join(self.root, STORE_FOLDER)
        for folder in (self.store_dir, self.output_dir, self.status_dir):
            os.makedirs(folder)
        _write_xml(self.store_dir, FILE_NAME, PRICEFULL_XML)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- helpers -----------------------------------------------------------

    async def _run(self):
        """One parsing run over the dump folder; returns its status tracker."""
        pipeline = _build_pipeline(
            self.root, self.output_dir, self.status_dir, FILE_TYPE
        )
        await pipeline.process(enabled_scraper=SCRAPER, enabled_file_types=FILE_TYPE)
        return pipeline.get_parser_status()

    def _csv_lines(self) -> int:
        path = os.path.join(self.output_dir, "price_full_file_shufersal.csv")
        with open(path, "r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)

    def _status(self) -> ParserStatusOutput:
        path = os.path.join(self.status_dir, f"{SCRAPER}_{FILE_TYPE}.json".lower())
        with open(path, "r", encoding="utf-8") as handle:
            return ParserStatusOutput(**json.load(handle))

    # -- tests -------------------------------------------------------------

    async def test_second_run_appends_no_rows(self) -> None:
        """The same dump found again is recorded as already parsed, not parsed."""
        await self._run()
        lines_after_first = self._csv_lines()

        status = await self._run()

        self.assertEqual(self._csv_lines(), lines_after_first)
        self.assertEqual(status.get_file_logs(), [])
        output = self._status()
        self.assertEqual(len(output.parsed_files), 1)
        self.assertEqual(len(output.parsed_files[0].content_sha256), 64)
        self.assertEqual(
            [(row.file_name, row.content_sha256) for row in output.already_parsed],
            [(FILE_NAME, output.parsed_files[0].content_sha256)],
        )
        _validate_status_file(self.status_dir)

    async def test_changed_content_is_parsed_again(self) -> None:
        """The scraper re-downloads a file under the same name when it changed."""
        await self._run()
        lines_after_first = self._csv_lines()
        _write_xml(
            self.store_dir,
            FILE_NAME,
            PRICEFULL_XML.replace("<ItemPrice>6.90", "<ItemPrice>7.20"),
        )

        await self._run()

        self.assertGreater(self._csv_lines(), lines_after_first)
        output = self._status()
        self.assertEqual(len({row.content_sha256 for row in output.parsed_files}), 2)
        self.assertEqual(output.already_parsed, [])
        _validate_status_file(self.status_dir)

    async def test_entry_without_hash_matches_on_name(self) -> None:
        """Registry rows written before #154 have no hash; the name decides."""
        db = JsonDataBase(f"{SCRAPER}_{FILE_TYPE}".lower(), base_path=self.status_dir)
        db.insert_document(
            "parsed_files",
            {
                "file_name": FILE_NAME,
                "store_folder": STORE_FOLDER,
                "file_type": FILE_TYPE,
                "row_count": 2,
                "task_id": "before-154",
                "system_timestamp": "2025-01-01T00:00:00",
            },
        )

        status = await self._run()

        self.assertEqual(status.get_file_logs(), [])
        self.assertEqual(len(self._status().already_parsed), 1)

    async def test_other_files_are_still_parsed(self) -> None:
        """Only the dump parsed before is left out."""
        await self._run()
        lines_after_first = self._csv_lines()
        _write_xml(
            self.store_dir, "PriceFull7290027600007-002-20250101.xml", PRICEFULL_XML
        )

        status = await self._run()

        self.assertEqual(len(status.get_file_logs()), 1)
        self.assertGreater(self._csv_lines(), lines_after_first)
        self.assertEqual(len(self._status().already_parsed), 1)


if __name__ == "__main__":
    unittest.main()
