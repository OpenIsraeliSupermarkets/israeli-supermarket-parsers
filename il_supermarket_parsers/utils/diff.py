from enum import Enum


class Action(Enum):
    """the action change"""

    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    SAME = "same"


def compare_documents(old_dict, new_dict, ignore_list):
    """compare two documents"""
    keys = list(set(set(old_dict.keys()) & set(new_dict.keys())))
    result = {}
    for key in keys:

        if key not in ignore_list:
            new_value = new_dict.pop(key, None)
            diff = _comapre_values(old_dict.pop(key, None), new_dict.pop(key, None))

            if diff != Action.SAME:
                result[key] = {"value": new_value, "action": diff.name}

    return result


def _comapre_values(old_value, new_value):
    """compare two values"""
    if old_value is None and new_value is not None:
        return Action.ADDED
    if old_value is not None and new_value is None:
        return Action.REMOVED
    if old_value is not None and new_value is not None:
        if old_value != new_value:
            return Action.CHANGED
        return Action.SAME
    raise ValueError("both old value and new value are None")
