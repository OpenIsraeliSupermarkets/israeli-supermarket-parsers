import unittest
import os
import tempfile
import gc
import asyncio
import csv
import sys
from typing import List

import pandas as pd
from il_supermarket_scarper import ScraperFactory
from il_supermarket_parsers.utils import DataLoader, FileTypesFilters, DumpFile
from il_supermarket_parsers.utils.test_utils import SampleDataOptions, get_sample_data
from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)
from il_supermarket_parsers.parser_factory import ParserFactory
from il_supermarket_parsers.engines.base import BaseFileConverter
from il_supermarket_parsers import read_data_rows

csv.field_size_limit(sys.maxsize)


def _validate_file_loading(files: List[DumpFile], sub_folder: str):
    """Validate that all files were loaded correctly."""
    complete_file_loaded = list(map(lambda x: x.get_full_path, files))
    files_from_folder = _list_xml_files_recursive(sub_folder)
    assert sorted(complete_file_loaded) == sorted(files_from_folder), (
        f"dataloader failed, failed to load"
        f": {list(set(files_from_folder) - set(complete_file_loaded))}"
    )


def _list_xml_files_recursive(directory):
    """list all xml files"""
    file_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            if "xml" in file:
                file_list.append(os.path.join(root, file))
    return file_list


async def _process_files(
    files: List[DumpFile], parser: BaseFileConverter, test_fill_forward: bool = True
):
    """Process all files and return sampled dataframes."""
    dfs = []
    for file in files:
        if not file.is_expected_to_be_readable:
            continue

        with tempfile.TemporaryDirectory() as file_tmp_dir:
            writer = CSVOutputWriter(
                output_folder=file_tmp_dir,
                enabled_scraper=file.extracted_chain_id,
                enabled_file_type=file.detected_filetype.name,
                reduce_duplicates=test_fill_forward,
            )
            await writer.initialize()

            async for row in parser.read(file):
                await writer.write_row(row)

            writer.close()

            # load the data from the writer
            if writer.exists():
                df = read_data_rows(writer.get_path(), ffill=test_fill_forward, as_records=False)
            else:
                df = pd.DataFrame()

        # Run validation against the created DataFrame
        parser.run_validation(df, file)

        if file.is_expected_to_have_records:
            assert df.shape[0] > 0, f"File {file.file_name} is empty"
            sampled_df = df.sample(n=min(10, df.shape[0]))
            del df
            dfs.append(sampled_df)
        else:
            assert df.shape[0] == 0, f"File {file.file_name} should be empty"
            del df
    return dfs


def make_test_case(scraper_enum, parser_enum):
    """create test suite for parser"""

    class TestParser(unittest.TestCase):
        """class with all the tests for scraper"""

        def __init__(self, name) -> None:
            super().__init__(name)
            self.scraper_enum = scraper_enum

            self.parser_class = ParserFactory.get(parser_enum)
            self.parser_name = parser_enum.name
            self.folder_name = "temp"
            self.refresh = True

        def _get_temp_folder(self, dump_folder):
            """get a temp folder to download the files into"""
            return os.path.join(self.folder_name, dump_folder)

        def _delete_folder_and_sub_folder(self, download_path):
            """delete a folder and all sub-folder"""
            files_found = os.listdir(download_path)
            for file in files_found:
                file_path = os.path.join(download_path, file)
                if os.path.isdir(file_path):
                    self._delete_folder_and_sub_folder(file_path)
                    os.rmdir(file_path)
                else:
                    os.remove(file_path)

        def _refresh_download_folder(self, download_path, file_type):
            """delete the download folder"""
            if os.path.isdir(download_path) and self.refresh:
                self._delete_folder_and_sub_folder(download_path)
                os.removedirs(download_path)

            get_sample_data(
                download_path,
                SampleDataOptions(
                    filter_type=file_type,
                    enabled_scrapers=[self.scraper_enum.name],
                    limit=10,
                ),
            )

        def _parser_validate(self, file_type):
            """test the sub case"""
            with tempfile.TemporaryDirectory() as tmpdirname:
                asyncio.run(self.__parser_validate(file_type, tmpdirname))

        async def __parser_validate(self, file_type, dump_path="temp"):
            """test the sub case"""
            sub_folder = self._get_temp_folder(dump_path)

            if ScraperFactory.is_scraper_enabled(self.scraper_enum):
                self._refresh_download_folder(sub_folder, file_type)

            parser = self.parser_class()
            # Collect files from async generator
            files = []
            async for file in DataLoader(
                folder=sub_folder,
            ).load(
                enabled_scraper=[self.parser_name],
                files_types=[file_type],
            ):
                files.append(file)

            assert len(files) > 0, f"No files found in {sub_folder}"
            _validate_file_loading(files, sub_folder)
            dfs = await _process_files(files, parser)

            if dfs:
                concatenated = pd.concat(dfs)
                del concatenated
            del dfs
            gc.collect()

        def test_parsing_store(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(FileTypesFilters.STORE_FILE.name)

        def test_parsing_promo(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(FileTypesFilters.PROMO_FILE.name)

        def test_parsing_promo_all(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(FileTypesFilters.PROMO_FULL_FILE.name)

        def test_parsing_prices(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(FileTypesFilters.PRICE_FILE.name)

        def test_parsing_prices_all(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(FileTypesFilters.PRICE_FULL_FILE.name)

    return TestParser
