import datetime
import re


class BaseValidator:
    # Validation functions
    @classmethod
    def validate_numeric(cls, data, column, length):
        return data[column].apply(lambda x: x.isdigit() and len(x) == length)

    @classmethod
    def validate_alphanumeric(cls, data, column, length):
        return data[column].apply(
            lambda x: len(x) <= length and re.match("^[a-zA-Zא-ת0-9 ]*$", x) is not None
        )

    @classmethod
    def validate_date(cls, data, column):
        return data[column].apply(
            lambda x: bool(re.match(r"^\d{6}$", x)) and cls.validate_date_format(x)
        )

    @classmethod
    def validate_time(cls, data, column):
        return data[column].apply(
            lambda x: bool(re.match(r"^\d{2}:\d{2}:\d{2}$", x))
            and cls.validate_time_format(x)
        )

    @classmethod
    def validate_date_format(cls, date_str):
        try:
            datetime.strptime(date_str, "%d%m%y")
            return True
        except ValueError:
            return False

    @classmethod
    def validate_time_format(cls, time_str):
        try:
            datetime.strptime(time_str, "%H:%M:%S")
            return True
        except ValueError:
            return False

    @classmethod
    def validate_store_type(cl, data, column):
        return data[column].apply(lambda x: x in ["0", "1"])
