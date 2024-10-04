# from base import BaseValidator
# import pandas as pd


# class ProductPriceStructure(BaseValidator):

#     def validate(cls, data):
#         # Applying validation to each column
#         invalid = pd.DataFrame(index=data.index)
#         invalid["קוד הרשת_valid"] = cls.validate_numeric(data, "קוד הרשת", 5)
#         invalid["קוד תת רשת_valid"] = cls.validate_numeric(data, "קוד תת רשת", 1)
#         invalid["מספר החנות_valid"] = cls.validate_numeric(data, "מספר החנות", 3)
#         invalid["ספרת ביקורת_valid"] = cls.validate_numeric(data, "ספרת ביקורת", 1)
#         invalid["שעת עדכון מחיר המצרך_valid"] = cls.validate_time(
#             data, "שעת עדכון מחיר המצרך"
#         )
#         invalid["מספר הברקוד של המצרך_valid"] = cls.validate_numeric(
#             data, "מספר הברקוד של המצרך", len(data["מספר הברקוד של המצרך"].iloc[0])
#         )  # No specific length given, use actual data
#         invalid["ברקוד פנימי_valid"] = cls.validate_store_type(data, "ברקוד פנימי")
#         invalid["שם המצרך_valid"] = cls.validate_alphanumeric(
#             data, "שם המצרך שנתן היצרן", 50
#         )
#         invalid["שם היצרן_valid"] = cls.validate_alphanumeric(
#             data, "שם היצרן או קוד היצרן", 50
#         )
#         invalid["ארץ ייצור_valid"] = cls.validate_alphanumeric(data, "ארץ ייצור", 20)
#         invalid["תיאור המצרך_valid"] = cls.validate_alphanumeric(
#             data, "תיאור המצרך", 50
#         )
#         invalid["מידת כמות המצרך_valid"] = cls.validate_alphanumeric(
#             data, "מידת כמות המצרך", 10
#         )
#         invalid["כמות המצרך_valid"] = cls.validate_numeric(data, "כמות המצרך", 4)
#         invalid["יחידת המידה_valid"] = cls.validate_alphanumeric(
#             data, "יחידת המידה", 10
#         )
#         invalid["כמות הפריטים_valid"] = cls.validate_numeric(
#             data, "כמות הפריטים במכירה במארז", 3
#         )
#         invalid["המחיר הכולל_valid"] = cls.validate_numeric(
#             data, "המחיר הכולל של המצרך", 5
#         )
#         invalid["מחיר ליחידת מידה_valid"] = cls.validate_numeric(
#             data, "מחיר ליחידת מידה של המצרך", 5
#         )
#         invalid["האם המצרך משתתף במבצע_valid"] = cls.validate_store_type(
#             data, "האם המצרך משתתף במבצע"
#         )
#         invalid["סטטוס רשומה_valid"] = cls.validate_store_type(data, "סטטוס רשומה")

#         return invalid
