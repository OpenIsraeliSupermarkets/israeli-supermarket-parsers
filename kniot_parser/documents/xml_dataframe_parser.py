import pandas as pd
from .base import XmlBaseConverter


class XmlDataFrameConverter(XmlBaseConverter):
    """parser the xml docuement"""

    def __init__(
        self,
        list_key,
        id_field,
        full_data_snapshot=False,
        roots=None,
        date_columns=None,
        float_columns=None,
        renames=None,
        **additional_constant,
    ):
        self.list_key = list_key
        self.roots = roots
        self.date_columns = date_columns
        self.float_columns = float_columns
        self.id_field = id_field
        self.full_data_snapshot = full_data_snapshot
        self.renames = renames
        self.additional_constant = additional_constant

    def _phrse(self, root, file, root_store, no_content, row_limit=None):
        cols = ["file_id"] + list(root_store.keys())
        rows = []

        add_columns = True
        if not root and "Super-Pharm" in file:
            return pd.DataFrame()  # shufersal don't add count=0

        elements = root.getchildren()
        if len(elements) == 0:
            if root.attrib.get("Count", None) == "0":
                return pd.DataFrame()
            else:
                raise ValueError(f"{self.list_key} is wrong")

        for elem in elements:

            values = {"file_id": file, **root_store}
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

        data_frame = pd.DataFrame(rows, columns=cols)

        if self.date_columns and not data_frame.empty:
            for column in self.date_columns:
                data_frame[column] = pd.to_datetime(data_frame[column])

        if self.float_columns and not data_frame.empty:
            for column in self.float_columns:
                data_frame[column] = pd.to_numeric(data_frame[column])
        return data_frame.fillna("NOT_APPLY")