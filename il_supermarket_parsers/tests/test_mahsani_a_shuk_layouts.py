"""Offline regression tests for Mahsani A Shuk (new source) promo layout drift.

The new source publishes promo files under ``<Promotions>``, matching the
already-working PromoFull parser. Incremental Promo files previously fell
through to the BigID default ``<Sales>`` wrapper and produced zero rows
(``CSV file was not created`` in CI). Both wrappers must keep parsing.
"""

import asyncio
import os
import tempfile
import unittest

from il_supermarket_parsers.parsers.mahsani_a_shuk import MahsaniAShukNewFileConverter
from il_supermarket_parsers.utils.loading_utils import file_name_to_components

PROMO_PROMOTIONS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainID>7290661400001</ChainID>
  <SubChainID>001</SubChainID>
  <StoreID>078</StoreID>
  <BikoretNo>0</BikoretNo>
  <Promotions>
    <Promotion>
      <PromotionID>9001</PromotionID>
      <PromotionDescription>Two for one</PromotionDescription>
      <PromotionUpdateTime>2026-08-27T16:12:15</PromotionUpdateTime>
    </Promotion>
    <Promotion>
      <PromotionID>9002</PromotionID>
      <PromotionDescription>Half price</PromotionDescription>
      <PromotionUpdateTime>2026-08-27T16:12:15</PromotionUpdateTime>
    </Promotion>
  </Promotions>
</Root>
"""

PROMO_SALES_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainID>7290661400001</ChainID>
  <SubChainID>001</SubChainID>
  <StoreID>078</StoreID>
  <BikoretNo>0</BikoretNo>
  <Sales>
    <Sale>
      <PromotionID>8001</PromotionID>
      <PromotionDescription>Bundle deal</PromotionDescription>
      <PromotionUpdateTime>2026-08-27T16:12:15</PromotionUpdateTime>
    </Sale>
  </Sales>
</Root>
"""


async def _read_rows(folder, file_name):
    """Parse one file with the Mahsani new-source converter and return the rows."""
    dump_file = file_name_to_components(folder, file_name)
    parser = MahsaniAShukNewFileConverter()
    return [row async for row in parser.read(dump_file)]


def _parse(file_name, content):
    """Write content to a temp folder and parse it."""
    with tempfile.TemporaryDirectory() as folder:
        with open(os.path.join(folder, file_name), "w", encoding="utf-8") as handle:
            handle.write(content)
        return asyncio.run(_read_rows(folder, file_name))


class MahsaniAShukNewSourceLayoutTestCase(unittest.TestCase):
    """Both current Promotions and legacy Sales promo layouts must parse."""

    def _assert_ids(self, rows, expected_ids):
        self.assertEqual(len(rows), len(expected_ids))
        self.assertEqual([row["promotionid"] for row in rows], expected_ids)

    def test_promo_promotions_layout(self):
        """Promo using the current <Promotions> wrapper yields rows."""
        rows = _parse(
            "Promo7290661400001-001-078-20260827-161215.xml", PROMO_PROMOTIONS_XML
        )
        self._assert_ids(rows, ["9001", "9002"])
        self.assertEqual(rows[0]["chainid"], "7290661400001")
        self.assertEqual(rows[0]["storeid"], "078")

    def test_promo_legacy_sales_layout(self):
        """Promo using the BigID legacy <Sales> wrapper still yields rows."""
        rows = _parse(
            "Promo7290661400001-001-078-20260827-161215.xml", PROMO_SALES_XML
        )
        self._assert_ids(rows, ["8001"])

    def test_promofull_promotions_layout(self):
        """PromoFull using the current <Promotions> wrapper yields rows."""
        rows = _parse(
            "PromoFull7290661400001-001-078-20260827-161215.xml", PROMO_PROMOTIONS_XML
        )
        self._assert_ids(rows, ["9001", "9002"])

    def test_promofull_legacy_sales_layout(self):
        """PromoFull using the BigID legacy <Sales> wrapper still yields rows."""
        rows = _parse(
            "PromoFull7290661400001-001-078-20260827-161215.xml", PROMO_SALES_XML
        )
        self._assert_ids(rows, ["8001"])


if __name__ == "__main__":
    unittest.main()
