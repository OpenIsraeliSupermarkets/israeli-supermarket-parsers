from .base_data_loader import BaseDataLoader
from .data_loader import DataLoader
from .queue_data_loader import QueueDataLoader
from ..types import SourceConfiguration, QueueSourceConfiguration


def get_data_loader(source_configuration: SourceConfiguration) -> BaseDataLoader:
    """get the data loader based on the source_configuration.

    Keys:
        queue_handlers  dict of queue handlers (streaming mode)
        folder          path to the data folder (file mode, default: "dumps")
    """
    if isinstance(source_configuration, QueueSourceConfiguration):
        return QueueDataLoader(source_configuration.queue_handlers)
    return DataLoader(folder=source_configuration.folder)
