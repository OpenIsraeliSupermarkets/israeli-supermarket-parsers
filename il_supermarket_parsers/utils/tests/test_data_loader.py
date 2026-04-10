from il_supermarket_parsers.utils.data_loaders import DataLoader
import pytest

@pytest.mark.asyncio
async def test_load_null_data():
    """Test loading null data"""
    data = await DataLoader("il_supermarket_parsers/utils/tests").load()
    assert len(data) == 3
