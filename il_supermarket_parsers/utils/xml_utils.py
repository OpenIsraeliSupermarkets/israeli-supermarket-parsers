import io
from collections import Counter
from typing import Optional, Union
import xml.etree.ElementTree as ET

from lxml import etree

GZIP_MAGIC_BYTES = b"\x1f\x8b"
ZIP_MAGIC_BYTES = b"PK"


def strip_namespace(tag):
    """Split the tag by the closing '}' of the namespace and return the tag part."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def is_compressed_payload(data: bytes) -> bool:
    """True when ``data`` starts with gzip or zip magic bytes."""
    if not data or len(data) < 2:
        return False
    return data[:2] in (GZIP_MAGIC_BYTES, ZIP_MAGIC_BYTES)


def raise_if_compressed(data: bytes, source: str = "") -> None:
    """Fail when a dump is still compressed.

    Extraction is the scraper's job. If the parser sees gzip/zip bytes, load
    must fail so the file is recorded as ``failed`` rather than silently
    inflated or skipped as "not picked up".
    """
    if not is_compressed_payload(data):
        return
    where = f" ({source})" if source else ""
    raise ValueError(
        f"Dump is still compressed{where}; "
        "the scraper must extract XML before parsing"
    )


def count_tag_in_xml(xml_file_path, tag_to_count):
    """recursive count the number of tags from 'tag_to_count' in 'xml_file_path'"""
    root = get_root(xml_file_path)

    # Recursive function to count "x" tags
    def count_tag_recursive(element):
        count = 0
        # If the current element tag is "x", increase the count
        if strip_namespace(element.tag).lower() == tag_to_count.lower():
            count += 1
        # Recurse through all children elements
        for child in element:
            count += count_tag_recursive(child)
        return count

    # Start counting from the root
    return count_tag_recursive(root)


def collect_unique_keys_from_xml(xml_file_path, ignore_tags=None):
    """find all the unique keys in the xml

    Args:
        xml_file_path: Path to the XML file
        ignore_tags: Optional list of tag names to ignore (will be normalized for comparison)
    """

    root = get_root(xml_file_path)

    # Set to store unique keys that have values
    keys_with_values = set()

    # Normalize ignore tags if provided
    ignore_set = None
    if ignore_tags:
        ignore_set = {normalize_tag(tag) for tag in ignore_tags}

    # Recursive function to collect keys with values
    def collect_keys_recursive(element):
        # Check if the element has a non-empty text value
        if element.text and element.text.strip():
            # Skip if this tag should be ignored
            if ignore_set is None or normalize_tag(element.tag) not in ignore_set:
                # Add the current element's tag to the set
                keys_with_values.add(element.tag)
        # Recurse through all child elements
        for child in element:
            collect_keys_recursive(child)

    # Start collecting keys from the root
    collect_keys_recursive(root)

    return keys_with_values


def normalize_tag(tag):
    """Strip namespace URI format ({URI}tag) and prefix format (prefix:tag)"""
    # First strip namespace URI format: {http://...}tag -> tag
    tag = strip_namespace(tag)
    # Then strip prefix format: xs:schema -> schema
    if ":" in tag:
        tag = tag.split(":", 1)[-1]
    return tag.lower()


def count_all_tags_in_xml(xml_file_path):
    """count all tag occurrences in the xml, returns dict {tag_name: count}"""
    root = get_root(xml_file_path)

    tag_counts = Counter()

    def count_recursive(element):
        tag_counts[strip_namespace(element.tag).lower()] += 1
        for child in element:
            count_recursive(child)

    count_recursive(root)
    return dict(tag_counts)


def collect_validation_data_from_xml(xml_file_path, id_field, ignore_tags=None):
    """Collect all validation data from XML in a single pass.

    Returns a dict with:
    - tag_count: count of id_field tags
    - xml_keys: set of unique keys with values
    - xml_counts: dict of all tag counts

    This is more memory efficient than calling the functions separately.
    """
    root = get_root(xml_file_path)

    tag_count = 0
    keys_with_values = set()
    tag_counts = Counter()

    ignore_set = None
    if ignore_tags:
        ignore_set = {normalize_tag(tag) for tag in ignore_tags}

    def collect_recursive(element):
        nonlocal tag_count

        tag = strip_namespace(element.tag)
        tag_lower = tag.lower()
        tag_counts[tag_lower] += 1

        # Count id_field tags
        if tag_lower == id_field.lower():
            tag_count += 1

        # Collect keys with values
        if element.text and element.text.strip():
            tag_normalized = normalize_tag(element.tag)
            if ignore_set is None or tag_normalized not in ignore_set:
                keys_with_values.add(element.tag)

        # Recurse through children
        for child in element:
            collect_recursive(child)

    collect_recursive(root)

    return {
        "tag_count": tag_count,
        "xml_keys": keys_with_values,
        "xml_counts": dict(tag_counts),
    }


def build_value(name, constant_mapping, no_content="NO_BODY"):
    """convert entry to json"""

    content = name.text
    # missing content something like '<ManufacturerName />'
    if not content:
        content = constant_mapping.get(name.tag, no_content)
    # Nested objects are identified by child elements, not by newlines in text.
    # Victory (and others) put line breaks inside leaf fields such as ItemName.
    if len(name) > 0:
        result = {}
        for item in name.findall("*"):
            key = item.tag.lower()
            value = build_value(item, constant_mapping)
            if key in result:
                # Multiple elements with same tag - collect into a list
                if isinstance(result[key], list):
                    result[key].append(value)
                else:
                    result[key] = [result[key], value]
            else:
                result[key] = value
        return result
    return content


def xml_element_to_value(element, empty=""):
    """Independent ground-truth value for an XML element.

    Nested iff the element has child tags. Leaf text (including newlines) stays
    a string. Must not call :func:`build_value` — validation has to catch that
    function turning a leaf into ``{}``.
    """
    if len(element) == 0:
        text = element.text
        if not text:
            return empty
        return text

    result = {}
    for child in element:
        key = child.tag.lower()
        value = xml_element_to_value(child, empty=empty)
        if key not in result:
            result[key] = value
            continue
        if isinstance(result[key], list):
            result[key].append(value)
        else:
            result[key] = [result[key], value]
    return result


def change_xml_encoding(file_path):
    """change the encoding if failing with utf-8"""
    with open(file_path, "rb") as file:  # pylint: disable=unspecified-encoding
        # Read the XML file content
        content = file.read()

    content = content.decode("ISO-8859-8", errors="replace")

    # Save the file with the new encoding declaration
    with open(file_path, "wb") as file:
        file.write(
            content.replace('encoding="ISO-8859-8"', 'encoding="UTF-8"').encode("utf-8")
        )


def try_to_recover_xml(file_path):
    """try to recover the xml"""

    parser = etree.XMLParser(recover=True, encoding="utf-8")
    with open(file_path, "rb") as f:
        tree = etree.parse(f, parser)
    fixed_xml = etree.tostring(tree, pretty_print=True, encoding="utf-8").decode(
        "utf-8"
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fixed_xml)


def get_root(file):
    """get ET root

    Only the first two bytes are read up front. If they are gzip (``\\x1f\\x8b``)
    or zip (``PK``) magic, parsing fails immediately without loading the body.
    Otherwise the file is parsed from disk.
    """
    with open(file, "rb") as handle:
        magic = handle.read(2)
        if is_compressed_payload(magic):
            raise_if_compressed(magic, source=file)
        handle.seek(0)
        try:
            return ET.parse(handle).getroot()
        except ET.ParseError:
            pass

    try:
        try_to_recover_xml(file)
        tree = ET.parse(file)
    except ET.ParseError:
        change_xml_encoding(file)
        tree = ET.parse(file)

    return tree.getroot()


def get_root_and_search(file, key_to_find, attributes_to_collect):
    """get the root and search for the key"""
    root = get_root(file)
    #
    root_store = {}
    root = _get_root(root, key_to_find, attributes_to_collect, root_store)
    return root, root_store


def _get_root(root, key_to_find, attributes_to_collect, collected):
    if strip_namespace(root.tag).lower() == key_to_find.lower():
        return root

    found_root = None
    for sub in list(root):
        # collect attributes
        if (
            len(list(sub)) == 0
            and attributes_to_collect is not None
            and any(
                strip_namespace(sub.tag).lower() == s.lower()
                for s in attributes_to_collect
            )
        ):
            collected[strip_namespace(sub.tag).lower()] = sub.text
        else:
            possible_root = _get_root(
                sub, key_to_find, attributes_to_collect, collected
            )

            # we are collecting also the infomration after the root
            if possible_root is not None:
                found_root = possible_root
    return found_root


def decode_bytes_to_string(content: bytes) -> str:
    """Decode bytes to string using a prioritized encoding fallback chain.

    Tries encodings in order: UTF-8 -> UTF-16 -> ISO-8859-8 (with replacement).
    This handles BOM-prefixed UTF-16 files (e.g., starting with b'\\xff\\xfe')
    which would otherwise be corrupted by direct ISO-8859-8 fallback.
    """
    # Try UTF-8 first (most common)
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        pass

    # Try UTF-16 (handles BOM automatically: \xff\xfe for LE, \xfe\xff for BE)
    try:
        return content.decode("utf-16")
    except UnicodeDecodeError:
        pass

    # Final fallback to ISO-8859-8 (Hebrew encoding) with replacement
    return content.decode("ISO-8859-8", errors="replace")


def get_root_from_content(
    file_content: Union[str, bytes], file_path: Optional[str] = None
):
    """get ET root from file content (bytes or string) or file path"""
    if isinstance(file_content, bytes):
        raise_if_compressed(file_content[:2], source=file_path or "")
        content_str = decode_bytes_to_string(file_content)
    else:
        content_str = file_content

    try:
        root = ET.fromstring(content_str)
    except ET.ParseError:
        # Try to recover XML
        try:
            parser = etree.XMLParser(recover=True, encoding="utf-8")
            root = etree.fromstring(content_str.encode("utf-8"), parser)
            root = ET.fromstring(etree.tostring(root, encoding="unicode"))
        except ET.ParseError:
            # Try with different encoding (fallback already attempted in decode_bytes_to_string,
            # but re-decoding may help if initial decode chose wrong encoding)
            try:
                if isinstance(file_content, bytes):
                    content_str = decode_bytes_to_string(file_content)
                root = ET.fromstring(content_str)
            except ET.ParseError:
                if file_path:
                    # Fallback to file-based parsing
                    return get_root(file_path)
                raise

    return root


def get_root_and_search_from_content(
    file_content: Union[str, bytes],
    key_to_find: str,
    attributes_to_collect: Optional[list] = None,
    file_path: Optional[str] = None,
):
    """get the root and search for the key from file content or path"""
    root = get_root_from_content(file_content, file_path)
    root_store = {}
    root = _get_root(root, key_to_find, attributes_to_collect, root_store)
    return root, root_store


def iterparse_streaming(
    file_content: Union[str, bytes, io.BytesIO], file_path: Optional[str] = None
):
    """
    Create streaming XML parser that can handle both file paths and in-memory content

    Args:
        file_content: XML content as bytes, string, or BytesIO, or None if using file_path
        file_path: Optional file path (used if file_content is None)

    Yields:
        (event, element) tuples from iterparse
    """
    if file_path:
        # Use file-based iterparse
        context = ET.iterparse(file_path, events=("start", "end"))
    elif isinstance(file_content, io.BytesIO):
        # Already a file-like object
        context = ET.iterparse(file_content, events=("start", "end"))
    else:
        # Convert content to BytesIO
        if isinstance(file_content, str):
            file_content = file_content.encode("utf-8")
        elif not isinstance(file_content, bytes):
            raise ValueError(f"Unsupported file_content type: {type(file_content)}")

        file_like = io.BytesIO(file_content)
        context = ET.iterparse(file_like, events=("start", "end"))

    return context
