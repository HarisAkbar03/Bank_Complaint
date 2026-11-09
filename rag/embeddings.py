
"""
Exercise 4.2.3 - Embeddings and Vector Indexing

Responsibilities:
- Generic document text extraction
- Read approved selected chunks
- Generate local MiniLM or mock embeddings
- Process chunks in batches
- Retry transient failures
- Write validation and operational reports

Vector storage is handled by rag/vector_index.py.

For PostgreSQL pgvector(384), use local MiniLM mode.
"""

import argparse
import hashlib
import json
import math
import os
import time

from pathlib import Path

from dotenv import load_dotenv

from rag.vector_index import (
    VectorIndex,
    REQUIRED_METADATA,
)


INPUT_PATH = Path(
    "reports/chunking/chunks_selected.jsonl"
)

OUTPUT_DIR = Path("reports/embeddings")

LOCAL_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

LOCAL_DIMENSIONS = 384
MOCK_DIMENSIONS = 64

MODEL_CACHE = {}


# --------------------------------------------------
# 1. GENERIC DOCUMENT EXTRACTION
# --------------------------------------------------

def extract_document(file_path):
    """
    Extract text from PDF, DOCX, TXT or Markdown.

    This utility does not replace the approved
    ingestion and chunking pipeline.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Document not found: {path}"
        )

    extension = path.suffix.lower()

    if extension == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    elif extension == ".docx":
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph

        document = Document(str(path))
        parts = []

        for block in document.iter_inner_content():
            if isinstance(block, Paragraph):
                value = block.text.strip()
                if value:
                    parts.append(value)

            elif isinstance(block, Table):
                for row in block.rows:
                    cells = [
                        cell.text.strip()
                        for cell in row.cells
                    ]
                    parts.append(" | ".join(cells))

        text = "\n".join(parts)

    elif extension in (".txt", ".md"):
        text = path.read_text(
            encoding="utf-8"
        )

    else:
        raise ValueError(
            f"Unsupported format: {extension}"
        )

    if not text.strip():
        raise ValueError(
            f"No extractable text: {path}"
        )

    return text


# --------------------------------------------------
# 2. CONFIGURATION
# --------------------------------------------------

def load_config():
    load_dotenv()

    mode = os.getenv(
        "EMBEDDING_MODE", "local"
    ).strip().lower()

    model = os.getenv(
        "EMBEDDING_MODEL", ""
    ).strip()

    batch_size = int(
        os.getenv("EMBEDDING_BATCH_SIZE", "10")
    )

    if batch_size <= 0:
        raise ValueError(
            "Batch size must be positive"
        )

    if mode == "local":
        model = model or LOCAL_MODEL

        if model not in (
            LOCAL_MODEL,
            "all-MiniLM-L6-v2",
        ):
            raise ValueError(
                "Only all-MiniLM-L6-v2 is "
                "supported in local mode"
            )

        dimensions = LOCAL_DIMENSIONS

    elif mode == "mock":
        model = "mock-sha256-64-v1"
        dimensions = MOCK_DIMENSIONS

    elif mode == "api":
        raise NotImplementedError(
            "Coach-approved embedding API "
            "integration is pending"
        )

    else:
        raise ValueError(
            "EMBEDDING_MODE must be local, mock or api"
        )

    return {
        "mode": mode,
        "model": model,
        "batch_size": batch_size,
        "dimensions": dimensions,
    }


# --------------------------------------------------
# 3. READ APPROVED CHUNKS
# --------------------------------------------------

def read_chunks(path):
    chunks = []
    seen = set()

    with Path(path).open(
        encoding="utf-8"
    ) as file:

        for line_number, line in enumerate(
            file, start=1
        ):
            if not line.strip():
                continue

            chunk = json.loads(line)
            chunk_id = chunk.get("chunk_id")

            if not chunk_id:
                raise ValueError(
                    f"Missing chunk_id on line {line_number}"
                )

            if chunk_id in seen:
                raise ValueError(
                    f"Duplicate chunk ID: {chunk_id}"
                )

            seen.add(chunk_id)

            if not chunk.get(
                "chunk_text", ""
            ).strip():
                raise ValueError(
                    f"Empty chunk text: {chunk_id}"
                )

            for field in REQUIRED_METADATA:
                value = chunk.get(field)

                if value is None or value == "":
                    raise ValueError(
                        f"Missing {field}: {chunk_id}"
                    )

            approval = str(
                chunk["approval_status"]
            ).strip().lower()

            if approval not in (
                "approved", "active"
            ):
                raise ValueError(
                    f"Unapproved chunk: {chunk_id}"
                )

            chunks.append(chunk)

    if not chunks:
        raise ValueError(
            "No selected chunks found"
        )

    return chunks


# --------------------------------------------------
# 4. MOCK EMBEDDINGS
# --------------------------------------------------

def mock_embed(
    text,
    dimensions=MOCK_DIMENSIONS
):
    """
    Deterministic test vector.
    Does not represent semantic meaning.
    """
    values = []

    for index in range(dimensions):
        digest = hashlib.sha256(
            f"{index}:{text}".encode("utf-8")
        ).digest()

        number = int.from_bytes(
            digest[:8], "big"
        )

        value = (
            number / (2**64 - 1)
        ) * 2 - 1

        values.append(value)

    magnitude = math.sqrt(
        sum(value * value for value in values)
    )

    if magnitude == 0:
        raise ValueError(
            "Cannot normalize zero vector"
        )

    return [
        value / magnitude
        for value in values
    ]


# --------------------------------------------------
# 5. LOCAL EMBEDDING MODEL
# --------------------------------------------------

def get_local_model(model_name):
    if model_name not in MODEL_CACHE:
        from sentence_transformers import (
            SentenceTransformer
        )

        MODEL_CACHE[model_name] = (
            SentenceTransformer(model_name)
        )

    return MODEL_CACHE[model_name]


def embed_batch(texts, config):
    """
    Generate embeddings for a batch.

    Returns:
        vectors, usage
    """
    if config["mode"] == "mock":
        vectors = [
            mock_embed(
                text, config["dimensions"]
            )
            for text in texts
        ]
        return vectors, None

    if config["mode"] == "local":
        model = get_local_model(
            config["model"]
        )

        embeddings = model.encode(
            texts,
            batch_size=config["batch_size"],
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist(), None

    raise RuntimeError(
        "Unsupported embedding mode"
    )


# --------------------------------------------------
# 6. RETRY HANDLING
# --------------------------------------------------

def generate_with_retry(
    texts,
    config,
    max_retries=3
):
    for attempt in range(max_retries + 1):
        try:
            return embed_batch(
                texts, config
            )

        except (
            ConnectionError,
            TimeoutError,
            OSError
        ):
            if attempt == max_retries:
                raise

            time.sleep(
                min(2 ** attempt, 8)
            )


# --------------------------------------------------
# 7. OPERATIONAL REPORTS
# --------------------------------------------------

def write_reports(
    output_dir,
    run_log,
    validation
):
    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    (
        output_dir / "embedding_run_log.json"
    ).write_text(
        json.dumps(run_log, indent=2),
        encoding="utf-8"
    )

    (
        output_dir / "index_validation.json"
    ).write_text(
        json.dumps(validation, indent=2),
        encoding="utf-8"
    )

    if run_log["mode"] == "local":
        usage_note = (
            "Local MiniLM model. "
            "No external embedding API calls "
            "or API token charges."
        )
        limitation = (
            "Real semantic embeddings. "
            "Retrieval quality requires "
            "separate evaluation."
        )
    else:
        usage_note = (
            "Mock mode. No external API calls "
            "or API token charges."
        )
        limitation = (
            "Mock vectors do not represent "
            "semantic meaning."
        )

    note = f"""# Embedding Operational Note

