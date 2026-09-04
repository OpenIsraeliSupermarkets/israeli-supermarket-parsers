import asyncio
import gzip
import os
import tempfile

import pandas as pd
import pytest

from il_supermarket_parsers.documents.xml_dataframe_parser import XmlDataFrameConverter
from il_supermarket_parsers.documents.xml_dataframe_subroot_praser import (
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
)
from il_supermarket_parsers.parsers.other import (
    KeshetFileConverter,
    RamiLevyFileConverter,
    WoltFileConverter,
)
from il_supermarket_parsers.parsers.salach_dabach import SalachDabachFileConverter
from il_supermarket_parsers.utils.loading_utils import EMPTY_FILE_TOEHOLD

TEST_DIR = "resources/xml"


def convert_to_dataframe(self, found_store, file_name, **kwarg):
    """Sync wrapper: run async convert and return a DataFrame."""

    async def _collect():
        rows = []
        async for row in self.convert(found_store, file_name, **kwarg):
            rows.append(row)
        return pd.DataFrame(rows)

    return asyncio.run(_collect())


def test_read_bad_encoding_1():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "PriceFull7290172900007-083-202409270311.xml",
    )
    converter.validate_succussful_extraction(
        df,
        f"{TEST_DIR}/PriceFull7290172900007-083-202409270311.xml",
        ignore_missing_columns=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
    )

    assert df.shape[0] > 0


def test_read_bad_encoding_2():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "PromoFull7290172900007-667-202409290706.xml",
    )
    converter.validate_succussful_extraction(
        df,
        f"{TEST_DIR}/PromoFull7290172900007-667-202409290706.xml",
        ignore_missing_columns=["SubChainId", "ChainId", "BikoretNo", "StoreId"],
    )
    assert df.shape[0] > 0


def test_bad_element():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="STORES", id_field="STOREID")
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "Stores7290027600007-000-202410020201",
    )
    converter.validate_succussful_extraction(
        df,
        f"{TEST_DIR}/Stores7290027600007-000-202410020201",
        ignore_missing_columns=["CHAINID", "LASTUPDATEDATE"],
    )
    assert df.shape[0] > 0


def test_gzip_dump_fails_to_convert():
    """Compressed dumps must not yield rows; extraction is the scraper's job."""
    source = os.path.join(TEST_DIR, "PriceFull7290172900007-083-202409270311.xml")
    with open(source, "rb") as handle:
        xml_bytes = handle.read()
    with tempfile.TemporaryDirectory() as tmp:
        gz_name = "PriceFull7290172900007-083-202409270311.xml.gz"
        gz_path = os.path.join(tmp, gz_name)
        with gzip.open(gz_path, "wb") as handle:
            handle.write(xml_bytes)
        converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
        with pytest.raises(ValueError, match="still compressed"):
            convert_to_dataframe(converter, tmp, gz_name)


def test_empty_file():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "Price7290725900003-9032-202410021600",
    )
    converter.validate_succussful_extraction(
        df,
        f"{TEST_DIR}/Price7290725900003-9032-202410021600",
        ignore_missing_columns=[
            "SubChainId",
            "DllVerNo",
            "ChainId",
            "BikoretNo",
            "StoreId",
            "XmlDocVersion",
        ],
    )


def test_empty_size():
    """test reading files that are the encoding in the file is not correct"""

    empty1 = os.path.getsize(
        f"{TEST_DIR}/PromoFull7290172900007-350-202410030634.xml",
    )

    assert empty1 <= EMPTY_FILE_TOEHOLD
    empty2 = os.path.getsize(
        f"{TEST_DIR}/Price7290725900003-9032-202410021600",
    )
    assert empty2 <= EMPTY_FILE_TOEHOLD


def test_file_1():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "PriceFull7290172900007-083-202409270311.xml",
    )
    converter.validate_succussful_extraction(
        df,
        f"{TEST_DIR}/PriceFull7290172900007-083-202409270311.xml",
        ignore_missing_columns=[
            "SubChainId",
            "DllVerNo",
            "ChainId",
            "BikoretNo",
            "StoreId",
            "XmlDocVersion",
        ],
    )


def test_file_2():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "PromoFull7290172900007-667-202409290706.xml",
    )
    converter.validate_succussful_extraction(
        df,
        f"{TEST_DIR}/PromoFull7290172900007-667-202409290706.xml",
        ignore_missing_columns=[
            "SubChainId",
            "DllVerNo",
            "ChainId",
            "BikoretNo",
            "StoreId",
            "XmlDocVersion",
        ],
    )


