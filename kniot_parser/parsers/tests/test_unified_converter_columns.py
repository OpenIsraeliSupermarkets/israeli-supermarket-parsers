import shutil
import pytest
from kniot_parser.parsers import UnifiedConverter
from kniot_parser.utils import (
    read_dump_folder,
    get_sample_price_data,
    get_sample_store_data,
    get_sample_promo_data,
    get_sample_price_full_data,
)


def templete(folder, expected_store_columns):

    files_to_scan = read_dump_folder(folder=folder)
    for _, row in files_to_scan.iterrows():

        converter = UnifiedConverter(row["store_name"], row["file_type"])
        data_frame = converter.convert(row["full_path"], row_limit=1)

        sorted_columns_names = sorted(data_frame.columns)
        if len(data_frame.columns) != len(expected_store_columns) or not (
            sorted_columns_names == expected_store_columns
        ):
            print()


@pytest.mark.run(order=1)
def test_unifiing_store_columns(folder="samples_store"):
    """test converting to data frame"""

    # get_sample_store_data(folder)

    templete(
        folder,
        [
            "address",
            "bikoretno",
            "chainid",
            "chainname",
            "city",
            "file_id",
            "lastupdatedate",
            "lastupdatetime",
            "storeid",
            "storename",
            "storetype",
            "subchainid",
            "subchainname",
            "zipcode",
        ],
    )


@pytest.mark.run(order=2)
def test_unifiing_prices_columns(folder="samples_price"):
    """test converting to data frame"""

    get_sample_price_data(folder)
    templete(
        folder,
        [
            "allowdiscount",
            "bikoretno",
            "bisweighted",
            "chainid",
            "file_id",
            "itemcode",
            "itemid",
            "itemname",
            "itemprice",
            "itemstatus",
            "itemtype",
            "manufacturecountry",
            "manufactureritemdescription",
            "manufacturername",
            "priceupdatedate",
            "qtyinpackage",
            "quantity",
            "storeid",
            "subchainid",
            "unitofmeasure",
            "unitofmeasureprice",
            "unitqty",
        ],
    )


@pytest.mark.run(order=3)
def test_unifiing_prices_full_columns(folder="samples_price_full"):
    """test converting to data frame"""

    get_sample_price_full_data(folder)
    templete(
        folder,
        [
            "allowdiscount",
            "bikoretno",
            "bisweighted",
            "chainid",
            "file_id",
            "itemcode",
            "itemid",
            "itemname",
            "itemprice",
            "itemstatus",
            "itemtype",
            "manufacturecountry",
            "manufactureritemdescription",
            "manufacturername",
            "priceupdatedate",
            "qtyinpackage",
            "quantity",
            "storeid",
            "subchainid",
            "unitofmeasure",
            "unitofmeasureprice",
            "unitqty",
        ],
    )

    # shutil.rmtree(folder)


@pytest.mark.run(order=3)
def test_unifiing_promo(folder="samples_promo"):
    """test converting to data frame"""

    get_sample_promo_data(folder)

    files_to_scan = read_dump_folder(folder=folder)

    for _, row in files_to_scan.iterrows():

        converter = UnifiedConverter(row["store_name"], row["file_type"])
        data_frame = converter.convert(row["full_path"])

        assert (
            data_frame.empty
            or len(data_frame[converter.get_key_column()].value_counts())
            == data_frame.shape[0]
        ), f"{row['full_path']}, key is not unique."

    # shutil.rmtree(folder)
