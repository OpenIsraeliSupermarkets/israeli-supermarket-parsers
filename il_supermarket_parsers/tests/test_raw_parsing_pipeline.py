"""Integration tests for RawParsingPipeline.

Creates a temporary directory with real XML files, runs the pipeline end-to-end,
and asserts on the written CSV output and parser status.
"""

import os
import tempfile
import unittest

import pandas as pd
from il_supermarket_scarper.utils import DumpFolderNames
from il_supermarket_scarper.utils.databases import JsonDataBase

from il_supermarket_parsers.raw_parsing_pipeline import RawParsingPipeline
from il_supermarket_parsers.utils.data_loaders.data_loader import DataLoader
from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)
from il_supermarket_parsers.utils.status.parser_status import ParserStatus
from il_supermarket_parsers.utils.csv_reader import read_data_rows

SCRAPER = "SHUFERSAL"
STORE_FOLDER = DumpFolderNames.SHUFERSAL.value  # "Shufersal"

# Minimal PriceFull XML matching ShufersalFileConverter's default pricefull_parser:
#   list_key="Items", id_field="ItemCode", roots=["ChainId","SubChainId","StoreId","BikoretNo"]
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

# Minimal Stores XML matching ShufersalFileConverter's stores_parser override:
#   list_key="STORES", id_field="STOREID", roots=["CHAINID","LASTUPDATEDATE"]
STORES_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <CHAINID>7290027600007</CHAINID>
  <LASTUPDATEDATE>2025-01-01</LASTUPDATEDATE>
  <STORES>
    <STORE>
      <STOREID>001</STOREID>
      <STORENAME>Main Branch</STORENAME>
      <ADDRESS>1 Main St</ADDRESS>
      <CITY>Tel Aviv</CITY>
    </STORE>
    <STORE>
      <STOREID>002</STOREID>
      <STORENAME>Second Branch</STORENAME>
      <ADDRESS>1 Main St</ADDRESS>
      <CITY>Tel Aviv</CITY>
    </STORE>
  </STORES>
