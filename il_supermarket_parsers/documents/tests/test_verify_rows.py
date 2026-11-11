"""Production extraction verifier (``verify_rows``) on small synthetic XML."""

import asyncio
import copy
import os

import pandas as pd
import pytest

from il_supermarket_parsers.documents.xml_dataframe_parser import XmlDataFrameConverter
from il_supermarket_parsers.documents.xml_dataframe_subroot_praser import (
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
)
from il_supermarket_parsers.documents.conditional_xml_dataframe_parser import (
    ConditionalXmlDataFrameConverter,
)

PROMO_XML = """<?xml version="1.0" encoding="utf-8"?>
<Root>
  <XmlDocVersion>1</XmlDocVersion>
  <ChainId>7290000000001</ChainId>
  <SubChainId>001</SubChainId>
  <StoreId>042</StoreId>
  <BikoretNo>9</BikoretNo>
  <Promotions>
    <Promotion>
      <PromotionId>100</PromotionId>
      <PromotionDescription>two for one</PromotionDescription>
      <PromotionItems>
        <Item><ItemCode>1</ItemCode><IsGiftItem>0</IsGiftItem></Item>
        <Item><ItemCode>2</ItemCode><IsGiftItem>0</IsGiftItem></Item>
      </PromotionItems>
    </Promotion>
    <Promotion>
      <PromotionId>101</PromotionId>
      <PromotionDescription>line
break</PromotionDescription>
      <PromotionItems>
        <Item><ItemCode>3</ItemCode><IsGiftItem>1</IsGiftItem></Item>
      </PromotionItems>
    </Promotion>
  </Promotions>
</Root>
"""

EMPTY_XML = """<?xml version="1.0" encoding="utf-8"?>
<Root><ChainId>7290000000001</ChainId><Promotions /></Root>
"""

STORES_XML = """<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290000000001</ChainId>
  <ChainName>Chain</ChainName>
  <SubChains>
    <SubChain>
      <SubChainId>1</SubChainId>
      <SubChainName>Main</SubChainName>
      <Stores>
        <Store><StoreId>1</StoreId><StoreName>A</StoreName></Store>
        <Store><StoreId>2</StoreId><StoreName>B</StoreName></Store>
      </Stores>
    </SubChain>
  </SubChains>
</Root>
"""


def _promo_converter():
    return XmlDataFrameConverter(
        list_key="Promotions",
        id_field="PromotionId",
        roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        ignore_column=["XmlDocVersion", "DllVerNo"],
    )


def _write(tmp_path, content, name="PromoFull7290000000001-001-042-202611110000.xml"):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(tmp_path), name


def _convert(converter, folder, name, keep_document=True):
    async def _collect():
        return [
            row
            async for row in converter.convert(
                folder, name, keep_document=keep_document
            )
        ]

    return asyncio.run(_collect())


def _expect_failure(converter, folder, name, mutate, match):
    rows = _convert(converter, folder, name)
    rows = mutate(copy.deepcopy(rows))
    with pytest.raises(ValueError, match=match):
        converter.verify_rows(rows)


def test_correct_file_passes(tmp_path):
    """Correct file passes."""
    folder, name = _write(tmp_path, PROMO_XML)
    converter = _promo_converter()
    rows = _convert(converter, folder, name)
    assert len(rows) == 2
    converter.verify_rows(rows)


def test_matches_test_suite_validation(tmp_path):
    """The old DataFrame check accepts what the new one accepts."""
    folder, name = _write(tmp_path, PROMO_XML)
    converter = _promo_converter()
    rows = _convert(converter, folder, name)
    converter.verify_rows(rows)
    converter.validate_succussful_extraction(
        pd.DataFrame(rows), os.path.join(folder, name)
    )


def test_empty_file_passes(tmp_path):
    """Empty file passes."""
    folder, name = _write(tmp_path, EMPTY_XML)
    converter = _promo_converter()
    rows = _convert(converter, folder, name)
    assert not rows
    converter.verify_rows(rows)


def test_dropped_row_fails(tmp_path):
    """Dropped row fails."""
    folder, name = _write(tmp_path, PROMO_XML)
    _expect_failure(
        _promo_converter(), folder, name, lambda rows: rows[:1], "missing data"
    )


def test_dropped_tag_fails(tmp_path):
    """Dropped tag fails."""

    def drop(rows):
        for row in rows:
            del row["promotiondescription"]
        return rows

    folder, name = _write(tmp_path, PROMO_XML)
    _expect_failure(_promo_converter(), folder, name, drop, "didn't get")


