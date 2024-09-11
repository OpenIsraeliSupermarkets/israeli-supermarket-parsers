import unittest
import os
import uuid
from il_supermarket_scarper.utils import FileTypesFilters
from il_supermarket_parsers.parser_factroy import ParserFactory
from il_supermarket_parsers.utils import get_sample_data


def make_test_case(scraper_enum, parser_enum, store_id):
    """create test suite for scraper"""

    class TestScapers(unittest.TestCase):
        """class with all the tests for scraper"""

        def __init__(self, name) -> None:
            super().__init__(name)
            self.scraper_enum = scraper_enum
            self.parser_enum = parser_enum
            self.folder_name = "temp"

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

        def _delete_download_folder(self, download_path):
            """delete the download folder"""
            if os.path.isdir(download_path):
                self._delete_folder_and_sub_folder(download_path)
                os.removedirs(download_path)

        def _parser_validate(self, scraper_enum, dump_path="temp"):
            self._delete_download_folder(dump_path)
            os.makedirs(dump_path)

            init_scraper_function = ParserFactory.get(scraper_enum)

            df = init_scraper_function(folder_name=dump_path)

            assert df.shape[0] > 0
            # TBD: add validation on the dataframe columns

        def _get_temp_folder(self):
            """get a temp folder to download the files into"""
            return self.folder_name + str(uuid.uuid4().hex)

        def test_parsing_store(self):
            """scrape one file and make sure it exists"""
            get_sample_data(
                "samples_store",
                FileTypesFilters.STORE_FILE.name,
                enabled_scrapers=[self.scraper_enum.name],
            )
            self._parser_validate(parser_enum, "samples_store", limit=1)

        def test_parsing_promo(self):
            """scrape one file and make sure it exists"""
            get_sample_data(
                "samples_promo",
                FileTypesFilters.PROMO_FILE.name,
                enabled_scrapers=[self.scraper_enum.name],
            )
            self._parser_validate(parser_enum, "samples_promo", limit=1)

        def test_parsing_promo_all(self):
            """scrape one file and make sure it exists"""
            get_sample_data(
                "samples_promo_all",
                FileTypesFilters.PROMO_FULL_FILE.name,
                enabled_scrapers=[self.scraper_enum.name],
            )
            self._parser_validate(parser_enum, "samples_promo_all", limit=1)

        def test_parsing_prices(self):
            """scrape one file and make sure it exists"""
            get_sample_data(
                "samples_prices",
                FileTypesFilters.PRICE_FILE.name,
                enabled_scrapers=[self.scraper_enum.name],
            )
            self._parser_validate(parser_enum, "samples_prices", limit=1)

        def test_parsing_prices_all(self):
            """scrape one file and make sure it exists"""
            get_sample_data(
                "samples_prices_all",
                FileTypesFilters.PRICE_FULL_FILE.name,
                enabled_scrapers=[self.scraper_enum.name],
            )
            self._parser_validate(parser_enum, "samples_prices_all", limit=1)

    return TestScapers