def test_nested_xml_dataframe():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(
        list_key="Promotions",
        id_field="PromotionId",
        roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        date_columns=["PromotionUpdateDate"],
        ignore_column=["XmlDocVersion", "DllVerNo"],
    )
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "PromoFull7290058140886-013-202512120010",
    )
    converter.validate_succussful_extraction(
        df,
        f"{TEST_DIR}/PromoFull7290058140886-013-202512120010",
    )


def test_wolt_promofull():
    """Test Wolt PromoFull with empty Promotions file (store without promos)."""
    converter = WoltFileConverter().promofull_parser
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "PromoFull7290058249350-000-038-20260217-000027",
    )
    assert df.shape[0] == 0


def test_salach_dabach_promofull():
    """Test Salach Dabach PromoFull parsing."""
    converter = SalachDabachFileConverter().promofull_parser
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "PromoFull7290526500006-013-202602170010",
    )
    assert df.shape[0] > 0
    assert "promotionid" in df.columns.str.lower()


def test_rami_levy_promofull():
    """Test Rami Levy PromoFull parsing."""
    converter = RamiLevyFileConverter().promofull_parser
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "PromoFull7290058140886-001-202602170010",
    )
    assert df.shape[0] > 0
    assert "promotionid" in df.columns.str.lower()


def test_keshet_promofull():
    """Test Keshet PromoFull parsing."""
    converter = KeshetFileConverter().promofull_parser
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "PromoFull7290785400000-002-202602170010",
    )
    assert df.shape[0] > 0
    assert "promotionid" in df.columns.str.lower()


def test_nested_xml_dataframe_with_ignore_column():
    """Test nested XML DataFrame Converter with ignore column."""
    converter = KeshetFileConverter().promofull_parser
    df = convert_to_dataframe(
        converter,
        TEST_DIR,
        "PromoFull7290785400000-002-202604250011",
    )
    converter.validate_succussful_extraction(
        df,
        f"{TEST_DIR}/PromoFull7290785400000-002-202604250011",
        ignore_missing_columns=["XmlDocVersion", "DllVerNo"],
    )


VICTORY_NEWLINE_PRICE_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainID>7290696200003</ChainID>
  <SubChainID>001</SubChainID>
  <StoreID>001</StoreID>
  <BikoretNo>0</BikoretNo>
  <Items>
    <Item>
      <PriceUpdateTime>2024-12-23T15:17:51.000</PriceUpdateTime>
      <ItemCode>3600523651870</ItemCode>
      <ItemType>1</ItemType>
      <ItemName>לניקוי יסודי  וחיזוק סיב השערה. 
</ItemName>
      <ManufactureItemDescription>שמפו אלביב ארג?ינין 
</ManufactureItemDescription>
      <ItemPrice>17.9</ItemPrice>
      <ItemStatus />
    </Item>
  </Items>
