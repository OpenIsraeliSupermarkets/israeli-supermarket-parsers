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
    output_configuration: List[OutputConfiguration],
) -> BaseOutputWriter:
    """Return a writer (or fan-out MultiOutputWriter) for the given configuration.

    Keys in output_configuration:
        output_queues     dict mapping (parser_name, file_type) to queue objects
        kafka_config      dict with bootstrap_servers and optional topic_template
        output_folder     directory for CSV output (default: "outputs")
        always_write_csv  also write CSV even when another writer is active (default: False)

    CSV is added when no other writer is active, or when always_write_csv=True.
    """
    writers: List[BaseOutputWriter] = []
    for output_configuration in output_configuration:
        if isinstance(output_configuration, QueueOutputConfiguration):
            writers.append(
                QueueOutputWriter(output_configuration.queues[(parser_name, file_type)])
            )
        elif isinstance(output_configuration, KafkaOutputConfiguration):
            writers.append(
                KafkaOutputWriter(
                    bootstrap_servers=output_configuration.kafka_config.bootstrap_servers,
                    topic_template=output_configuration.kafka_config.topic_template.format(
                        enabled_scraper=parser_name, enabled_file_type=file_type
                    ),
                )
            )
        elif isinstance(output_configuration, CsvOutputConfiguration):
            writers.append(
                CSVOutputWriter(
                    output_configuration.output_folder,
                    parser_name.lower() + "_" + parser_name.lower(),
                )
            )
    if len(writers) > 1:
        return MultiOutputWriter(writers)
    return writers[0]