def test_wrong_nested_count_fails(tmp_path):
    """Wrong nested count fails."""

    def drop_item(rows):
        items = rows[0]["promotionitems"]["item"]
        rows[0]["promotionitems"]["item"] = items[:1]
        return rows

    folder, name = _write(tmp_path, PROMO_XML)
    _expect_failure(
        _promo_converter(), folder, name, drop_item, "element count mismatch"
    )


def test_edited_cell_fails(tmp_path):
    """Edited cell fails."""

    def edit(rows):
        rows[1]["promotiondescription"] = "something else"
        return rows

    folder, name = _write(tmp_path, PROMO_XML)
    _expect_failure(_promo_converter(), folder, name, edit, "content mismatch")


def test_edited_header_fails(tmp_path):
    """Edited header fails."""

    def edit(rows):
        rows[0]["storeid"] = "043"
        return rows

    folder, name = _write(tmp_path, PROMO_XML)
    _expect_failure(_promo_converter(), folder, name, edit, "content mismatch")


def test_missing_root_column_fails(tmp_path):
    """Missing root column fails."""

    def drop(rows):
        for row in rows:
            del row["bikoretno"]
        return rows

    folder, name = _write(tmp_path, PROMO_XML)
    _expect_failure(_promo_converter(), folder, name, drop, "bikoretno missing")


def test_ignored_tag_on_a_row_fails(tmp_path):
    """Ignored tag on a row fails."""
    xml = PROMO_XML.replace(
        "<PromotionId>101</PromotionId>",
        "<PromotionId>101</PromotionId><DllVerNo>5</DllVerNo>",
    )
    folder, name = _write(tmp_path, xml)
    converter = _promo_converter()
    rows = _convert(converter, folder, name)
    with pytest.raises(ValueError, match="ignored tag"):
        converter.verify_rows(rows)


def test_needs_kept_document(tmp_path):
    """Needs kept document."""
    folder, name = _write(tmp_path, PROMO_XML)
    converter = _promo_converter()
    rows = _convert(converter, folder, name, keep_document=False)
    with pytest.raises(RuntimeError, match="keep_document"):
        converter.verify_rows(rows)


def test_document_released_after_verify(tmp_path):
    """Document released after verify."""
    folder, name = _write(tmp_path, PROMO_XML)
    converter = _promo_converter()
    rows = _convert(converter, folder, name)
    converter.verify_rows(rows)
    with pytest.raises(RuntimeError):
        converter.verify_rows(rows)


def test_queue_content_is_verified():
    """Queue content is verified."""
    converter = _promo_converter()

    async def _collect():
        return [
            row
            async for row in converter.convert(
                "queue",
                "PromoFull.xml",
                file_content=PROMO_XML.encode("utf-8"),
                keep_document=True,
            )
        ]

    converter.verify_rows(asyncio.run(_collect()))
    rows = asyncio.run(_collect())[1:]
    with pytest.raises(ValueError):
        converter.verify_rows(rows)


def _stores_converter():
    return SubRootedXmlDataFrameConverter(
        list_key="SubChains",
        id_field="StoreId",
        options=SubRootedXmlOptions(
            sub_roots=["SubChainId", "SubChainName"],
            list_sub_key="Stores",
            roots=["ChainId", "ChainName"],
        ),
    )


def test_sub_rooted_file(tmp_path):
    """Sub rooted file."""
    folder, name = _write(
        tmp_path, STORES_XML, "Stores7290000000001-000-202611110000.xml"
    )
    converter = _stores_converter()
    rows = _convert(converter, folder, name)
    assert len(rows) == 2
    converter.verify_rows(rows)

    def edit(rows):
        rows[1]["subchainname"] = "Other"
        return rows

    _expect_failure(_stores_converter(), folder, name, edit, "content mismatch")


def test_conditional_delegates_to_picked_parser(tmp_path):
    """Conditional delegates to picked parser."""
    folder, name = _write(tmp_path, PROMO_XML)
    converter = ConditionalXmlDataFrameConverter(
        option_a=_promo_converter(),
        option_b=XmlDataFrameConverter(list_key="Items", id_field="ItemCode"),
        check_key="Promotions",
    )
    rows = _convert(converter, folder, name)
    converter.verify_rows(rows)
    rows = _convert(converter, folder, name)
    with pytest.raises(ValueError):
        converter.verify_rows(rows[1:])
