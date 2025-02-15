from il_supermarket_parsers import ConvertingTask

if __name__ == "__main__":

    ConvertingTask(
        enabled_parsers=["shufersal"],
        files_types=[""],
        data_folder="dumps",
        multiprocessing=None,
        output_folder=None,
    ).start()

    # checkout 'outputs' folder and 'dumps' folder
