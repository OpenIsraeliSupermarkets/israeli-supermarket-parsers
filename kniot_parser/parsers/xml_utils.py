import xml.etree.ElementTree as ET

def build_value(name, no_content="NO_BODY"):
    """convert entry to json"""

    content = name.text
    # missing content something like '<ManufacturerName />'
    if not content:
        content = no_content
    if "\n" in content:
        normaled_keys = list()  # shufersal as 'ClubId' and 'Clubid", normoalize this
        keys = list()
        content = list()
        for item in name.findall("*"):
            content.append(build_value(item))
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

def get_root(file):
    """ get ET root """
    tree = ET.parse(file)
    root = tree.getroot()

    envelope = root.find("Envelope")
    if envelope:
        return envelope
    return root
