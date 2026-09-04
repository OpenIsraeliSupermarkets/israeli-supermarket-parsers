"""Tests for xml_utils module."""
import gzip
import os
import tempfile
import xml.etree.ElementTree as ET

import pytest

from il_supermarket_parsers.utils.xml_utils import (
    build_value,
    decode_bytes_to_string,
    get_root,
    get_root_from_content,
    raise_if_compressed,
)


class TestDecodeBytesTOString:
    """Test the decode_bytes_to_string function."""

    def test_utf8_decoding(self):
        """Test that UTF-8 encoded bytes are decoded correctly."""
        content = b'<?xml version="1.0" encoding="UTF-8"?><Root><Item>Test</Item></Root>'
        result = decode_bytes_to_string(content)
        assert "<Root>" in result
        assert "<Item>Test</Item>" in result

    def test_utf16_le_with_bom(self):
        """Test UTF-16 LE decoding with BOM (b'\\xff\\xfe')."""
        xml_str = '<?xml version="1.0"?><Root><ChainID>123</ChainID></Root>'
        content = xml_str.encode("utf-16-le")
        content_with_bom = b"\xff\xfe" + content
        result = decode_bytes_to_string(content_with_bom)
        assert "<Root>" in result
        assert "<ChainID>123</ChainID>" in result
        assert "\ufffd" not in result  # No replacement characters

    def test_utf16_be_with_bom(self):
        """Test UTF-16 BE decoding with BOM (b'\\xfe\\xff')."""
        xml_str = '<?xml version="1.0"?><Root><ChainID>456</ChainID></Root>'
        content = xml_str.encode("utf-16-be")
        content_with_bom = b"\xfe\xff" + content
        result = decode_bytes_to_string(content_with_bom)
        assert "<Root>" in result
        assert "<ChainID>456</ChainID>" in result
        assert "\ufffd" not in result  # No replacement characters

    def test_iso88598_fallback(self):
        """Test fallback to ISO-8859-8 for Hebrew content."""
        hebrew_content = b"\xe9\xf9\xf8\xe0\xec"  # Some Hebrew chars in ISO-8859-8
        result = decode_bytes_to_string(hebrew_content)
        assert isinstance(result, str)

    def test_utf16_bom_does_not_corrupt_xml_root(self):
        """Regression test: UTF-16 BOM should not corrupt the XML root node.

        Previously, UTF-16 files with BOM would fall through to ISO-8859-8
        decoding with replacement characters, corrupting the root node
        (e.g., '<Root>' would become '\u200f<Root>').
        """
        xml_str = '<?xml version="1.0"?><Root><ChainID>789</ChainID></Root>'
        utf16_bytes = xml_str.encode("utf-16")
        result = decode_bytes_to_string(utf16_bytes)
        # Root should start cleanly without corruption
        assert result.lstrip().startswith("<?xml") or result.lstrip().startswith(
            "<Root"
        )
        # No right-to-left mark or other corruption artifacts
        assert "\u200f" not in result
        assert "\x00" not in result  # No null bytes from failed UTF-16 decode


class TestGetRootFromContent:
    """Test the get_root_from_content function."""

    def test_utf8_xml_content(self):
        """Test parsing UTF-8 XML content."""
        content = b'<?xml version="1.0" encoding="UTF-8"?><Root><Item>Test</Item></Root>'
        root = get_root_from_content(content)
        assert root.tag == "Root"
        assert root.find("Item").text == "Test"

    def test_utf16_xml_content_with_bom(self):
        """Regression test: UTF-16 encoded XML with BOM should parse correctly."""
        xml_str = '<?xml version="1.0"?><Root><ChainID>123</ChainID></Root>'
        utf16_bytes = xml_str.encode("utf-16")
        root = get_root_from_content(utf16_bytes)
        assert root.tag == "Root"
        assert root.find("ChainID").text == "123"

    def test_string_content(self):
        """Test parsing string content (no decoding needed)."""
        content = '<?xml version="1.0"?><Root><Item>Value</Item></Root>'
        root = get_root_from_content(content)
        assert root.tag == "Root"
        assert root.find("Item").text == "Value"

    def test_gzip_xml_content_is_rejected(self):
        """Compressed bytes must not parse; extraction belongs to the scraper."""
        xml = b'<?xml version="1.0"?><Root><Item>Gz</Item></Root>'
        with pytest.raises(ValueError, match="still compressed"):
            get_root_from_content(gzip.compress(xml))


