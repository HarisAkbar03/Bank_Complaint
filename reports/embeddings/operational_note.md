# Embedding Operational Note

## Configuration

- Database: PostgreSQL
- Storage: SQLAlchemy ORM + pgvector
- Mode: local
- Model: sentence-transformers/all-MiniLM-L6-v2
- Batch size: 10
- Vector dimensions: 384

## Embedding Run

- Input chunks: 175
- Embedding batches: 18
- Inserted or updated: 175
- Skipped unchanged: 0
- Failed chunks: 0
- Total duration: 18.238 seconds

## Usage and Cost

- Local MiniLM model. No external embedding API calls or API token charges.
- External API token usage: not applicable
- External embedding API charges: none
- Local CPU/GPU and electricity costs: not measured
- Per-batch latency: embedding_run_log.json

## Validation

- Expected vectors: 175
- Stored vectors: 175
- Validation issues: 0
- Valid index: True

## Limitations

Real semantic embeddings. Retrieval quality requires separate evaluation.

## Pending

Coach-approved API integration, if required.
