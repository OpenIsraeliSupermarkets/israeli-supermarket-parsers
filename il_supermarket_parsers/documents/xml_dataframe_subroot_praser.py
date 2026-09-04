from dataclasses import dataclass
from typing import List, Optional

from .xml_dataframe_parser import XmlDataFrameConverter
from ..utils import normalize_tag


@dataclass
class SubRootedXmlOptions:
    """Layout and column options for :class:`SubRootedXmlDataFrameConverter`."""

    roots: Optional[List[str]] = None
    ignore_column: Optional[List[str]] = None
    sub_roots: Optional[List[str]] = None
    list_sub_key: str = ""
    last_mile: Optional[List[str]] = None


class SubRootedXmlDataFrameConverter(XmlDataFrameConverter):
    """parser the xml docuement with extra indentations"""

    def __init__(
        self,
        list_key,
        id_field,
        *,
        options: Optional[SubRootedXmlOptions] = None,
        **additional_constant,
    ):
        opts = options or SubRootedXmlOptions()
        super().__init__(
            list_key=list_key,
            id_field=id_field,
            roots=opts.roots,
            ignore_column=opts.ignore_column,
            additional_constant=additional_constant,
        )
        self.sub_roots = opts.sub_roots if opts.sub_roots is not None else []
        self.last_mile = opts.last_mile if opts.last_mile is not None else []
        self.list_sub_key = opts.list_sub_key

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

    def _iter_row_elements(self, root):
        """Yield store/row elements under each sub-chain, matching :meth:`_parse`."""
        if root is None or len(root) == 0:
            return
        ignore = {normalize_tag(x) for x in self.ignore_column}
        for sub_elem in root:
            current_elem = sub_elem
            if self.last_mile:
                for last in self.last_mile:
                    current_elem = (
                        current_elem.find(last) if current_elem is not None else None
                    )
                    if current_elem is None:
                        break
            if current_elem is None:
                continue
            list_sub_elem = current_elem.find(self.list_sub_key)
            if list_sub_elem is None:
                continue
            for elem in list_sub_elem:
                if normalize_tag(elem.tag) not in ignore:
                    yield elem

    async def _parse(
        self,
        root,
        found_folder,
        file_name,
        root_store,
        **_,
    ):
        """parse file to async generator of row dicts"""

        if root is None or len(root) == 0:
            return

        # Yield rows one by one as they're parsed
        for sub_elem in root:
            sub_root_store = root_store.copy()

            for k in sub_elem:
                if any(k.tag.lower() == s.lower() for s in self.sub_roots):
                    sub_root_store[k.tag.lower()] = k.text

            current_elem = sub_elem
            if self.last_mile:
                for last in self.last_mile:
                    current_elem = (
                        current_elem.find(last) if current_elem is not None else None
                    )
                    if current_elem is None:
                        break

            if current_elem is not None:
                list_sub_elem = current_elem.find(self.list_sub_key)
                if list_sub_elem is not None:
                    ignore = {normalize_tag(x) for x in self.ignore_column}
                    for elem in list_sub_elem:
                        if normalize_tag(elem.tag) not in ignore:
                            row = self.list_single_entry(
                                elem,
                                found_folder=found_folder,
                                file_name=file_name,
                                **sub_root_store,
                            )
                            yield row
