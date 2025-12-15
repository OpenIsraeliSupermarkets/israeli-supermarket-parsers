import json
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
    df_filled = df.ffill()

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
    for row in df_filled.itertuples(index=False):
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
