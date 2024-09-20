from .xml_dataframe_parser import XmlDataFrameConverter
import pandas as pd


class SubRootedXmlDataFrameConverter(XmlDataFrameConverter):
    """parser the xml docuement with extra indentations"""

    def __init__(
        self,
        list_key,
        id_field,
        roots=None,
        sub_roots=[],
        list_sub_key="",
        ignore_column=[],
        **additional_constant,
    ):
        super().__init__(
            list_key=list_key,
            id_field=id_field,
            roots=roots,
            ignore_column=ignore_column,
            additional_constant=additional_constant,
        )
        self.sub_roots = sub_roots
        self.list_sub_key = list_sub_key


    def validate_succussful_extraction(self,data,source_file):
        super().validate_succussful_extraction(data,source_file)
        for root in self.sub_roots:
            if root not in data.columns:
                raise ValueError(f"parse error, columns {root} missing from {data.columns}")

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
        """parse file to data frame"""

        rows = []

        if root is None:
            raise ValueError(f"{self.list_key} is wrong")

        if len(root) == 0 :
            columns = self.sub_roots + [self.id_field] + self.roots
            return pd.DataFrame(columns=columns)
        
        for sub_elem in list(root):
            sub_root_store = root_store.copy()

            for k in self.sub_roots:
                sub_root_store[k] = sub_elem.find(k).text

            for elem in sub_elem.find(self.list_sub_key):
                values = {
                    "found_folder": found_folder,
                    "file_name": file_name,
                    **sub_root_store,
                }
                for name in list(elem):
                    tag = name.tag
                    value = self.build_value(name, no_content=no_content)

                    if value == no_content:
                        print(f"for value {name} found no content!")
                    values[tag] = value
                rows.append(values.copy())
                add_columns = False

                if row_limit and len(rows) >= row_limit:
                    break

        return pd.DataFrame(rows)
