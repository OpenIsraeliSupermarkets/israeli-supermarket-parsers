import os
import tempfile
import unittest

from il_supermarket_scarper import FileTypesFilters
from il_supermarket_scarper.utils import DumpFolderNames

from il_supermarket_parsers.utils.data_loaders.data_loader import DataLoader


STORE_ENUM = DumpFolderNames.BAREKET
STORE_FOLDER_NAME = STORE_ENUM.value  # e.g. "Bareket"


def _make_store_dir(root: str, store_folder_name: str = STORE_FOLDER_NAME) -> str:
    path = os.path.join(root, store_folder_name)
    os.makedirs(path, exist_ok=True)
    return path


def _touch(folder: str, filename: str) -> None:
    open(os.path.join(folder, filename), "w").close()


async def _collect(loader: DataLoader, **kwargs) -> list:
    results = []
    async for dump_file in loader.load(**kwargs):
        results.append(dump_file)
    return results


class TestDataLoaderBasic(unittest.IsolatedAsyncioTestCase):
    """DataLoader reads real files from a temporary directory."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.store_dir = _make_store_dir(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    async def test_returns_xml_files(self) -> None:
        _touch(self.store_dir, "PriceFull7290000000000-001-20250101.xml")
        loader = DataLoader(self.root)
        results = await _collect(loader)
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].file_name, "PriceFull7290000000000-001-20250101.xml"
        )

    async def test_skips_non_xml_files(self) -> None:
        _touch(self.store_dir, "PriceFull7290000000000-001-20250101.xml")
        _touch(self.store_dir, "readme.txt")
        _touch(self.store_dir, "data.csv")
        loader = DataLoader(self.root)
        results = await _collect(loader)
        self.assertEqual(len(results), 1)

    async def test_skips_files_at_root_level(self) -> None:
        """Files directly under root (not inside a store sub-folder) are ignored."""
        _touch(self.root, "PriceFull7290000000000-001-20250101.xml")
        loader = DataLoader(self.root)
        results = await _collect(loader)
        self.assertEqual(len(results), 0)

    async def test_empty_directory_returns_nothing(self) -> None:
        loader = DataLoader(self.root)
        results = await _collect(loader)
        self.assertEqual(results, [])

    async def test_results_sorted_by_date(self) -> None:
        _touch(self.store_dir, "PriceFull7290000000000-001-20250103.xml")
        _touch(self.store_dir, "PriceFull7290000000000-001-20250101.xml")
        _touch(self.store_dir, "PriceFull7290000000000-001-20250102.xml")
        loader = DataLoader(self.root)
        results = await _collect(loader)
        dates = [r.extracted_date for r in results]
        self.assertEqual(dates, sorted(dates))

    async def test_detects_file_type(self) -> None:
        _touch(self.store_dir, "PriceFull7290000000000-001-20250101.xml")
        _touch(self.store_dir, "Promo7290000000000-001-20250101.xml")
        loader = DataLoader(self.root)
        results = await _collect(loader)
        detected = {r.detected_filetype.name for r in results}
        self.assertIn("PRICE_FULL_FILE", detected)
        self.assertIn("PROMO_FILE", detected)

    async def test_detects_store_folder(self) -> None:
        _touch(self.store_dir, "PriceFull7290000000000-001-20250101.xml")
        loader = DataLoader(self.root)
        results = await _collect(loader)
        self.assertTrue(results[0].store_folder.endswith(STORE_FOLDER_NAME))


class TestDataLoaderLimit(unittest.IsolatedAsyncioTestCase):
    """DataLoader respects the ``limit`` parameter."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.store_dir = _make_store_dir(self.root)
        for day in range(1, 6):
            _touch(
                self.store_dir,
                f"PriceFull7290000000000-001-2025010{day}.xml",
            )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    async def test_limit_respected(self) -> None:
        loader = DataLoader(self.root)
        results = await _collect(loader, limit=2)
        self.assertEqual(len(results), 2)

    async def test_no_limit_returns_all(self) -> None:
        loader = DataLoader(self.root)
        results = await _collect(loader)
        self.assertEqual(len(results), 5)


class TestDataLoaderStoreFilter(unittest.IsolatedAsyncioTestCase):
    """DataLoader respects the ``enabled_scraper`` parameter."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.store_a_dir = _make_store_dir(self.root, DumpFolderNames.BAREKET.value)
        self.store_b_dir = _make_store_dir(self.root, DumpFolderNames.COFIX.value)
        _touch(self.store_a_dir, "PriceFull7290000000000-001-20250101.xml")
        _touch(self.store_b_dir, "PriceFull7290000000000-001-20250101.xml")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    async def test_filter_by_store_name(self) -> None:
        loader = DataLoader(self.root)
        results = await _collect(loader, enabled_scraper=["BAREKET"])
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].store_folder.endswith(DumpFolderNames.BAREKET.value))

    async def test_no_filter_returns_all_stores(self) -> None:
        loader = DataLoader(self.root)
        results = await _collect(loader)
        self.assertEqual(len(results), 2)


class TestDataLoaderFileTypeFilter(unittest.IsolatedAsyncioTestCase):
    """DataLoader respects the ``files_types`` parameter."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.store_dir = _make_store_dir(self.root)
        _touch(self.store_dir, "PriceFull7290000000000-001-20250101.xml")
        _touch(self.store_dir, "Promo7290000000000-001-20250101.xml")
        _touch(self.store_dir, "Stores7290000000000-001-20250101.xml")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    async def test_filter_single_type(self) -> None:
        loader = DataLoader(self.root)
        results = await _collect(loader, files_types=["PROMO_FILE"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].detected_filetype, FileTypesFilters.PROMO_FILE)

    async def test_filter_multiple_types(self) -> None:
        loader = DataLoader(self.root)
        results = await _collect(loader, files_types=["PROMO_FILE", "PRICE_FULL_FILE"])
        self.assertEqual(len(results), 2)

    async def test_no_filter_returns_all_types(self) -> None:
        loader = DataLoader(self.root)
        results = await _collect(loader)
        self.assertEqual(len(results), 3)


if __name__ == "__main__":
    unittest.main()
