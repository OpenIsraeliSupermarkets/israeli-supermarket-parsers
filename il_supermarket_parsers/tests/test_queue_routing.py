"""Test queue routing to verify files are not lost when multiple file types read one queue.

This test validates the fix for the issue where queue sources lose files when
several file types read one scraper queue. The fix routes messages by file type
so each (chain, file_type) job reads only its own files.
"""

import asyncio
import gzip
import unittest
from typing import Dict, List

from il_supermarket_parsers.utils.data_loaders.queue_router import (
    QueueRouter,
    RoutedQueueWrapper,
)


def make_minimal_xml(file_type: str, chain_id: str = "7290700100008") -> bytes:
    """Create minimal valid XML for a given file type."""
    if file_type in ("PRICE_FILE", "PRICE_FULL_FILE"):
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <ChainId>{chain_id}</ChainId>
    <SubChainId>1</SubChainId>
    <StoreId>001</StoreId>
    <Items>
        <Item>
            <ItemCode>1</ItemCode>
            <ItemName>Test Item</ItemName>
            <ItemPrice>10.00</ItemPrice>
        </Item>
    </Items>
</root>"""
    elif file_type in ("PROMO_FILE", "PROMO_FULL_FILE"):
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <ChainId>{chain_id}</ChainId>
    <SubChainId>1</SubChainId>
    <StoreId>001</StoreId>
    <Promotions>
        <Promotion>
            <PromotionId>1</PromotionId>
            <PromotionDescription>Test Promo</PromotionDescription>
        </Promotion>
    </Promotions>
</root>"""
    elif file_type == "STORE_FILE":
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <ChainId>{chain_id}</ChainId>
    <Stores>
        <Store>
            <StoreId>001</StoreId>
            <StoreName>Test Store</StoreName>
            <Address>Test Address</Address>
            <City>Test City</City>
        </Store>
    </Stores>
</root>"""
    else:
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <ChainId>{chain_id}</ChainId>
</root>"""
    return gzip.compress(xml.encode("utf-8"))


def make_queue_message(file_type: str, chain_id: str, index: int) -> dict:
    """Create a queue message for a file of the given type."""
    prefix_map = {
        "PRICE_FILE": "Price",
        "PRICE_FULL_FILE": "PriceFull",
        "PROMO_FILE": "Promo",
        "PROMO_FULL_FILE": "PromoFull",
        "STORE_FILE": "Stores",
    }
    prefix = prefix_map.get(file_type, "Unknown")
    file_name = f"{prefix}{chain_id}-001-20250101{index:04d}.xml.gz"
    return {
        "file_name": file_name,
        "file_content": make_minimal_xml(file_type, chain_id),
        "file_link": f"http://example.com/{file_name}",
        "metadata": {},
    }


class MockAsyncQueueHandler:
    """Mock async queue handler that yields messages from a list."""

    def __init__(self, messages: List[dict]):
        self._messages = list(messages)
        self._closed = False

    async def get_all_messages(self):
        """Yield messages until exhausted."""
        for msg in self._messages:
            yield msg

    async def send(self, msg: dict) -> None:
        """Track put-back attempts - should not happen with routing."""
        raise AssertionError(f"send() should not be called with routing: {msg}")

    async def close(self) -> None:
        """Mark as closed."""
        self._closed = True


class MockQueueWrapper:
    """Wraps MockAsyncQueueHandler to match scraper queue handler interface."""

    def __init__(self, handler: MockAsyncQueueHandler):
        self.queue_handler = handler


