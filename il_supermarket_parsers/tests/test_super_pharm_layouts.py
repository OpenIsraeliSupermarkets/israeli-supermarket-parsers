"""Offline regression tests for Super-Pharm XML layout drift.

Super-Pharm migrated price files from the legacy ``<Details>`` wrapper to the
standard ``<Items>`` layout. Both shapes must keep parsing, because historical
dumps still use the legacy wrapper.

These tests run without network access, so they still guard the parser when the
live-source tests in ``parsers/tests/test_all.py`` skip due to an unreachable
Super-Pharm endpoint.
"""

import asyncio
import os
import tempfile
import unittest

from il_supermarket_parsers.parsers.super_pharm import SuperPharmFileConverter
from il_supermarket_parsers.utils.loading_utils import file_name_to_components

PRICE_ITEMS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290172900007</ChainId>
  <SubChainId>000</SubChainId>
  <StoreId>667</StoreId>
  <BikoretNo>0</BikoretNo>
  <Items>
    <Item>
      <ItemCode>1001</ItemCode>
      <ItemName>Shampoo</ItemName>
      <ItemPrice>19.90</ItemPrice>
    </Item>
    <Item>
      <ItemCode>1002</ItemCode>
      <ItemName>Toothpaste</ItemName>
      <ItemPrice>12.50</ItemPrice>
    </Item>
  </Items>
</Root>
"""

PRICE_DETAILS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290172900007</ChainId>
  <SubChainId>000</SubChainId>
  <StoreId>667</StoreId>
  <BikoretNo>0</BikoretNo>
  <Details>
    <Line>
      <ItemCode>2001</ItemCode>
      <ItemName>Soap</ItemName>
      <ItemPrice>8.90</ItemPrice>
    </Line>
    <Line>
      <ItemCode>2002</ItemCode>
      <ItemName>Vitamins</ItemName>
      <ItemPrice>45.00</ItemPrice>
    </Line>
  </Details>
</Root>
"""

PROMO_PROMOTIONS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290172900007</ChainId>
  <SubChainId>000</SubChainId>
  <StoreId>667</StoreId>
  <BikoretNo>0</BikoretNo>
  <Promotions>
    <Promotion>
      <PromotionId>3001</PromotionId>
      <PromotionDescription>Two for one</PromotionDescription>
    </Promotion>
  </Promotions>
</Root>
"""

PROMO_DETAILS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290172900007</ChainId>
  <SubChainId>000</SubChainId>
  <StoreId>667</StoreId>
  <BikoretNo>0</BikoretNo>
  <Details>
    <Line>
      <PromotionId>4001</PromotionId>
      <PromotionDescription>Half price</PromotionDescription>
    </Line>
  </Details>
</Root>
"""


async def _read_rows(folder, file_name):
    """Parse one file with the Super-Pharm converter and return the rows."""
    dump_file = file_name_to_components(folder, file_name)
    parser = SuperPharmFileConverter()
    return [row async for row in parser.read(dump_file)]


def _parse(file_name, content):
    """Write content to a temp folder and parse it."""
    with tempfile.TemporaryDirectory() as folder:
        with open(os.path.join(folder, file_name), "w", encoding="utf-8") as handle:
            handle.write(content)
        return asyncio.run(_read_rows(folder, file_name))


class SuperPharmLayoutTestCase(unittest.TestCase):
    """Both the current and legacy Super-Pharm layouts must parse."""

    def _assert_ids(self, rows, expected_ids, id_column):
        self.assertEqual(len(rows), len(expected_ids))
        self.assertEqual([row[id_column] for row in rows], expected_ids)

    def test_pricefull_items_layout(self):
        """PriceFull using the standard <Items> wrapper yields rows."""
        rows = _parse("PriceFull7290172900007-000-202608260000.xml", PRICE_ITEMS_XML)
        self._assert_ids(rows, ["1001", "1002"], "itemcode")

    def test_pricefull_legacy_details_layout(self):
        """PriceFull using the legacy <Details> wrapper still yields rows."""
        rows = _parse("PriceFull7290172900007-000-202608260000.xml", PRICE_DETAILS_XML)
        self._assert_ids(rows, ["2001", "2002"], "itemcode")

    def test_price_items_layout(self):
        """Price using the standard <Items> wrapper yields rows."""
        rows = _parse("Price7290172900007-000-202608260000.xml", PRICE_ITEMS_XML)
        self._assert_ids(rows, ["1001", "1002"], "itemcode")

    def test_price_legacy_details_layout(self):
        """Price using the legacy <Details> wrapper still yields rows."""
        rows = _parse("Price7290172900007-000-202608260000.xml", PRICE_DETAILS_XML)
        self._assert_ids(rows, ["2001", "2002"], "itemcode")

    def test_promofull_promotions_layout(self):
        """PromoFull using the standard <Promotions> wrapper yields rows."""
        rows = _parse(
            "PromoFull7290172900007-000-202608260000.xml", PROMO_PROMOTIONS_XML
        )
        self._assert_ids(rows, ["3001"], "promotionid")

    def test_promofull_legacy_details_layout(self):
        """PromoFull using the legacy <Details> wrapper still yields rows."""
        rows = _parse("PromoFull7290172900007-000-202608260000.xml", PROMO_DETAILS_XML)
        self._assert_ids(rows, ["4001"], "promotionid")

    def test_promo_legacy_details_layout(self):
        """Promo using the legacy <Details> wrapper still yields rows."""
        rows = _parse("Promo7290172900007-000-202608260000.xml", PROMO_DETAILS_XML)
        self._assert_ids(rows, ["4001"], "promotionid")

    def test_price_roots_are_promoted_to_columns(self):
        """Header fields are attached to rows in both layouts."""
        for content in (PRICE_ITEMS_XML, PRICE_DETAILS_XML):
            rows = _parse("PriceFull7290172900007-000-202608260000.xml", content)
            self.assertEqual(rows[0]["chainid"], "7290172900007")
            self.assertEqual(rows[0]["storeid"], "667")


if __name__ == "__main__":
    unittest.main()
