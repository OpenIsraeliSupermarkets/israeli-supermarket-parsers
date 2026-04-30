from .base_data_loader import BaseDataLoader
from .data_loader import DataLoader
from .queue_data_loader import QueueDataLoader


def get_data_loader(source_configuration: dict) -> BaseDataLoader:
    """get the data loader based on the source_configuration.

    Keys:
        queue_handlers  dict of queue handlers (streaming mode)
        folder          path to the data folder (file mode, default: "dumps")
    """
    queue_handlers = source_configuration.get("queue_handlers")
    folder = source_configuration.get("folder", "dumps")
    if queue_handlers:
        return QueueDataLoader(queue_handlers)
    return DataLoader(folder=folder)
