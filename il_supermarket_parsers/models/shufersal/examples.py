# Example data for each schema type

SINGLE_ITEM_PRICE_EXAMPLE = {
    "ChainId": "7290027600007",
    "SubChainId": "001",
    "StoreId": "000",
    "BikoretNo": "001",
    "ItemCode": "7290000066318",
    "ItemName": "חלב טרי 3% שטראוס",
    "ItemPrice": 6.90,
    "ItemUnit": "ליטר",
    "ManufacturerName": "שטראוס",
    "ManufacturerItemDescription": "חלב טרי 3% שומן",
}

SINGLE_PROMO_FULL_EXAMPLE = {
    "ChainId": "7290027600007",
    "SubChainId": "001",
    "StoreId": "000",
    "BikoretNo": "001",
    "PromotionId": "PROMO123",
    "PromotionDescription": "Buy 1 Get 1 Free",
    "PromotionStartDate": "2024-01-01T00:00:00",
    "PromotionEndDate": "2024-01-31T23:59:59",
    "PromotionStartHour": "00:00",
    "PromotionEndHour": "23:59",
    "RewardType": "Discount",
    "DiscountType": "Percentage",
    "DiscountRate": 50.0,
    "DiscountedPricePerMida": None,
    "MinQty": 1,
    "MaxQty": None,
    "MinPurchaseAmnt": None,
    "MinNoOfItemOfered": None,
    "AdditionalRestrictions": None,
    "Remark": "Limited time offer",
    "IsWeightedPromo": False,
    "AllowMultipleDiscounts": True,
}
STORES_EXAMPLE_JSON = {
    "ChainId": "7290027600007",
    "ChainName": "שופרסל",
    "SubChainId": "001",
    "SubChainName": "שופרסל דיל",
    "StoreId": "001",
    "StoreName": "שופרסל דיל רמת אביב",
    "StoreAddress": "ברודצקי 43",
    "StoreCity": "תל אביב",
    "StoreType": "1",
    "LastUpdateDate": "20240101"
}

# # Price updates are similar to full price but typically contain only changed items
# PRICE_UPDATE_EXAMPLE = {
#     "ChainId": "7290027600007",
#     "SubChainId": "001",
#     "StoreId": "000",
#     "BikoretNo": "002",
#     "Items": [
#         {
#             "ItemCode": "7290000066318",
#             "ItemName": "חלב טרי 3% שטראוס",
#             "ItemPrice": 7.90,  # Updated price
#             "ItemUnit": "ליטר",
#             "ManufacturerName": "שטראוס",
#             "ManufacturerItemDescription": "חלב טרי 3% שומן"
#         }
#     ]
# }

# # Promo updates are similar to full promos but typically contain only new/changed promotions
# PROMO_UPDATE_EXAMPLE = {
#     "ChainId": "7290027600007",
#     "SubChainId": "001",
#     "StoreId": "000",
#     "BikoretNo": "002",
#     "Promotions": [
#         {
#             "PromotionId": "7290000066318",
#             "PromotionDescription": "2+1 על כל מוצרי החלב",  # Updated promotion
#             "PromotionStartDate": "2024-01-08T00:00:00",
#             "PromotionEndDate": "2024-01-14T23:59:59",
#             "RewardType": "1"
#         }
#     ]
# }
