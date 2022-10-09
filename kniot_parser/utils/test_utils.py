from il_supermarket_scarper import MainScrapperRunner


def get_sample_data(dump_folder_name):
    """ get data to scrape """
    scraper = MainScrapperRunner(dump_folder_name=dump_folder_name)
    scraper.run(limit=1)