class TestQueueRouter(unittest.TestCase):
    """Test the QueueRouter class."""

    def test_routes_messages_by_file_type(self):
        """Test that messages are routed to correct file type queues."""
        chain_id = "7290700100008"
        messages = [
            make_queue_message("PRICE_FILE", chain_id, 1),
            make_queue_message("PROMO_FILE", chain_id, 2),
            make_queue_message("PRICE_FILE", chain_id, 3),
            make_queue_message("STORE_FILE", chain_id, 4),
            make_queue_message("PROMO_FILE", chain_id, 5),
        ]

        mock_handler = MockQueueWrapper(MockAsyncQueueHandler(messages))
        enabled_types = ["PRICE_FILE", "PROMO_FILE", "STORE_FILE"]

        router = QueueRouter("TEST_CHAIN", mock_handler, enabled_types)

        price_handler = router.get_routed_handler("PRICE_FILE")
        promo_handler = router.get_routed_handler("PROMO_FILE")
        store_handler = router.get_routed_handler("STORE_FILE")

        router.start()

        received_price = []
        received_promo = []
        received_store = []

        async def collect_messages():
            async for msg in price_handler.queue_handler.get_all_messages():
                received_price.append(msg["file_name"])
            async for msg in promo_handler.queue_handler.get_all_messages():
                received_promo.append(msg["file_name"])
            async for msg in store_handler.queue_handler.get_all_messages():
                received_store.append(msg["file_name"])

        asyncio.run(collect_messages())

        self.assertEqual(len(received_price), 2)
        self.assertEqual(len(received_promo), 2)
        self.assertEqual(len(received_store), 1)

        for name in received_price:
            self.assertTrue(name.startswith("Price"))
        for name in received_promo:
            self.assertTrue(name.startswith("Promo"))
        for name in received_store:
            self.assertTrue(name.startswith("Stores"))

    def test_end_sentinel_reaches_all_queues(self):
        """Test that end-of-stream sentinel is sent to all routed queues."""
        messages = [make_queue_message("PRICE_FILE", "7290700100008", 1)]
        mock_handler = MockQueueWrapper(MockAsyncQueueHandler(messages))
        enabled_types = ["PRICE_FILE", "PROMO_FILE", "STORE_FILE"]

        router = QueueRouter("TEST_CHAIN", mock_handler, enabled_types)

        handlers = {
            ft: router.get_routed_handler(ft) for ft in enabled_types
        }

        router.start()

        finished_queues = []

        async def check_sentinel(file_type: str, handler: RoutedQueueWrapper):
            count = 0
            async for _ in handler.queue_handler.get_all_messages():
                count += 1
            finished_queues.append(file_type)
            return count

        async def check_all():
            results = await asyncio.gather(
                *[check_sentinel(ft, h) for ft, h in handlers.items()]
            )
            return dict(zip(enabled_types, results))

        counts = asyncio.run(check_all())
        self.assertEqual(counts["PRICE_FILE"], 1)
        self.assertEqual(counts["PROMO_FILE"], 0)
        self.assertEqual(counts["STORE_FILE"], 0)
        self.assertEqual(set(finished_queues), set(enabled_types))

    def test_interleaved_consumption_with_delays(self):
        """Test that files are not lost when consumers start at different times."""
        chain_id = "7290700100008"
        messages = []
        for i in range(10):
            file_type = ["PRICE_FILE", "PROMO_FILE", "STORE_FILE"][i % 3]
            messages.append(make_queue_message(file_type, chain_id, i))

        mock_handler = MockQueueWrapper(MockAsyncQueueHandler(messages))
        enabled_types = ["PRICE_FILE", "PROMO_FILE", "STORE_FILE"]

        router = QueueRouter("TEST_CHAIN", mock_handler, enabled_types)
        handlers = {ft: router.get_routed_handler(ft) for ft in enabled_types}

        router.start()

        received: Dict[str, List[str]] = {ft: [] for ft in enabled_types}

        async def consume_with_delay(
            file_type: str, handler: RoutedQueueWrapper, delay: float
        ):
            await asyncio.sleep(delay)
            async for msg in handler.queue_handler.get_all_messages():
                received[file_type].append(msg["file_name"])

        async def run_consumers():
            await asyncio.gather(
                consume_with_delay("PRICE_FILE", handlers["PRICE_FILE"], 0.0),
                consume_with_delay("PROMO_FILE", handlers["PROMO_FILE"], 0.05),
                consume_with_delay("STORE_FILE", handlers["STORE_FILE"], 0.1),
            )

        asyncio.run(run_consumers())

        total = sum(len(v) for v in received.values())
        self.assertEqual(total, 10, f"Expected 10 files, got {total}: {received}")

        self.assertEqual(len(received["PRICE_FILE"]), 4)
        self.assertEqual(len(received["PROMO_FILE"]), 3)
        self.assertEqual(len(received["STORE_FILE"]), 3)


