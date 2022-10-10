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
        if isinstance(self.id_field,list):
            return self.id_field
        return [self.id_field]

    def convert(self, file, no_content="NO-CONTENT"):
        """parse file to data frame"""
        root = get_root(file)

        # add the roots to the document
        root_store = {}
        for k in self.roots:
            root_store[k] = root.find(k).text

        data_frame = self._phrse(root, file, root_store, no_content)

        if self.date_columns and not data_frame.empty:
            for column in self.date_columns:
                data_frame[column] = pd.to_datetime(data_frame[column])

        if self.float_columns and not data_frame.empty:
            for column in self.float_columns:
                data_frame[column] = pd.to_numeric(data_frame[column])
        return data_frame.fillna("NOT_APPLY")

    def _phrse(self, root, file, root_store, no_content):
        cols = ["file_id"] + list(root_store.keys())
        rows = []

        add_columns = True
        elements = root.find(self.list_key)#.getchildren()
        if len(elements) == 0:
            if root.find(self.list_key).attrib.get("Count", None) == "0":
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
            list_key, id_field,full_data_snapshot, roots, date_columns, float_columns
        )
        self.sub_roots = sub_roots
        self.list_sub_key = list_sub_key

    def _phrse(self, root, file, root_store, no_content):
        """parse file to data frame"""

        cols = ["file_id"] + list(root_store.keys())
        rows = []

        add_columns = True
        elements = root.find(self.list_key)#.getchildren()
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

        return pd.DataFrame(rows, columns=cols)
