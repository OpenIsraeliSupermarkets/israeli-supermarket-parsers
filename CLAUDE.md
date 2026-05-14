# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**Run all tests:**
```bash
python -m pytest .
```

**Run a single test file:**
```bash
python -m pytest il_supermarket_parsers/tests/test_parser_factory.py
```

**Lint:**
```bash
pylint $(git ls-files '*.py') --disable=E0401,R0801,R0903,W0707,R0917,R0913
```

**Format:**
```bash
black .
```

**Docker (matches CI):**
```bash
docker build -t erlichsefi/israeli-supermarket-parsers:test --target test .
docker run --rm -v ./temp:/usr/src/app/temp erlichsefi/israeli-supermarket-parsers:test
```

## Architecture

The package parses XML price/promo/store data published by Israeli supermarket chains (per government transparency regulations) and streams rows to pluggable output sinks (CSV, Kafka, MongoDB, or in-memory queue).

### Processing Pipeline

`ConvertingTask` → `ParallelParser` (multiprocessing, one process per store × file-type combination) → `RawParsingPipeline` (async streaming) → `BaseFileConverter.read()` (async generator) → `XmlBaseConverter.convert()` (yields `dict` rows) → `BaseOutputWriter`.

`ParallelParser` builds the cartesian product of (store names × file types) and dispatches each combination as an independent `RawProcessing` job. Status is tracked per-file via `ParserStatus` and persisted to JSON or MongoDB.

### Layer Breakdown

**`il_supermarket_parsers/`** — public API
- `task.py` — `ConvertingTask` + `ConvertingTaskConfig` (Pydantic): main entry point. Runs `ParallelParser` in a background thread. Accepts multiple output configurations simultaneously (fan-out). Supports both folder-based and queue-based sources.
- `parser_factory.py` — `ParserFactory` enum mapping store names (e.g. `SHUFERSAL`) to converter classes.
- `raw_parsing_pipeline.py` — `RawParsingPipeline`: async streaming pipeline. For each `DumpFile` yielded by the data loader it calls `parser.read(file)` (an async generator of `dict` rows) and forwards each row to `output_writer.write_row()`. Tracks per-file status (registered, skipped, processed, failed).
- `multiprocess_pharser.py` — `ParallelParser` + `RawProcessing`: builds the job list and runs them in a `MultiProcessor` pool.

**`engines/`** — wires file-type → document converter
- `BaseFileConverter` — dispatches to the correct `XmlBaseConverter` based on `DumpFile.detected_filetype` (PRICE, PRICE_FULL, PROMO, PROMO_FULL, STORE). `read()` is an `async` generator yielding `dict` rows. Supports both file-system and queue-based (`DumpFile.is_queue_based`) files.
- `BigIDFileConverter` — variant for stores using `ChainID`/`StoreID` (uppercase) and `Products`/`Sales` list keys.
- `BigIdBranchesFileConverter` — additionally uses the `Branches` list key instead of `Stores`.
- Most per-chain parsers in `parsers/` subclass one of these and only override the parsers that differ from the engine defaults.

**`documents/`** — XML → row-dict converters (async generators, no pandas in hot path)
- `XmlBaseConverter` — abstract base; `convert()` returns `AsyncIterator[dict]`.
- `BaseXMLParser` — concrete base implementing `convert()` via `get_root_and_search` / `get_root_and_search_from_content`; subclasses implement `_parse()`.
- `XmlDataFrameConverter` — iterates a repeated XML element (e.g. `<Items>/<Item>`) and yields flat `dict` rows. Params: `list_key`, `id_field`, `roots` (header fields promoted as columns), `ignore_column`, `date_columns`.
- `SubRootedXmlDataFrameConverter` — handles two-level nesting (e.g. `<SubChains>/<Stores>`) via `SubRootedXmlOptions`.
- `ConditionalXmlDataFrameConverter` — variant with conditional parsing logic.
- `validate_succussful_extraction()` is called separately (not during streaming) and is not supported for queue-based files.

**`utils/`**
- `types.py` — Pydantic config models:
  - *Source*: `FolderSourceConfiguration` (local directory) | `QueueSourceConfiguration` (in-memory queue from scraper).
  - *Output*: `CsvOutputConfiguration` | `KafkaOutputConfiguration` | `MongoOutputConfiguration` | `QueueOutputConfiguration`. `output_configuration` in `ConvertingTaskConfig` is a **list** — pass multiple to fan-out.
  - *Status*: `JsonStatusConfiguration` | `MongoStatusConfiguration`.
  - Messages: `FileCompleteMessage`, `FileExecutionLog`, `ExecutionLog`.
- `loading_utils.py` — `DumpFile` (Pydantic model): describes one scraped file. Key properties: `is_queue_based` (True when `file_content` is set), `is_expected_to_be_readable`, `get_full_path`.
- `data_loaders/` — `BaseDataLoader` hierarchy; `get_data_loader(source_config)` factory. Loaders are async generators yielding `DumpFile` objects.
- `output_writers/` — `BaseOutputWriter` hierarchy; `get_output_writer(parser_name, file_type, output_configs)` factory. Writers: `CsvOutputWriter`, `KafkaOutputWriter`, `MongoOutputWriter`, `QueueOutputWriter`, `MultiOutputWriter` (fan-out).
- `status/` — `ParserStatus`, status event classes (`StartedParsingStatus`, `RegisteredFileToProcessStatus`, `ProcessedFileStatus`, `SkippedFileStatus`, `FailedFileStatus`, `CompletedParsingStatus`).
- `xml_utils.py`, `dataframe_utils.py`, `csv_reader.py`, `test_utils.py`.

**`validators/`** — post-parse validation for price, promo, store, and promo-code data.

### Adding a New Supermarket Parser

1. Create a file in `parsers/` subclassing the appropriate engine (`BaseFileConverter`, `BigIDFileConverter`, or `BigIdBranchesFileConverter`).
2. Override only the document parsers (`price_parser`, `pricefull_parser`, etc.) that differ from the engine defaults.
3. Export the class from `parsers/__init__.py`.
4. Add an entry to `ParserFactory` in `parser_factory.py` — the name **must** match the corresponding entry in `il_supermarket_scarper.ScraperFactory` (validated by `test_enum_are_aligned`).

### Key External Dependency

`il_supermarket_scarper` (note: different spelling from this package) provides `FileTypesFilters` (the file-type enum) and `ScraperFactory` (used in alignment tests). The `ParserFactory` enum must stay in sync with `ScraperFactory`.
