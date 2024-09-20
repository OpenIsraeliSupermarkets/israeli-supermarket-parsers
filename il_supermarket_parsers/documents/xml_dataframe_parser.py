import pandas as pd
from .base import XmlBaseConverter
from il_supermarket_parsers.utils import count_tag_in_xml,collect_unique_keys_from_xml,collect_unique_columns_from_nested_json


class XmlDataFrameConverter(XmlBaseConverter):
    """parser the xml docuement"""

    def _normlize_columns(
        self,
        data,
        missing_columns_default_values,
        columns_to_remove,
        columns_to_rename,
        date_columns=[],
        float_columns=[],
        empty_value="NOT_APPLY",
        **kwarg,
    ):
        if date_columns and not data.empty:
            for column in date_columns:
                data[column] = pd.to_datetime(data[column])

        if float_columns and not data.empty:
            for column in float_columns:
                data[column] = pd.to_numeric(data[column])
        data = data.fillna(empty_value)

        #
        for column, fill_value in missing_columns_default_values.items():
            if column not in data.columns:

                if isinstance(fill_value, str):
                    data[column] = fill_value
                else:
                    data[column] = fill_value()

        data = data.drop(columns=columns_to_remove, errors="ignore")
        return data.rename(columns=columns_to_rename)


    def validate_succussful_extraction(self,data, source_file):
        for root in self.roots:
            if root not in data.columns:
                raise ValueError(f"parse error, columns {root} missing from {data.columns}")
            
        if self.id_field not in data.columns:
            raise ValueError(f"parse error, id {self.id_field} missing from {data.columns}")

        # if there is an empty file
        # we expected it to reuturn none
        tag_count = count_tag_in_xml(source_file,self.id_field)
        if data.shape[0] != max(tag_count,1):
            raise ValueError(f"missing data")

        keys_not_used = set(collect_unique_keys_from_xml(source_file)) - collect_unique_columns_from_nested_json(data) - set(self.ignore_column)
        if len(keys_not_used) > 0:
            raise ValueError(f"there is data we didn't get {keys_not_used}")





    def _phrse(
        self,
        root,
        found_folder,
        file_name,
        root_store,
        no_content,
        row_limit=None,
        **kwarg,
    ):
        rows = []

        # if not root and "Super-Pharm" in file:
        #     return pd.DataFrame()  # shufersal don't add count=0

        if root is None:
            raise ValueError(f"{self.list_key} is wrong")

        elements = list(root)
        if len(root) == 0 :
            columns = [self.id_field] + self.roots
            return pd.DataFrame([root_store],columns=columns)

        for elem in elements:

            values = {
                "found_folder": found_folder,
                "file_name": file_name,
                **root_store,
            }
            for name in list(elem):
                tag = name.tag
                value = self.build_value(name, no_content=no_content)

                if value == no_content:
                    print(f"for value {name} found no content!")

                values[tag] = value
            rows.append(values.copy())

            if row_limit and len(rows) >= row_limit:
                break

        return pd.DataFrame(rows)
