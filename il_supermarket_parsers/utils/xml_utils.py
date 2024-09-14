import xml.etree.ElementTree as ET


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

        if len(set(normaled_keys)) != 1:
            # we will create a dict and sort it
            content = dict(zip(keys, content))
            content = {k: v for k, v in sorted(content.items())}
        else:
            # we will create a list, sort by the string value
            # we don't care what is the order- just that they are in the same order.
            content = sorted(content, key=str)
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

    root_children = root.getchildren()

    for sub in root_children:
        # collect attributes
        if len(sub.getchildren()) == 0 and sub.tag in attributes_to_collect:
            collected[sub.tag] = sub.text
        else:
            possible_root = _get_root(
                sub, key_to_find, attributes_to_collect, collected
            )
            if possible_root is not None:
                return possible_root
