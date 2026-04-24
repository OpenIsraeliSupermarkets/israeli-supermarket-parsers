from .base_data_loader import BaseDataLoader
from .data_loader import DataLoader
from .queue_data_loader import QueueDataLoader


def get_data_loader(queue_handlers: dict, folder: str) -> BaseDataLoader:
    """get the data loader based on the queue handlers"""
    if queue_handlers:
        return QueueDataLoader(queue_handlers)
    return DataLoader(folder=folder)
