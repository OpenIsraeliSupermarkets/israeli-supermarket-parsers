import json


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

    # Iterate over each column in the DataFrame
    for col in df.columns:
        # Check for nested JSON data in each cell
        for cell in df[col]:
            if isinstance(cell, str):
                try:
                    # Try to parse the cell as JSON (if it's a string)
                    json_data = json.loads(cell)
                    collect_keys_recursive(json_data)
                except (ValueError, TypeError):
                    # Skip cells that are not valid JSON
                    continue
            elif isinstance(cell, (dict, list)):
                # Directly collect keys if it's already a dict or list
                collect_keys_recursive(cell)

    return set(unique_columns) | set(df.columns)
