from il_supermarket_parsers.utils.data_loader import DataLoader


def test_load_null_data():
    """Test loading null data"""
    data = DataLoader("il_supermarket_parsers/utils/tests").load()
    assert len(data) == 3
