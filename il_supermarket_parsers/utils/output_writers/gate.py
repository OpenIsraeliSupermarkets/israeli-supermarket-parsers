from typing import List

from .queue_output_writer import QueueOutputWriter
from .kafka_output_writer import KafkaOutputWriter
from .csv_output_writer import CSVOutputWriter
from .base_output_writer import BaseOutputWriter
from .multi_output_writer import MultiOutputWriter


def get_output_writer(  # pylint: disable=too-many-positional-arguments
    parser_name: str,
    file_type: str,
    output_queues: dict,
    kafka_config: dict,
    output_folder: str,
    always_write_csv: bool = False,
) -> BaseOutputWriter:
    """Return a writer (or fan-out MultiOutputWriter) for the given configuration.

    CSV is added when no other writer is active, or when always_write_csv=True.
    """
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
