from il_supermarket_parsers.utils import Logger


class BaseDataFrameNormlizer(object):
    """
    unified converter across all types and sources
    """

    def __init__(self) -> None:
        pass

    def _typing_normlize(self, data):
        data = self.fix_chain_ids(data)
        return self._stores_processing(data)

    def drop_duplicate(self, data_frame):
        """drop duplicate entries in the database"""
        unique_rows = data_frame.astype("str").drop_duplicates().index

        if not unique_rows.empty:
            Logger.info(
                f"Droping {data_frame.shape[0]-unique_rows.shape[0]} duplicate entries."
            )
            return data_frame.iloc[unique_rows, :]
        return data_frame

    def fix_chain_ids(self, data_frame):

        # fix chain ids.
        data_frame["chainid"] = data_frame["chainid"].replace("72906", "7290696200003")
        data_frame["chainid"] = data_frame["chainid"].replace("72908", "7290875100001")
        data_frame["chainid"] = data_frame["chainid"].replace(
            "72906390", "7290639000004"
        )

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
