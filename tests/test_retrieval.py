
import pytest

from unittest.mock import MagicMock

from sqlalchemy.exc import OperationalError

from rag.retrieval import (
    retrieve,
    rerank_results,
)

from rag.vector_index import (
    VectorIndex,
    VectorStoreUnavailableError,
)


TEST_CONFIG = {
    "mode": "local",
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "dimensions": 384,
    "batch_size": 10,
}


class FakeVector:
    def tolist(self):
        return [0.0] * 384


class FakeModel:
    def encode(self, *args, **kwargs):
        return [FakeVector()]


def test_empty_query():
    with pytest.raises(
        ValueError,
        match="Query cannot be empty"
    ):
        retrieve(
            query="   ",
            top_k=3
        )


def test_no_matches():
    fake_index = MagicMock()
    fake_index.search_similar.return_value = []

    result = retrieve(
        query="Unmatched question",
        top_k=3,
        index=fake_index,
        model=FakeModel(),
        config=TEST_CONFIG,
    )

    assert result["result_count"] == 0
    assert result["results"] == []


def test_unavailable_vector_store(monkeypatch):
    class BrokenSession:
        def execute(self, statement):
            raise OperationalError(
                "SELECT",
                {},
                Exception("Database unavailable")
            )

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(
        "rag.vector_index.SessionLocal",
        lambda: BrokenSession()
    )

    with VectorIndex(
        model_name=TEST_CONFIG["model"]
    ) as index:

        with pytest.raises(
            VectorStoreUnavailableError,
            match="unavailable"
        ):
            index.search_similar(
                query_vector=[0.0] * 384,
                limit=3,
            )


def test_reranking_preserves_original_score():
    matches = [
        {
            "chunk_id": "A",
            "chunk_text": "Unrelated content",
            "similarity": 0.9,
            "metadata": {},
        },
        {
            "chunk_id": "B",
            "chunk_text": "Immediate complaint escalation",
            "similarity": 0.8,
            "metadata": {},
        },
    ]

    results = rerank_results(
        "Immediate complaint escalation",
        matches
    )

    assert results[0]["chunk_id"] == "B"
    assert results[0]["original_score"] == 0.8
    assert results[0]["reranked_score"] == pytest.approx(
        0.84
    )


def test_invalid_filter():
    with pytest.raises(
        ValueError,
        match="Unsupported filters"
    ):
        retrieve(
            query="Complaint escalation",
            filters={"unknown_field": "value"},
        )
