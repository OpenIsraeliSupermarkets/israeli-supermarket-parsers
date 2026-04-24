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

The package parses XML price/promo/store data published by Israeli supermarket chains (per government transparency regulations) and converts it to CSV files.

### Processing Pipeline

`ConvertingTask` → `ParallelParser` (multiprocessing) → `RawParsingPipeline` (per store × file-type combination) → `BaseFileConverter.read()` → document parser → pandas DataFrame → CSV output.

`ParallelParser` creates a cartesian product of (store names × file types) and runs each combination as an independent job in a process pool. Results are aggregated into `outputs/parser-status.json`.

### Layer Breakdown

**`il_supermarket_parsers/`** — public API  
- `task.py` — `ConvertingTask`: main entry point, wraps `ParallelParser`  
- `parser_factory.py` — `ParserFactory` enum mapping store names (e.g. `SHUFERSAL`) to converter classes  
- `raw_parsing_pipeline.py` — `RawParsingPipeline`: locates files, calls the parser, appends rows to a per-(store, file-type) CSV

**`engines/`** — base converter hierarchy  
- `BaseFileConverter` — dispatches to the correct document parser based on `FileTypesFilters` (PRICE, PRICE_FULL, PROMO, PROMO_FULL, STORE)  
- `BigIDFileConverter` — variant for stores using `ChainID`/`StoreID` (uppercase) instead of `ChainId`/`StoreId`  
- `BigIdBranchesFileConverter` — additionally uses `Branches` list key instead of `Stores`  
- Most store-specific parsers in `parsers/` subclass one of these engine classes and only override the parsers that differ from the defaults

**`documents/`** — XML → DataFrame conversion  
- `XmlDataFrameConverter` — iterates a repeated XML element (e.g. `<Items>/<Item>`) and builds a flat DataFrame  
- `SubRootedXmlDataFrameConverter` — handles two-level nesting (e.g. `<SubChains>/<Stores>`)  
- `ConditionalXmlDataFrameParser` — variant with conditional parsing logic  
- Parsers receive `list_key` (repeated element name), `id_field`, `roots` (header fields to promote as columns), and `ignore_column`

**`validators/`** — post-parse validation for price, promo, store, and promo-code data

**`utils/`** — XML utilities (`xml_utils.py`), DataFrame helpers (`dataframe_utils.py`), file discovery (`data_loader.py`, `loading_utils.py`), and test fixtures (`test_utils.py`)

### Adding a New Supermarket Parser

1. Create a file in `parsers/` subclassing the appropriate engine (`BaseFileConverter`, `BigIDFileConverter`, or `BigIdBranchesFileConverter`)
2. Override only the document parsers (`price_parser`, `pricefull_parser`, etc.) that differ from the engine defaults
3. Export the class from `parsers/__init__.py`
4. Add an entry to `ParserFactory` in `parser_factory.py` — the name **must** match the corresponding entry in `il_supermarket_scarper.ScraperFactory` (validated by `test_enum_are_aligned`)

### Key External Dependency

`il_supermarket_scarper` (note: different spelling from this package) provides `FileTypesFilters` (the file-type enum) and `ScraperFactory` (used in alignment tests). The `ParserFactory` enum must stay in sync with `ScraperFactory`.
