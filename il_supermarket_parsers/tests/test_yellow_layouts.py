"""Offline regression tests for Yellow price/promo XML layout drift.

Store 255 PriceFull files (#91) parsed with zero rows under the default
``<Items>`` wrapper. Yellow also ships ``<Products>`` and legacy ``<Details>``
price dumps, plus ``<Promotions>`` / ``<Sales>`` / ``<Details>`` promo dumps.
All of those wrappers must keep yielding rows.
"""

import asyncio
import os
import tempfile
import unittest

from il_supermarket_parsers.parsers.other import YellowFileConverter
from il_supermarket_parsers.utils.loading_utils import file_name_to_components

PRICE_ITEMS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290644700005</ChainId>
  <SubChainId>001</SubChainId>
  <StoreId>255</StoreId>
  <BikoretNo>0</BikoretNo>
  <Items>
    <Item>
      <ItemCode>1001</ItemCode>
      <ItemName>Coffee</ItemName>
      <ItemPrice>12.90</ItemPrice>
    </Item>
    <Item>
      <ItemCode>1002</ItemCode>
      <ItemName>Milk</ItemName>
      <ItemPrice>6.50</ItemPrice>
    </Item>
  </Items>
</Root>
"""

PRICE_PRODUCTS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290644700005</ChainId>
  <SubChainId>001</SubChainId>
  <StoreId>255</StoreId>
  <BikoretNo>0</BikoretNo>
  <Products>
    <Product>
      <ItemCode>2001</ItemCode>
      <ItemName>Bread</ItemName>
      <ItemPrice>8.90</ItemPrice>
    </Product>
  </Products>
</Root>
"""

PRICE_DETAILS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290644700005</ChainId>
  <SubChainId>001</SubChainId>
  <StoreId>255</StoreId>
  <BikoretNo>0</BikoretNo>
  <Details>
    <Line>
      <ItemCode>3001</ItemCode>
      <ItemName>Eggs</ItemName>
      <ItemPrice>14.90</ItemPrice>
    </Line>
  </Details>
</Root>
"""

PROMO_PROMOTIONS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290644700005</ChainId>
  <SubChainId>001</SubChainId>
  <StoreId>202</StoreId>
  <BikoretNo>0</BikoretNo>
  <Promotions>
    <Promotion>
      <PromotionId>4001</PromotionId>
      <PromotionDescription>Two for one</PromotionDescription>
      <PromotionUpdateDate>2026-09-02 00:16</PromotionUpdateDate>
    </Promotion>
  </Promotions>
</Root>
"""

PROMO_SALES_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290644700005</ChainId>
  <SubChainId>001</SubChainId>
  <StoreId>202</StoreId>
  <BikoretNo>0</BikoretNo>
  <Sales>
    <Sale>
      <PromotionId>5001</PromotionId>
      <PromotionDescription>Bundle</PromotionDescription>
      <PromotionUpdateDate>2026-09-02 00:16</PromotionUpdateDate>
    </Sale>
  </Sales>
</Root>
"""

PROMO_DETAILS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290644700005</ChainId>
  <SubChainId>001</SubChainId>
  <StoreId>202</StoreId>
  <BikoretNo>0</BikoretNo>
  <Details>
    <Line>
      <PromotionId>6001</PromotionId>
      <PromotionDescription>Legacy promo</PromotionDescription>
      <PromotionUpdateDate>2026-09-02 00:16</PromotionUpdateDate>
    </Line>
  </Details>
</Root>
"""

# Exact names from issue #91.
PRICEFULL_255_NAME = "PriceFull7290644700005-001-255-20260902-001501.xml"
PRICEFULL_255_NEXT_DAY = "PriceFull7290644700005-001-255-20260903-001514.xml"
PROMOFULL_NAME = "PromoFull7290644700005-001-202-20260902-001615.xml"


async def _read_rows(folder, file_name):
    """Parse one file with the Yellow converter and return the rows."""
    dump_file = file_name_to_components(folder, file_name)
    parser = YellowFileConverter()
    return [row async for row in parser.read(dump_file)]


def _parse(file_name, content):
    """Write content to a temp folder and parse it."""
    with tempfile.TemporaryDirectory() as folder:
        with open(os.path.join(folder, file_name), "w", encoding="utf-8") as handle:
            handle.write(content)
        return asyncio.run(_read_rows(folder, file_name))


class YellowLayoutTestCase(unittest.TestCase):
    """Yellow price and promo wrappers must all parse, including store 255."""

    def test_pricefull_items_layout(self):
        """Store 255 PriceFull using the default <Items> wrapper yields rows."""
        rows = _parse(PRICEFULL_255_NAME, PRICE_ITEMS_XML)
        self.assertEqual([row["itemcode"] for row in rows], ["1001", "1002"])
        self.assertEqual(rows[0]["chainid"], "7290644700005")
        self.assertEqual(rows[0]["storeid"], "255")

    def test_pricefull_products_layout(self):
        """Store 255 PriceFull using <Products> still yields rows."""
        rows = _parse(PRICEFULL_255_NEXT_DAY, PRICE_PRODUCTS_XML)
        self.assertEqual([row["itemcode"] for row in rows], ["2001"])
        self.assertEqual(rows[0]["storeid"], "255")

    def test_pricefull_legacy_details_layout(self):
        """Store 255 PriceFull using legacy <Details> still yields rows."""
        rows = _parse(PRICEFULL_255_NAME, PRICE_DETAILS_XML)
        self.assertEqual([row["itemcode"] for row in rows], ["3001"])

    def test_promofull_promotions_layout(self):
        """PromoFull using the current <Promotions> wrapper yields rows."""
        rows = _parse(PROMOFULL_NAME, PROMO_PROMOTIONS_XML)
        self.assertEqual([row["promotionid"] for row in rows], ["4001"])
        self.assertEqual(rows[0]["storeid"], "202")

    def test_promofull_legacy_sales_layout(self):
        """PromoFull using the BigID legacy <Sales> wrapper still yields rows."""
        rows = _parse(PROMOFULL_NAME, PROMO_SALES_XML)
        self.assertEqual([row["promotionid"] for row in rows], ["5001"])

    def test_promofull_legacy_details_layout(self):
        """PromoFull using the legacy <Details> wrapper still yields rows."""
        rows = _parse(PROMOFULL_NAME, PROMO_DETAILS_XML)
        self.assertEqual([row["promotionid"] for row in rows], ["6001"])


if __name__ == "__main__":
    unittest.main()
