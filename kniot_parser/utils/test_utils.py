import os
from il_supermarket_scarper import ScarpingTask, FileTypesFilters


def get_sample_data(dump_folder_name, filter_type=None):
    """get data to scrape"""
    if not os.path.exists(dump_folder_name):
        if filter_type:
            task = ScarpingTask(
                dump_folder_name=dump_folder_name, limit=10, files_types=[filter_type]
            )
            task.start()
        else:
            ScarpingTask(dump_folder_name=dump_folder_name, limit=10).start()


def get_sample_store_data(dump_folder_name):
    """get only store to scrape"""
    get_sample_data(dump_folder_name, FileTypesFilters.STORE_FILE.name)


def get_sample_price_data(dump_folder_name):
    """get only price to scrape"""
    get_sample_data(dump_folder_name, FileTypesFilters.PRICE_FILE.name)


def get_sample_price_full_data(dump_folder_name):
    """get only price full to scrape"""
    get_sample_data(dump_folder_name, FileTypesFilters.PRICE_FULL_FILE.name)


def get_sample_promo_data(dump_folder_name):
    """get only promo to scrape"""
    get_sample_data(dump_folder_name, FileTypesFilters.PROMO_FILE.name)


def get_sample_promo_full_data(dump_folder_name):
    """get only promo full to scrape"""
    get_sample_data(dump_folder_name, FileTypesFilters.PROMO_FULL_FILE.name)
