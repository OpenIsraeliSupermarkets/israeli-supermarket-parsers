import asyncio
import os

import pandas as pd

from il_supermarket_parsers.documents.xml_dataframe_parser import XmlDataFrameConverter
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
