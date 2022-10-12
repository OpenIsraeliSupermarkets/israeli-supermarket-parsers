import os
import re
import datetime
import pandas as pd
from . import Logger


def _find_file_type_and_chain_id(file_name):
    """get the file type"""
    lower_file_name = file_name.lower()
    match = re.search(r"\d", lower_file_name)
    index = match.start()
    return lower_file_name[:index], lower_file_name[index:]


def _file_name_to_components(xml_file_name, empty_store_id=0000):
    """ " split file to components"""
    try:
        file_name, store_number, date, *_ = xml_file_name.split(".")[0].split("-")
    except ValueError:
        # global files
        file_name, date, *_ = xml_file_name.split(".")[0].split("-")
        store_number = empty_store_id

    file_type, chain_id = _find_file_type_and_chain_id(file_name)

    if file_type == "storesfull":
        file_type = "stores"

    return (
        file_name,
        store_number,
        datetime.datetime.strptime(date, "%Y%m%d%H%M"),
        file_type,
        chain_id,
    )


def read_dump_folder(folder, store_names=None, files_types=None, empty_store_id=0000):
    """load details about the files in the folder"""
    files_in_dir = os.listdir(folder)

    files_types = files_types if files_types else ["xml"]
    files = []
    for store_name in files_in_dir:
        #
        store_folder = os.path.join(folder, store_name)

        # ignore list
        ignore_reason = None
        if store_name.startswith("."):
            ignore_reason = " contains '.'"
        if os.path.isfile(store_folder):
            ignore_reason = "is file and not folder"
        if store_names and store_name not in store_names:
            ignore_reason = "not in requested chains to scan"

        if ignore_reason:
            Logger.warning(f"Ignoreing file {store_folder}, {ignore_reason}")
            continue
        #
        for xml in os.listdir(store_folder):

            # skip files that are not xml
            ignore_file_reseaon = ""
            extension = xml.split(".")[-1]
            if extension not in files_types:
                ignore_file_reseaon = (
                    ignore_file_reseaon + f"file type not in {files_types}"
                )
            if "null" in xml.lower():
                ignore_file_reseaon = ignore_file_reseaon + " null file "

            if len(ignore_file_reseaon) > 0:
                Logger.warning(f"Ignoreing file {store_folder}, {ignore_file_reseaon}.")
                continue

            (
                file_name,
                store_number,
                date,
                file_type,
                chain_id,
            ) = _file_name_to_components(xml, empty_store_id=empty_store_id)
            full_path = os.path.join(store_folder, xml)

            files.append(
                (
                    file_name,
                    full_path,
                    chain_id,
                    file_type,
                    store_number,
                    date,
                    store_name,
                )
            )

    dumps_details = pd.DataFrame(
        files,
        columns=[
            "file",
            "full_path",
            "chain_id",
            "file_type",
            "branch_store_id",
            "update_date",
            "store_name",
        ],
    )
    dumps_details["branch_store_id"] = (
        dumps_details["branch_store_id"].replace("", empty_store_id).astype(int)
    )
    dumps_details["update_date"] = pd.to_datetime(dumps_details.update_date)
    return dumps_details
