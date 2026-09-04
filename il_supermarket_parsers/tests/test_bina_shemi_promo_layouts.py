"""Offline regression tests for Bina/Shemi promo layout.

Maayan, Shuk Ahir, Super Sapir, and Netiv Hased share this dump shape.

These chains publish promo files under ``<Promotions>`` with ``ChainID`` /
``PromotionID`` / ``PromotionUpdateTime``. Incremental Promo dumps are often a
header plus an empty ``<Promotions></Promotions>`` wrapper (no daily changes).
That is genuine empty XML, not a missing ``list_key``. Files that do contain
promotions — and the BigID legacy ``<Sales>`` wrapper — must keep parsing.

These tests run without network access, so they still guard the parser when the
live-source tests in ``parsers/tests/test_all.py`` skip.
"""

import asyncio
import os
import tempfile
import unittest

from il_supermarket_parsers.parsers.other import (
    Maayan2000FileConverter,
    NetivHasedFileConverter,
    ShukAhirFileConverter,
    SuperSapirFileConverter,
)
from il_supermarket_parsers.utils.loading_utils import file_name_to_components

_CONVERTERS = (
    Maayan2000FileConverter,
    NetivHasedFileConverter,
    ShukAhirFileConverter,
    SuperSapirFileConverter,
)

PROMO_PROMOTIONS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainID>7290058159628</ChainID>
  <SubChainID>000</SubChainID>
  <StoreID>065</StoreID>
  <BikoretNo>0</BikoretNo>
  <Promotions>
    <Promotion>
      <PromotionUpdateTime>2026-09-03T17:03:10.734</PromotionUpdateTime>
      <PromotionID>254332</PromotionID>
      <PromotionDescription>Two for one</PromotionDescription>
    </Promotion>
    <Promotion>
      <PromotionUpdateTime>2026-09-03T17:03:10.734</PromotionUpdateTime>
      <PromotionID>254331</PromotionID>
      <PromotionDescription>Half price</PromotionDescription>
    </Promotion>
  </Promotions>
</Root>
"""

PROMO_SALES_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainID>7290058159628</ChainID>
  <SubChainID>000</SubChainID>
  <StoreID>065</StoreID>
  <BikoretNo>0</BikoretNo>
  <Sales>
    <Sale>
      <PromotionUpdateTime>2026-09-03T17:03:10.734</PromotionUpdateTime>
      <PromotionID>8001</PromotionID>
      <PromotionDescription>Bundle deal</PromotionDescription>
    </Sale>
  </Sales>
</Root>
"""

PROMO_EMPTY_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainID>7290058159628</ChainID>
  <SubChainID>000</SubChainID>
  <StoreID>078</StoreID>
  <BikoretNo>0</BikoretNo>
  <Promotions></Promotions>
</Root>
"""


async def _read_rows(converter_cls, folder, file_name):
    """Parse one file with the given converter and return the rows."""
    dump_file = file_name_to_components(folder, file_name)
    parser = converter_cls()
    return [row async for row in parser.read(dump_file)]


def _parse(converter_cls, file_name, content):
    """Write content to a temp folder and parse it."""
    with tempfile.TemporaryDirectory() as folder:
        with open(os.path.join(folder, file_name), "w", encoding="utf-8") as handle:
            handle.write(content)
        return asyncio.run(_read_rows(converter_cls, folder, file_name))


class BinaShemiPromoLayoutTestCase(unittest.TestCase):
    """Promotions, legacy Sales, and empty Promotions wrappers must all be handled."""

    def _assert_ids(self, rows, expected_ids):
        self.assertEqual(len(rows), len(expected_ids))
        self.assertEqual([row["promotionid"] for row in rows], expected_ids)

    def test_promo_promotions_layout(self):
        """Promo using the current <Promotions> wrapper yields rows."""
        for converter_cls in _CONVERTERS:
            with self.subTest(converter=converter_cls.__name__):
                rows = _parse(
                    converter_cls,
                    "Promo7290058159628-000-065-20260903-170052.xml",
                    PROMO_PROMOTIONS_XML,
                )
                self._assert_ids(rows, ["254332", "254331"])
                self.assertEqual(rows[0]["chainid"], "7290058159628")
                self.assertEqual(rows[0]["storeid"], "065")

    def test_promo_legacy_sales_layout(self):
        """Promo using the BigID legacy <Sales> wrapper still yields rows."""
        for converter_cls in _CONVERTERS:
            with self.subTest(converter=converter_cls.__name__):
                rows = _parse(
                    converter_cls,
                    "Promo7290058159628-000-065-20260903-170052.xml",
                    PROMO_SALES_XML,
                )
                self._assert_ids(rows, ["8001"])

    def test_promofull_promotions_layout(self):
        """PromoFull using the current <Promotions> wrapper yields rows."""
        for converter_cls in _CONVERTERS:
            with self.subTest(converter=converter_cls.__name__):
                rows = _parse(
                    converter_cls,
                    "PromoFull7290058159628-000-065-20260904-050352.xml",
                    PROMO_PROMOTIONS_XML,
                )
                self._assert_ids(rows, ["254332", "254331"])

    def test_promofull_legacy_sales_layout(self):
        """PromoFull using the BigID legacy <Sales> wrapper still yields rows."""
        for converter_cls in _CONVERTERS:
            with self.subTest(converter=converter_cls.__name__):
                rows = _parse(
                    converter_cls,
                    "PromoFull7290058159628-000-065-20260904-050352.xml",
                    PROMO_SALES_XML,
                )
                self._assert_ids(rows, ["8001"])

    def test_empty_promotions_is_not_a_wrong_list_key(self):
        """An empty <Promotions/> wrapper yields zero rows for both Promo and PromoFull.

        Live incremental dumps (and some stores with no promotions) publish this
        exact document. The wrapper is present; there are simply no Promotion
        children. A Sales-only parser would look the same (zero rows), so the
        Promotions-with-data tests above are what prove the list_key.
        """
        for converter_cls in _CONVERTERS:
            for file_name in (
                "Promo7290058156016-000-078-20260902-083910.xml",
                "PromoFull7290058148776-000-322-20260902-051138.xml",
            ):
                with self.subTest(converter=converter_cls.__name__, file_name=file_name):
                    rows = _parse(converter_cls, file_name, PROMO_EMPTY_XML)
                    self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
