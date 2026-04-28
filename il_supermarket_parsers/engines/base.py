from abc import ABC
from typing import AsyncIterator
import os
import pandas as pd
from il_supermarket_scarper import FileTypesFilters
from il_supermarket_parsers.documents import (
    XmlBaseConverter,
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
)
from il_supermarket_parsers.utils import DumpFile


class BaseFileConverter(ABC):
    """abstract parser"""

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        pricefull_parser: XmlBaseConverter = None,
        promofull_parser: XmlBaseConverter = None,
        stores_parser: XmlBaseConverter = None,
        price_parser: XmlBaseConverter = None,
        promo_parser: XmlBaseConverter = None,
    ) -> None:
        self.pricefull_parser = (
            pricefull_parser
            if pricefull_parser
            else XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            )
        )
        self.promofull_parser: XmlBaseConverter = (
            promofull_parser
            if promofull_parser
            else XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            )
        )
        self.stores_parser: XmlBaseConverter = (
            stores_parser
            if stores_parser
            else SubRootedXmlDataFrameConverter(
                list_key="SubChains",
                id_field="StoreId",
                options=SubRootedXmlOptions(
                    sub_roots=["SubChainId", "SubChainName"],
                    list_sub_key="Stores",
                    roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                    ignore_column=["XmlDocVersion", "DllVerNo"],
                ),
            )
        )
        self.price_parser: XmlBaseConverter = (
            price_parser
            if price_parser
            else XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            )
        )
        self.promo_parser: XmlBaseConverter = (
            promo_parser
            if promo_parser
            else XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            )
        )

    async def read(
        self, dump_file: DumpFile, run_validation: bool = False
    ) -> AsyncIterator[dict]:
        """covert the dump file to the target format according to the filetype

        Args:
            dump_file: DumpFile object (can be file system or queue-based)
            run_validation: Whether to run validation (not supported in streaming mode yet)

        Yields:
            dict: Row data as dictionaries
        """
        parser: XmlBaseConverter = self._get_parser(dump_file)
        # Determine if file is queue-based or file system based
        if dump_file.is_queue_based:
            # Queue-based file (in-memory content)
            async for row in parser.convert(
                dump_file.store_folder,
                dump_file.file_name,
                file_content=dump_file.file_content,
            ):
                yield row
        else:
            # File system based
            async for row in parser.convert(
                dump_file.store_folder,
                dump_file.file_name,
            ):
                yield row

        # Note: Validation is not yet supported in streaming mode
        # Would need to collect all rows first, which defeats the purpose of streaming
        if run_validation:
            raise NotImplementedError("Validation not yet supported in streaming mode")

    def _get_parser(self, dump_file: DumpFile) -> XmlBaseConverter:
        """get the appropriate parser based on file type"""
        if dump_file.detected_filetype == FileTypesFilters.PRICE_FILE:
            return self.price_parser
        if dump_file.detected_filetype == FileTypesFilters.PRICE_FULL_FILE:
            return self.pricefull_parser
        if dump_file.detected_filetype == FileTypesFilters.PROMO_FILE:
            return self.promo_parser
        if dump_file.detected_filetype == FileTypesFilters.PROMO_FULL_FILE:
            return self.promofull_parser
        if dump_file.detected_filetype == FileTypesFilters.STORE_FILE:
            return self.stores_parser
        raise ValueError(f"Unknown file type: {dump_file.detected_filetype}")

    def run_validation(self, df: pd.DataFrame, dump_file: DumpFile) -> None:
        """run the validation"""
        parser: XmlBaseConverter = self._get_parser(dump_file)

        # Get source file path
        assert (
            not dump_file.is_queue_based
        ), "Validation not supported for queue-based files"

        source_file = dump_file.get_full_path
        if not os.path.exists(source_file):
            raise FileNotFoundError(f"Source file not found: {source_file}")

        # Run validation
        parser.validate_succussful_extraction(df, source_file)
