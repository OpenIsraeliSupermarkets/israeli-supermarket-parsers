from il_supermarket_scarper.utils.databases import JsonDataBase, MongoDataBase
from .parser_status import ParserStatus
from ..types import (
    StatusConfiguration,
    JsonStatusConfiguration,
)


def create_parser_status(
    enabled_scraper: str,
    enabled_file_type: str,
    status_configuration: StatusConfiguration,
) -> ParserStatus:
    """Factory: build a ParserStatus backed by the configured database.

    Keys (same convention as ScarpingTask.status_configuration):
        database_type    "json" (default) | "mongo"
        base_path        directory for the JSON file  (json only)
        default_base_path fallback base_path when base_path is not set (default: "outputs")
        db_name          MongoDB database name         (mongo only, default: database_name)

    The JsonDataBase creates one file per database_name:
        {base_path}/{database_name}.json
    """
    database_name = f"{enabled_scraper}_{enabled_file_type}".lower()
    if isinstance(status_configuration, JsonStatusConfiguration):
        return ParserStatus(
            status_database=JsonDataBase(
                database_name, base_path=status_configuration.base_path
            ),
        )
    db = MongoDataBase(
        status_configuration.db_name,
        connection_url=status_configuration.connection_url,
        collection_name=status_configuration.collection_name,
    )
    db.create_connection()
    return ParserStatus(status_database=db)
