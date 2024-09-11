from .xml_dataframe_parser import XmlDataFrameConverter
import pandas as pd


class SubRootedXmlDataFrameConverter(XmlDataFrameConverter):
    """parser the xml docuement with extra indentations"""

    def __init__(
        self,
        list_key,
        id_field,
        roots=None,
        sub_roots=None,
        list_sub_key="",
        **additional_constant,
    ):
        super().__init__(
            list_key,
            id_field,
            roots,
            additional_constant=additional_constant,
        )
        self.sub_roots = sub_roots
        self.list_sub_key = list_sub_key

    def _phrse(self, root, file, root_store, no_content, row_limit=None,**kwarg):
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
                    value = self.build_value(name, no_content=no_content)

                    if value == no_content:
                        print(f"for value {name} found no content!")
                    values[tag] = value
                rows.append(values.copy())
                add_columns = False

                if row_limit and len(rows) >= row_limit:
                    break

        return pd.DataFrame(rows, columns=cols)
