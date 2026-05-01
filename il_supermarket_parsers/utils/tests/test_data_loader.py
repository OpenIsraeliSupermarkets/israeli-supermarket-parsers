import pytest

from il_supermarket_parsers.utils.data_loaders import DataLoader


@pytest.mark.asyncio
async def test_load_null_data():
    """Test loading null data"""
    data = [
        item async for item in DataLoader("il_supermarket_parsers/utils/tests").load()
    ]
    assert len(data) == 3
