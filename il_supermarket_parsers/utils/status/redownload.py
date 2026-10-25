"""Diff scraper downloads against parser results to request re-downloads."""

from typing import Iterable, List


def normalize_dump_file_name(file_name: str) -> str:
    """Normalize a dump file name so scraper and parser names compare equal."""
    return (
        file_name.replace(".aspx", "")
        .replace(".xml", "")
        .replace(".gz", "")
        .replace("NULL", "")
    )


def files_to_download(
    downloaded_names: Iterable[str], parsed_names: Iterable[str]
) -> List[str]:
    """Return downloaded files the parser never resolved, normalized and sorted.

    ``downloaded_names`` is typically every ``verified_downloads`` file name in
    the scraper status; ``parsed_names`` every ``parsed_files`` file name in the
    parser status for the same chain.
    """
    parsed = {normalize_dump_file_name(name) for name in parsed_names if name}
    downloaded = {normalize_dump_file_name(name) for name in downloaded_names if name}
    return sorted(downloaded - parsed)
