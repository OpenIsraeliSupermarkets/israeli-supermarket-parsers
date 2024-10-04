import os
import pandas as pd
from tqdm import tqdm
from .parser_factroy import ParserFactory
from .utils import DataLoader


class RawParseingPipeline:
    """
    processing files to dataframe
    """

    def __init__(self, folder, store_name, file_type, output_folder) -> None:
        self.store_name = store_name
        self.file_type = file_type
        self.folder = folder
        self.output_folder = output_folder

    def process(self):
        """start processing the files selected in the pipeline input"""
        parser_class = ParserFactory.get(self.store_name)

        data_frames = []
        files_to_process = DataLoader(
            self.folder,
            store_names=[self.store_name],
            files_types=[self.file_type],
        ).load()

        for file in tqdm(
            files_to_process,
            total=len(files_to_process),
            desc=f"Processing {self.file_type}@{self.store_name}",
        ):

            parser = parser_class()
            file.data = parser.read(file)
            data_frames.append(file.data)

        create_csv = os.path.join(
            self.output_folder,
            self.file_type.lower() + "_" + self.store_name.lower() + ".csv",
        )

        if data_frames:
            pd.concat(data_frames).to_csv(
                create_csv,
                index=False,
            )
            return {"status": True, "path": create_csv}
        return {
            "status": False,
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
