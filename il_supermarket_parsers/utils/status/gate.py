from typing import Optional
from il_supermarket_scarper.utils.databases import JsonDataBase, MongoDataBase
from il_supermarket_scarper.utils.databases.base import AbstractDataBase
from .parser_status import ParserStatus


def create_parser_status(
    enabled_scraper: str,
    enabled_file_type: str,
    status_configuration: Optional[dict] = None,
    default_base_path: str = "outputs",
) -> ParserStatus:
    """Factory: build a ParserStatus backed by the configured database.

    Keys (same convention as ScarpingTask.status_configuration):
        database_type  "json" (default) | "mongo"
        base_path      directory for the JSON file  (json only)
        db_name        MongoDB database name         (mongo only, default: database_name)

    The JsonDataBase creates one file per database_name:
        {base_path}/{database_name}.json
    """
    database_name = f"{enabled_scraper}_{enabled_file_type}".lower()
    config = status_configuration or {
        "database_type": "json",
        "base_path": default_base_path,
    }
    db_type = config.get("database_type", "json")

    if db_type == "json":
        base_path = config.get("base_path", default_base_path)
        db = JsonDataBase(database_name, base_path=base_path)
        return ParserStatus(database_name, status_database=db)

    if db_type == "mongo":
        connection_url = status_configuration.get("connection_url", "localhost")
        collection_name = status_configuration.get("collection_name", "scraper_status")
        db = MongoDataBase(
            database_name,
            connection_url=connection_url,
            collection_name=collection_name,
        )
        db.create_connection()
        return ParserStatus(database_name, status_database=db)

    raise ValueError(f"Unknown database_type: {db_type!r}. Must be 'json' or 'mongo'.")
