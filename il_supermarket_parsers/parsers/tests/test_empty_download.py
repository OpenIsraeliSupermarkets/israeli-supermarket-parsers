"""A chain test that downloads no files must skip with a reason or fail (#133)."""

import os
import unittest
from unittest import mock

from il_supermarket_scarper import ScraperFactory
from il_supermarket_parsers.parser_factory import ParserFactory
from il_supermarket_parsers.parsers.tests import test_case
from il_supermarket_parsers.parsers.tests.test_case import (
    empty_download_skip_reason,
    make_test_case,
)


def _make_empty_download(folder, _options):
    """stand-in for get_sample_data: the scraper creates the folder, no files"""
    os.makedirs(folder, exist_ok=True)


def _run_store_test(enabled, approved):
    """Run one chain test with no network: the download yields nothing."""
    # built here, not at module level, so pytest does not collect the real
    # (network) chain tests from this module
    chain = make_test_case(ScraperFactory.BAREKET, ParserFactory.BAREKET)
    with mock.patch.object(
        test_case.ScraperFactory, "is_scraper_enabled", return_value=enabled
    ), mock.patch.object(
        test_case, "get_sample_data", side_effect=_make_empty_download
    ) as download, mock.patch.object(
        test_case.ScraperStability,
        "is_validate_scraper_found_no_files",
        return_value=approved,
    ) as stability:
        result = unittest.TestResult()
        chain("test_parsing_store").run(result)
    return result, download, stability


class TestEmptyDownload(unittest.TestCase):
    """the three paths of a chain test with no downloaded files"""

    def test_disabled_scraper_is_skipped_not_passed(self):
        """deprecated / DISABLED_SCRAPPERS -> skip, nothing downloaded"""
        result, download, _ = _run_store_test(enabled=False, approved=False)
        self.assertEqual(len(result.skipped), 1)
        self.assertIn("disabled", result.skipped[0][1])
        self.assertEqual(result.failures + result.errors, [])
        download.assert_not_called()

    def test_approved_empty_download_is_skipped(self):
        """stability rule approves the empty listing -> skip with reason"""
        result, download, stability = _run_store_test(enabled=True, approved=True)
        self.assertEqual(len(result.skipped), 1)
        self.assertIn("approved by ScraperStability", result.skipped[0][1])
        self.assertEqual(result.failures + result.errors, [])
        download.assert_called_once()
        # stability sees the same filters and execution time as the download
        options = download.call_args.args[1]
        kwargs = stability.call_args.kwargs
        self.assertEqual(kwargs["files_types"], [options.filter_type])
        self.assertEqual(kwargs["limit"], options.limit)
        self.assertEqual(kwargs["when_date"], options.when_date)
        self.assertIsNotNone(options.when_date)

    def test_unapproved_empty_download_fails(self):
        """nothing downloaded and no stability rule -> failure"""
        result, _, _ = _run_store_test(enabled=True, approved=False)
        self.assertEqual(len(result.failures), 1)
        self.assertIn("No STORE_FILE files downloaded", result.failures[0][1])
        self.assertEqual(result.skipped, [])

    def test_skip_reason_helper(self):
        """the helper returns None exactly when the empty result is not approved"""
        with mock.patch.object(
            test_case.ScraperStability,
            "is_validate_scraper_found_no_files",
            return_value=False,
        ):
            self.assertIsNone(
                empty_download_skip_reason(
                    ScraperFactory.BAREKET, "STORE_FILE", 1, None
                )
            )
