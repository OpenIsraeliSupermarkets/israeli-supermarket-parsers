---
name: fix-supermarket-parser
description: Diagnose and fix failing Israeli supermarket XML parser tests in this repo by running the test, inspecting the real XML, and adjusting only the converter configuration in the chain's parser class. Use when a test under il_supermarket_parsers/parsers/tests/test_all.py fails with errors like "columns chainid missing", "id ItemCode missing", "element count mismatch", or "list_key element was not found".
---

# Fix Supermarket Parser

Fix a failing parser test by changing **only the converter configuration** in the chain's parser class (e.g., `il_supermarket_parsers/parsers/*.py`). Do not touch the shared engines, document converters, or validation code — they are correct; the per-chain configuration is what drifts when a chain changes its XML shape.


NOTE: 
- you are not allowd to ignore columns that contains data! the goal is to capture a much data which is not the xml metadata!
- In a case like this either change fix the validation or change the parsers, you can't ignore 


## Workflow

Track progress with this checklist:

```
- [ ] 1. Run the failing test and capture the error + file path
- [ ] 2. Open the failing XML and identify list_key, id_field, roots
- [ ] 3. Pick the correct converter from il_supermarket_parsers/documents
- [ ] 4. Keep the OLD shape working too (see "Backward compatibility" below)
- [ ] 5. Update the chain's parser class (parsers/<chain>.py) only
- [ ] 6. Add an offline regression test covering BOTH shapes
- [ ] 7. Re-run that test, then the full chain test class
```

### Step 1: Run the failing test

```bash
python -m pytest il_supermarket_parsers/parsers/tests/test_all.py::<ChainTestCase>::<test_name> -v
```

From the failure, note:

- The file written under `/tmp/.../<ChainFolder>/<FileName>.xml` and the matching download URL from the `Processing https://...` log lines.
- Which `FileTypesFilters` the failing test uses:
  - `test_parsing_store` → `stores_parser`
  - `test_parsing_prices` → `price_parser`
  - `test_parsing_prices_all` → `pricefull_parser`
  - `test_parsing_promo` → `promo_parser` (note: base stores it as `promo_parsers` — do NOT rely on that name; always pass via `super().__init__(promo_parser=...)`)
  - `test_parsing_promo_all` → `promofull_parser`

### Step 2: Inspect the real XML

The tests download live data. Fetch the same `.gz` directly and print the head:

```python
import urllib.request, gzip
url = "<Processing URL from test logs>"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as r:
    data = gzip.decompress(r.read())
print(data[:6000].decode("utf-8", errors="replace"))
```

From the XML, extract the three things the converter needs:

- **`list_key`** — the parent element whose children are the rows (e.g., `Items`, `Products`, `Promotions`, `Sales`, `Branches`, `SubChains`, `Details`, `STORES`).
- **`id_field`** — the per-row unique identifier tag (e.g., `ItemCode`, `PromotionID`, `PromotionId`, `StoreID`, `StoreId`). Case matters because validation uses the exact name for counting. When a file contains several candidate tags, choose the one whose count equals the number of children under `list_key`.
- **`roots`** — the header fields at the top of the document (typically `ChainID` / `ChainId`, `SubChainID` / `SubChainId`, `StoreID` / `StoreId`, `BikoretNo`). Match the casing used in the XML.
- Any `date_columns` referenced in the current code must actually exist in the XML (e.g., `PriceUpdateDate`, `PromotionUpdateTime`, `PromotionUpdateDate`).

Quick way to confirm row/id counts:

```python
from il_supermarket_parsers.utils.xml_utils import collect_validation_data_from_xml
for idf in ["ItemCode", "PromotionID", "PromotionId", "StoreID"]:
    d = collect_validation_data_from_xml("/tmp/<file>.xml", idf, ignore_tags=[])
    print(idf, d["tag_count"])
```

### Step 3: Pick a converter from `il_supermarket_parsers/documents`

All converters live in `il_supermarket_parsers/documents/` and are re-exported from that package. Pick one by XML shape:

