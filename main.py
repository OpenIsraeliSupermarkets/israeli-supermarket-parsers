import os
from il_supermarket_parsers import ConvertingTask, ParserFactory, FileTypesFilters


def load_params():
    """load params from env variables with validation.

    Returns a dict suitable for ``ConvertingTask(**kwargs)`` and an optional file
    limit for ``task.start(limit=...)``.
    """
    kwargs: dict = {}

    kwargs["source_configuration"] = {
        "folder": os.getenv("DATA_FOLDER", "dumps"),
    }
    kwargs["output_configuration"] = [
        {
            "output_mode": "csv",
            "output_folder": os.getenv("OUTPUT_FOLDER", "outputs"),
        }
    ]
    kwargs["status_configuration"] = {
        "database_type": "json",
        "base_path": os.getenv("STATUS_FOLDER", os.getenv("OUTPUT_FOLDER", "outputs")),
    }

    limit = os.getenv("LIMIT", None)

    # validate scrapers
    enabled_parsers = os.getenv("ENABLED_PARSERS", None)
    if enabled_parsers:
        enabled_parsers = enabled_parsers.split(",")

        not_valid = list(
            filter(
                lambda scraper: scraper not in ParserFactory.all_parsers_name(),
                enabled_parsers,
            )
        )
        if not_valid:
            raise ValueError(f"ENABLED_PARSERS contains invalid {not_valid}")

        kwargs["enabled_parsers"] = enabled_parsers

    # validate file types
    enabled_file_types = os.getenv("ENABLED_FILE_TYPES", None)
    if enabled_file_types:

        enabled_file_types = enabled_file_types.split(",")

        not_valid = list(
            filter(
                lambda f_types: f_types not in FileTypesFilters.all_types(),
                enabled_file_types,
            )
        )
        if not_valid:
            raise ValueError(f"ENABLED_FILE_TYPES contains invalid {not_valid}")

        kwargs["files_types"] = enabled_file_types

    # validate number of processes
    number_of_processes = os.getenv("NUMBER_OF_PROCESSES", None)
    if number_of_processes:
        try:
            kwargs["multiprocessing"] = int(number_of_processes)
        except ValueError as exc:
            raise ValueError("NUMBER_OF_PROCESSES must be an integer") from exc

    if limit:
        try:
            limit = int(limit)
        except ValueError as exc:
            raise ValueError(f"LIMIT must be an integer, but got {limit}") from exc
    else:
        limit = None

    return kwargs, limit


if __name__ == "__main__":
    args, limit_value = load_params()
    task = ConvertingTask(**args)
    task.start(limit=limit_value)
    task.join()
