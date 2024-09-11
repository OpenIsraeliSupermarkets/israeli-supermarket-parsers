import unittest
import os
import uuid
from il_supermarket_scarper.utils import FileTypesFilters
from il_supermarket_parsers.parser_factroy import ParserFactory
from il_supermarket_parsers.utils import get_sample_data


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

        def _refresh_download_folder(self, download_path,file_type):
            """delete the download folder"""
            if os.path.isdir(download_path) and self.refresh:
                self._delete_folder_and_sub_folder(download_path)
                os.removedirs(download_path)


            if not os.path.isdir(download_path):
                get_sample_data(
                    download_path,
                    filter_type=file_type,
                    enabled_scrapers=[self.scraper_enum.name],
            )

        def _parser_validate(self, parser_enum, file_type, dump_path="temp"):
            self._refresh_download_folder(dump_path,file_type)

            init_parser_function = ParserFactory.get(parser_enum.name)

            parser = init_parser_function()
            df = parser.read()

            assert df.shape[0] > 0
            # TBD: add validation on the dataframe columns

        def _get_temp_folder(self):
            """get a temp folder to download the files into"""
            return self.folder_name + str(uuid.uuid4().hex)

        def test_parsing_store(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(parser_enum,FileTypesFilters.STORE_FILE.name, "samples_store")

        def test_parsing_promo(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(parser_enum,FileTypesFilters.PROMO_FILE.name, "samples_promo")

        def test_parsing_promo_all(self):
            """scrape one file and make sure it exists"""
            
            self._parser_validate(parser_enum,FileTypesFilters.PROMO_FULL_FILE.name, "samples_promo_all")

        def test_parsing_prices(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(parser_enum, FileTypesFilters.PRICE_FILE.name,"samples_prices")

        def test_parsing_prices_all(self):
            """scrape one file and make sure it exists"""
            self._parser_validate(parser_enum, FileTypesFilters.PRICE_FULL_FILE.name,"samples_prices_all")

    return TestParser
