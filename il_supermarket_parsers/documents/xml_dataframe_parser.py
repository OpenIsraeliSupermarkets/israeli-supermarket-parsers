import pandas as pd
from il_supermarket_parsers.utils import (
    count_tag_in_xml,
    collect_unique_keys_from_xml,
    collect_unique_columns_from_nested_json,
)
from .base import BaseXMLParser


class XmlDataFrameConverter(BaseXMLParser):
    """parser the xml docuement"""

    def reduce_size(self, data):
        """reduce the size"""
        data = data.fillna("")
        # remove duplicate columns
        for col in data.columns:
            data[col] = data[col].mask(data[col] == data[col].shift())
        return data

    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None
    ):
        """validate column requested"""
        # if there is an empty file
        # we expected it to return none
        tag_count = count_tag_in_xml(source_file, self.id_field)

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

        ignore_list = self.ignore_column
        if ignore_missing_columns:
            ignore_list = ignore_list + ignore_missing_columns
        keys_not_used = (
            set(map(lambda x: x.lower(), collect_unique_keys_from_xml(source_file)))
            - set(
                map(lambda x: x.lower(), collect_unique_columns_from_nested_json(data))
            )
            - set(map(lambda x: x.lower(), ignore_list))
        )
        if len(keys_not_used) > 0:
            raise ValueError(
                f"for file {source_file}, there is data we didn't get {keys_not_used}"
            )
        assert "found_folder" in data.columns
        assert "file_name" in data.columns

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
            return pd.DataFrame(columns=columns)

        rows = [
            self.list_single_entry(
                elem, found_folder=found_folder, file_name=file_name, **root_store
            )
            for elem in root
        ]
        if len(rows) == 0:
            return pd.DataFrame(columns=columns)

        return pd.DataFrame(rows)
