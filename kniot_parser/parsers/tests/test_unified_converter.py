import shutil
from kniot_parser.parsers import UnifiedConverter
from kniot_parser.utils import read_dump_folder,get_sample_price_data,get_sample_store_data,get_sample_promo_data



def test_unifiing_store(folder = "samples_store"):
    """ test converting to data frame """

    #get_sample_store_data(folder)

    files_to_scan = read_dump_folder(folder=folder)

    for _, row in files_to_scan.iterrows():

        try:
            converter = UnifiedConverter(row['store_name'],row['file_type'])
            data_frame = converter.convert(row['full_path'])

            assert data_frame.empty or len(data_frame[converter.get_key_column()].value_counts()
                ) == data_frame.shape[0],f"{row['full_path']}, key is not unique." 
        except:
            converter.convert(row['full_path'])
    #shutil.rmtree(folder)


def test_unifiing_prices(folder = "samples_price"):
    """ test converting to data frame """

    #get_sample_price_data(folder)

    files_to_scan = read_dump_folder(folder=folder)

    for _, row in files_to_scan.iterrows():

        converter = UnifiedConverter(row['store_name'],row['file_type'])

        try:
            data_frame = converter.convert(row['full_path'])

            assert data_frame.empty or len(data_frame[converter.get_key_column()].value_counts()
                ) == data_frame.shape[0],f"{row['full_path']}, key is not unique."
        except:
            converter.convert(row['full_path'])


def test_unifiing_promo(folder = "samples_promo"):
    """ test converting to data frame """

    #get_sample_promo_data(folder)

    files_to_scan = read_dump_folder(folder=folder)

    for _, row in files_to_scan.iterrows():

        converter = UnifiedConverter(row['store_name'],row['file_type'])

        try:
            data_frame = converter.convert(row['full_path'])

            assert data_frame.empty or len(data_frame[converter.get_key_column()].value_counts()
                ) == data_frame.shape[0],f"{row['full_path']}, key is not unique."
        except:
            converter.convert(row['full_path'])

    #shutil.rmtree(folder)