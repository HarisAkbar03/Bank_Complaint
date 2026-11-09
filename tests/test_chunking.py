
from rag.chunking import (
    fixed_chunk,
    structure_aware_chunk,
    validate_chunks,
)


def sample_record(text):
    return {
        "chunk_id": "KB-001-V3.0-CHUNK-0001",
        "source_id": "KB-001",
        "version": "3.0",
        "access_label": "Internal",
        "approval_status": "Approved",
        "checksum": "abc123",
        "section_name": "Complaint Escalation",
        "sequence_number": 1,
        "chunk_text": text,
    }


def test_baseline_preserves_metadata():
    record = sample_record("word " * 100)

    chunks = fixed_chunk(record, chunk_size=30, overlap=5)

    assert len(chunks) > 1
    assert all(c["source_id"] == "KB-001" for c in chunks)
    assert all(c["version"] == "3.0" for c in chunks)
    assert all(c["access_label"] == "Internal" for c in chunks)


def test_structure_aware_preserves_heading():
    record = sample_record(
        "Complaints must be investigated.\n"
        "Exception: urgent cases require escalation."
    )

    chunks = structure_aware_chunk(
        record, chunk_size=50, overlap=5
    )

    assert len(chunks) == 1
    assert "Complaint Escalation" in chunks[0]["chunk_text"]
    assert "Exception:" in chunks[0]["chunk_text"]


def test_empty_text_creates_no_chunks():
    record = sample_record("")

    assert fixed_chunk(record) == []
    assert structure_aware_chunk(record) == []


def test_unique_chunk_ids():
    record = sample_record("word " * 100)

    chunks = fixed_chunk(record, chunk_size=30, overlap=5)

    ids = [chunk["chunk_id"] for chunk in chunks]

    assert len(ids) == len(set(ids))


def test_validation():
    record = sample_record("Policy text for testing.")

    chunks = structure_aware_chunk(record)

    result = validate_chunks(
        chunks, [record], max_words=500
    )

    assert result["issue_count"] == 0


def test_chunk_size_limit():
    record = sample_record("word " * 1000)

    chunks = structure_aware_chunk(
        record, chunk_size=100, overlap=10
    )

    assert all(c["word_count"] <= 100 for c in chunks)