| XML shape | Converter | Import |
|-----------|-----------|--------|
| Flat list: `<Root>...<list_key><row>...</row>...</list_key></Root>` | `XmlDataFrameConverter` | `from il_supermarket_parsers.documents import XmlDataFrameConverter` |
| Nested list with sub-headers (e.g., `SubChains → SubChain → Stores → Store`) | `SubRootedXmlDataFrameConverter` with `SubRootedXmlOptions` | `from il_supermarket_parsers.documents import SubRootedXmlDataFrameConverter, SubRootedXmlOptions` |
| XML where two different shapes are possible and must be chosen at runtime | `ConditionalXmlDataFrameConverter(option_a, option_b, root_value=... or check_key=...)` | `from il_supermarket_parsers.documents import ConditionalXmlDataFrameConverter` |

Rule of thumb: if a single `list_key` directly contains the rows you want, use `XmlDataFrameConverter`. If you must descend through intermediate wrappers (store files are the common case), use `SubRootedXmlDataFrameConverter`. Only reach for `ConditionalXmlDataFrameConverter` when the same file type ships in two shapes across branches.

`SubRootedXmlDataFrameConverter` signature:

```python
SubRootedXmlDataFrameConverter(
    list_key="SubChains",
    id_field="StoreId",
    options=SubRootedXmlOptions(
        roots=["ChainId", "ChainName", "LastUpdateDate"],
        sub_roots=["SubChainId", "SubChainName"],
        list_sub_key="Stores",
        ignore_column=["XmlDocVersion", "DllVerNo"],
    ),
)
```

### Step 4: Backward compatibility (required)

A chain changing its XML shape does **not** mean the old shape is gone. Historical dumps, slow-migrating branches, and re-published archives keep the previous wrapper around for a long time. Never swap one hardcoded `list_key` for another — that just trades a new bug for an old one, and it fails silently (zero rows, no error).

Wrap both shapes in `ConditionalXmlDataFrameConverter`, with `check_key` set to the **new** wrapper so the legacy converter stays as the fallback:

```python
def _price_converter(list_key):
    return XmlDataFrameConverter(
        list_key=list_key,
        id_field="ItemCode",
        roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
    )


price_parser = ConditionalXmlDataFrameConverter(
    option_a=_price_converter("Items"),    # current shape
    option_b=_price_converter("Details"),  # legacy shape, still parsed
    check_key="Items",
)
```

`check_key` is resolved per file at runtime: when the element exists `option_a` runs, otherwise `option_b`. That makes the change non-regressive — files parsing correctly today keep taking the exact same path.

Apply this to **every** parser on the chain that could drift (`price`, `pricefull`, `promo`, `promofull`, `stores`), not only the one whose test failed. Adding the conditional to a parser that has not drifted yet costs nothing: when the new wrapper is absent, the legacy converter runs exactly as before.

Precedents to copy: `parsers/shufersal.py` (stores: nested `SubChains` vs flat `STORES`) and `parsers/tiv_taam.py` (prices: `Items` vs `NewDataSet`). When a chain has three shapes, nest them — `option_b` accepts another `ConditionalXmlDataFrameConverter`.

### Step 5: Change the chain's parser class only

Edit only the file under `il_supermarket_parsers/parsers/<chain>.py`. Pass every parser you override into `super().__init__(...)` so the engine's `_get_parser` picks the updated instance (do NOT set attributes after `super().__init__()` — the base class stores promo under `self.promo_parsers`, and future subclasses may reassign in `__init__`, so constructor injection is the safe path).

```python
from il_supermarket_parsers.engines import BigIdBranchesFileConverter  # or BigIDFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class SomeChainFileConverter(BigIdBranchesFileConverter):
    """some chain"""

    def __init__(self):
        super().__init__(
            price_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            ),
            pricefull_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            ),
            promo_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PromotionUpdateTime"],
            ),
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PromotionUpdateTime"],
            ),
        )
```

Choose the base:

- `BigIDFileConverter` — chains using `ChainID` / `StoreID` casing.
- `BigIdBranchesFileConverter` — same, but store files are laid out as `Branches → Branch` (not `Stores → Store`).
- `BaseFileConverter` — everything else (default casing `ChainId` / `StoreId`). Only use directly when no specialization fits.

