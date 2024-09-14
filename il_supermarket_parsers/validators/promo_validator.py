from base import BaseValidator
import pandas as pd


class PromotionsStructure(BaseValidator):

    def validate(cls, data):
        # Applying validation to each column
        invalid = pd.DataFrame(index=data.index)
        invalid["קוד הרשת_valid"] = cls.validate_numeric(data, "קוד הרשת", 5)
        invalid["קוד תת-רשת_valid"] = cls.validate_numeric(data, "קוד תת-רשת", 1)
        invalid["מספר החנות_valid"] = cls.validate_numeric(data, "מספר החנות", 3)
        invalid["ספרת ביקורת_valid"] = cls.validate_numeric(data, "ספרת ביקורת", 1)
        invalid["שעת עדכון המבצע_valid"] = cls.validate_time(
            data, "שעת עדכון המבצע בנוגע למוצר"
        )
        invalid["מספר הברקוד של המצרך_valid"] = cls.validate_numeric(
            data, "מספר הברקוד של המצרך", len(data["מספר הברקוד של המצרך"].iloc[0])
        )  # No specific length given, use actual data
        invalid["ברקוד פנימי_valid"] = cls.validate_store_type(
            data, "ברקוד פנימי", ["0", "1"]
        )
        invalid["קוד מבצע_valid"] = cls.validate_numeric(data, "קוד מבצע", 2)
        invalid["כפל מבצעים_valid"] = cls.validate_store_type(
            data, "כפל מבצעים", ["0", "1"]
        )
        invalid["מזהה מבצע_valid"] = cls.validate_numeric(data, "מזהה מבצע", 10)
        invalid["תיאור המבצע_valid"] = cls.validate_alphanumeric(
            data, "תיאור המבצע", 50
        )
        invalid["תאריך תחילת המבצע_valid"] = cls.validate_date(
            data, "תאריך תחילת המבצע"
        )
        invalid["שעת תחילת המבצע_valid"] = cls.validate_time(data, "שעת תחילת המבצע")
        invalid["תאריך סיום המבצע_valid"] = cls.validate_date(data, "תאריך סיום המבצע")
        invalid["שעת סיום המבצע_valid"] = cls.validate_time(data, "שעת סיום המבצע")
        invalid["האוכלוסייה שאליה מכוון המבצע_valid"] = cls.validate_store_type(
            data, "האוכלוסייה שאליה מכוון המבצע", ["0", "1", "2", "3"]
        )
        invalid["כמות מזערית_valid"] = cls.validate_numeric(
            data, "כמות מזערית להשתתפות במבצע", 2
        )
        invalid["הגבלת כמות_valid"] = cls.validate_numeric(
            data, "הגבלת כמות לרכישה במסגרת המבצע", 3
        )
        invalid["שיעור ההנחה_valid"] = cls.validate_numeric(data, "שיעור ההנחה", 4)
        invalid["סכום הרכישה המזערי_valid"] = cls.validate_numeric(
            data, "סכום הרכישה המזערי", 5
        )
        invalid["המחיר הכולל_valid"] = cls.validate_numeric(
            data, "המחיר הכולל של המבצע", 5
        )
        invalid["מחיר ליחידת מידה_valid"] = cls.validate_numeric(
            data, "מחיר ליחידת מידה של המצרך לאחר המבצע", 7
        )
        invalid["המספר המזערי_valid"] = cls.validate_numeric(
            data, "המספר המזערי של המצרכים המוצעים במבצע בחנות", 5
        )
        invalid["הגבלות נוספות_valid"] = cls.validate_alphanumeric(
            data, "הגבלות נוספות על המבצע", 50
        )
        invalid["מלל נוסף_valid"] = cls.validate_alphanumeric(
            data, "מלל נוסף של המבצע", 20
        )

        return invalid
