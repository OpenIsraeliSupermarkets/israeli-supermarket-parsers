from typing import List

from .queue_output_writer import QueueOutputWriter
from .kafka_output_writer import KafkaOutputWriter
from .csv_output_writer import CSVOutputWriter
from .base_output_writer import BaseOutputWriter
from .multi_output_writer import MultiOutputWriter


def get_output_writer(
    parser_name: str,
    file_type: str,
    output_configuration: dict,
) -> BaseOutputWriter:
    """Return a writer (or fan-out MultiOutputWriter) for the given configuration.

    Keys in output_configuration:
        output_queues     dict mapping (parser_name, file_type) to queue objects
        kafka_config      dict with bootstrap_servers and optional topic_template
        output_folder     directory for CSV output (default: "outputs")
        always_write_csv  also write CSV even when another writer is active (default: False)

    CSV is added when no other writer is active, or when always_write_csv=True.
    """
    output_queues = output_configuration.get("output_queues")
    kafka_config = output_configuration.get("kafka_config")
    output_folder = output_configuration.get("output_folder", "outputs")
    always_write_csv = output_configuration.get("always_write_csv", False)

    queue_key = (parser_name, file_type)
    writers: List[BaseOutputWriter] = []

    if output_queues and queue_key in output_queues:
        writers.append(QueueOutputWriter(output_queues[queue_key]))

    if kafka_config:
        writers.append(
            KafkaOutputWriter(
                bootstrap_servers=kafka_config["bootstrap_servers"],
                enabled_scraper=parser_name,
                enabled_file_type=file_type,
                topic_template=kafka_config.get(
                    "topic_template", "{enabled_scraper}_{enabled_file_type}"
                ),
            )
        )

    if not writers or always_write_csv:
        writers.append(CSVOutputWriter(output_folder, parser_name, file_type))

    if len(writers) == 1:
        return writers[0]
    return MultiOutputWriter(writers)
