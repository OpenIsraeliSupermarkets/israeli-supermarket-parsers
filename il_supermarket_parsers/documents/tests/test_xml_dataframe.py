import os
from il_supermarket_parsers.documents.xml_dataframe_parser import XmlDataFrameConverter
from il_supermarket_parsers.utils import EMPTY_FILE_TOEHOLD
import time


def test_read_bad_encoding_1():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = converter.convert(
        "il_supermarket_parsers/documents/tests",
        "PriceFull7290172900007-083-202409270311.xml",
    )
    converter.validate_succussful_extraction(
        df,
        "il_supermarket_parsers/documents/tests/PriceFull7290172900007-083-202409270311.xml",
        ignore_missing_columns=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
    )

    assert df.shape[0] > 0


def test_read_bad_encoding_2():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = converter.convert(
        "il_supermarket_parsers/documents/tests",
        "PromoFull7290172900007-667-202409290706.xml",
    )
    converter.validate_succussful_extraction(
        df,
        "il_supermarket_parsers/documents/tests/PromoFull7290172900007-667-202409290706.xml",
        ignore_missing_columns=["SubChainId", "ChainId", "BikoretNo", "StoreId"],
    )
    assert df.shape[0] > 0


def test_bad_element():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="STORES", id_field="STOREID")
    df = converter.convert(
        "il_supermarket_parsers/documents/tests",
        "Stores7290027600007-000-202410020201",
    )
    converter.validate_succussful_extraction(
        df,
        "il_supermarket_parsers/documents/tests/Stores7290027600007-000-202410020201",
        ignore_missing_columns=["CHAINID", "LASTUPDATEDATE"],
    )
    assert df.shape[0] > 0


def test_empty_file():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = converter.convert(
        "il_supermarket_parsers/documents/tests",
        "Price7290725900003-9032-202410021600",
    )
    converter.validate_succussful_extraction(
        df,
        "il_supermarket_parsers/documents/tests/Price7290725900003-9032-202410021600",
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
        "il_supermarket_parsers/documents/tests/PromoFull7290172900007-350-202410030634.xml",
    )

    assert empty1 <= EMPTY_FILE_TOEHOLD
    empty2 = os.path.getsize(
        "il_supermarket_parsers/documents/tests/Price7290725900003-9032-202410021600",
    )
    assert empty2 <= EMPTY_FILE_TOEHOLD


def test_file_1():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = converter.convert(
        "il_supermarket_parsers/documents/tests",
        "PriceFull7290172900007-083-202409270311.xml",
    )
    converter.validate_succussful_extraction(
        df,
        "il_supermarket_parsers/documents/tests/PriceFull7290172900007-083-202409270311.xml",
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
    df = converter.convert(
        "il_supermarket_parsers/documents/tests",
        "PromoFull7290172900007-667-202409290706.xml",
    )
    converter.validate_succussful_extraction(
        df,
        "il_supermarket_parsers/documents/tests/PromoFull7290172900007-667-202409290706.xml",
        ignore_missing_columns=[
            "SubChainId",
            "DllVerNo",
            "ChainId",
            "BikoretNo",
            "StoreId",
            "XmlDocVersion",
        ],
    )