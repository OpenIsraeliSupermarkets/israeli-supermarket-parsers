import unittest
import os
import tempfile
import pandas as pd
from il_supermarket_scarper import ScraperFactory
from il_supermarket_parsers.utils import get_sample_data, DataLoader, FileTypesFilters
from il_supermarket_parsers.parser_factory import ParserFactory


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
            self.refresh = False

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
                filter_type=file_type,
                enabled_scrapers=[self.scraper_enum.name],
                limit=5,
            )

        def _parser_validate(self, file_type):
            """test the sub case"""
            with tempfile.TemporaryDirectory() as tmpdirname:
                self.__parser_validate(file_type, tmpdirname)

        def __parser_validate(self, file_type, dump_path="temp"):
            """test the sub case"""
            sub_folder = self._get_temp_folder(dump_path)

            if ScraperFactory.is_scraper_enabled(self.scraper_enum):
                self._refresh_download_folder(sub_folder, file_type)

            parser = self.parser_class()

            files = DataLoader(
                folder=sub_folder,
                store_names=[self.parser_name],
                files_types=[file_type],
            ).load()

            complete_file_loaded = list(map(lambda x: x.get_full_path(), files))
            files_from_folder = self.list_xml_files_recursive(sub_folder)
            assert sorted(complete_file_loaded) == sorted(files_from_folder), (
                f"dataloader failed, failed to load"
                f": {list(set(files_from_folder) - set(complete_file_loaded))}"
            )
            dfs = []
            for file in files:

                try:
                    if file.is_empty_file():
                        continue

                    df = parser.read(file, run_validation=True)
                    # none empty file
                    if file.is_expected_to_have_data():

                        # should contain data
                        assert df.shape[0] > 0, f"File {file} is empty"

                        dfs.append(df)

                    else:
                        assert df.shape[0] == 0, f"File {file} should be full"
                except Exception as e:  # pylint: disable=broad-exception-caught
                    raise ValueError(f"File {file}, Failed with {e}")

            if dfs:
                pd.concat(dfs)

        def list_xml_files_recursive(self, directory):
            """list all xml files"""
            file_list = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if "xml" in file:
                        file_list.append(os.path.join(root, file))
            return file_list

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
