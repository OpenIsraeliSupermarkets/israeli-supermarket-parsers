from schema_matching import (
    schema_matching,
)  # https://github.com/fireindark707/Python-Schema-Matching
import json
import os
import itertools
import xmltodict
import pandas as pd
import numpy as np


def convert_to_json(xml_file_name, output_folder):
    # open the input xml file and read
    # data in form of python dictionary
    # using xmltodict module
    json_file_name = xml_file_name.replace("/", "_").replace("xml", "json")

    encoding = None
    if "Super-Pharm" in xml_file_name:
        encoding = "ISO-8859-8"
    with open(xml_file_name, encoding=encoding) as xml_file:

        data_dict = xmltodict.parse(xml_file.read())
        json_data = json.dumps(data_dict)

        # json file
        json_location = os.path.join(output_folder, json_file_name)
        with open(json_location, "w", encoding=encoding) as json_file:
            json_file.write(json_data)
    return json_location


def convert_all_folders_to_jsons(chain_folder, output_folder, limit=None):
    all_xml_files = os.listdir(chain_folder)

    if limit:
        all_xml_files = np.random.choice(
            all_xml_files, size=min(limit, len(all_xml_files))
        )

    json_files = []
    for xml_file in all_xml_files:
        json_files.append(
            convert_to_json(os.path.join(chain_folder, xml_file), output_folder)
        )

    return json_files


def delete_all_files(output_folder):
    for file in os.listdir(output_folder):
        os.remove(os.path.join(output_folder, file))


def match_two_files(file_a, file_b):
    _, _, predicted_pairs = schema_matching(file_a, file_b, strategy="one-to-one")
    return predicted_pairs


def create_permutations(list_a, list_b):
    permutations = list(itertools.product(list_a, list_b))
    return permutations, list(map(lambda x: "_VS_".join(x), permutations))


def match_to_frame(data):
    return pd.DataFrame(data, columns=["base", "other", "match"])


def get_all_groups_to_compare(dump_folder, limit=None):
    all_chains = os.listdir(dump_folder)

    output_folder = os.path.join(dump_folder, "TEMP")
    os.mkdir(output_folder)

    base_chain = all_chains[0]
    all_chains = all_chains[1:]

    for chain in all_chains:

        base_json_files = convert_all_folders_to_jsons(
            os.path.join(dump_folder, base_chain), output_folder, limit=limit
        )
        other_json_files = convert_all_folders_to_jsons(
            os.path.join(dump_folder, chain), output_folder, limit=limit
        )

        chain_matchs = dict()
        permutations, names = create_permutations(base_json_files, other_json_files)
        for permutation, name in zip(permutations, names):
            match = match_two_files(*permutation)
            chain_matchs[name] = match_to_frame(match)

        full_match = None
        for match_name, match in chain_matchs.items():
            if full_match is not None:
                full_match = pd.merge(
                    left=full_match,
                    right=match.rename(columns={"match": f"match_{match_name}"}),
                    on=["base", "other"],
                    how="left",
                )
            else:
                full_match = match.rename(columns={"match": f"match_{match_name}"})

        delete_all_files(output_folder)

        full_match.to_csv(os.path.join(dump_folder, f"{base_chain} to {chain}.csv"))


if __name__ == "__main__":
    get_all_groups_to_compare("samples_price", limit=2)
