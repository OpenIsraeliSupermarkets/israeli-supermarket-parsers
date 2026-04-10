# import datetime
# import os
# import pymongo

# from .diff import compare_documents
# from .logger import Logger


# class MongoDb(object):
#     """mongo db interface"""

#     UPDATED_FIELD = "UpdateDate"
#     DELETED_FIELD = "IsDeleted"
#     URL = os.getenv("MONGO_URL", "localhost:27017")

#     def __init__(self, store_name, branch_store_id, file_type) -> None:
#         self.store_name = store_name
#         self.branch_store_id = branch_store_id
#         self.file_type = file_type
#         self.ignore_list = ["file_id", "_id", self.UPDATED_FIELD]

#         Logger.info(f"Using {self.URL} mongo.")
#         self.db_name = self.store_name.replace(" ", "_").lower()

#         myclient = self._get_mongo()
#         store_db = myclient[self.db_name]

#         self.data_sources_collection = store_db[f"{self.file_type}_data_sources"]
#         self.data_collection = store_db[f"{self.file_type}_{self.branch_store_id}"]
#         self.failures_collection = store_db[f"{self.file_type}_runtime_error"]

#     def _get_mongo(self):
#         return pymongo.MongoClient(f"mongodb://{self.URL}/")

#     def drop(self):
#         """drop all contant"""
#         self.data_sources_collection.drop()
#         self.data_collection.drop()
#         self.failures_collection.drop()

#     def get_store_last_state(self, id_field_name):
#         return list(
#             map(
#                 lambda x: x["_id"],
#                 self.data_collection.aggregate(
#                     [
#                         {"$sort": {id_field_name: 1, self.UPDATED_FIELD: 1}},
#                         {
#                             "$group": {
#                                 "_id": f"${id_field_name}",
#                                 "last_update": {"$first": f"${self.UPDATED_FIELD}"},
#                                 "is_deleted": {"$first": f"${self.DELETED_FIELD}"},
#                             }
#                         },
#                         {"$match": {"is_deleted": {"$eq": False}}},
#                     ]
#                 ),
#             )
#         )

#     def is_file_already_processed(self, full_path):
#         return self.data_sources_collection.find_one({"full_path": full_path}) != None

#     def validate_all_data_source_processed_was_before(self, update_date):
#         later_docs = self.data_sources_collection.find_one(
#             {
#                 "file_type": self.file_type,
#                 "store_name": self.store_name,
#                 "branch_store_id": self.branch_store_id,
#                 "update_date": {"$gt": update_date},
#             }
#         )
#         if later_docs:
#             raise ValueError(
#                 f"System failure, was asked to processed when {later_docs} already processed."
#             )

#     def find_one_doc(self, id, id_value):
#         return self.data_collection.find_one({id: id_value})

#     def insert_one_doc(self, inserted_doc, update_date=datetime.datetime.now()):
#         return self.data_collection.insert_one(
#             {**inserted_doc, self.UPDATED_FIELD: update_date, self.DELETED_FIELD: False}
#         )

#     def insert_file_processed(self, inserted_doc, update_date=datetime.datetime.now()):
#         return self.data_sources_collection.insert_one(
#             {
#                 **inserted_doc,
#                 self.UPDATED_FIELD: update_date,
#             }
#         )

#     def insert_failure(self, inserted_doc, update_date=datetime.datetime.now()):
#         return self.failures_collection.insert_one(
#             {
#                 **inserted_doc,
#                 self.UPDATED_FIELD: update_date,
#             }
#         )

#     def update_one_doc(self, entry_left, id_field_name, mark_deleted=False):
#         return self.data_collection.update_one(
#             {id_field_name: entry_left}, {"$set": {self.DELETED_FIELD: mark_deleted}}
#         )

#     def list_failure(self):
#         return list(self.failures_collection.find({}))

#     def clear(self):
#         self._get_mongo().drop_database(self.db_name)  # pass db name as string

#     def document_had_changed(self, inserted_doc, existing_doc):
#         return existing_doc[self.DELETED_FIELD] or not compare_documents(
#             inserted_doc, existing_doc, self.ignore_list + [self.DELETED_FIELD]
#         )

#     def diff_document(self, inserted_doc, existing_doc):
#         return compare_documents(inserted_doc, existing_doc, self.ignore_list)