</Root>
"""


def _victory_newline_converter():
    return XmlDataFrameConverter(
        list_key="Items",
        id_field="ItemCode",
        roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
    )


def _write_temp_xml(folder, file_name, content):
    path = os.path.join(folder, file_name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path


def test_validate_compares_leaf_text_with_newlines():
    """Leaf text with a newline must match the XML, not become a nested dict."""
    converter = _victory_newline_converter()
    file_name = "Price7290696200003-001-202401010000.xml"
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_temp_xml(tmp, file_name, VICTORY_NEWLINE_PRICE_XML)
        df = convert_to_dataframe(converter, tmp, file_name)
        converter.validate_succussful_extraction(df, source)

        item_name = df.iloc[0]["itemname"]
        assert not isinstance(item_name, dict)
        assert item_name != {}
        assert "לניקוי יסודי" in str(item_name)


def test_validate_rejects_empty_dict_for_leaf_text():
    """Structure checks pass when a leaf is {}, content comparison must not."""
    converter = _victory_newline_converter()
    file_name = "Price7290696200003-001-202401010000.xml"
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_temp_xml(tmp, file_name, VICTORY_NEWLINE_PRICE_XML)
        df = convert_to_dataframe(converter, tmp, file_name)
        records = df.to_dict(orient="records")
        records[0]["itemname"] = {}
        df = pd.DataFrame(records)
        with pytest.raises(ValueError, match="content mismatch for 'itemname'"):
            converter.validate_succussful_extraction(df, source)


def test_validate_rejects_json_empty_object_string_for_leaf_text():
    """CSV round-trip stores {} as the string '{}'; that is still a mismatch."""
    converter = _victory_newline_converter()
    file_name = "Price7290696200003-001-202401010000.xml"
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_temp_xml(tmp, file_name, VICTORY_NEWLINE_PRICE_XML)
        df = convert_to_dataframe(converter, tmp, file_name)
        df = df.copy()
        df.at[0, "itemname"] = "{}"
        with pytest.raises(ValueError, match="content mismatch for 'itemname'"):
            converter.validate_succussful_extraction(df, source)


def test_validate_rejects_wrong_header_value():
    """Document headers must match on every row, not only exist as columns."""
    converter = _victory_newline_converter()
    file_name = "Price7290696200003-001-202401010000.xml"
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_temp_xml(tmp, file_name, VICTORY_NEWLINE_PRICE_XML)
        df = convert_to_dataframe(converter, tmp, file_name)
        records = df.to_dict(orient="records")
        records[0]["chainid"] = "WRONG"
        df = pd.DataFrame(records)
        with pytest.raises(ValueError, match="content mismatch for 'chainid'"):
            converter.validate_succussful_extraction(df, source)


def test_validate_rejects_missing_column_for_empty_tag():
    """Empty tags like ItemStatus still must be extracted as a column."""
    converter = _victory_newline_converter()
    file_name = "Price7290696200003-001-202401010000.xml"
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_temp_xml(tmp, file_name, VICTORY_NEWLINE_PRICE_XML)
        df = convert_to_dataframe(converter, tmp, file_name)
        df = df.drop(columns=["itemstatus"])
        with pytest.raises(ValueError, match="column 'itemstatus' missing"):
            converter.validate_succussful_extraction(df, source)


def test_validate_rejects_ignore_column_on_item_data():
    """ignore_column cannot drop a field that appears on a data row."""
    converter = XmlDataFrameConverter(
        list_key="Items",
        id_field="ItemCode",
        roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
        ignore_column=["ItemName"],
    )
    file_name = "Price7290696200003-001-202401010000.xml"
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_temp_xml(tmp, file_name, VICTORY_NEWLINE_PRICE_XML)
        df = convert_to_dataframe(converter, tmp, file_name)
        with pytest.raises(ValueError, match="ignored tag 'ItemName'"):
            converter.validate_succussful_extraction(df, source)


STORES_SUBCHAIN_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>123</ChainId>
  <ChainName>TestChain</ChainName>
  <LastUpdateDate>2024-01-01</LastUpdateDate>
  <SubChains>
    <SubChain>
      <SubChainId>1</SubChainId>
      <SubChainName>North</SubChainName>
      <Stores>
        <Store>
          <StoreId>10</StoreId>
          <StoreName>StoreA</StoreName>
        </Store>
      </Stores>
    </SubChain>
    <SubChain>
      <SubChainId>2</SubChainId>
      <SubChainName>South</SubChainName>
      <Stores>
        <Store>
          <StoreId>20</StoreId>
          <StoreName>StoreB</StoreName>
        </Store>
      </Stores>
    </SubChain>
  </SubChains>
</Root>
"""


def test_validate_rejects_wrong_subchain_header():
    """Sub-chain headers copied onto store rows must match the XML."""
    converter = SubRootedXmlDataFrameConverter(
        list_key="SubChains",
        id_field="StoreId",
        options=SubRootedXmlOptions(
            roots=["ChainId", "ChainName", "LastUpdateDate"],
            sub_roots=["SubChainId", "SubChainName"],
            list_sub_key="Stores",
        ),
    )
    file_name = "Stores123-000-202401010000.xml"
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_temp_xml(tmp, file_name, STORES_SUBCHAIN_XML)
        df = convert_to_dataframe(converter, tmp, file_name)
        converter.validate_succussful_extraction(df, source)
        records = df.to_dict(orient="records")
        records[1]["subchainname"] = "WRONG"
        df = pd.DataFrame(records)
        with pytest.raises(ValueError, match="content mismatch for 'subchainname'"):
            converter.validate_succussful_extraction(df, source)
