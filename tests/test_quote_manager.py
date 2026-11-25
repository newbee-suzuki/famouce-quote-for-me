import tempfile
import unittest
from pathlib import Path

from quote_manager import QuoteStore


class QuoteStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary_directory.name) / "quotes.jsonl"
        self.store = QuoteStore(self.path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_add_load_search_and_delete(self) -> None:
        first = self.store.add(
            "Stay hungry, stay foolish.", "Steve Jobs", ["life", "Motivation"]
        )
        second = self.store.add("Knowledge is power.", "Francis Bacon", ["wisdom"])

        self.assertEqual(first["type"], "quote")
        self.assertEqual(len(self.store.load()), 2)
        self.assertEqual(self.store.search("hungry"), [first])
        self.assertEqual(self.store.search(author="jobs"), [first])
        self.assertEqual(self.store.search(tag="motivation"), [first])
        self.assertEqual(self.store.search(record_id=second["id"]), [second])

        self.assertTrue(self.store.delete(first["id"]))
        self.assertFalse(self.store.delete(first["id"]))
        self.assertEqual(self.store.load(), [second])

    def test_tags_are_trimmed_deduplicated_and_split(self) -> None:
        record = self.store.add("Test quote", "Test Author", ["life, wisdom", "LIFE"])
        self.assertEqual(record["tag"], ["life", "wisdom"])


if __name__ == "__main__":
    unittest.main()
