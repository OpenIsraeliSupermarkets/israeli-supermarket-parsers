# from .utils.data_loading import read_dump_folder
# from database_interface import MongoDb
# from multiprocess_pharser import ConvertingProcess

# # def get_sample_from_all(dump_folder_name):
# #     from kniot_scrapper.main import Main
# #     from kniot_scrapper.utils.file_types import FileTypesFilters
# #     return Main().start(limit=1,files_types=FileTypesFilters.all_large(),dump_folder_name=dump_folder_name)

# # TODO: make sure we can pharse files
# # TODO: check why shufersal is not downloading right


# def read_all(store_name="bareket"):

#     failed = list()
#     files_to_scan = (
#         read_dump_folder(folder="dumps", store_names=[store_name])
#         .groupby("file_type")
#         .sample(frac=0.1)
#         .head(2)
#         .sort_values("update_date")
#     )

#     for index, row in files_to_scan.iterrows():

#         MongoDb(row["store_name"], row["branch_store_id"], row["file_type"]).clear()
#         insert_states = False
#         try:
#             insert_states = (
#                 ConvertingProcess.insert_task(**row),
#                 f"{index}: {row} failed.",
#             )
#         finally:

#             if not insert_states:
#                 failed.append(row)

#             # make sure no failure was captured
#             all_failures = MongoDb(
#                 row["store_name"], row["branch_store_id"], row["file_type"]
#             ).list_failure()
#             assert len(all_failures) == 0
#     assert len(failed) == 0, f" should be empty {failed}"


# def test_bareket():
#     read_all("bareket")


# def test_cofix():
#     read_all("cofix")


# def test_dor_alon():
#     read_all("Dor Alon")


# def test_good_pharm():
#     read_all("GoodPharm")


# def test_hazi_hinam():
#     read_all("Hazi Hinam")


# def test_keshet_taamim():
#     read_all("Keshet Taamim")


# def test_king_store():
#     read_all("King Store")


# def test_maayan2000():
#     read_all("Maayan2000")


# def test_mahsan_shuk():
#     read_all("mahsani a shuk")


# def test_mega():
#     read_all("mega")


# def test_mega_market():
#     read_all("mega-market")


# def test_mega_market():
#     read_all("mega-market")


# def test_netiv_hasef():
#     read_all("Netiv Hasef")


# def test_polizer():
#     read_all("Polizer")


# def test_osher_ad():
#     read_all("Osher Ad")


# def test_rami_levy():
#     read_all("Rami Levy")


# def test_salachdabach():
#     read_all("salachdabach")


# def test_shefa_barcart_ashem():
#     read_all("ShefaBarcartAshem")


# def test_shufersal():
#     read_all("Shufersal")


# def test_shuk_ahir():
#     read_all("Shuk Ahir")


# def test_super_dosh():
#     read_all("Super Dosh")


# def test_super_pharm():
#     read_all("Super-Pharm")


# def test_super_yuda():
#     read_all("SuperYuda")


# def test_tiv_taam():
#     read_all("Tiv Taam")


# def test_victory():
#     read_all("Victory")


# def test_yellow():
#     read_all("Yellow")


# def test_yohananof():
#     read_all("Yohananof")


# def test_zol_ve_begadol():
#     read_all("ZolVeBegadol")
