import asyncio
import os
import tempfile

import pandas as pd
import pytest

from il_supermarket_parsers.documents import (
    FirstPresentXmlDataFrameConverter,
    XmlDataFrameConverter,
)

_ROOTS = ["ChainId", "SubChainId", "StoreId", "BikoretNo"]

HEADER = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290644700005</ChainId>
  <SubChainId>001</SubChainId>
  <StoreId>255</StoreId>
  <BikoretNo>0</BikoretNo>
"""


def _price_converter(list_key):
    """Minimal price converter for a given row wrapper."""
    return XmlDataFrameConverter(
        list_key=list_key,
        id_field="ItemCode",
        roots=_ROOTS,
    )


def _first_present():
    """Items → Products → Details (legacy fallback)."""
    return FirstPresentXmlDataFrameConverter(
        [
            _price_converter("Items"),
            _price_converter("Products"),
            _price_converter("Details"),
        ]
    )


def convert_to_dataframe(converter, found_store, file_name, **kwarg):
    """Sync wrapper: run async convert and return a DataFrame."""

    async def _collect():
        rows = []
        async for row in converter.convert(found_store, file_name, **kwarg):
            rows.append(row)
        return pd.DataFrame(rows)

    return asyncio.run(_collect())


def _write_and_parse(content, file_name="Price.xml"):
    """Write XML to a temp folder and parse it with the 3-way converter."""
    converter = _first_present()
    with tempfile.TemporaryDirectory() as folder:
        with open(os.path.join(folder, file_name), "w", encoding="utf-8") as handle:
            handle.write(content)
        return convert_to_dataframe(converter, folder, file_name)


def test_first_key_present():
    """When the first wrapper exists, that converter is used."""
    xml = (
        HEADER
        + """\
  <Items>
    <Item>
      <ItemCode>1001</ItemCode>
      <ItemName>Coffee</ItemName>
    </Item>
  </Items>
</Root>
"""
    )
    df = _write_and_parse(xml)
    assert list(df["itemcode"]) == ["1001"]


def test_middle_key_present():
    """When only a middle wrapper exists, that converter is used."""
    xml = (
        HEADER
        + """\
  <Products>
    <Product>
      <ItemCode>2001</ItemCode>
      <ItemName>Bread</ItemName>
    </Product>
  </Products>
</Root>
"""
    )
    df = _write_and_parse(xml)
    assert list(df["itemcode"]) == ["2001"]


def test_only_fallback_present():
    """When none of the earlier wrappers exist, the last converter runs."""
    xml = (
        HEADER
        + """\
  <Details>
    <Line>
      <ItemCode>3001</ItemCode>
      <ItemName>Eggs</ItemName>
    </Line>
  </Details>
</Root>
"""
    )
    df = _write_and_parse(xml)
    assert list(df["itemcode"]) == ["3001"]


def test_empty_first_wrapper_does_not_fall_through():
    """An empty but present first wrapper wins over later wrappers with data."""
    xml = (
        HEADER
        + """\
  <Items></Items>
  <Products>
    <Product>
      <ItemCode>9999</ItemCode>
      <ItemName>Should not be parsed</ItemName>
    </Product>
  </Products>
</Root>
"""
    )
    df = _write_and_parse(xml)
    assert df.empty


def test_missing_wrappers_yields_no_rows():
    """No candidate or fallback wrapper: zero rows, no error."""
    xml = HEADER + "</Root>\n"
    converter = _first_present()
    file_name = "PriceEmpty.xml"
    with tempfile.TemporaryDirectory() as folder:
        with open(os.path.join(folder, file_name), "w", encoding="utf-8") as handle:
            handle.write(xml)
        df = convert_to_dataframe(converter, folder, file_name)
        assert df.empty
        converter.validate_succussful_extraction(df, os.path.join(folder, file_name))


def test_in_memory_content_uses_first_present_key():
    """Queue-based files (file_content) still pick the first present wrapper."""
    xml = (
        HEADER
        + """\
  <Products>
    <Product>
      <ItemCode>2001</ItemCode>
      <ItemName>Bread</ItemName>
    </Product>
  </Products>
</Root>
"""
    )
    converter = _first_present()
    df = convert_to_dataframe(
        converter,
        "queue",
        "Price.xml",
        file_content=xml.encode("utf-8"),
    )
    assert list(df["itemcode"]) == ["2001"]


def test_requires_at_least_two_options():
    """A single converter is not a first-present chain."""
    with pytest.raises(ValueError, match="at least two"):
        FirstPresentXmlDataFrameConverter([_price_converter("Items")])
