from il_supermarket_parsers.documents.xml_dataframe_parser import XmlDataFrameConverter


def test_read_bad_encoding():

    converter = XmlDataFrameConverter(list_key="Details", id_field="ItemCode")
    df = converter.convert(
        "il_supermarket_parsers/documents/tests",
        "PriceFull7290172900007-083-202409270311.xml",
    )
    assert df.shape[0] > 0
