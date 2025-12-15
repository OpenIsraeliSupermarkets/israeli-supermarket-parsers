import pandas as pd
from il_supermarket_parsers.utils import (
    count_tag_in_xml,
    collect_unique_keys_from_xml,
    collect_unique_columns_from_nested_json,
    count_all_tags_in_xml,
    count_elements_in_nested_json,
    normalize_tag,
    collect_validation_data_from_xml,
)
from .base import BaseXMLParser


class XmlDataFrameConverter(BaseXMLParser):
    """parser the xml docuement"""

    def reduce_size(self, data):
        """reduce the size"""
        if len(data) == 0:
            return data
        # Use inplace operations to avoid creating copies
        data = data.fillna("", inplace=False)
        # remove duplicate columns - optimize by only processing non-empty columns
        for col in data.columns:
            # Only process if column has data
            if data[col].notna().any():
                data[col] = data[col].mask(data[col] == data[col].shift())
        return data

    def _validate_columns_and_counts(self, data, source_file, tag_count):
        """Validate required columns and row count match."""
        if self.roots and tag_count > 0:
            for root in self.roots:
                if root.lower() not in data.columns:
                    raise ValueError(
                        f"parse error for file {source_file},"
                        f"columns {root.lower()} missing from {data.columns}"
                    )

        if self.id_field.lower() not in data.columns:
            raise ValueError(
                f"parse error for file {source_file}, "
                f"id {self.id_field.lower()} missing from {data.columns}"
            )

        if data.shape[0] != tag_count:
            raise ValueError(
                f"for file {source_file}, missing data,"
                f"data shape {data.shape} tag count is {tag_count}"
            )

    def _validate_unused_keys(self, data, source_file, ignore_list, xml_keys=None):
        """Validate that all XML keys are captured in the DataFrame."""
        if xml_keys is None:
            xml_keys = {
                normalize_tag(key)
                for key in collect_unique_keys_from_xml(
                    source_file, ignore_tags=ignore_list
                )
            }
        data_keys = {
            normalize_tag(key) for key in collect_unique_columns_from_nested_json(data)
        }
        ignore_keys = {normalize_tag(key) for key in ignore_list}
        if keys_not_used := xml_keys - data_keys - ignore_keys:
            raise ValueError(
                f"for file {source_file}, there is data we didn't get {keys_not_used}"
            )

    def _validate_element_counts(self, data, source_file, xml_counts=None):
        """Validate that element counts match between XML and DataFrame."""
        if xml_counts is None:
            xml_counts = count_all_tags_in_xml(source_file)
        df_counts = count_elements_in_nested_json(data)

        for tag, df_count in df_counts.items():
            xml_count = xml_counts.get(tag, 0)
            if xml_count != df_count:
                raise ValueError(
                    f"for file {source_file}, element count mismatch for '{tag}': "
                    f"XML has {xml_count}, DataFrame has {df_count}"
                )

    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None, cached_xml_data=None
    ):
        """validate column requested

        Args:
            data: DataFrame to validate
            source_file: Path to source XML file
            ignore_missing_columns: Optional list of columns to ignore
            cached_xml_data: Optional dict with cached XML parsing results to avoid re-parsing.
                            If None, will collect all data in a single pass for efficiency.
        """
        # if there is an empty file
        # we expected it to return none

        ignore_list = (
            self.ignore_column + ignore_missing_columns
            if ignore_missing_columns
            else self.ignore_column
        )

        # If no cached data provided, collect all validation data in a single XML pass
        if cached_xml_data is None:
            cached_xml_data = collect_validation_data_from_xml(
                source_file, self.id_field, ignore_tags=ignore_list
            )
            # Normalize the keys
            cached_xml_data["xml_keys"] = {
                normalize_tag(key) for key in cached_xml_data["xml_keys"]
            }

        tag_count = cached_xml_data.get(
            "tag_count", count_tag_in_xml(source_file, self.id_field)
        )
        self._validate_columns_and_counts(data, source_file, tag_count)

        # Use cached data if available, otherwise collect it
        xml_keys = cached_xml_data.get("xml_keys")
        if xml_keys is None:
            xml_keys = {
                normalize_tag(key)
                for key in collect_unique_keys_from_xml(
                    source_file, ignore_tags=ignore_list
                )
            }

        self._validate_unused_keys(data, source_file, ignore_list, xml_keys)

        assert "found_folder" in data.columns
        assert "file_name" in data.columns

        # Use cached data if available
        xml_counts = cached_xml_data.get("xml_counts")
        self._validate_element_counts(data, source_file, xml_counts)

    def list_single_entry(self, elem, found_folder, file_name, **sub_root_store):
        """build a single row"""
        return {
            "found_folder": found_folder,
            "file_name": file_name,
            **sub_root_store,
            **{
                name.tag.lower(): self.build_value(name, no_content="") for name in elem
            },
        }

    def _parse(
        self,
        root,
        found_folder,
        file_name,
        root_store,
        **kwarg,
    ):

        columns = [self.id_field.lower(), "found_folder", "file_name"]
        if self.roots:
            columns.extend(root.lower() for root in self.roots)

        if root is None:
            # If root is None, it means the list_key element was not found in the XML
            # This could happen if the XML structure is different than expected
            # Return empty DataFrame with proper columns
            return pd.DataFrame(columns=columns)

        # Use generator instead of list comprehension to reduce memory
        rows = (
            self.list_single_entry(
                elem, found_folder=found_folder, file_name=file_name, **root_store
            )
            for elem in root
            if normalize_tag(elem.tag) not in self.ignore_column
        )

        # Convert generator to DataFrame directly
        df = pd.DataFrame(rows)
        if len(df) == 0:
            # Root was found but has no children
            # This could happen if the XML structure is different than expected
            return pd.DataFrame(columns=columns)

        return df
