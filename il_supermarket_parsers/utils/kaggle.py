import os



class KaggleDatasetManager:
    def __init__(self, username=None, key=None):
        from kaggle.api.kaggle_api_extended  import KaggleApi
        self.api = KaggleApi()
        if username and key:
            os.environ["KAGGLE_USERNAME"] = username
            os.environ["KAGGLE_KEY"] = key
        self.api.authenticate()

    def download_dataset(self, dataset, path="."):
        """
        Download a dataset from Kaggle.

        :param dataset: str, the dataset to download in the format 'owner/dataset-name'
        :param path: str, the path where to save the dataset (default is current directory)
        """
        try:
            self.api.dataset_download_files(dataset, path=path, unzip=True)
            print(f"Dataset '{dataset}' downloaded successfully to {path}")
        except Exception as e:
            print(f"Error downloading dataset: {e}")

    def upload_to_dataset(self, dataset, file_path, new_file_name=None):
        """
        Upload a new file to an existing Kaggle dataset.

        :param dataset: str, the dataset to upload to in the format 'owner/dataset-name'
        :param file_path: str, the path to the file to upload
        :param new_file_name: str, optional new name for the file in the dataset
        """
        try:
            if new_file_name is None:
                new_file_name = os.path.basename(file_path)

            metadata = {
                "path": file_path,
                "name": new_file_name,
            }

            self.api.dataset_create_version(dataset, metadata, dir_mode="replace")
            print(
                f"File '{new_file_name}' uploaded successfully to dataset '{dataset}'"
            )
        except Exception as e:
            print(f"Error uploading file: {e}")


# Example usage:
if __name__ == "__main__":
    manager = KaggleDatasetManager()

    # Upload a file to a dataset (make sure you have write permissions)
    manager.upload_to_dataset("israeli-supermarkets-2024", "tmp/file.csv")
