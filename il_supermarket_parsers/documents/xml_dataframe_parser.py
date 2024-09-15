import pandas as pd
from .base import XmlBaseConverter


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
        cols = ["found_folder", "file_name"] + list(root_store.keys())
        rows = []

        add_columns = True
        # if not root and "Super-Pharm" in file:
        #     return pd.DataFrame()  # shufersal don't add count=0

        elements = root.getchildren()
        if len(elements) == 0:
            if root.attrib.get("Count", None) == "0":
                return pd.DataFrame()
            else:
                raise ValueError(f"{self.list_key} is wrong")

        for elem in elements:

            values = {
                "found_folder": found_folder,
                "file_name": file_name,
                **root_store,
            }
            for name in elem.getchildren():
                tag = name.tag
                if add_columns:
                    cols.append(tag)
                value = self.build_value(name, no_content=no_content)

                if value == no_content:
                    print(f"for value {name} found no content!")
                values[tag] = value
            rows.append(values.copy())
            add_columns = False

            if row_limit and len(rows) >= row_limit:
                break

        return pd.DataFrame(rows, columns=cols)