### Step 6: Add an offline regression test

The live-source tests in `parsers/tests/test_all.py` **skip** when a chain's endpoint is unreachable or bot-protected, so they cannot be relied on to guard a parser. Add a network-free test under `il_supermarket_parsers/tests/` that feeds synthetic XML of **both** shapes through the real converter and asserts non-zero rows plus the expected ids.

Copy the pattern from `il_supermarket_parsers/tests/test_super_pharm_layouts.py`.

### Step 7: Re-run tests

```bash
python -m pytest il_supermarket_parsers/parsers/tests/test_all.py::<ChainTestCase>::<test_name> -v
python -m pytest il_supermarket_parsers/parsers/tests/test_all.py::<ChainTestCase> -v
python -m pytest il_supermarket_parsers/tests/ -v
```

A live-source test reporting SKIPPED means the source was unreachable — it did **not** validate your fix. The offline test from Step 6 is what proves the parser works.

Then run `ReadLints` on the edited `parsers/<chain>.py`.

## Mapping error messages to fixes

| Error | Likely cause | Fix |
|-------|--------------|-----|
| `columns chainid missing from RangeIndex(start=0, stop=0, step=1)` (empty DataFrame, non-zero `tag_count`) | `list_key` not present in XML, so `_get_root` returns `None` and no rows are parsed | Add the wrapper the rows actually live under via `ConditionalXmlDataFrameConverter`, keeping the previous `list_key` as `option_b` (Step 4) |
| `id <x> missing from <columns>` (DataFrame has rows) | Wrong `id_field` for this XML | Use the tag whose count equals `len(children of list_key)` |
| `columns chainid missing` but DataFrame has rows | `roots` casing mismatch with the XML | Match case exactly (`ChainID` vs `ChainId`) |
| `element count mismatch for '<tag>': XML has N, DataFrame has M` | Parser produced too few/many rows — usually nested repeats not flattened | Use `SubRootedXmlDataFrameConverter` or add the offending wrapper tag to `ignore_column` if it's metadata |
| `missing data, data shape (N, ...) tag count is K` with N != K | `id_field` tag appears in multiple nesting levels | Pick an `id_field` that only exists at row level, or use `SubRootedXmlDataFrameConverter` to descend past the wrapper |
| `for file ..., expected empty data, got N rows` | File was supposed to be empty but parser picked up rows from a sibling wrapper | Tighten `list_key` to the exact row parent |

## Out of scope

Do not modify — these are shared and correct:

- `il_supermarket_parsers/documents/*` (converter implementations)
- `il_supermarket_parsers/engines/*` (base wiring)
- `il_supermarket_parsers/utils/xml_utils.py` (XML parsing/validation helpers)
- `il_supermarket_parsers/parsers/tests/test_case.py` (shared test harness)

If the fix seems to require changes there, re-check the XML — the correct answer is almost always a different `list_key` / `id_field` / `roots` / converter choice in the chain's `parsers/<chain>.py`.


## Report

When you fix a supermarket parser, provide a quick report summarizing the structural mapping.

**Structure in XML:**
```
<xml section>
<example or path of XML elements (e.g., Root/Items/Item, or Root/Branches/Branch)>
```

**How it appeared in the CSV before the fix:**
```
<Columns and sample rows as found in failed output, e.g., missing columns, bad casing, wrong row count>
```

**Corrected structure (after the fix):**
```
<Columns and structure as they now appear in CSV>
```

Describe any changes in the mapping (e.g., list_key from 'Branches' to 'Stores', id_field casing, addition of roots, converter class changed).
This helps future maintainers quickly see what was wrong and how it was addressed.

Also state explicitly which shapes remain supported after the fix, e.g.:

```
price/pricefull: <Items> (current) | <Details> (legacy fallback)
stores:          <SubChains>/<Stores> (current) | flat <Stores> (legacy fallback)
```

If you dropped support for a shape, say so and justify why it can no longer appear.