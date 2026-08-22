"""Tests for xml_utils module."""
import pytest
from il_supermarket_parsers.utils.xml_utils import (
    decode_bytes_to_string,
    get_root_from_content,
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
