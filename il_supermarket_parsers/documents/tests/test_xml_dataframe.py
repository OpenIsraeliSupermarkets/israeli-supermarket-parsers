from il_supermarket_parsers.documents.xml_dataframe_parser import XmlDataFrameConverter


def test_read_bad_encoding_1():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = converter.convert(
        "il_supermarket_parsers/documents/tests",
        "PriceFull7290172900007-083-202409270311.xml",
    )
    converter.validate_succussful_extraction(df,"il_supermarket_parsers/documents/tests/PriceFull7290172900007-083-202409270311.xml",ignore_missing_columns=['ChainId', 'SubChainId', 'StoreId', 'BikoretNo'])

    assert df.shape[0] > 0


def test_read_bad_encoding_2():
    """test reading files that are the encoding in the file is not correct"""

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = converter.convert(
        "il_supermarket_parsers/documents/tests",
        "PromoFull7290172900007-667-202409290706.xml",
    )
    converter.validate_succussful_extraction(df,"il_supermarket_parsers/documents/tests/PromoFull7290172900007-667-202409290706.xml",ignore_missing_columns=['SubChainId', 'ChainId', 'BikoretNo', 'StoreId'])
    assert df.shape[0] > 0
