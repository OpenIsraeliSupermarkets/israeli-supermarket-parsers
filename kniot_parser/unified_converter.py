from kniot_parser.utils import Logger
from .parsers.all_files_parsers import (
    BareketFileConverter,
    DefualtFileConverter,
    SuperPharmFileConverter,
    VictoryFileConverter,
    ShufersalFileConverter,
    CofixFileConverter,
    MahsaniAShukPromoFileConverter,
    SalachDabachFileConverter,
)


class UnifiedConverter(object):
    """
    unified converter across all types and sources
    """

    parsers = {
        "bareket": BareketFileConverter,
        "mahsani a shuk": MahsaniAShukPromoFileConverter,
        "Victory": VictoryFileConverter,
        "Super-Pharm": SuperPharmFileConverter,
        "Shufersal": ShufersalFileConverter,
        "cofix": CofixFileConverter,
        "salachdabach": SalachDabachFileConverter,
    }
    defult_parser = DefualtFileConverter

    def __init__(self, store_name, file_type) -> None:
        self.file_type_parser = (
            self.parsers[store_name]()
            if store_name in self.parsers
            else self.defult_parser()
        ).get(file_type)

        self.file_type = file_type
        self.store_name = store_name

    def should_convert_to_incremental(self):
        """should we convert this file to incremenal to save storage"""
        return self.file_type_parser.is_full_data_snapshot()

    def get_key_column(self):
        """the key check document is index base on"""
        return [i.lower() for i in self.file_type_parser.get_id()]

    def convert(self, file, row_limit=None):
        """convert a file base on the type,chain"""
        Logger.info(f" converting file {file}.")
        data_frame = self.file_type_parser.convert(file, row_limit=row_limit)

        data_frame = data_frame.replace(r"\n", " ", regex=True)
        data_frame = data_frame.replace(r"\r", " ", regex=True)

        Logger.info(f"file {file}, dataframe shape is {data_frame.shape}")
        data_frame = self.drop_duplicate(data_frame)

        Logger.info(
            f"file {file}, after duplicate drop, dataframe shape is {data_frame.shape}"
        )

        data_frame = self.drop_duplicate_missing_inforamtion(data_frame)

        data_frame = self.adjust_to_file_type(data_frame)

        return self.scheme_fixing(data_frame)

    def drop_duplicate(self, data_frame):
        """drop duplicate entries in the database"""
        unique_rows = data_frame.astype("str").drop_duplicates().index

        if not unique_rows.empty:
            Logger.info(
                f"Droping {data_frame.shape[0]-unique_rows.shape[0]} duplicate entries."
            )
            return data_frame.iloc[unique_rows, :]
        return data_frame

    def drop_duplicate_missing_inforamtion(self, data_frame):
        def group_function(data):
            if data.shape[0] == 1:
                return data.head(1)
            elif data.shape[0] == 2:
                change = data.loc[:, ~(data.iloc[0] == data.iloc[1]).values]
                if (
                    change.shape[1] == 1
                    and "UnitQty" in change.columns
                    #                    and "Unknown " in change["UnitQty"].values
                ):
                    return data.tail(1)
                else:
                    raise ValueError(f"Change of {change} is not detected.")
            else:
                raise ValueError("Don't support duplicate for more the 2 rows.")

        if not data_frame.empty:
            if (data_frame[self.file_type_parser.get_id()].value_counts() > 1).any():
                return (
                    data_frame.groupby(self.file_type_parser.get_id())
                    .apply(group_function)
                    .reset_index(drop=True)
                )

        return data_frame

    def adjust_to_file_type(self, data_frame):
        if data_frame.empty:
            return data_frame

        data_frame.columns = map(lambda x: x.lower(), data_frame.columns)

        if self.file_type == "stores":
            columns_nan_mapping = {
                "subchainid": "not_apply",
                "subchainname": "not_apply",
                "chainid": lambda: self.file_type_parser.get_constant("chainid"),
                "lastupdatedate": "unknown",
                "lastupdatetime": "unknown",
                "doclastupdatedate": "unknown",
                "doclastupdatetime": "unknown",
            }
            ignore_columns = ["latitude", "longitude"]
            rename = {}

        elif self.file_type in ["pricefull", "price"]:
            columns_nan_mapping = {
                "itemid": "not_apply",
                "itemtype": "not_apply",
                "lastupdatedate": "unknown",
                "lastupdatetime": "unknown",
            }
            ignore_columns = []
            rename = {
                "blsweighted": "bisweighted",
                "itemnm": "itemname",
                "manufactureitemdescription": "manufactureritemdescription",
                "manufacturename": "manufacturername",
                "unitmeasure": "unitofmeasure",
            }
        elif self.file_type in ["promo", "promofull"]:
            columns_nan_mapping = {
                "additionalrestrictions": "not_apply",
                "clubs": "not_apply",
                "discountrate": "not_apply",
                "discounttype": "not_apply",
                "minqty": "not_apply",
                "promotiondescription": "not_apply",
                "weightunit": "not_apply",
                "promotionstarthour": "not_apply",
                "promotionupdatedate": "not_apply",
                "minnoofitemofered": "not_apply",
                "promotionendhour": "not_apply",
                "isweightedpromo": "not_apply",
                "promotionitems": "not_apply",
                "promotionenddate": "not_apply",
                "promotionstartdate": "not_apply",
                "promotiondetails": "not_apply",
                "isgiftitem": "not_apply",
                "itemcode": "not_apply",
                "priceupdatedate": "not_apply",
                "discountedpricepermida": "not_apply",
                "discountedprice": "not_apply",
                "minpurchaseamnt": "not_apply",
                "maxqty": "not_apply",
                "remarks": "not_apply",
                "remark": "not_apply",
                "giftsitems": "not_apply",
                "additionalscoupon": "not_apply",
                "clubid": "not_apply",
                "additionalsgiftcount": "not_apply",
                "minpurchaseamount": "not_apply",
                "additionalstotals": "not_apply",
                "additionalsminbasketamount": "not_apply",
                "minnoofitemsoffered": "not_apply",
                "itemtype": "not_apply",
            }
            ignore_columns = []
            rename = {}

        for column, fill_value in columns_nan_mapping.items():
            if column not in data_frame.columns:

                if isinstance(fill_value, str):
                    data_frame[column] = fill_value
                else:
                    data_frame[column] = fill_value()

        data_frame = data_frame.drop(columns=ignore_columns, errors="ignore")
        data_frame = data_frame.rename(columns=rename)

        # fix chain ids.
        data_frame["chainid"] = data_frame["chainid"].replace("72906", "7290696200003")
        data_frame["chainid"] = data_frame["chainid"].replace("72908", "7290875100001")
        data_frame["chainid"] = data_frame["chainid"].replace(
            "72906390", "7290639000004"
        )

        return data_frame

    def scheme_fixing(self, data_frame):
        if self.file_type == "stores":
            return self._stores_processing(data_frame)

        return data_frame

    def _stores_processing(self, data_frame):

        def merge_to_last_update_date(x, prefix=""):
            never_value = "01/01/0001 00:00:00"
            if x[f"{prefix}lastupdatedate"] == never_value:
                return "never"
            if (
                x[f"{prefix}lastupdatetime"] == "unknown"
                and x[f"{prefix}lastupdatedate"] == "unknown"
            ):
                return "unknown"
            if x[f"{prefix}lastupdatetime"] == "unknown":
                return x[f"{prefix}lastupdatedate"]
            return (
                str(x[f"{prefix}lastupdatedate"])
                + " "
                + str(x[f"{prefix}lastupdatetime"])
            )

        data_frame["lastupdatedatetime"] = data_frame[
            ["lastupdatedate", "lastupdatetime"]
        ].apply(merge_to_last_update_date, axis=1)
        data_frame["doclastupdatedatetime"] = data_frame[
            ["doclastupdatedate", "doclastupdatetime"]
        ].apply(merge_to_last_update_date, axis=1, prefix="doc")

        data_frame = data_frame.drop(columns=["lastupdatedate", "lastupdatetime"])
        data_frame = data_frame.drop(columns=["doclastupdatedate", "doclastupdatetime"])

        words_indacting_online = [
            "אונליין",
            "אינטרנט",
            "חנות עסקאות",
            "ליקוט",
            'ממ"ר',
            "ONLINE",
            "אתר סחר",
        ]
        data_frame["is_online"] = data_frame["storename"].str.contains(
            "|".join(words_indacting_online)
        )

        def fill_sub_chainname(x):
            if x["subchainname"] != "NO-CONTENT":
                return x["subchainname"]
            if x["chainname"] == "שופרסל":
                mapping = {"3": "שערי רווחה", "18": "GOOD MARKET"}
                return mapping.get(str(x["subchainid"]), x["subchainname"])
            if x["chainname"] == "סופר פארם ישראל":
                return "סופר פארם ישראל"
            if x["chainname"] == "ברקת":
                return "ברקת"
            return x["subchainname"]

        data_frame["subchainname"] = data_frame.apply(fill_sub_chainname, axis=1)

        def fix_store_type(x):
            if x["storetype"] != "NO-CONTENT":
                return x["storetype"]
            if x["subchainname"] == "BE":
                return 1
            if x["subchainname"] == "ויקטורי":
                return 1

        data_frame["storetype"] = data_frame.apply(fix_store_type, axis=1)
        return data_frame.drop(columns=["bikoretno"])
