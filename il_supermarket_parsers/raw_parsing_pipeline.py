import os
import csv

from typing import List
import pandas as pd
from tqdm import tqdm
from .parser_factory import ParserFactory
from .utils import DataLoader, DumpFile


class RawParsingPipeline:
    """
    processing files to dataframe
    """

    def __init__(self, folder, store_name, file_type, output_folder) -> None:
        self.store_name = store_name
        self.file_type = file_type
        self.folder = folder
        self.output_folder = output_folder

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
        execution_log = []

        for file in tqdm(
            files_to_process,
            total=len(files_to_process),
            desc=f"Processing {self.file_type}@{self.store_name}",
        ):

            try:
                parser = parser_class()
                df = parser.read(file)

                if not os.path.exists(create_csv):
                    df.to_csv(create_csv, index=False, mode="w", header=True)
                else:
                    # align columns
                    existing_df = pd.read_csv(create_csv, nrows=0)

                    # if there is missing columns in the existing file, append them
                    missing_columns = set(df.columns) - set(existing_df.columns)
                    if missing_columns:
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

                del df

                execution_log.append(
                    {
                        "status": True,
                        **file.to_log_dict(),
                    }
                )

            except Exception as error:  # pylint: disable=broad-exception-caught
                execution_log.append(
                    {
                        "status": False,
                        "error": error,
                        **file.to_log_dict(),
                    }
                )

        return {
            "status": True,
            "execution_log": execution_log,
            "file_was_created": len(files_to_process) > 0,
            "file_created_path": create_csv,
            "files_to_process": [dumpfile.file_name for dumpfile in files_to_process],
            "store_name": self.store_name,
            "files_types": self.file_type,
        }

    # def convert(self, full_path, file_type, update_date):
    #     """convert xml to database"""
    #     #
    #     try:
    #         id_field_name = xml.get_key_column()

    #         if not self.database.is_file_already_processed(full_path):

    #             # check there is not file that process after it.
    #             self.database.validate_all_data_source_processed_was_before(update_date)

    #             # insert line by line
    #             try:
    #                 if os.path.getsize(full_path) == 0:
    #                     raise Empty(f"File {full_path} is empty.")

    #                 raw = xml.convert(full_path)

    #                 if xml.should_convert_to_incremental():

    #                     # get the last not deleted entriees
    #                     not_deleted_entries = self.database.get_store_last_state(
    #                         id_field_name
    #                     )
    #                     #
    #                     if id_field_name not in raw.columns:
    #                         raise ValueError("pharse error, no id field")

    #                     for _, line in raw.iterrows():

    #                         # remove the Id from the list of doc in the collection
    #                         doc_id = line[id_field_name]

    #                         if doc_id in not_deleted_entries:
    #                             not_deleted_entries.remove(doc_id)

    #                         existing_doc = self.database.find_one_doc(
    #                             id_field_name, line[id_field_name]
    #                         )
    #                         insert_doc = line[line != "NOT_APPLY"].to_dict()

    #                         if not existing_doc or self.database.document_had_changed(
    #                             insert_doc, existing_doc
    #                         ):

    #                             # if there exits a document -> found a change
    #                             if existing_doc:
    #                                 print(
    #                                     f"Found an update for
    #                                       {existing_doc[id_field_name]}: \n"
    #                                     f"{self.database.diff_document
    #                                       (insert_doc,existing_doc)}\n"
    #                                 )

    #                             # insert with new update
    #                             self.database.insert_one_doc(insert_doc, update_date)

    #                     # mark deleted for the document left.
    #                     for entry_left in not_deleted_entries:
    #                         self.database.update_one_doc(
    #                             {id_field_name: entry_left},
    #                             id_field_name,
    #                             mark_deleted=True,
    #                         )
    #                 else:
    #                     # simpley add all
    #                     for _, line in raw.iterrows():
    #                         self.database.insert_one_doc(line.to_dict(), update_date)
    #             except Empty as error:
    #                 self.database.insert_file_processed(
    #                     {
    #                         "execption": str(error),
    #                         **self._to_doc(
    #                             full_path, file_type, update_date, id_field_name
    #                         ),
    #                     }
    #                 )
    #             else:
    #                 # update when all is done
    #                 self.database.insert_file_processed(
    #                     self._to_doc(full_path, file_type, update_date, id_field_name)
    #                 )
    #         return True
    #     except Exception as error:
    #         self.database.insert_failure(
    #             {
    #                 "execption": str(error),
    #                 **self._to_doc(full_path, file_type, update_date, id_field_name),
    #             }
    #         )
    #         return False

    # def _to_doc(self, full_path, file_type, update_date, id_field_name):
    #     return {
    #         "full_path": full_path,
    #         "update_date": update_date,
    #         "branch_store_id": self.branch_store_id,
    #         "store_name": self.store_name,
    #         "file_type": file_type,
    #         "id_field_name": id_field_name,
    #     }
