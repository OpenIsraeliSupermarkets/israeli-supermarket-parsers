"""Regression tests for Cerberus PromoFull dump discovery.

Rami Levy, Fresh Market / Super Dosh, and Yellow publish PromoFull files as
``PromoFull{chain}-001-{store}-{YYYYMMDD}-{HHMMSS}`` (often ``.gz`` or with no
extension). Quality tickets #91/#93/#95 flagged those names as never picked up.
The loader must classify them as PROMO_FULL_FILE and the chain parsers must
emit rows from the standard ``<Promotions>`` wrapper.
"""

import os
import tempfile
import unittest

from il_supermarket_scarper import FileTypesFilters
from il_supermarket_scarper.utils import DumpFolderNames

from il_supermarket_parsers.parser_factory import ParserFactory
from il_supermarket_parsers.utils.data_loaders.data_loader import DataLoader
from il_supermarket_parsers.utils.loading_utils import file_name_to_components

# Exact stems from the parse-gap issues (no extension).
RAMI_LEVY_PROMOFULL = "PromoFull7290058140886-001-003-20260902-060113"
FRESH_MARKET_PROMOFULL = "PromoFull7290876100000-001-001-20260902-001238"
YELLOW_PROMOFULL = "PromoFull7290644700005-001-202-20260902-001615"

_PROMOFULL_CASES = (
    ("RAMI_LEVY", RAMI_LEVY_PROMOFULL, "003"),
    ("FRESH_MARKET_AND_SUPER_DOSH", FRESH_MARKET_PROMOFULL, "001"),
    ("YELLOW", YELLOW_PROMOFULL, "202"),
)

_EXTENSIONS = ("", ".xml", ".gz", ".xml.gz")


def _promotions_xml(chain_id, store_id):
    return f"""\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>{chain_id}</ChainId>
  <SubChainId>001</SubChainId>
  <StoreId>{store_id}</StoreId>
  <BikoretNo>0</BikoretNo>
  <Promotions>
    <Promotion>
      <PromotionId>9001</PromotionId>
      <PromotionDescription>Test promo</PromotionDescription>
      <PromotionUpdateDate>2026-09-02 00:00</PromotionUpdateDate>
    </Promotion>
    <Promotion>
      <PromotionId>9002</PromotionId>
      <PromotionDescription>Second promo</PromotionDescription>
      <PromotionUpdateDate>2026-09-02 00:00</PromotionUpdateDate>
    </Promotion>
  </Promotions>
</Root>
"""


async def _collect(loader, **kwargs):
    results = []
    async for dump_file in loader.load(**kwargs):
        results.append(dump_file)
    return results


async def _read_rows(parser_name, folder, file_name):
    dump_file = file_name_to_components(folder, file_name)
    parser = ParserFactory.get(parser_name)()
    return [row async for row in parser.read(dump_file)]


class PromoFullFilenameDetectionTestCase(unittest.TestCase):
    """Issue filename patterns must map to PROMO_FULL_FILE, including .gz names."""

    def test_issue_stems_are_promofull(self):
        """Every stem from issues #91/#93/#95 is classified as PromoFull."""
        for _parser, stem, store in _PROMOFULL_CASES:
            for ext in _EXTENSIONS:
                name = stem + ext
                with self.subTest(name=name):
                    dump_file = file_name_to_components("/tmp", name)
                    self.assertEqual(
                        dump_file.detected_filetype, FileTypesFilters.PROMO_FULL_FILE
                    )
                    self.assertEqual(dump_file.extracted_store_number, store)
                    self.assertEqual(
                        dump_file.extracted_date.strftime("%Y%m%d"), "20260902"
                    )


class PromoFullDataLoaderPickupTestCase(unittest.IsolatedAsyncioTestCase):
    """DataLoader must yield PromoFull dumps from PascalCase and kaggle-stem folders."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self._tmp.name

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write(self, folder_name, filename):
        path = os.path.join(self.root, folder_name)
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, filename), "w", encoding="utf-8") as handle:
            handle.write("")
        return path

    async def test_pascal_case_folders_with_issue_names(self):
        """Production DumpFolderNames folders still pick up the issue filenames."""
        for parser_name, stem, _store in _PROMOFULL_CASES:
            folder = DumpFolderNames[parser_name].value
            self._write(folder, stem + ".gz")

        loader = DataLoader(self.root)
        for parser_name, stem, _store in _PROMOFULL_CASES:
            with self.subTest(parser=parser_name):
                results = await _collect(
                    loader,
                    enabled_scraper=[parser_name],
                    files_types=["PROMO_FULL_FILE"],
                )
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].file_name, stem + ".gz")
                self.assertEqual(
                    results[0].detected_filetype, FileTypesFilters.PROMO_FULL_FILE
                )

    async def test_lowercase_kaggle_stems_with_issue_names(self):
        """Kaggle zips use lowercase dump stems; those folders must still match."""
        for parser_name, stem, _store in _PROMOFULL_CASES:
            folder = DumpFolderNames[parser_name].value.lower()
            self._write(folder, stem)

        loader = DataLoader(self.root)
        for parser_name, stem, _store in _PROMOFULL_CASES:
            with self.subTest(parser=parser_name):
                results = await _collect(
                    loader,
                    enabled_scraper=[parser_name],
                    files_types=["PROMO_FULL_FILE"],
                )
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].file_name, stem)
                self.assertEqual(
                    results[0].detected_filetype, FileTypesFilters.PROMO_FULL_FILE
                )


class PromoFullParserEmitsRowsTestCase(unittest.IsolatedAsyncioTestCase):
    """Each chain's PromoFull parser must emit rows for the issue filename."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.folder = self._tmp.name

    def tearDown(self) -> None:
        self._tmp.cleanup()

    async def test_promotions_layout_yields_rows(self):
        """Standard <Promotions> PromoFull XML yields two rows per chain."""
        for parser_name, stem, store in _PROMOFULL_CASES:
            dump_file = file_name_to_components("/tmp", stem)
            xml = _promotions_xml(dump_file.extracted_chain_id, store)
            path = os.path.join(self.folder, stem + ".xml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(xml)
            with self.subTest(parser=parser_name, name=stem):
                rows = await _read_rows(parser_name, self.folder, stem + ".xml")
                self.assertEqual(len(rows), 2)
                self.assertEqual([row["promotionid"] for row in rows], ["9001", "9002"])
                self.assertEqual(rows[0]["chainid"], dump_file.extracted_chain_id)
                self.assertEqual(rows[0]["storeid"], store)


if __name__ == "__main__":
    unittest.main()
