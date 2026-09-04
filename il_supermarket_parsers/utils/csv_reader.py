from typing import Union, List, Dict

import pandas as pd


def read_data_rows(
    csv_path: str, ffill: bool = False, as_records: bool = True
) -> Union[List[Dict[str, str]], pd.DataFrame]:
    """Read data rows from the CSV file.

    Empty CSV fields (RLE-masked duplicates) become NA so :meth:`ffill` can
    restore them. Literal XML tokens such as ``null`` must stay strings —
    pandas' default NA list would turn them into NA and ffill would copy the
    previous row.
    """
    df = pd.read_csv(
        csv_path,
        dtype=str,
        keep_default_na=False,
        na_values=[""],
    )
    if ffill and not df.empty:
        df = df.ffill()
    if as_records:
        return df.to_dict(orient="records")
    return df