## Configuration

- Database: PostgreSQL
- Storage: SQLAlchemy ORM + pgvector
- Mode: {run_log['mode']}
- Model: {run_log['model']}
- Batch size: {run_log['batch_size']}
- Vector dimensions: {validation['dimensions']}

## Embedding Run

- Input chunks: {run_log['input_chunks']}
- Embedding batches: {run_log['embedding_batches']}
- Inserted or updated: {run_log['inserted_or_updated']}
- Skipped unchanged: {run_log['skipped_unchanged']}
- Failed chunks: {run_log['failed']}
- Total duration: {run_log['duration_seconds']} seconds

## Usage and Cost

- {usage_note}
- External API token usage: not applicable
- External embedding API charges: none
- Local CPU/GPU and electricity costs: not measured
- Per-batch latency: embedding_run_log.json

## Validation

- Expected vectors: {validation['expected_count']}
- Stored vectors: {validation['vector_count']}
- Validation issues: {validation['issue_count']}
- Valid index: {validation['valid']}

## Limitations

{limitation}

## Pending

Coach-approved API integration, if required.
"""

    (
        output_dir / "operational_note.md"
    ).write_text(
        note,
        encoding="utf-8"
    )


# --------------------------------------------------
# 8. MAIN EMBEDDING PIPELINE
# --------------------------------------------------

def run(
    input_path=INPUT_PATH,
    output_dir=OUTPUT_DIR,
    batch_size=None,
    rebuild=False,
    max_retries=3,
    config=None
):
    if config is None:
        config = load_config()

    if batch_size is None:
        batch_size = config["batch_size"]

    if batch_size <= 0:
        raise ValueError(
            "Batch size must be positive"
        )

    if max_retries < 0:
        raise ValueError(
            "Maximum retries cannot be negative"
        )

    # The ORM model uses Vector(384).
    if config["mode"] != "local":
        raise ValueError(
            "The PostgreSQL vector(384) index "
            "requires local MiniLM mode. "
            "Set EMBEDDING_MODE=local."
        )

    chunks = read_chunks(input_path)

    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    started = time.perf_counter()

    inserted = 0
    skipped = 0
    failed = 0
    embedding_batches = 0
    failures = []
    batch_metrics = []

    VectorIndex.initialize_database()

    with VectorIndex(
        model_name=config["model"],
        dimensions=config["dimensions"]
    ) as index:

        if rebuild:
            index.rebuild()
        else:
            index.check_model()

        for offset in range(
            0, len(chunks), batch_size
        ):
            batch = chunks[
                offset:offset + batch_size
            ]

            pending = []

            for chunk in batch:
                if index.is_unchanged(chunk):
                    skipped += 1
                else:
                    pending.append(chunk)

            if not pending:
                continue

            texts = [
                chunk["chunk_text"]
                for chunk in pending
            ]

            embedding_batches += 1
            batch_started = time.perf_counter()

            try:
                vectors, usage = generate_with_retry(
                    texts,
                    config,
                    max_retries
                )

                if len(vectors) != len(pending):
                    raise ValueError(
                        "Embedding count does not "
                        "match batch size"
                    )

                for vector in vectors:
                    if len(vector) != config["dimensions"]:
                        raise ValueError(
                            "Unexpected vector dimensions"
                        )

                    if not all(
                        isinstance(value, (int, float))
                        and math.isfinite(value)
                        for value in vector
                    ):
                        raise ValueError(
                            "Invalid embedding values"
                        )

                index.save_batch(
                    pending,
                    vectors
                )

                inserted += len(pending)

                batch_metrics.append({
                    "batch_number": embedding_batches,
                    "chunk_count": len(pending),
                    "duration_seconds": round(
                        time.perf_counter()
                        - batch_started, 3
                    ),
                    "status": "success",
                    "api_usage": usage,
                })

            except (
                ConnectionError,
                TimeoutError,
                OSError
            ) as error:
                failed += len(pending)

                failures.append({
                    "batch_offset": offset,
                    "error": type(error).__name__,
                })

                batch_metrics.append({
                    "batch_number": embedding_batches,
                    "chunk_count": len(pending),
                    "duration_seconds": round(
                        time.perf_counter()
                        - batch_started, 3
                    ),
                    "status": "failed",
                })

        validation = index.validate(chunks)

    duration = round(
        time.perf_counter() - started, 3
    )

    run_log = {
        "mode": config["mode"],
        "model": config["model"],
        "input_chunks": len(chunks),
        "batch_size": batch_size,
        "embedding_batches": embedding_batches,
        "inserted_or_updated": inserted,
        "skipped_unchanged": skipped,
        "failed": failed,
        "duration_seconds": duration,
        "token_usage": None,
        "batch_metrics": batch_metrics,
        "failures": failures,
    }

    write_reports(
        output_dir,
        run_log,
        validation
    )

    return run_log, validation


# --------------------------------------------------
# 9. COMMAND-LINE INTERFACE
# --------------------------------------------------

def main():
    config = load_config()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        default=str(INPUT_PATH)
    )

    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR)
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=config["batch_size"]
    )

    parser.add_argument(
        "--rebuild",
        action="store_true"
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3
    )

    args = parser.parse_args()

    run_log, validation = run(
        input_path=args.input,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        rebuild=args.rebuild,
        max_retries=args.max_retries,
        config=config
    )

    print("\nEmbedding pipeline completed")
    print(f"Mode: {run_log['mode']}")
    print(f"Model: {run_log['model']}")
    print(f"Input chunks: {run_log['input_chunks']}")
    print(
        "Inserted/updated:",
        run_log["inserted_or_updated"]
    )
    print(
        "Skipped unchanged:",
        run_log["skipped_unchanged"]
    )
    print(
        "Stored vectors:",
        validation["vector_count"]
    )
    print(
        "Vector dimensions:",
        validation["dimensions"]
    )
    print(
        "Validation issues:",
        validation["issue_count"]
    )
    print(
        "Index valid:",
        validation["valid"]
    )

    if not validation["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
