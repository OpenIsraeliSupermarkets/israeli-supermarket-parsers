from il_supermarket_scarper import ScarpingTask, FileTypesFilters, ScraperFactory


def get_sample_data(dump_folder_name, filter_type=None, enabled_scrapers=None, limit=3):
    """get data to scrape"""
    if filter_type:
        task = ScarpingTask(
            dump_folder_name=dump_folder_name,
            limit=limit,
            files_types=[filter_type],
            enabled_scrapers=enabled_scrapers if enabled_scrapers else None,
            lookup_in_db=True,
        )
        task.start()
    else:
        ScarpingTask(
            dump_folder_name=dump_folder_name, limit=limit, lookup_in_db=True
        ).start()
    return dump_folder_name


def get_sample_store_data():
    """get only store to scrape"""
    return


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


# def get_scraper_name_from_id(chain_id):
#     """get the constractor name from the chain id"""
#     for chain_constractor in ScraperFactory.all_scrapers():
#         if str(chain_id) in (chain_constractor().get_chain_id()):
#             return chain_constractor.__name__
#     raise ValueError(f"chain_id {chain_id} is not recognized ")
