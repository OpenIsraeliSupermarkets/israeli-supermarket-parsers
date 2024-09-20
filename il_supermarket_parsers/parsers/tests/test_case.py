import unittest
import os
import pandas as pd
from il_supermarket_scarper.utils import FileTypesFilters,DumpFolderNames
from il_supermarket_parsers.utils import get_sample_data, DataLoader


def make_test_case(scraper_enum, parser_enum):
    """create test suite for parser"""

    class TestParser(unittest.TestCase):
        """class with all the tests for scraper"""

        def __init__(self, name) -> None:
            super().__init__(name)
            self.scraper_enum = scraper_enum
            self.parser_enum = parser_enum
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
            )

        def _parser_validate(self, parser_enum, file_type, dump_path="temp"):
            """test the subcase"""
            sub_folder = self._get_temp_folder(dump_path)
            self._refresh_download_folder(sub_folder, file_type)

            parser = parser_enum.value()

            # TBD: add option to take the folder from enum
            # TBD: FileType, add function get enum by filter
            files = DataLoader(
                folder=sub_folder,
                store_names=[DumpFolderNames[self.scraper_enum.name].value],
                files_types=[file_type],
            ).load()
            assert len(files) > 0, "no files downloaded"

            dfs = []
            for file in files:
                df = parser.read(file)

                # none empty file
                if os.path.getsize(file.get_full_path()) > 256:

                    # should contain data
                    assert df.shape[0] > 0, f"File {file} is empty"
                    # assert df.isna().all().all(), f"File {file} contains NaN"
                    # assert set(df.columns) & set(parser.load_column_config()['missing_columns_default_values'].keys())

                    dfs.append(df)

                else:
                    assert df.shape[0] == 1

            if dfs:
                joined = pd.concat(dfs)

                folders = []
                for source in joined["found_folder"].unique():
                    folders.append(os.path.split(source)[1])

                joined.to_csv(
                    os.path.join(
                        self.folder_name, file_type + "_" + "_".join(folders) + ".csv"
                    ),
                    index=False,
                )

        def test_parsing_store(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(
                parser_enum, FileTypesFilters.STORE_FILE.name, "samples_store"
            )

        def test_parsing_promo(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(
                parser_enum, FileTypesFilters.PROMO_FILE.name, "samples_promo"
            )

        def test_parsing_promo_all(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(
                parser_enum, FileTypesFilters.PROMO_FULL_FILE.name, "samples_promo_all"
            )

        def test_parsing_prices(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(
                parser_enum, FileTypesFilters.PRICE_FILE.name, "samples_prices"
            )

        def test_parsing_prices_all(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(
                parser_enum, FileTypesFilters.PRICE_FULL_FILE.name, "samples_prices_all"
            )

    return TestParser
