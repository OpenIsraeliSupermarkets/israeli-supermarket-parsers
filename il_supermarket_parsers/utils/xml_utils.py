import xml.etree.ElementTree as ET


def count_tag_in_xml(xml_file_path, tag_to_count):
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Recursive function to count "x" tags
    def count_tag_recursive(element):
        count = 0
        # If the current element tag is "x", increase the count
        if element.tag.lower() == tag_to_count.lower():
            count += 1
        # Recurse through all children elements
        for child in element:
            count += count_tag_recursive(child)
        return count

    # Start counting from the root
    return count_tag_recursive(root)


def collect_unique_keys_from_xml(xml_file_path):
    # Parse the XML file
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Set to store unique keys that have values
    keys_with_values = set()

    # Recursive function to collect keys with values
    def collect_keys_recursive(element):
        # Check if the element has a non-empty text value
        if element.text and element.text.strip():
            # Add the current element's tag to the set
            keys_with_values.add(element.tag)
        # Recurse through all child elements
        for child in element:
            collect_keys_recursive(child)

    # Start collecting keys from the root
    collect_keys_recursive(root)

    return keys_with_values


def build_value(name, constant_mapping, no_content="NO_BODY"):
    """convert entry to json"""

    content = name.text
    # missing content something like '<ManufacturerName />'
    if not content:
        content = constant_mapping.get(name.tag, no_content)
    if "\n" in content:
        normaled_keys = list()  # shufersal as 'ClubId' and 'Clubid", normoalize this
        keys = list()
        content = list()
        for item in name.findall("*"):
            content.append(build_value(item, constant_mapping))
            keys.append(item.tag)
            normaled_keys.append(item.tag.lower())

        content = dict(zip(keys, content))
        content = {k: v for k, v in sorted(content.items())}

    return content


def get_root(file, key_to_find, attributes_to_collect):
    """get ET root"""
    tree = ET.parse(file)
    root = tree.getroot()
    #
    root_store = dict()
    root = _get_root(root, key_to_find, attributes_to_collect, root_store)
    return root, root_store


def _get_root(root, key_to_find, attributes_to_collect, collected):
    if root.tag == key_to_find:
        return root

    for sub in list(root):
        # collect attributes
        if len(list(sub)) == 0 and sub.tag in attributes_to_collect:
            collected[sub.tag] = sub.text
        else:
            possible_root = _get_root(
                sub, key_to_find, attributes_to_collect, collected
            )
            if possible_root is not None:
                return possible_root