</Root>
"""


def _write_xml(folder: str, filename: str, content: str) -> str:
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _build_pipeline(root: str, output_dir: str, status_dir: str, file_type: str):
    """Construct a fully wired RawParsingPipeline for SHUFERSAL."""
    data_loader = DataLoader(root)
    csv_file_name = f"{file_type.lower()}_{SCRAPER.lower()}"
    output_writer = CSVOutputWriter(
        output_folder=output_dir,
        csv_file_name=csv_file_name,
    )
    db = JsonDataBase(f"{SCRAPER}_{file_type}".lower(), base_path=status_dir)
    return RawParsingPipeline(
        data_loader=data_loader,
        output_writer=output_writer,
        parser_status=ParserStatus(db),
    )


class TestRawParsingPipelinePriceFull(unittest.IsolatedAsyncioTestCase):
    """End-to-end: pipeline reads a PriceFull XML and writes a CSV."""

    def setUp(self) -> None:
        """Set up the test environment."""
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self._tmp.name
        self.output_dir = tempfile.mkdtemp()
        self.status_dir = tempfile.mkdtemp()

        store_dir = os.path.join(self.root, STORE_FOLDER)
        os.makedirs(store_dir)
        _write_xml(store_dir, "PriceFull7290027600007-001-20250101.xml", PRICEFULL_XML)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    async def test_csv_created_with_expected_rows(self) -> None:
        """Test that the CSV file is created with the expected rows."""
        pipeline = _build_pipeline(
            self.root, self.output_dir, self.status_dir, "PRICE_FULL_FILE"
        )
        await pipeline.process(
            enabled_scraper=SCRAPER,
            enabled_file_types=["PRICE_FULL_FILE"],
        )

        csv_path = os.path.join(self.output_dir, "price_full_file_shufersal.csv")
        self.assertTrue(os.path.exists(csv_path), "CSV output file was not created")
        df = pd.read_csv(csv_path)
        self.assertEqual(df.shape[0], 2, f"Expected 2 rows, got {df.shape[0]}")
        self.assertIn("itemcode", df.columns)
        self.assertIn("chainid", df.columns)

    async def test_parser_status_registers_processed_file(self) -> None:
        """Test that the parser status is registered correctly."""
        pipeline = _build_pipeline(
            self.root, self.output_dir, self.status_dir, "PRICE_FULL_FILE"
        )
        await pipeline.process(
            enabled_scraper=SCRAPER,
            enabled_file_types=["PRICE_FULL_FILE"],
        )

        logs = pipeline.get_parser_status().get_file_logs()
        self.assertEqual(len(logs), 1)
        self.assertTrue(logs[0].succusfull)
        self.assertEqual(logs[0].detected_num_rows, 2)


class TestRawParsingPipelineStores(unittest.IsolatedAsyncioTestCase):
    """End-to-end: pipeline reads a Stores XML and writes a CSV."""

    def setUp(self) -> None:
        """Set up the test environment."""
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self._tmp.name
        self.output_dir = tempfile.mkdtemp()
        self.status_dir = tempfile.mkdtemp()

        store_dir = os.path.join(self.root, STORE_FOLDER)
        os.makedirs(store_dir)
        for day in range(1, 4):
            _write_xml(
                store_dir,
                f"Stores7290027600007-001-2025010{day}.xml",
                STORES_XML,
            )

    def tearDown(self) -> None:
        """Tear down the test environment."""
        self._tmp.cleanup()

    async def test_csv_created_with_store_rows(self) -> None:
        """Test that the CSV file is created with the expected rows."""
        pipeline = _build_pipeline(
            self.root, self.output_dir, self.status_dir, "STORE_FILE"
        )
        await pipeline.process(
            enabled_scraper=SCRAPER,
            enabled_file_types=["STORE_FILE"],
        )

        csv_path = os.path.join(self.output_dir, "store_file_shufersal.csv")
        self.assertTrue(os.path.exists(csv_path), "CSV output file was not created")
        df = read_data_rows(csv_path, ffill=True, as_records=True)

        store_dir = os.path.join(self.root, STORE_FOLDER)
        shared = {"chainid": "7290027600007", "lastupdatedate": "2025-01-01"}

        self.assertEqual(
            df[0],
            {
                **shared,
                "found_folder": store_dir,
                "file_name": "Stores7290027600007-001-20250101.xml",
                "storeid": "001",
                "storename": "Main Branch",
                "address": "1 Main St",
                "city": "Tel Aviv",
            },
        )
        self.assertEqual(
            df[1],
            {
                **shared,
                "found_folder": store_dir,
                "file_name": "Stores7290027600007-001-20250101.xml",
                "storeid": "002",
                "storename": "Second Branch",
                "address": "1 Main St",
                "city": "Tel Aviv",
            },
        )
        self.assertEqual(
            df[2],
            {
                **shared,
                "found_folder": store_dir,
                "file_name": "Stores7290027600007-001-20250102.xml",
                "storeid": "001",
                "storename": "Main Branch",
                "address": "1 Main St",
                "city": "Tel Aviv",
            },
        )
        self.assertEqual(
            df[3],
            {
                **shared,
                "found_folder": store_dir,
                "file_name": "Stores7290027600007-001-20250102.xml",
                "storeid": "002",
                "storename": "Second Branch",
                "address": "1 Main St",
                "city": "Tel Aviv",
            },
        )
        self.assertEqual(
            df[4],
            {
                **shared,
                "found_folder": store_dir,
                "file_name": "Stores7290027600007-001-20250103.xml",
                "storeid": "001",
                "storename": "Main Branch",
                "address": "1 Main St",
                "city": "Tel Aviv",
            },
        )
        self.assertEqual(
            df[5],
            {
                **shared,
                "found_folder": store_dir,
                "file_name": "Stores7290027600007-001-20250103.xml",
                "storeid": "002",
                "storename": "Second Branch",
                "address": "1 Main St",
                "city": "Tel Aviv",
            },
        )


class TestRawParsingPipelineEmptyFolder(unittest.IsolatedAsyncioTestCase):
    """Pipeline handles an empty store folder gracefully (no crash, no output)."""

    def setUp(self) -> None:
        """Set up the test environment."""
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self._tmp.name
        self.output_dir = tempfile.mkdtemp()
        self.status_dir = tempfile.mkdtemp()

        store_dir = os.path.join(self.root, STORE_FOLDER)
        os.makedirs(store_dir)

    def tearDown(self) -> None:
        """Tear down the test environment."""
        self._tmp.cleanup()

    async def test_no_csv_when_no_files(self) -> None:
        """Test that the CSV file is not created when the folder is empty."""
        pipeline = _build_pipeline(
            self.root, self.output_dir, self.status_dir, "PRICE_FULL_FILE"
        )
        await pipeline.process(
            enabled_scraper=SCRAPER,
            enabled_file_types=["PRICE_FULL_FILE"],
        )

        csv_path = os.path.join(self.output_dir, "price_full_file_shufersal.csv")
        self.assertFalse(
            os.path.exists(csv_path), "CSV should not exist for empty input"
        )
        self.assertEqual(pipeline.get_parser_status().get_file_logs(), [])


class TestRawParsingPipelineLimit(unittest.IsolatedAsyncioTestCase):
    """Pipeline respects the ``limit`` parameter."""

    def setUp(self) -> None:
        """Set up the test environment."""
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self._tmp.name
        self.output_dir = tempfile.mkdtemp()
        self.status_dir = tempfile.mkdtemp()

        store_dir = os.path.join(self.root, STORE_FOLDER)
        os.makedirs(store_dir)
        for day in range(1, 4):
            _write_xml(
                store_dir,
                f"PriceFull7290027600007-001-2025010{day}.xml",
                PRICEFULL_XML,
            )

    def tearDown(self) -> None:
        """Tear down the test environment."""
        self._tmp.cleanup()

    async def test_limit_one_processes_one_file(self) -> None:
        """Test that the pipeline processes one file when the limit is set to one."""
        pipeline = _build_pipeline(
            self.root, self.output_dir, self.status_dir, "PRICE_FULL_FILE"
        )
        await pipeline.process(
            enabled_scraper=SCRAPER,
            enabled_file_types=["PRICE_FULL_FILE"],
            limit=1,
        )

        logs = pipeline.get_parser_status().get_file_logs()
        self.assertEqual(len(logs), 1)

    async def test_no_limit_processes_all_files(self) -> None:
        """Test that the pipeline processes all files when the limit is not set."""
        pipeline = _build_pipeline(
            self.root, self.output_dir, self.status_dir, "PRICE_FULL_FILE"
        )
        await pipeline.process(
            enabled_scraper=SCRAPER,
            enabled_file_types=["PRICE_FULL_FILE"],
        )

        logs = pipeline.get_parser_status().get_file_logs()
        self.assertEqual(len(logs), 3)


if __name__ == "__main__":
    unittest.main()
