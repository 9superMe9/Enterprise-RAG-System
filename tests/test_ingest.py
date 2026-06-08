"""
Enterprise-RAG-System 单元测试
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingest import (
    split_documents,
    _get_existing_sources,
    _filter_new_chunks,
    _generate_chunk_ids,
)
from langchain_core.documents import Document
from unittest.mock import MagicMock


class TestIngest(unittest.TestCase):

    def test_split_documents(self):
        docs = [
            Document(
                page_content="这是一个测试文档。" * 150,
                metadata={"source": "test.txt"}
            )
        ]
        chunks = split_documents(docs)
        self.assertGreater(len(chunks), 1, "长文档应被分割为多个块")
        for chunk in chunks:
            self.assertIn("test.txt", chunk.metadata["source"])

    def test_split_short_document(self):
        docs = [
            Document(
                page_content="短文本",
                metadata={"source": "short.txt"}
            )
        ]
        chunks = split_documents(docs)
        self.assertEqual(len(chunks), 1)

    def test_get_existing_sources(self):
        mock_db = MagicMock()
        mock_db.get.return_value = {
            "metadatas": [
                {"source": "doc1.pdf"},
                {"source": "doc2.txt"},
                {"source": "doc1.pdf"},
            ]
        }
        sources = _get_existing_sources(mock_db)
        self.assertEqual(sources, {"doc1.pdf", "doc2.txt"})

    def test_get_existing_sources_empty(self):
        mock_db = MagicMock()
        mock_db.get.return_value = {}
        sources = _get_existing_sources(mock_db)
        self.assertEqual(sources, set())

    def test_filter_new_chunks_all_new(self):
        chunks = [
            Document(page_content="A", metadata={"source": "a.pdf"}),
            Document(page_content="B", metadata={"source": "b.pdf"}),
        ]
        existing = set()
        new, skipped = _filter_new_chunks(chunks, existing)
        self.assertEqual(len(new), 2)
        self.assertEqual(skipped, 0)

    def test_filter_new_chunks_partial(self):
        chunks = [
            Document(page_content="A", metadata={"source": "a.pdf"}),
            Document(page_content="B", metadata={"source": "b.pdf"}),
        ]
        existing = {"a.pdf"}
        new, skipped = _filter_new_chunks(chunks, existing)
        self.assertEqual(len(new), 1)
        self.assertEqual(new[0].metadata["source"], "b.pdf")
        self.assertEqual(skipped, 1)

    def test_generate_chunk_ids(self):
        chunks = [
            Document(page_content="X", metadata={"source": "x.pdf", "page": 1}),
            Document(page_content="Y", metadata={"source": "y.pdf", "page": 2}),
        ]
        ids = _generate_chunk_ids(chunks)
        self.assertEqual(len(ids), 2)
        self.assertNotEqual(ids[0], ids[1])
        self.assertIn("x.pdf", ids[0])
        self.assertIn("y.pdf", ids[1])


class TestConfig(unittest.TestCase):

    def test_settings_have_required_fields(self):
        from app.config import settings
        self.assertTrue(hasattr(settings, "DEEPSEEK_API_KEY"))
        self.assertTrue(hasattr(settings, "DEEPSEEK_BASE_URL"))
        self.assertTrue(hasattr(settings, "DEEPSEEK_MODEL_NAME"))
        self.assertTrue(hasattr(settings, "VECTOR_DB_PATH"))
        self.assertTrue(hasattr(settings, "BASE_DIR"))


if __name__ == "__main__":
    unittest.main()
