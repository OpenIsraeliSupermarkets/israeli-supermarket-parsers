from il_supermarket_scarper import FileTypesFilters


class DumpFile:

    def __init__(self, file_path) -> None:
        self.file_path = file_path
        self.file_type = FileTypesFilters
