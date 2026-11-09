
import json
import sqlite3

from rag.embeddings import (
    mock_embed,
    read_chunks,
    run,
)


def sample_chunk():
    return {
        "chunk_id": "KB-001-V1-S0001-baseline-0001",
        "chunk_text": "Example approved banking policy",
        "source_id": "KB-001",
        "version": "1",
        "access_label": "internal",
        "approval_status": "approved",
        "checksum": "abc123",
        "section_name": "Overview",
        "sequence_number": 1,
    }


def test_mock_embedding_dimensions():
    vector = mock_embed("Banking complaint")

    assert len(vector) == 64


def test_mock_embedding_deterministic():
    first = mock_embed("Supervisor approval")
    second = mock_embed("Supervisor approval")

    assert first == second


def test_different_text_produces_different_vectors():
    first = mock_embed("Supervisor approval")
    second = mock_embed("Fraud escalation")

    assert first != second


def test_read_chunks(tmp_path):
    path = tmp_path / "chunks.jsonl"

    path.write_text(
        json.dumps(sample_chunk()) + "\n",
        encoding="utf-8"
    )

    chunks = read_chunks(path)

    assert len(chunks) == 1
    assert chunks[0]["source_id"] == "KB-001"


def test_embedding_pipeline(tmp_path):
    source = tmp_path / "chunks.jsonl"

    source.write_text(
        json.dumps(sample_chunk()) + "\n",
        encoding="utf-8"
    )

    output = tmp_path / "embeddings"

    log, validation = run(
        input_path=source,
        output_dir=output,
        batch_size=1
    )

    assert log["inserted_or_updated"] == 1
    assert validation["vector_count"] == 1
    assert validation["valid"] is True

    assert (
        output / "vector_index.sqlite"
    ).exists()

    assert (
        output / "index_validation.json"
    ).exists()


def test_no_duplicate_embeddings(tmp_path):
    source = tmp_path / "chunks.jsonl"

    source.write_text(
        json.dumps(sample_chunk()) + "\n",
        encoding="utf-8"
    )

    output = tmp_path / "embeddings"

    run(
        input_path=source,
        output_dir=output,
        batch_size=1
    )

    log, validation = run(
        input_path=source,
        output_dir=output,
        batch_size=1
    )

    assert log["inserted_or_updated"] == 0
    assert log["skipped_unchanged"] == 1
    assert validation["vector_count"] == 1


def test_full_rebuild(tmp_path):
    source = tmp_path / "chunks.jsonl"

    source.write_text(
        json.dumps(sample_chunk()) + "\n",
        encoding="utf-8"
    )

    output = tmp_path / "embeddings"

    run(
        input_path=source,
        output_dir=output,
        batch_size=1
    )

    log, validation = run(
        input_path=source,
        output_dir=output,
        batch_size=1,
        rebuild=True
    )

    assert log["inserted_or_updated"] == 1
    assert validation["valid"] is True

    with sqlite3.connect(
        output / "vector_index.sqlite"
    ) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM embeddings"
        ).fetchone()[0]

    assert count == 1
