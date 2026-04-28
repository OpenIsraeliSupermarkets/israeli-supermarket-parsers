import pandas as pd
from typing import Union


def read_data_rows(
    csv_path: str, ffill: bool = False, as_records: bool = True
) -> Union[List[Dict[str, str]], pd.DataFrame]:
    """Read data rows from the CSV file."""
    df = pd.read_csv(csv_path, dtype=str)
    if ffill and not df.empty:
        df = df.ffill()
    if as_records:
        return df.to_dict(orient="records")
    return df
