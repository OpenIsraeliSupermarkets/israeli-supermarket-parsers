# from base import BaseValidator
# import pandas as pd


# class StoreStracture(BaseValidator):

#     def validate(cls, data):

#         # Applying validation to each column
#         invalid = pd.DataFrame(index=data.index)
#         invalid["קוד הרשת_valid"] = cls.validate_numeric(data, "קוד הרשת", 5)
#         invalid["קוד תת-רשת_valid"] = cls.validate_numeric(data, "קוד תת-רשת", 1)
#         invalid["מספר חנות_valid"] = cls.validate_numeric(data, "מספר חנות", 3)
#         invalid["ספרת ביקורת_valid"] = cls.validate_numeric(data, "ספרת ביקורת", 1)
#         invalid["סוג החנות_valid"] = cls.validate_store_type(data, "סוג החנות")
#         invalid["שם הרשת בעברית_valid"] = cls.validate_alphanumeric(
#             data, "שם הרשת בעברית", 50
#         )
#         invalid["שם תת-הרשת בעברית_valid"] = cls.validate_alphanumeric(
#             data, "שם תת-הרשת בעברית", 50
#         )
#         invalid["שם החנות בעברית_valid"] = cls.validate_alphanumeric(
#             data, "שם החנות בעברית", 50
#         )
#         invalid["כתובת החנות_valid"] = cls.validate_alphanumeric(
#             data, "כתובת החנות", 50
#         )
#         invalid["יישוב_valid"] = cls.validate_alphanumeric(data, "יישוב", 20)
#         invalid["מיקוד_valid"] = cls.validate_numeric("מיקוד", 7)
#         invalid["תאריך עדכון אחרון_valid"] = cls.validate_date(
#             data, "תאריך עדכון אחרון"
#         )
#         invalid["שעת עדכון אחרונה_valid"] = cls.validate_time(data, "שעת עדכון אחרונה")

#         return invalid
