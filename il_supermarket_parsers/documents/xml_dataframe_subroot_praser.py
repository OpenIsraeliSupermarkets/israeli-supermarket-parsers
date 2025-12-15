import pandas as pd
from .xml_dataframe_parser import XmlDataFrameConverter
from ..utils import normalize_tag


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
        last_mile=None,
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
        self.last_mile = last_mile if last_mile else []
        self.list_sub_key = list_sub_key

    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None, cached_xml_data=None
    ):
        """validation"""
        super().validate_succussful_extraction(
            data,
            source_file,
            ignore_missing_columns=ignore_missing_columns,
            cached_xml_data=cached_xml_data,
        )

        # if the user asked to include the headers
        if self.sub_roots:
            for root in self.sub_roots:
                if root.lower() not in data.columns:
                    raise ValueError(
                        f"parse error for file {source_file}, "
                        f"columns {root} missing from {data.columns}"
                    )

    def _parse(
        self,
        root,
        found_folder,
        file_name,
        root_store,
        **_,
    ):
        """parse file to data frame"""

        if root is None or len(root) == 0:
            return pd.DataFrame(
                columns=list(map(lambda x: x.lower(), self.sub_roots))
                + [self.id_field.lower(), "found_folder", "file_name"]
                + (list(map(lambda x: x.lower(), self.roots)) if self.roots else [])
            )

        # Use generator instead of list to reduce memory
        def row_generator():
            for sub_elem in root:
                sub_root_store = root_store.copy()

                for k in sub_elem:
                    if any(k.tag.lower() == s.lower() for s in self.sub_roots):
                        sub_root_store[k.tag.lower()] = k.text

                current_elem = sub_elem
                if self.last_mile:
                    for last in self.last_mile:
                        current_elem = (
                            current_elem.find(last)
                            if current_elem is not None
                            else None
                        )
                        if current_elem is None:
                            break

                if current_elem is not None:
                    list_sub_elem = current_elem.find(self.list_sub_key)
                    if list_sub_elem is not None:
                        for elem in list_sub_elem:
                            if normalize_tag(elem.tag) not in self.ignore_column:
                                yield self.list_single_entry(
                                    elem,
                                    found_folder=found_folder,
                                    file_name=file_name,
                                    **sub_root_store,
                                )

        # Convert generator to DataFrame directly
        return pd.DataFrame(row_generator())
