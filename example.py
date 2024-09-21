from il_supermarket_parsers import ConvertingTask

if __name__ == "__main__":
    scraper = ConvertingTask(
        dump_folder_name="dumps",
        multiprocessing=2
    )
    scraper.start()