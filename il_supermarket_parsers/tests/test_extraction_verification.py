"""PARSER_VERIFY_EXTRACTION: pipeline wiring and env parsing."""

import json
import os
import tempfile
import unittest
from unittest import mock

import pandas as pd
from il_supermarket_scarper.utils.databases import JsonDataBase

from il_supermarket_parsers.engines.base import BaseFileConverter
from il_supermarket_parsers.raw_parsing_pipeline import RawParsingPipeline
from il_supermarket_parsers.utils.data_loaders.data_loader import DataLoader
from il_supermarket_parsers.utils.extraction_verification import (
    ENV_VAR,
    ExtractionVerification,
    get_extraction_verification,
)
from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)
from il_supermarket_parsers.utils.status.parser_status import ParserStatus
from il_supermarket_parsers.utils.status.parser_status_contract import (
    ParserStatusOutput,
)

SCRAPER = "SHUFERSAL"
STORE_FOLDER = "Shufersal"
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
      <ItemName>Milk 3%</ItemName>
      <ItemPrice>6.90</ItemPrice>
    </Item>
    <Item>
      <ItemCode>1002</ItemCode>
      <ItemName>Bread</ItemName>
      <ItemPrice>5.50</ItemPrice>
    </Item>
  </Items>
</Root>
"""


def _write_xml(folder, filename, content):
    with open(os.path.join(folder, filename), "w", encoding="utf-8") as handle:
        handle.write(content)


def _validate_status_file(status_dir):
    for status_file in os.listdir(status_dir):
        if status_file.endswith(".json"):
            with open(
                os.path.join(status_dir, status_file), "r", encoding="utf-8"
            ) as handle:
                assert ParserStatusOutput(**json.load(handle)).validate_file_status()


class TestModeParsing(unittest.TestCase):
    """The env var only accepts off/full."""

    def test_unset_is_off(self):
        """Unset is off."""
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(ENV_VAR, None)
            self.assertEqual(get_extraction_verification(), ExtractionVerification.OFF)

    def test_values(self):
        """Values."""
        self.assertEqual(get_extraction_verification(""), ExtractionVerification.OFF)
        self.assertEqual(
            get_extraction_verification(" FULL "), ExtractionVerification.FULL
        )
        with mock.patch.dict(os.environ, {ENV_VAR: "full"}):
            self.assertEqual(get_extraction_verification(), ExtractionVerification.FULL)

    def test_unknown_value_raises(self):
        """Unknown value raises."""
        with self.assertRaises(ValueError):
            get_extraction_verification("yes")
        with mock.patch.dict(os.environ, {ENV_VAR: "counts"}):
            with self.assertRaises(ValueError):
                RawParsingPipeline(
                    data_loader=None, output_writer=None, parser_status=None
                )


class TestPipelineVerification(unittest.IsolatedAsyncioTestCase):
    """End-to-end on a small PriceFull file."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self._tmp.name
        self.output_dir = os.path.join(self.root, "out")
        self.status_dir = os.path.join(self.root, "status")
        os.makedirs(self.output_dir)
        os.makedirs(self.status_dir)
        store_dir = os.path.join(self.root, STORE_FOLDER)
        os.makedirs(store_dir)
        _write_xml(store_dir, "PriceFull7290027600007-001-20250101.xml", PRICEFULL_XML)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _pipeline(self, mode):
        db = JsonDataBase(
            f"{SCRAPER}_price_full_file".lower(), base_path=self.status_dir
        )
        return RawParsingPipeline(
            data_loader=DataLoader(self.root),
            output_writer=CSVOutputWriter(
                output_folder=self.output_dir,
                csv_file_name=f"price_full_file_{SCRAPER.lower()}",
            ),
            parser_status=ParserStatus(db),
            extraction_verification=mode,
        )

    async def _run(self, pipeline):
        await pipeline.process(
            enabled_scraper=SCRAPER, enabled_file_types="PRICE_FULL_FILE"
        )
        logs = pipeline.get_parser_status().get_file_logs()
        self.assertEqual(len(logs), 1)
        _validate_status_file(self.status_dir)
        return logs[0]

    def _csv_rows(self):
        path = os.path.join(self.output_dir, f"price_full_file_{SCRAPER.lower()}.csv")
        return pd.read_csv(path).shape[0]

    async def test_full_passes_on_correct_file(self):
        """Full passes on correct file."""
        log = await self._run(self._pipeline("full"))
        self.assertTrue(log.succusfull)
        self.assertEqual(log.detected_num_rows, 2)
        self.assertEqual(self._csv_rows(), 2)

    async def test_full_marks_mismatch_failed_but_keeps_rows(self):
        """Full marks mismatch failed but keeps rows."""

        def drop_last_row(self_, dump_file, rows):  # pylint: disable=unused-argument
            raise ValueError("for file x, missing data")

        with mock.patch.object(BaseFileConverter, "verify_extraction", drop_last_row):
            log = await self._run(self._pipeline("full"))
        self.assertFalse(log.succusfull)
        self.assertIn("missing data", log.error)
        self.assertEqual(log.detected_num_rows, 2)
        self.assertEqual(self._csv_rows(), 2)

    async def test_full_catches_a_parser_dropping_rows(self):
        """Full catches a parser dropping rows."""
        original = BaseFileConverter.read

        async def lossy_read(self_, dump_file, run_validation=False):
            rows = [row async for row in original(self_, dump_file, run_validation)]
            for row in rows[:-1]:
                yield row

        with mock.patch.object(BaseFileConverter, "read", lossy_read):
            log = await self._run(self._pipeline("full"))
        self.assertFalse(log.succusfull)
        self.assertIn("missing data", log.error)

    async def test_off_does_not_verify(self):
        """Off does not verify."""
        with mock.patch.object(
            BaseFileConverter, "verify_extraction", side_effect=AssertionError
        ):
            log = await self._run(self._pipeline("off"))
        self.assertTrue(log.succusfull)
