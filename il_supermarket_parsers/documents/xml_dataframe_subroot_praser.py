import pandas as pd
from .xml_dataframe_parser import XmlDataFrameConverter


class SubRootedXmlDataFrameConverter(XmlDataFrameConverter):
    """parser the xml docuement with extra indentations"""

    def __init__(
        self,
        list_key,
        id_field,
        roots=None,
        sub_roots=None,
        list_sub_key="",
        ignore_column=None,
        **additional_constant,
    ):
        super().__init__(
            list_key=list_key,
            id_field=id_field,
            roots=roots,
            ignore_column=ignore_column,
            additional_constant=additional_constant,
        )
        self.sub_roots = sub_roots if sub_roots else []
        self.list_sub_key = list_sub_key

    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None
    ):
        """validation"""
        super().validate_succussful_extraction(
            data, source_file, ignore_missing_columns=ignore_missing_columns
        )

        # if the user asked to include the headers
        if self.sub_roots:
            for root in self.sub_roots:
                if root not in data.columns:
                    raise ValueError(
                        f"parse error for file {source_file}, "
                        f"columns {root} missing from {data.columns}"
                    )

    def _phrse(
        self,
        root,
        found_folder,
        file_name,
        root_store,
        **_,
    ):
        """parse file to data frame"""

        rows = []

        if root is None or len(root) == 0:
            return pd.DataFrame(
                columns=self.sub_roots
                + [self.id_field, "found_folder", "file_name"]
                + (self.roots if self.roots else [])
            )

        for sub_elem in list(root):
            sub_root_store = root_store.copy()

            for k in self.sub_roots:
                sub_root_store[k] = sub_elem.find(k).text

            for elem in sub_elem.find(self.list_sub_key):
                rows.append(
                    self.list_single_entry(
                        elem, found_folder, file_name, **sub_root_store
                    )
                )

        return pd.DataFrame(rows)
