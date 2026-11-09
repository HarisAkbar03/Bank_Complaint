# Semantic Retriever — Input/Output Contract

## Purpose

Retrieve relevant approved document chunks from PostgreSQL using MiniLM embeddings and pgvector cosine similarity.

The retriever is intended for later use by RAG services and AI agents.

## Python Interface

```python
retrieve(
    query: str,
    top_k: int = 3,
    filters: dict | None = None,
    rerank: bool = False,
    candidate_k: int | None = None
) -> dict
```

## Inputs

| Parameter | Type | Description |
|---|---|---|
| query | string | Nonempty natural-language question |
| top_k | integer | Maximum number of returned chunks |
| filters | dictionary | Exact-match metadata filters |
| rerank | boolean | Enable deterministic lexical reranking |
| candidate_k | integer or null | Number of initial vector candidates before reranking |

Supported filters:

- `document_type`
- `version`
- `access_label`

The `version` field supports exact matching. Effective-date selection is not implemented because effective date fields are not present in the current metadata model.

## Output

```json
{
  "query": "What cases need immediate escalation?",
  "top_k": 3,
  "filters": {
    "access_label": "Restricted"
  },
  "reranking_enabled": true,
  "candidate_k": 10,
  "result_count": 1,
  "results": [
    {
      "rank": 1,
      "chunk_id": "EXAMPLE-CHUNK-001",
      "text": "Example retrieved document passage.",
      "original_score": 0.82,
      "reranked_score": 0.86,
      "metadata": {
        "source_id": "KB-002",
        "version": "1",
        "access_label": "Restricted",
        "approval_status": "Approved",
        "checksum": "example-checksum",
        "section_name": "Escalation",
        "sequence_number": 1
      }
    }
  ]
}
```

*This JSON is illustrative, not an actual retrieval result.*

## Retrieval Behavior

1. Validate query, top_k, and metadata filters.
2. Generate a normalized 384-dimensional MiniLM embedding.
3. Search PostgreSQL using pgvector cosine distance.
4. Apply metadata filters before vector ranking.
5. Optionally rerank candidate passages using lexical overlap.
6. Return ranked text, original scores, optional reranked scores, and approved metadata.

## Failure Behavior

| Condition | Behavior |
|---|---|
| Empty query | Raise `ValueError` |
| Invalid top_k | Raise `ValueError` |
| Unsupported metadata filter | Raise `ValueError` |
| No matching documents | Return empty `results` and `result_count: 0` |
| Vector database unavailable during search | Raise `VectorStoreUnavailableError` |
| Embedding model mismatch | Raise `RuntimeError` |

## Security and Limitations

Metadata filtering is not a substitute for authenticated authorization. The calling service must enforce the user's permitted access labels.

Cosine similarity and deterministic reranking scores are relevance signals, not calibrated probabilities.

The retriever returns evidence passages; it does not generate answers or verify that a passage fully answers the question.

The current implementation is a Python service interface, not an HTTP endpoint. It can be wrapped in FastAPI for later agent integration.
