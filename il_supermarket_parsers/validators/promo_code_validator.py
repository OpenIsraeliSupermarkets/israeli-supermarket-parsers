# from base import BaseValidator
# import pandas as pd


# class PromoCodeValidator(BaseValidator):

#     def validate(cls, data):
#         # Define the valid promo codes and their corresponding descriptions
#         promo_codes = {
#             "0": "בלא מבצע",
#             "1": "הנחה המותנית ברכישת כמות",
#             "2": "הנחה באחוזים",
#             "3": "סכום הנחה ברכישת מצרך",
#             "4": "מבצע המותנה בסכום רכישה מזערי",
#             "5": "הנחת מועדון הקמעונאי",
#             "6": "מבצע המותנה ברכישת מוצרים מסוימים",
#             "7": "מצרך שני/שלישי בחינם",
#             "8": "מצרך שני זהה בהנחה",
#             "9": "מצרך שני לא זהה בהנחה",
#             "10": "אוסף מוצרים בהנחה",
#             "11": "אחר",
#         }

#         # Validation: Check if promo code exists and matches the valid values
#         invalid = pd.DataFrame(index=data.index)
#         invalid["קוד מבצע_valid"] = data["קוד מבצע"].apply(
#             lambda x: x in promo_codes.keys()
#         )

#         # Validation: Check if the description matches the corresponding promo code
#         invalid["תיאור המבצע_valid"] = data.apply(
#             lambda row: promo_codes.get(row["קוד מבצע"], "") == row["תיאור המבצע"],
#             axis=1,
#         )

#         return invalid
