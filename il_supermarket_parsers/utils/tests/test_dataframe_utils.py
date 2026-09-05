"""Tests for DataFrame/XML content matching helpers."""

import math

from il_supermarket_parsers.utils.dataframe_utils import extracted_value_matches


def test_null_xml_text_matches_csv_nan():
    """pandas.read_csv turns the literal XML text 'null' into NaN."""
    assert extracted_value_matches("null", float("nan"))
    assert extracted_value_matches("NULL", float("nan"))
    assert extracted_value_matches("null", None)


def test_empty_sentinels_still_match():
    """Parser and CSV empty markers stay equivalent to missing XML text."""
    assert extracted_value_matches("", "''")
    assert extracted_value_matches("", "NO_BODY")
    assert extracted_value_matches(None, float("nan"))
    assert extracted_value_matches("", math.nan)


def test_leaf_empty_dict_is_still_a_mismatch():
    """A leaf with real text must not match {} / '{}' (the original bug)."""
    assert not extracted_value_matches("shampoo\n", {})
    assert not extracted_value_matches("shampoo\n", "{}")
    assert not extracted_value_matches("null", {})
    assert not extracted_value_matches("null", "{}")


def test_numeric_string_matches_float():
    """CSV may drop a trailing zero on prices."""
    assert extracted_value_matches("17.90", "17.9")
    assert extracted_value_matches("17.90", 17.9)
