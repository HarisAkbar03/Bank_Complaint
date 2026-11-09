
import hashlib
import math

from datetime import datetime, timezone

from sqlalchemy import (
    select,
    delete,
    func,
)
from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal, engine
from repositories.models import Embedding


REQUIRED_METADATA = (
    "source_id",
    "version",
    "access_label",
    "approval_status",
    "checksum",
    "section_name",
    "sequence_number",
)

APPROVED_METADATA = REQUIRED_METADATA + (
    "document_type",
    "parent_section_id",
    "strategy",
)

FILTER_FIELDS = {
    "document_type",
    "version",
    "access_label",
}


def text_hash(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def get_metadata(chunk):
    return {
        key: chunk[key]
        for key in APPROVED_METADATA
        if key in chunk
    }


def validate_vector(vector, dimensions):
    values = (
        vector.tolist()
        if hasattr(vector, "tolist")
        else list(vector)
    )

    if len(values) != dimensions:
        raise ValueError(
            f"Expected {dimensions} dimensions, "
            f"got {len(values)}"
        )

    if not all(
        isinstance(value, (int, float))
        and math.isfinite(value)
        for value in values
    ):
        raise ValueError("Invalid vector values")

    return [float(value) for value in values]


class VectorStoreUnavailableError(RuntimeError):
    pass


class VectorIndex:

    def __init__(self, model_name, dimensions=384):
        self.model_name = model_name
        self.dimensions = dimensions
        self.session = SessionLocal()

    @staticmethod
    def initialize_database():
        Embedding.__table__.create(
            bind=engine,
            checkfirst=True
        )

    def check_model(self):
        try:
            models = set(
                self.session.scalars(
                    select(Embedding.model).distinct()
                ).all()
            )

            dimensions = set(
                self.session.scalars(
                    select(Embedding.dimensions).distinct()
                ).all()
            )

        except SQLAlchemyError as error:
            self.session.rollback()
            raise VectorStoreUnavailableError(
                "Unable to access the vector store"
            ) from error

        if models and models != {self.model_name}:
            raise RuntimeError(
                "Embedding model mismatch. "
                "Rebuild the index."
            )

        if dimensions and dimensions != {
            self.dimensions
        }:
            raise RuntimeError(
                "Vector dimensions mismatch. "
                "Rebuild the index."
            )

    def rebuild(self):
        try:
            self.session.execute(
                delete(Embedding)
            )
            self.session.commit()

        except SQLAlchemyError:
            self.session.rollback()
            raise

    def is_unchanged(self, chunk):
        existing = self.session.get(
            Embedding,
            chunk["chunk_id"]
        )

        if existing is None:
            return False

        return (
            existing.text_hash
            == text_hash(chunk["chunk_text"])
            and existing.model == self.model_name
            and existing.dimensions == self.dimensions
            and existing.chunk_text
            == chunk["chunk_text"]
            and existing.metadata_json
            == get_metadata(chunk)
        )

    def save_batch(self, chunks, vectors):
        if len(chunks) != len(vectors):
            raise ValueError(
                "Chunk/vector count mismatch"
            )

        ids = [
            chunk["chunk_id"]
            for chunk in chunks
        ]

        if len(ids) != len(set(ids)):
            raise ValueError(
                "Duplicate chunk IDs in batch"
            )

        try:
            for chunk, vector in zip(
                chunks, vectors
            ):
                values = validate_vector(
                    vector,
                    self.dimensions
                )

                record = self.session.get(
                    Embedding,
                    chunk["chunk_id"]
                )

                if record is None:
                    record = Embedding(
                        chunk_id=chunk["chunk_id"]
                    )
                    self.session.add(record)

                record.text_hash = text_hash(
                    chunk["chunk_text"]
                )
                record.model = self.model_name
                record.dimensions = self.dimensions
                record.vector = values
                record.chunk_text = chunk["chunk_text"]
                record.metadata_json = get_metadata(
                    chunk
                )
                record.created_at = datetime.now(
                    timezone.utc
                )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

    def count(self):
        return self.session.scalar(
            select(func.count())
            .select_from(Embedding)
        ) or 0

    def validate(self, chunks):
        expected = {
            chunk["chunk_id"]: chunk
            for chunk in chunks
        }

        records = self.session.scalars(
            select(Embedding)
        ).all()

        issues = []
        found = set()

        for record in records:
            chunk_id = record.chunk_id
            found.add(chunk_id)

            original = expected.get(chunk_id)

            if original is None:
                issues.append(
                    f"Unexpected chunk: {chunk_id}"
                )
                continue

            if record.model != self.model_name:
                issues.append(
                    f"Model mismatch: {chunk_id}"
                )

            if record.dimensions != self.dimensions:
                issues.append(
                    f"Dimension mismatch: {chunk_id}"
                )

            if record.chunk_text != original["chunk_text"]:
                issues.append(
                    f"Text mismatch: {chunk_id}"
                )

            if record.text_hash != text_hash(
                original["chunk_text"]
            ):
                issues.append(
                    f"Hash mismatch: {chunk_id}"
                )

            if record.metadata_json != get_metadata(
                original
            ):
                issues.append(
                    f"Metadata mismatch: {chunk_id}"
                )

            try:
                validate_vector(
                    record.vector,
                    self.dimensions
                )
            except (ValueError, TypeError) as error:
                issues.append(
                    f"Invalid vector {chunk_id}: {error}"
                )

        for chunk_id in expected.keys() - found:
            issues.append(
                f"Missing chunk: {chunk_id}"
            )

        if len(records) != len(chunks):
            issues.append(
                "Stored vector count mismatch"
            )

        return {
            "expected_count": len(chunks),
            "vector_count": len(records),
            "dimensions": self.dimensions,
            "model": self.model_name,
            "issue_count": len(issues),
            "issues": issues,
            "valid": not issues,
        }

    def search_similar(
        self,
        query_vector,
        limit=5,
        filters=None,
    ):
        if limit <= 0:
            raise ValueError(
                "top_k must be greater than zero"
            )

        values = validate_vector(
            query_vector,
            self.dimensions
        )

        filters = filters or {}

        if not isinstance(filters, dict):
            raise ValueError(
                "Filters must be a dictionary"
            )

        unknown = set(filters) - FILTER_FIELDS

        if unknown:
            raise ValueError(
                f"Unsupported filters: {sorted(unknown)}"
            )

        distance = (
            Embedding.vector.cosine_distance(values)
        )

        statement = (
            select(
                Embedding,
                distance.label("distance")
            )
            .where(
                Embedding.model == self.model_name
            )
        )

        for field, value in filters.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Invalid filter value: {field}"
                )

            statement = statement.where(
                Embedding.metadata_json[
                    field
                ].as_string() == value
            )

        statement = (
            statement
            .order_by(distance, Embedding.chunk_id)
            .limit(limit)
        )

        try:
            rows = self.session.execute(
                statement
            ).all()

        except SQLAlchemyError as error:
            self.session.rollback()
            raise VectorStoreUnavailableError(
                "Vector store unavailable during search"
            ) from error

        return [
            {
                "chunk_id": record.chunk_id,
                "chunk_text": record.chunk_text,
                "metadata": record.metadata_json,
                "distance": float(distance_value),
                "similarity": (
                    1.0 - float(distance_value)
                ),
            }
            for record, distance_value in rows
        ]

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):
        if exc_type is not None:
            self.session.rollback()

        self.close()
        return False