class TestRaiseIfCompressed:
    """Compressed dumps must fail load instead of being inflated."""

    def test_passthrough_plain_xml(self):
        """Uncompressed XML does not raise."""
        raise_if_compressed(b'<?xml version="1.0"?><Root/>')

    def test_gzip_raises(self):
        """Gzip payload is an error the pipeline records as failed."""
        xml = b'<?xml version="1.0"?><Root/>'
        with pytest.raises(ValueError, match="still compressed"):
            raise_if_compressed(gzip.compress(xml), source="dump.gz")

    def test_zip_magic_two_bytes_raise(self):
        """Only the PK zip magic is needed; the body is never inspected."""
        with pytest.raises(ValueError, match="still compressed"):
            raise_if_compressed(b"PK")

    def test_gzip_magic_two_bytes_raise(self):
        """Only the gzip magic is needed; the body is never inspected."""
        with pytest.raises(ValueError, match="still compressed"):
            raise_if_compressed(b"\x1f\x8b")


class TestGetRootGzipFile:
    """get_root must fail dumps that are still gzip on disk."""

    def test_get_root_rejects_gzip_file(self):
        """A .gz dump raises so the pipeline can mark the file failed."""
        xml = b'<?xml version="1.0"?><Root><Item>Disk</Item></Root>'
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "PromoFull7290000000000-001-001-20260831-001227.gz")
            with open(path, "wb") as handle:
                handle.write(gzip.compress(xml))
            with pytest.raises(ValueError, match="still compressed"):
                get_root(path)


VICTORY_ITEM_XML = """
<Item>
      <PriceUpdateTime>2024-12-23T15:17:51.000</PriceUpdateTime>
      <ItemCode>3600523651870</ItemCode>
      <LastSaleDateTime>2026-06-21T07:55:54.000</LastSaleDateTime>
      <ItemType>1</ItemType>
      <ItemName>לניקוי יסודי  וחיזוק סיב השערה. 
</ItemName>
      <ManufactureName>IDC EU - Istanbul</ManufactureName>
      <ManufactureCountry>TR</ManufactureCountry>
      <ManufactureItemDescription>שמפו אלביב ארג?ינין 
</ManufactureItemDescription>
      <UnitQty>מיליליטר</UnitQty>
      <Quantity>550</Quantity>
      <UnitOfMeasure>מיליליטר 100</UnitOfMeasure>
      <bIsWeighted>0</bIsWeighted>
      <QtyInPackage>1</QtyInPackage>
      <ItemPrice>17.9</ItemPrice>
      <UnitOfMeasurePrice>3.25</UnitOfMeasurePrice>
      <AllowDiscount>0</AllowDiscount>
      <ItemStatus />
    </Item>
"""


class TestBuildValue:
    """build_value must treat child elements, not newlines in text, as nesting."""

    def test_victory_item_newline_in_text_is_not_empty_dict(self):
        """Victory leaf fields can contain a newline without any sub-children."""
        item = ET.fromstring(VICTORY_ITEM_XML)

        item_name = build_value(item.find("ItemName"), {})
        assert item_name != {}
        assert isinstance(item_name, str)
        assert "לניקוי יסודי" in item_name
        assert "\n" in item_name

        description = build_value(item.find("ManufactureItemDescription"), {})
        assert description != {}
        assert isinstance(description, str)
        assert "שמפו" in description
        assert "\n" in description

        item_status = build_value(item.find("ItemStatus"), {}, no_content="")
        assert item_status == ""

        assert build_value(item.find("ItemCode"), {}) == "3600523651870"

    def test_nested_children_still_become_dict(self):
        """An element with real children still collapses to a nested dict."""
        item = ET.fromstring(VICTORY_ITEM_XML)
        nested = build_value(item, {}, no_content="")
        assert isinstance(nested, dict)
        assert nested["itemcode"] == "3600523651870"
        assert isinstance(nested["itemname"], str)
        assert nested["itemname"] != {}
        assert "לניקוי יסודי" in nested["itemname"]
        assert nested["itemstatus"] == "NO_BODY"

        promo = ET.fromstring(
            "<PromotionItems>"
            "<Item><ItemCode>123</ItemCode><ItemName>nested</ItemName></Item>"
            "<Item><ItemCode>456</ItemCode><ItemName>other</ItemName></Item>"
            "</PromotionItems>"
        )
        result = build_value(promo, {})
        assert isinstance(result, dict)
        assert isinstance(result["item"], list)
        assert result["item"][0]["itemcode"] == "123"
        assert result["item"][1]["itemcode"] == "456"
