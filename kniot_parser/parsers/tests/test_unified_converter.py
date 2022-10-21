import shutil
import pytest
from kniot_parser.parsers import UnifiedConverter
from kniot_parser.utils import (
    read_dump_folder,
    get_sample_price_data,
    get_sample_store_data,
    get_sample_promo_data,
    get_sample_price_full_data,
    get_sample_promo_full_data,
)


def check_converting_to_data_frame_and_index(folder):
    """ check converting to df and index """
    files_to_scan = read_dump_folder(folder=folder)

    for _, row in files_to_scan.iterrows():

        try:
            converter = UnifiedConverter(row["store_name"], row["file_type"])
            data_frame = converter.convert(row["full_path"])
        except Exception as e:
            converter.convert(row["full_path"])
        assert (
            data_frame.empty
            or len(data_frame[converter.get_key_column()].value_counts())
            == data_frame.shape[0]
        ), f"{row['full_path']}, key is not unique."


@pytest.mark.run(order=1)
def test_unifiing_store():
    """test converting to data frame"""

    folder = "samples_store"
    get_sample_store_data(folder)
    check_converting_to_data_frame_and_index(folder)
    # shutil.rmtree(folder)


@pytest.mark.run(order=2)
def test_unifiing_prices():
    """test converting to data frame"""

    folder = "samples_price"
    get_sample_price_data(folder)
    check_converting_to_data_frame_and_index(folder)
    # shutil.rmtree(folder)


@pytest.mark.run(order=3)
def test_unifiing_prices_full():
    """test converting to data frame"""

    folder = "samples_price_full"
    get_sample_price_full_data(folder)
    check_converting_to_data_frame_and_index(folder)
    # shutil.rmtree(folder)


@pytest.mark.run(order=4)
def test_unifiing_promo():
    """test converting to data frame"""

    folder = "samples_promo"
    get_sample_promo_data(folder)
    check_converting_to_data_frame_and_index(folder)
    # shutil.rmtree(folder)


@pytest.mark.run(order=5)
def test_unifiing_promo_full():
    """test converting to data frame"""

    folder = "samples_promo_full"
    get_sample_promo_full_data(folder)
    check_converting_to_data_frame_and_index(folder)
    # shutil.rmtree(folder)