class TestQueueRoutingIntegration(unittest.TestCase):
    """Integration test for queue routing with ParallelParser."""

    def test_parallel_parser_creates_routed_configs(self):
        """Test that ParallelParser creates routed source configs for queue sources.

        This verifies that each (parser, file_type) job gets a source config
        with only its routed queue, not the original shared queue.
        """
        # pylint: disable=import-outside-toplevel
        from il_supermarket_parsers.multiprocess_pharser import (
            ParallelParser,
            ParallelParserParams,
        )
        from il_supermarket_parsers.utils.types import QueueSourceConfiguration

        enabled_scrapers = ["SHUFERSAL", "VICTORY"]
        enabled_types = ["PRICE_FILE", "PROMO_FILE", "STORE_FILE"]

        queue_handlers = {
            scraper: MockQueueWrapper(MockAsyncQueueHandler([]))
            for scraper in enabled_scrapers
        }

        params = ParallelParserParams(
            enabled_parsers=enabled_scrapers,
            enabled_file_types=enabled_types,
            source_configuration=QueueSourceConfiguration(
                queue_handlers=queue_handlers
            ),
            output_configuration=[],
            status_configuration={"database_type": "json", "base_path": "temp"},
        )

        parser = ParallelParser(params, multiprocessing=1)
        args_list = parser.get_arguments_list(limit=1)

        self.assertEqual(
            len(args_list),
            len(enabled_scrapers) * len(enabled_types),
        )

        for args in args_list:
            source_config = args["source_configuration"]
            self.assertIsInstance(source_config, QueueSourceConfiguration)

            parser_name = args["store_enum"]
            self.assertIn(parser_name, source_config.queue_handlers)
            self.assertEqual(len(source_config.queue_handlers), 1)

    def test_routing_preserves_all_messages(self):
        """Test that routing preserves all messages without loss.

        This is the key regression test - verifying that all messages
        arrive at the correct routed queue.
        """
        enabled_types = ["PRICE_FILE", "PROMO_FILE", "STORE_FILE"]
        chain_id = "7290027600007"

        messages = []
        for i in range(30):
            file_type = enabled_types[i % len(enabled_types)]
            messages.append(make_queue_message(file_type, chain_id, i))

        mock_handler = MockQueueWrapper(MockAsyncQueueHandler(messages))

        router = QueueRouter("TEST_CHAIN", mock_handler, enabled_types)
        handlers = {ft: router.get_routed_handler(ft) for ft in enabled_types}
        router.start()

        received: Dict[str, List[str]] = {ft: [] for ft in enabled_types}

        async def consume_all():
            tasks = []
            for file_type in enabled_types:
                async def consume(ft=file_type):
                    async for msg in handlers[ft].queue_handler.get_all_messages():
                        received[ft].append(msg["file_name"])
                tasks.append(consume())
            await asyncio.gather(*tasks)

        asyncio.run(consume_all())

        total = sum(len(v) for v in received.values())
        self.assertEqual(
            total, 30, f"Expected 30 files, got {total}. Distribution: {received}"
        )

        self.assertEqual(len(received["PRICE_FILE"]), 10)
        self.assertEqual(len(received["PROMO_FILE"]), 10)
        self.assertEqual(len(received["STORE_FILE"]), 10)


class TestNoRegressionFolderSource(unittest.TestCase):
    """Verify folder sources still work unchanged."""

    def test_folder_source_not_affected(self):
        """Test that folder sources are unaffected by queue routing changes."""
        # pylint: disable=import-outside-toplevel
        from il_supermarket_parsers.multiprocess_pharser import (
            ParallelParser,
            ParallelParserParams,
        )
        from il_supermarket_parsers.utils.types import FolderSourceConfiguration

        params = ParallelParserParams(
            enabled_parsers=["SHUFERSAL", "VICTORY"],
            enabled_file_types=["PRICE_FILE", "PROMO_FILE"],
            source_configuration=FolderSourceConfiguration(folder="test_dumps"),
            output_configuration=[],
            status_configuration={"database_type": "json", "base_path": "temp"},
        )

        parser = ParallelParser(params, multiprocessing=2)
        args_list = parser.get_arguments_list(limit=1)

        self.assertEqual(len(args_list), 4)

        for args in args_list:
            self.assertIsInstance(
                args["source_configuration"], FolderSourceConfiguration
            )
            self.assertEqual(args["source_configuration"].folder, "test_dumps")


if __name__ == "__main__":
    unittest.main()
