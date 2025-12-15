from collections import Counter
import xml.etree.ElementTree as ET
from lxml import etree


def strip_namespace(tag):
    """Split the tag by the closing '}' of the namespace and return the tag part."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def count_tag_in_xml(xml_file_path, tag_to_count):
    """recursive count the number of tags from 'tag_to_count' in 'xml_file_path'"""
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

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

    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

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
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

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
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

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
    if "\n" in content:
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
    """get ET root"""
    try:
        tree = ET.parse(file)
    except ET.ParseError:
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
