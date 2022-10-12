from il_supermarket_scarper import MainScrapperRunner

def get_sample_data(dump_folder_name):
    """ get data to scrape """
    scraper = MainScrapperRunner(dump_folder_name=dump_folder_name)
    scraper.run(limit=10)


def get_sample_store_data(dump_folder_name):
    """ get data to scrape """
    scraper = MainScrapperRunner(dump_folder_name=dump_folder_name)
    scraper.run(limit=10,files_types=['store_file'])


def get_sample_price_data(dump_folder_name):
    """ get data to scrape """
    scraper = MainScrapperRunner(dump_folder_name=dump_folder_name)
    scraper.run(limit=10,files_types=['price_file'])


def get_sample_promo_data(dump_folder_name):
    """ get data to scrape """
    scraper = MainScrapperRunner(dump_folder_name=dump_folder_name)
    scraper.run(limit=10,files_types=['promo_file'])
