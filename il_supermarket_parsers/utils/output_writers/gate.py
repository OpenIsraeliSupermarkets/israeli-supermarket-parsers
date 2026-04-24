from .queue_output_writer import QueueOutputWriter
from .kafka_output_writer import KafkaOutputWriter
from .csv_output_writer import CSVOutputWriter
from .base_output_writer import BaseOutputWriter


def get_output_writer(
    parser_name: str,
    file_type: str,
    output_queues: dict,
    kafka_config: dict,
    output_folder: str,
) -> BaseOutputWriter:
    """get the output writer based on the queue handlers"""
    queue_key = (parser_name, file_type)
    if output_queues and queue_key in output_queues:
        return QueueOutputWriter(output_queues[queue_key])
    elif kafka_config:
        return KafkaOutputWriter(
            bootstrap_servers=kafka_config["bootstrap_servers"],
            key_columns=kafka_config.get("key_columns"),
            enabled_scraper=parser_name,
            enabled_file_type=file_type,
            topic_template=kafka_config.get(
                "topic_template", "{enabled_scraper}_{enabled_file_type}"
            ),
        )
    else:
        return CSVOutputWriter(output_folder, parser_name, file_type)
