import unittest
import os
from unittest.mock import patch

from main import load_params


class TestLoadParams(unittest.TestCase):
    """Test cases for the load_params function"""

    def runner_module(self) -> str:
        """Module under test (helps test tooling introspection)."""
        return "main"

    @staticmethod
    def _clear_env_vars():
        """Helper method to clear relevant environment variables."""
        env_vars_to_clear = [
            "ENABLED_PARSERS",
            "ENABLED_FILE_TYPES",
            "NUMBER_OF_PROCESSES",
            "LIMIT",
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

    def setUp(self):
        """Set up test fixtures before each test method."""
        self._clear_env_vars()

    def tearDown(self):
        """Clean up after each test method."""
        self._clear_env_vars()

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_no_environment_variables(self, mock_file_types, mock_parser_factory):
        """Test load_params when no environment variables are set"""
        result = load_params()
        self.assertEqual(result, {})

        # Verify that the factory methods were not called since no env vars were set
        mock_parser_factory.all_parsers_name.assert_not_called()
        mock_file_types.all_types.assert_not_called()

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_valid_enabled_parsers(self, _mock_file_types, mock_parser_factory):
        """Test load_params with valid ENABLED_PARSERS"""
        # Mock the available parsers
        mock_parser_factory.all_parsers_name.return_value = [
            "BAREKET",
            "SHUFERSAL",
            "RAMI_LEVY",
            "SUPER_PHARM",
        ]

        # Set environment variable
        os.environ["ENABLED_PARSERS"] = "BAREKET,SHUFERSAL"

        result = load_params()

        expected = {"enabled_parsers": ["BAREKET", "SHUFERSAL"]}
        self.assertEqual(result, expected)
        # Verify that all_parsers_name was called (may be called multiple times in validation)
        self.assertTrue(mock_parser_factory.all_parsers_name.called)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_invalid_enabled_parsers(self, _mock_file_types, mock_parser_factory):
        """Test load_params with invalid ENABLED_PARSERS"""
        # Mock the available parsers
        mock_parser_factory.all_parsers_name.return_value = [
            "BAREKET",
            "SHUFERSAL",
            "RAMI_LEVY",
        ]

        # Set environment variable with invalid parser
        os.environ["ENABLED_PARSERS"] = "BAREKET,INVALID_PARSER"

        with self.assertRaises(ValueError) as context:
            load_params()

        self.assertIn("ENABLED_PARSERS contains invalid", str(context.exception))
        self.assertIn("INVALID_PARSER", str(context.exception))

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_valid_enabled_file_types(self, mock_file_types, _mock_parser_factory):
        """Test load_params with valid ENABLED_FILE_TYPES"""
        # Mock the available file types
        mock_file_types.all_types.return_value = [
            "PRICE_FILE",
            "PROMO_FILE",
            "STORE_FILE",
            "PRICE_FULL_FILE",
            "PROMO_FULL_FILE",
        ]

        # Set environment variable
        os.environ["ENABLED_FILE_TYPES"] = "PRICE_FILE,PROMO_FILE"

        result = load_params()

        expected = {"files_types": ["PRICE_FILE", "PROMO_FILE"]}
        self.assertEqual(result, expected)
        # Verify that all_types was called (may be called multiple times in validation)
        self.assertTrue(mock_file_types.all_types.called)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_invalid_enabled_file_types(self, mock_file_types, _mock_parser_factory):
        """Test load_params with invalid ENABLED_FILE_TYPES"""
        # Mock the available file types
        mock_file_types.all_types.return_value = [
            "PRICE_FILE",
            "PROMO_FILE",
            "STORE_FILE",
        ]

        # Set environment variable with invalid file type
        os.environ["ENABLED_FILE_TYPES"] = "PRICE_FILE,INVALID_TYPE"

        with self.assertRaises(ValueError) as context:
            load_params()

        self.assertIn("ENABLED_FILE_TYPES contains invalid", str(context.exception))
        self.assertIn("INVALID_TYPE", str(context.exception))

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_valid_number_of_processes(self, _mock_file_types, _mock_parser_factory):
        """Test load_params with valid NUMBER_OF_PROCESSES"""
        os.environ["NUMBER_OF_PROCESSES"] = "4"

        result = load_params()

        expected = {"multiprocessing": 4}
        self.assertEqual(result, expected)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_invalid_number_of_processes(self, _mock_file_types, _mock_parser_factory):
        """Test load_params with invalid NUMBER_OF_PROCESSES"""
        os.environ["NUMBER_OF_PROCESSES"] = "not_a_number"

        with self.assertRaises(ValueError) as context:
            load_params()

        self.assertEqual(
            str(context.exception), "NUMBER_OF_PROCESSES must be an integer"
        )

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_valid_limit(self, _mock_file_types, _mock_parser_factory):
        """Test load_params with valid LIMIT"""
        os.environ["LIMIT"] = "100"

        result = load_params()

        expected = {"limit": 100}
        self.assertEqual(result, expected)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_invalid_limit(self, _mock_file_types, _mock_parser_factory):
        """Test load_params with invalid LIMIT"""
        os.environ["LIMIT"] = "not_a_number"

        with self.assertRaises(ValueError) as context:
            load_params()

        self.assertEqual(
            str(context.exception), "LIMIT must be an integer, but got not_a_number"
        )

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_all_valid_parameters(self, mock_file_types, mock_parser_factory):
        """Test load_params with all valid environment variables set"""
        # Mock the available options
        mock_parser_factory.all_parsers_name.return_value = [
            "BAREKET",
            "SHUFERSAL",
            "RAMI_LEVY",
            "SUPER_PHARM",
        ]
        mock_file_types.all_types.return_value = [
            "PRICE_FILE",
            "PROMO_FILE",
            "STORE_FILE",
            "PRICE_FULL_FILE",
            "PROMO_FULL_FILE",
        ]

        # Set all environment variables
        os.environ["ENABLED_PARSERS"] = "BAREKET,SHUFERSAL"
        os.environ["ENABLED_FILE_TYPES"] = "PRICE_FILE,STORE_FILE"
        os.environ["NUMBER_OF_PROCESSES"] = "8"
        os.environ["LIMIT"] = "500"

        result = load_params()

        expected = {
            "enabled_parsers": ["BAREKET", "SHUFERSAL"],
            "files_types": ["PRICE_FILE", "STORE_FILE"],
            "multiprocessing": 8,
            "limit": 500,
        }
        self.assertEqual(result, expected)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_empty_enabled_parsers(self, _mock_file_types, mock_parser_factory):
        """Test load_params with empty ENABLED_PARSERS"""
        mock_parser_factory.all_parsers_name.return_value = ["BAREKET", "SHUFERSAL"]

        os.environ["ENABLED_PARSERS"] = ""

        result = load_params()

        # Empty string should not trigger validation since it's falsy
        self.assertEqual(result, {})

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_empty_enabled_file_types(self, mock_file_types, _mock_parser_factory):
        """Test load_params with empty ENABLED_FILE_TYPES"""
        mock_file_types.all_types.return_value = ["PRICE_FILE", "PROMO_FILE"]

        os.environ["ENABLED_FILE_TYPES"] = ""

        result = load_params()

        # Empty string should not trigger validation since it's falsy
        self.assertEqual(result, {})

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_single_parser(self, _mock_file_types, mock_parser_factory):
        """Test load_params with single parser (no comma)"""
        mock_parser_factory.all_parsers_name.return_value = ["BAREKET", "SHUFERSAL"]

        os.environ["ENABLED_PARSERS"] = "BAREKET"

        result = load_params()

        expected = {"enabled_parsers": ["BAREKET"]}
        self.assertEqual(result, expected)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_single_file_type(self, mock_file_types, _mock_parser_factory):
        """Test load_params with single file type (no comma)"""
        mock_file_types.all_types.return_value = ["PRICE_FILE", "PROMO_FILE"]

        os.environ["ENABLED_FILE_TYPES"] = "PRICE_FILE"

        result = load_params()

        expected = {"files_types": ["PRICE_FILE"]}
        self.assertEqual(result, expected)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_zero_processes(self, _mock_file_types, _mock_parser_factory):
        """Test load_params with zero NUMBER_OF_PROCESSES"""
        os.environ["NUMBER_OF_PROCESSES"] = "0"

        result = load_params()

        expected = {"multiprocessing": 0}
        self.assertEqual(result, expected)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_zero_limit(self, _mock_file_types, _mock_parser_factory):
        """Test load_params with zero LIMIT"""
        os.environ["LIMIT"] = "0"

        result = load_params()

        expected = {"limit": 0}
        self.assertEqual(result, expected)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_negative_number_of_processes(self, _mock_file_types, _mock_parser_factory):
        """Test load_params with negative NUMBER_OF_PROCESSES"""
        os.environ["NUMBER_OF_PROCESSES"] = "-1"

        result = load_params()

        expected = {"multiprocessing": -1}
        self.assertEqual(result, expected)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_negative_limit(self, _mock_file_types, _mock_parser_factory):
        """Test load_params with negative LIMIT"""
        os.environ["LIMIT"] = "-10"

        result = load_params()

        expected = {"limit": -10}
        self.assertEqual(result, expected)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_multiple_invalid_parsers(self, _mock_file_types, mock_parser_factory):
        """Test load_params with multiple invalid parsers"""
        mock_parser_factory.all_parsers_name.return_value = ["BAREKET"]

        os.environ["ENABLED_PARSERS"] = "INVALID1,INVALID2,BAREKET"

        with self.assertRaises(ValueError) as context:
            load_params()

        error_msg = str(context.exception)
        self.assertIn("ENABLED_PARSERS contains invalid", error_msg)
        self.assertIn("INVALID1", error_msg)
        self.assertIn("INVALID2", error_msg)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_multiple_invalid_file_types(self, mock_file_types, _mock_parser_factory):
        """Test load_params with multiple invalid file types"""
        mock_file_types.all_types.return_value = ["PRICE_FILE"]

        os.environ["ENABLED_FILE_TYPES"] = "INVALID1,INVALID2,PRICE_FILE"

        with self.assertRaises(ValueError) as context:
            load_params()

        error_msg = str(context.exception)
        self.assertIn("ENABLED_FILE_TYPES contains invalid", error_msg)
        self.assertIn("INVALID1", error_msg)
        self.assertIn("INVALID2", error_msg)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_whitespace_in_enabled_parsers(self, _mock_file_types, mock_parser_factory):
        """Test load_params with whitespace in ENABLED_PARSERS"""
        mock_parser_factory.all_parsers_name.return_value = [
            "BAREKET",
            "SHUFERSAL",
            "RAMI_LEVY",
        ]

        # Test spaces after comma
        os.environ["ENABLED_PARSERS"] = "BAREKET, SHUFERSAL"

        with self.assertRaises(ValueError) as context:
            load_params()

        # Should fail because ' SHUFERSAL' (with leading space) is not in valid parsers
        self.assertIn("ENABLED_PARSERS contains invalid", str(context.exception))

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_leading_trailing_whitespace_parsers(
        self, _mock_file_types, mock_parser_factory
    ):
        """Test load_params with leading/trailing whitespace in ENABLED_PARSERS"""
        mock_parser_factory.all_parsers_name.return_value = ["BAREKET", "SHUFERSAL"]

        # Test leading and trailing spaces
        os.environ["ENABLED_PARSERS"] = " BAREKET,SHUFERSAL "

        with self.assertRaises(ValueError) as context:
            load_params()

        # Should fail because ' BAREKET' and 'SHUFERSAL ' are not in valid parsers
        self.assertIn("ENABLED_PARSERS contains invalid", str(context.exception))

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_empty_elements_in_parsers(self, _mock_file_types, mock_parser_factory):
        """Test load_params with empty elements in ENABLED_PARSERS"""
        mock_parser_factory.all_parsers_name.return_value = ["BAREKET", "SHUFERSAL"]

        # Test double comma creating empty element
        os.environ["ENABLED_PARSERS"] = "BAREKET,,SHUFERSAL"

        with self.assertRaises(ValueError) as context:
            load_params()

        # Should fail because empty string is not in valid parsers
        self.assertIn("ENABLED_PARSERS contains invalid", str(context.exception))

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_whitespace_in_enabled_file_types(
        self, mock_file_types, _mock_parser_factory
    ):
        """Test load_params with whitespace in ENABLED_FILE_TYPES"""
        mock_file_types.all_types.return_value = [
            "PRICE_FILE",
            "PROMO_FILE",
            "STORE_FILE",
        ]

        # Test spaces after comma
        os.environ["ENABLED_FILE_TYPES"] = "PRICE_FILE, PROMO_FILE"

        with self.assertRaises(ValueError) as context:
            load_params()

        # Should fail because ' PROMO_FILE' (with leading space) is not in valid types
        self.assertIn("ENABLED_FILE_TYPES contains invalid", str(context.exception))

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_leading_trailing_whitespace_file_types(
        self, mock_file_types, _mock_parser_factory
    ):
        """Test load_params with leading/trailing whitespace in ENABLED_FILE_TYPES"""
        mock_file_types.all_types.return_value = ["PRICE_FILE", "PROMO_FILE"]

        # Test leading and trailing spaces
        os.environ["ENABLED_FILE_TYPES"] = " PRICE_FILE,PROMO_FILE "

        with self.assertRaises(ValueError) as context:
            load_params()

        # Should fail because ' PRICE_FILE' and 'PROMO_FILE ' are not in valid types
        self.assertIn("ENABLED_FILE_TYPES contains invalid", str(context.exception))

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_case_sensitivity_parsers_lowercase(
        self, _mock_file_types, mock_parser_factory
    ):
        """Test load_params with lowercase parser names"""
        mock_parser_factory.all_parsers_name.return_value = ["BAREKET", "SHUFERSAL"]

        # Test lowercase names
        os.environ["ENABLED_PARSERS"] = "bareket,shufersal"

        with self.assertRaises(ValueError) as context:
            load_params()

        # Should fail because case doesn't match
        error_msg = str(context.exception)
        self.assertIn("ENABLED_PARSERS contains invalid", error_msg)
        self.assertIn("bareket", error_msg)
        self.assertIn("shufersal", error_msg)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_case_sensitivity_parsers_mixed_case(
        self, _mock_file_types, mock_parser_factory
    ):
        """Test load_params with mixed case parser names"""
        mock_parser_factory.all_parsers_name.return_value = ["BAREKET", "SHUFERSAL"]

        # Test mixed case names
        os.environ["ENABLED_PARSERS"] = "Bareket,Shufersal"

        with self.assertRaises(ValueError) as context:
            load_params()

        # Should fail because case doesn't match
        error_msg = str(context.exception)
        self.assertIn("ENABLED_PARSERS contains invalid", error_msg)
        self.assertIn("Bareket", error_msg)
        self.assertIn("Shufersal", error_msg)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_case_sensitivity_file_types_lowercase(
        self, mock_file_types, _mock_parser_factory
    ):
        """Test load_params with lowercase file type names"""
        mock_file_types.all_types.return_value = ["PRICE_FILE", "PROMO_FILE"]

        # Test lowercase names
        os.environ["ENABLED_FILE_TYPES"] = "price_file,promo_file"

        with self.assertRaises(ValueError) as context:
            load_params()

        # Should fail because case doesn't match
        error_msg = str(context.exception)
        self.assertIn("ENABLED_FILE_TYPES contains invalid", error_msg)
        self.assertIn("price_file", error_msg)
        self.assertIn("promo_file", error_msg)

    @patch("main.ParserFactory")
    @patch("main.FileTypesFilters")
    def test_case_sensitivity_file_types_mixed_case(
        self, mock_file_types, _mock_parser_factory
    ):
        """Test load_params with mixed case file type names"""
        mock_file_types.all_types.return_value = ["PRICE_FILE", "PROMO_FILE"]

        # Test mixed case names
        os.environ["ENABLED_FILE_TYPES"] = "Price_File,Promo_File"

        with self.assertRaises(ValueError) as context:
            load_params()

        # Should fail because case doesn't match
        error_msg = str(context.exception)
        self.assertIn("ENABLED_FILE_TYPES contains invalid", error_msg)
        self.assertIn("Price_File", error_msg)
        self.assertIn("Promo_File", error_msg)


if __name__ == "__main__":
    unittest.main()
