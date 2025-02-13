# Example data for each schema type

PRICE_FULL_EXAMPLE = {
    "ChainId": "7290027600007",
    "SubChainId": "001",
    "StoreId": "000",
    "BikoretNo": "001",
    "Items": [
        {
            "ItemCode": "7290000066318",
            "ItemName": "חלב טרי 3% שטראוס",
            "ItemPrice": 6.90,
            "ItemUnit": "ליטר",
            "ManufacturerName": "שטראוס",
            "ManufacturerItemDescription": "חלב טרי 3% שומן"
        },
        {
            "ItemCode": "7290002288589",
            "ItemName": "לחם אחיד פרוס",
            "ItemPrice": 7.50,
            "ItemUnit": "יחידה",
            "ManufacturerName": "אנג׳ל",
            "ManufacturerItemDescription": "לחם אחיד פרוס 750 גרם"
        }
    ]
}

PROMO_FULL_EXAMPLE = {
    "ChainId": "7290027600007",
    "SubChainId": "001",
    "StoreId": "000",
    "BikoretNo": "001",
    "Promotions": [
        {
            "PromotionId": "7290000066318",
            "PromotionDescription": "1+1 על כל מוצרי החלב",
            "PromotionStartDate": "2024-01-01T00:00:00",
            "PromotionEndDate": "2024-01-07T23:59:59",
            "RewardType": "1"
        },
        {
            "PromotionId": "7290002288589",
            "PromotionDescription": "הנחת 20% על לחם",
            "PromotionStartDate": "2024-01-01T00:00:00",
            "PromotionEndDate": "2024-01-07T23:59:59",
            "RewardType": "2"
        }
    ]
}

STORES_EXAMPLE = {
    "ChainId": "7290027600007",
    "ChainName": "שופרסל",
    "LastUpdateDate": "20240101",
    "LastUpdateTime": "080000",
    "SubChains": [
        {
            "SubChainId": "001",
            "SubChainName": "שופרסל דיל",
            "Stores": [
                {
                    "StoreId": "001",
                    "StoreName": "שופרסל דיל רמת אביב",
                    "StoreAddress": "ברודצקי 43",
                    "StoreCity": "תל אביב",
                    "StoreType": "1"
                },
                {
                    "StoreId": "002",
                    "StoreName": "שופרסל דיל דיזינגוף",
                    "StoreAddress": "דיזינגוף 50",
                    "StoreCity": "תל אביב",
                    "StoreType": "1"
                }
            ]
        },
        {
            "SubChainId": "002",
            "SubChainName": "שופרסל אקספרס",
            "Stores": [
                {
                    "StoreId": "003",
                    "StoreName": "שופרסל אקספרס אלנבי",
                    "StoreAddress": "אלנבי 99",
                    "StoreCity": "תל אביב",
                    "StoreType": "2"
                }
            ]
        }
    ]
}

# Price updates are similar to full price but typically contain only changed items
PRICE_UPDATE_EXAMPLE = {
    "ChainId": "7290027600007",
    "SubChainId": "001",
    "StoreId": "000",
    "BikoretNo": "002",
    "Items": [
        {
            "ItemCode": "7290000066318",
            "ItemName": "חלב טרי 3% שטראוס",
            "ItemPrice": 7.90,  # Updated price
            "ItemUnit": "ליטר",
            "ManufacturerName": "שטראוס",
            "ManufacturerItemDescription": "חלב טרי 3% שומן"
        }
    ]
}

# Promo updates are similar to full promos but typically contain only new/changed promotions
PROMO_UPDATE_EXAMPLE = {
    "ChainId": "7290027600007",
    "SubChainId": "001",
    "StoreId": "000",
    "BikoretNo": "002",
    "Promotions": [
        {
            "PromotionId": "7290000066318",
            "PromotionDescription": "2+1 על כל מוצרי החלב",  # Updated promotion
            "PromotionStartDate": "2024-01-08T00:00:00",
            "PromotionEndDate": "2024-01-14T23:59:59",
            "RewardType": "1"
        }
    ]
} 
