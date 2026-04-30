from typing import List

from .queue_output_writer import QueueOutputWriter
from .kafka_output_writer import KafkaOutputWriter
from .csv_output_writer import CSVOutputWriter
from .base_output_writer import BaseOutputWriter
from .multi_output_writer import MultiOutputWriter
from ..types import (
    OutputConfiguration,
    QueueOutputConfiguration,
    KafkaOutputConfiguration,
    CsvOutputConfiguration,
)


def get_output_writer(
    parser_name: str,
    file_type: str,
    configurations: List[OutputConfiguration],
) -> BaseOutputWriter:
    """Return a writer (or fan-out MultiOutputWriter) for the given configuration.

    Keys in configurations:
        output_queues     dict mapping (parser_name, file_type) to queue objects
        kafka_config      dict with bootstrap_servers and optional topic_template
        output_folder     directory for CSV output (default: "outputs")
        always_write_csv  also write CSV even when another writer is active (default: False)

    CSV is added when no other writer is active, or when always_write_csv=True.
    """
    writers: List[BaseOutputWriter] = []
    for cfg in configurations:
        if isinstance(cfg, QueueOutputConfiguration):
            writers.append(QueueOutputWriter(cfg.queues[(parser_name, file_type)]))
        elif isinstance(cfg, KafkaOutputConfiguration):
            writers.append(
                KafkaOutputWriter(
                    bootstrap_servers=cfg.kafka_config.bootstrap_servers,
                    topic_template=cfg.kafka_config.topic_template.format(
                        enabled_scraper=parser_name, enabled_file_type=file_type
                    ),
                )
            )
        elif isinstance(cfg, CsvOutputConfiguration):
            writers.append(
                CSVOutputWriter(
                    cfg.output_folder,
                    f"{file_type.lower()}_{parser_name.lower()}",
                )
            )
    if len(writers) > 1:
        return MultiOutputWriter(writers)
    return writers[0]
