import os
import csv
import traceback

from typing import List
import pandas as pd
from tqdm import tqdm
from .parser_factory import ParserFactory
from .utils import DataLoader, DumpFile, Logger


class RawParsingPipeline:
    """
    processing files to dataframe
    """

    def __init__(self, folder, store_name, file_type, output_folder, when_date) -> None:
        self.store_name = store_name
        self.file_type = file_type
        self.folder = folder
        self.output_folder = output_folder
        self.when_date = when_date

    def append_columns_to_csv(self, existing_file, new_columns):
        """Append new columns to an existing CSV file"""
        output_file = existing_file.replace(".csv", "_temp.csv")
        with open(existing_file, "r", encoding="utf-8") as infile, open(
            output_file, "w+", newline="", encoding="utf-8"
        ) as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # Add header
            header = next(reader)
            writer.writerow(header + list(new_columns))

            # Add data row-by-row
            for row in reader:
                writer.writerow(row + [""] * len(new_columns))
        os.remove(existing_file)
        os.rename(output_file, existing_file)

    def process(self, limit=None):
        """start processing the files selected in the pipeline input"""
        parser_class = ParserFactory.get(self.store_name)
        create_csv = os.path.join(
            self.output_folder,
            self.file_type.lower() + "_" + self.store_name.lower() + ".csv",
        )

        files_to_process: List[DumpFile] = DataLoader(
            self.folder,
            store_names=[self.store_name],
            files_types=[self.file_type],
        ).load(limit=limit)

        Logger.info(
            f"Processing {len(files_to_process)} files"
            f"of type {self.file_type} for store {self.store_name}"
        )
        execution_log = []
        execution_errors = 0
        for file in tqdm(
            files_to_process,
            total=len(files_to_process),
            desc=f"Processing {self.file_type}@{self.store_name}",
        ):

            Logger.debug(f"Processing file {file.file_name}")
            # ignore but log empty files
            if file.is_expected_to_be_readable():
                execution_log.append(
                    {
                        "loaded": False,
                        **file.to_log_dict(),
                    }
                )
                Logger.debug(f"File {file.file_name} is empty, skipping")
                continue

            # if the file is not empty, process it
            try:
                parser = parser_class()
                df = parser.read(file)

                if not os.path.exists(create_csv):
                    Logger.debug(f"Creating new file {create_csv}")
                    df.to_csv(create_csv, index=False, mode="w", header=True)
                else:
                    Logger.debug(f"File {file.file_name} is not empty, processing")
                    # align columns
                    existing_df = pd.read_csv(create_csv, nrows=0)

                    # if there is missing columns in the existing file, append them
                    missing_columns = set(df.columns) - set(existing_df.columns)
                    if missing_columns:
                        Logger.debug(
                            f"Appending missing columns {missing_columns} to {create_csv}"
                        )
                        self.append_columns_to_csv(create_csv, missing_columns)

                    existing_df = pd.read_csv(create_csv, nrows=0)
                    # if there is missing columns in the new file, append them
                    all_columns = list(set(existing_df.columns) - set(df.columns))
                    for column in all_columns:
                        if column not in df.columns:
                            df[column] = None  # Add missing columns with None values

                    existing_df = pd.read_csv(create_csv, nrows=0)
                    df[existing_df.columns].to_csv(
                        create_csv, index=False, mode="a", header=False
                    )
                    Logger.debug(f"Appending data to {create_csv}")

                execution_log.append(
                    {
                        "loaded": True,
                        "succusfull": True,
                        "detected_num_rows": df.shape[0],
                        **file.to_log_dict(),
                    }
                )

                del df

            except Exception as error:  # pylint: disable=broad-exception-caught
                Logger.error(f"Error processing file {file.file_name}: {error}")
                execution_errors += 1
                execution_log.append(
                    {
                        "loaded": True,
                        "succusfull": False,
                        "error": str(error),
                        "trace": traceback.format_exc(),
                        **file.to_log_dict(),
                    }
                )

        return {
            "status": True,
            "store_name": self.store_name,
            "files_types": self.file_type,
            "when_date": self.when_date,
            "processed_files": len(files_to_process) > 0,
            "execution_errors": execution_errors > 0,
            "file_was_created": os.path.exists(create_csv),
            "file_created_path": create_csv,
            "files_to_process": [dumpfile.file_name for dumpfile in files_to_process],
            "execution_log": execution_log,
        }
