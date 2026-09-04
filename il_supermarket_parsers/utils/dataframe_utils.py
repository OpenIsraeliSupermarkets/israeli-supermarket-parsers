import json
import math
from collections import Counter


def collect_unique_columns_from_nested_json(df):
    """collect all json keys (including nested)"""
    # Set to store all unique column names
    unique_columns = set()

    # Recursive function to collect all keys from nested JSON structures
    def collect_keys_recursive(data):
        if isinstance(data, dict):  # If the data is a dictionary
            for key, value in data.items():
                unique_columns.add(key)  # Add the key to the unique set
                collect_keys_recursive(value)  # Recursively check nested values
        elif isinstance(data, list):  # If the data is a list
            for item in data:
                collect_keys_recursive(item)  # Recursively check each item in the list

    # Use itertuples for memory efficiency - only iterate once
    for row in df.itertuples(index=False):
        for cell in row:
            if isinstance(cell, str):
                # Only try to parse if it looks like JSON (starts with { or [)
                if cell and (
                    cell.strip().startswith("{") or cell.strip().startswith("[")
                ):
                    try:
                        json_data = json.loads(cell)
                        collect_keys_recursive(json_data)
                    except (ValueError, TypeError):
                        # Skip cells that are not valid JSON
                        continue
            elif isinstance(cell, (dict, list)):
                # Directly collect keys if it's already a dict or list
                collect_keys_recursive(cell)

    return set(unique_columns) | set(df.columns)


def count_elements_in_nested_json(df):
    """count element occurrences in nested JSON structures.
    This catches repeated sibling elements (like multiple <Item> under <PromotionItems>).
    - When a dict key maps to a list, counts each list item under that key
    - When a dict key maps to a single dict, counts it as 1 (single child element)
    - When a dict key maps to a scalar inside a nested dict, counts it as 1
    Returns dict {key: count}"""
    element_counts = Counter()
    # Use forward fill in-place to avoid creating a copy
    # df_filled = df.ffill()

    def count_recursive(data, in_nested_dict=False):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    # Key maps to a list - count each list item under this key
                    element_counts[key.lower()] += len(value)
                    for item in value:
                        count_recursive(item, in_nested_dict=True)
                elif isinstance(value, dict):
                    # Key maps to a single dict - count as 1 (single child element)
                    element_counts[key.lower()] += 1
                    count_recursive(value, in_nested_dict=True)
                elif in_nested_dict:
                    # Scalar value inside a nested dict - count as 1
                    element_counts[key.lower()] += 1
        elif isinstance(data, list):
            for item in data:
                count_recursive(item, in_nested_dict=in_nested_dict)

    # Use itertuples for memory efficiency - only iterate once
    for row in df.itertuples(index=False):
        for cell in row:
            if isinstance(cell, str):
                # Only try to parse if it looks like JSON (starts with { or [)
                if cell and (
                    cell.strip().startswith("{") or cell.strip().startswith("[")
                ):
                    try:
                        json_data = json.loads(cell)
                        count_recursive(json_data, in_nested_dict=True)
                    except (ValueError, TypeError):
                        continue
            elif isinstance(cell, (dict, list)):
                count_recursive(cell, in_nested_dict=True)

    return dict(element_counts)


def _is_missing_cell(value):
    """True for None, NaN, empty string, or parser/CSV empty sentinels."""
    if value is None:
        return True
    if isinstance(value, str) and value in ("", "''", "NO_BODY"):
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return type(value).__name__ in ("NAType", "NaTType")


def _coerce_container(actual, expected_type):
    """Return actual as dict/list, parsing JSON strings from the CSV round-trip."""
    if isinstance(actual, expected_type):
        return actual
    if isinstance(actual, str):
        stripped = actual.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                parsed = json.loads(actual)
            except (ValueError, TypeError):
                return None
            if isinstance(parsed, expected_type):
                return parsed
    return None


def _leaves_equal(expected, actual):
    """Compare a leaf XML string to a DataFrame cell."""
    if isinstance(actual, (dict, list)):
        return False
    if isinstance(actual, str) and actual.strip() in ("{}", "[]"):
        return False
    expected_text = "" if _is_missing_cell(expected) else str(expected).strip()
    actual_text = "" if _is_missing_cell(actual) else str(actual).strip()
    if expected_text == actual_text:
        return True
    try:
        return float(expected_text) == float(actual_text)
    except (TypeError, ValueError):
        return False


def extracted_value_matches(expected, actual):
    """True when an extracted cell equals the independent XML ground-truth value.

    Nested values may be dict/list or a JSON string (CSV writer). A leaf must
    stay scalar text — an empty dict or ``"{}"`` is a mismatch.
    """
    if isinstance(expected, dict):
        actual_parsed = _coerce_container(actual, dict)
        if not isinstance(actual_parsed, dict):
            return False
        if set(expected) != set(actual_parsed):
            return False
        return all(
            extracted_value_matches(expected[key], actual_parsed[key])
            for key in expected
        )
    if isinstance(expected, list):
        actual_parsed = _coerce_container(actual, list)
        if not isinstance(actual_parsed, list) or len(expected) != len(actual_parsed):
            return False
        return all(
            extracted_value_matches(left, right)
            for left, right in zip(expected, actual_parsed)
        )
    return _leaves_equal(expected, actual)


def preview_extracted_value(value, limit=120):
    """Short repr for content-mismatch errors."""
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + "..."
    return text
