import os
from il_supermarket_scarper import ScarpingTask, FileTypesFilters, ScraperFactory


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
    return dump_folder_name


def get_sample_store_data():
    """get only store to scrape"""
    return get_sample_data("samples_store", FileTypesFilters.STORE_FILE.name)


def get_sample_price_data():
    """get only price to scrape"""
    return get_sample_data("samples_price", FileTypesFilters.PRICE_FILE.name)


def get_sample_price_full_data():
    """get only price full to scrape"""
    return get_sample_data("samples_price_full", FileTypesFilters.PRICE_FULL_FILE.name)


def get_sample_promo_data():
    """get only promo to scrape"""
    return get_sample_data("samples_promo", FileTypesFilters.PROMO_FILE.name)


def get_sample_promo_full_data():
    """get only promo full to scrape"""
    return get_sample_data("samples_promo_full", FileTypesFilters.PROMO_FULL_FILE.name)


def get_all_chain_ids():
    """get all chain ids"""
    all_ids = []
    for chain_constractor in ScraperFactory.all_scrapers():
        all_ids.extend(chain_constractor().get_chain_id())
    return all_ids

def get_all_scrapers_names():
    """get all chain ids"""
    all_names = []
    for chain_constractor in ScraperFactory.all_scrapers():
        all_names.append(chain_constractor.__name__)
    return all_names

def get_scraper_name_from_id(chain_id):
    """ get the constractor name from the chain id """
    for chain_constractor in ScraperFactory.all_scrapers():
        print(chain_constractor().get_chain_id())
        if str(chain_id) in (chain_constractor().get_chain_id()):
            return chain_constractor.__name__
