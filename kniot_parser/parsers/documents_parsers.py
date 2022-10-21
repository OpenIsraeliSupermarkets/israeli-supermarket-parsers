import pandas as pd
from .xml_utils import build_value, get_root


class XmlDataFrameConverter:
    """parser the xml docuement"""

    def __init__(
        self,
        list_key,
        id_field,
        full_data_snapshot=False,
        roots=None,
        date_columns=None,
        float_columns=None,
    ):
        self.list_key = list_key
        self.roots = roots
        self.date_columns = date_columns
        self.float_columns = float_columns
        self.id_field = id_field
        self.full_data_snapshot = full_data_snapshot

    def get_id(self):
        """get the id in each entery of the list"""
        if isinstance(self.id_field, list):
            return self.id_field
        return [self.id_field]

    def convert(self, file, no_content="NO-CONTENT", row_limit=None):
        """parse file to data frame"""
        root, root_store = get_root(file, self.list_key, self.roots)

        data_frame = self._phrse(
            root, file, root_store, no_content, row_limit=row_limit
        )

        if self.date_columns and not data_frame.empty:
            for column in self.date_columns:
                data_frame[column] = pd.to_datetime(data_frame[column])

        if self.float_columns and not data_frame.empty:
            for column in self.float_columns:
                data_frame[column] = pd.to_numeric(data_frame[column])
        return data_frame.fillna("NOT_APPLY")

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
                value = build_value(name, no_content=no_content)

                if value == no_content:
                    print(f"for value {name} found no content!")
                values[tag] = value
            rows.append(values.copy())
            add_columns = False

            if row_limit and len(rows) >= row_limit:
                break

        return pd.DataFrame(rows, columns=cols)

    def is_full_data_snapshot(self):
        """does document contain full snapshot and will be converted to
        incremental, or store as is.
        """
        return self.full_data_snapshot


class SubRootedXmlDataFrameConverter(XmlDataFrameConverter):
    """parser the xml docuement with extra indentations"""

    def __init__(
        self,
        list_key,
        id_field,
        full_data_snapshot=False,
        roots=None,
        date_columns=None,
        float_columns=None,
        sub_roots=None,
        list_sub_key="",
    ):
        super().__init__(
            list_key, id_field, full_data_snapshot, roots, date_columns, float_columns
        )
        self.sub_roots = sub_roots
        self.list_sub_key = list_sub_key

    def _phrse(self, root, file, root_store, no_content, row_limit=None):
        """parse file to data frame"""

        cols = ["file_id"] + list(root_store.keys())
        rows = []

        add_columns = True
        elements = root.getchildren()
        if len(elements) == 0:
            raise ValueError(f"{self.list_key} is wrong")

        for sub_elem in elements:
            sub_root_store = root_store.copy()

            for k in self.sub_roots:
                sub_root_store[k] = sub_elem.find(k).text

            for elem in sub_elem.find(self.list_sub_key):
                values = {"file_id": file, **sub_root_store}
                for name in elem.getchildren():
                    tag = name.tag
                    if add_columns:
                        cols.append(tag)
                    value = build_value(name, no_content=no_content)

                    if value == no_content:
                        print(f"for value {name} found no content!")
                    values[tag] = value
                rows.append(values.copy())
                add_columns = False

                if row_limit and len(rows) >= row_limit:
                    break

        return pd.DataFrame(rows, columns=cols)
