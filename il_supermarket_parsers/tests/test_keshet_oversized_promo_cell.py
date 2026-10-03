"""Regression test for oversized promo cells in the CSV output.

Keshet's PromoFull parser keeps each ``<Promotion>`` as one row, so the nested
``<PromotionItems>`` list is serialised into a single JSON cell. A promotion
covering a few thousand items pushes that cell past the 128 KiB field limit of
the stdlib ``csv`` module. Re-reading such a file to append a column (what
happens when a later file in the same job carries a new tag) aborted the whole
store x file-type job with ``_csv.Error``.

The live Keshet test in ``parsers/tests/test_all.py`` skips whenever the chain's
endpoint is unreachable, so this covers the same path without any network.
"""

import csv
import json
import os
import tempfile
import unittest

from il_supermarket_parsers.parser_factory import ParserFactory
from il_supermarket_parsers.utils.loading_utils import file_name_to_components
from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)
from il_supermarket_parsers.utils.csv_reader import read_data_rows

KESHET_PROMOFULL = "PromoFull7290785400000-001-021-20261003-001151"

# csv's own default, hardcoded so the test stays deterministic no matter what
# raised the process-wide limit before it.
_CSV_DEFAULT_FIELD_LIMIT = 131072

# Enough items for the serialised cell to clear the limit with room to spare.
_ITEMS_IN_LARGE_PROMOTION = 4000


def _promofull_xml(item_count, extra_tags=""):
    items = "".join(
        f"<Item><ItemCode>7290{index:09d}</ItemCode><ItemType>1</ItemType></Item>"
        for index in range(item_count)
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290785400000</ChainId>
  <SubChainId>001</SubChainId>
  <StoreId>021</StoreId>
  <BikoretNo>0</BikoretNo>
  <Promotions>
    <Promotion>
      <PromotionId>9001</PromotionId>
      <PromotionUpdateDate>2026-10-03 00:00</PromotionUpdateDate>{extra_tags}
      <PromotionItems>{items}</PromotionItems>
    </Promotion>
  </Promotions>
</Root>
"""


class KeshetOversizedPromoCellTestCase(unittest.IsolatedAsyncioTestCase):
    """A promo cell above csv's field limit must not abort the parsing job."""

    def setUp(self) -> None:
        # pylint: disable=consider-using-with
        self._dumps = tempfile.TemporaryDirectory()
        self._outputs = tempfile.TemporaryDirectory()
        self.dump_folder = self._dumps.name
        self.output_folder = self._outputs.name
        previous_limit = csv.field_size_limit(_CSV_DEFAULT_FIELD_LIMIT)
        self.addCleanup(csv.field_size_limit, previous_limit)

    def tearDown(self) -> None:
        self._dumps.cleanup()
        self._outputs.cleanup()

    async def _parse_into_csv(self, file_name, xml):
        """Run one dump file through the Keshet parser into the shared CSV."""
        path = os.path.join(self.dump_folder, file_name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(xml)

        dump_file = file_name_to_components(self.dump_folder, file_name)
        parser = ParserFactory.get("KESHET")()
        writer = CSVOutputWriter(self.output_folder, "promo_full_file_keshet")
        await writer.initialize()
        rows = [row async for row in parser.read(dump_file)]
        for row in rows:
            await writer.write_row(row)
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        return rows, writer.output_path

    async def test_large_promotion_then_new_column_keeps_the_job_alive(self):
        """A second file adding a tag must still widen a CSV holding a big cell."""
        rows, _ = await self._parse_into_csv(
            f"{KESHET_PROMOFULL}.xml",
            _promofull_xml(_ITEMS_IN_LARGE_PROMOTION),
        )
        serialized = json.dumps(rows[0]["promotionitems"], ensure_ascii=False)
        self.assertGreater(len(serialized), _CSV_DEFAULT_FIELD_LIMIT)

        # A later file in the same job carries a tag the first one lacked, so the
        # writer has to re-read the CSV that already holds the oversized cell.
        _, output_path = await self._parse_into_csv(
            f"{KESHET_PROMOFULL[:-1]}2.xml",
            _promofull_xml(1, extra_tags="\n      <ClubId>7</ClubId>"),
        )

        written = read_data_rows(output_path, ffill=True)
        self.assertEqual(len(written), 2)
        self.assertEqual([row["promotionid"] for row in written], ["9001", "9001"])
        self.assertEqual(
            len(json.loads(written[0]["promotionitems"])["item"]),
            _ITEMS_IN_LARGE_PROMOTION,
        )
        self.assertEqual(written[0]["clubid"], CSVOutputWriter.EMPTY_STRING)
        self.assertEqual(written[1]["clubid"], "7")


if __name__ == "__main__":
    unittest.main()
