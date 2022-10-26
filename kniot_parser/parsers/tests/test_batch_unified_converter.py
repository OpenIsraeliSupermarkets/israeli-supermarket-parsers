from kniot_parser.parsers.batch_unified_converter import MultiUnifiedConverter
from kniot_parser.utils import (
    get_sample_price_data,
    get_sample_store_data,
    get_sample_promo_full_data,
    get_sample_promo_data,
    get_sample_price_full_data,
)


# def test_merge_stores():

if __name__ == "__main__":
    """ merge all store files """
    folder = get_sample_store_data()
    #folder = "stores_test"
    MultiUnifiedConverter(
        dump_folder=folder, file_type="stores", number_of_processes=2
    ).execute().to_csv("stores.csv",index=False)


# # def test_merge_price():
#     """ merge all prices files """
#     folder = get_sample_price_data()
#     MultiUnifiedConverter(
#         dump_folder=folder, file_type="price", number_of_processes=3
#     ).execute().to_csv("prices.csv")


# # # def test_merge_price_full():
#     """ merge all prices full files """
#     folder = get_sample_price_full_data()
#     MultiUnifiedConverter(
#         dump_folder=folder, file_type="pricefull", number_of_processes=3
#     ).execute().to_csv("prices_full.csv")


# # # def test_merge_promo():
#     """ merge all promo files """
#     folder = get_sample_promo_data()
#     MultiUnifiedConverter(
#         dump_folder=folder, file_type="promo", number_of_processes=3
#     ).execute().to_csv("promo.csv")


# # # def test_merge_promo_full():
#     """ merge all promo full files """
#     folder = get_sample_promo_full_data()
#     MultiUnifiedConverter(
#         dump_folder=folder, file_type="promofull", number_of_processes=3
#     ).execute().to_csv("promo_full.csv")
