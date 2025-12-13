import os
from .xml_dataframe_parser import XmlDataFrameConverter
from ..utils import get_root_and_search,strip_namespace


class FilteredXmlDataFrameConverter(XmlDataFrameConverter):
    """
    Converter that filters XML elements by tag name.

    This converter extends XmlDataFrameConverter to filter child elements
    of the root list_key element by a specific tag name, useful for XML
    files that contain schema elements or other unwanted elements mixed
    with the data elements.

    Example:
        For XML with NewDataSet containing Item and schema elements,
        this can filter to only process Item elements.
    """

    def __init__(self, list_key, id_field, filter_element, roots=None, ignore_column=None, **additional_constant):
        """
        Initialize filtered converter.

        Args:
            list_key: The XML element key to search for (e.g., "NewDataSet")
            id_field: The field name that uniquely identifies each record
            filter_element: The tag name to filter for (case-insensitive, e.g., "item")
            roots: Optional list of root attribute names to collect
            ignore_column: Optional list of column names to ignore during validation
            **additional_constant: Additional constant values to include in each row
        """
        super().__init__(
            list_key=list_key,
            id_field=id_field,
            roots=roots,
            ignore_column=ignore_column,
            **additional_constant,
        )
        self.filter_element = filter_element.lower()

    def convert(self, found_store, file_name, **kwarg):
        """Parse file to data frame, filtering elements by tag name"""
        source_file = os.path.join(found_store, file_name)

        # Find the root element using list_key
        root, root_store = get_root_and_search(source_file, self.list_key, self.roots)

        if root is not None:
            # Filter to only process elements matching filter_element

            # Filter elements by tag name (case-insensitive, namespace-aware)
            root = [
                elem
                for elem in root
                if strip_namespace(elem.tag).lower() == self.filter_element
            ]

        # Parse using the filtered root
        data = self._parse(
            root,
            found_store,
            file_name,
            root_store,
            **kwarg,
        )
        return self.reduce_size(data)

