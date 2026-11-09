
class InvalidCitationError(ValueError):
    pass


def format_citation(result):
    metadata = result.get("metadata", {})

    source_id = metadata.get("source_id")
    chunk_id = result.get("chunk_id")

    if not source_id or not chunk_id:
        raise InvalidCitationError(
            "Citation is missing source or chunk ID"
        )

    title = (
        metadata.get("document_title")
        or metadata.get("title")
        or source_id
    )

    section = (
        metadata.get("section_name")
        or "Not provided"
    )

    version = (
        metadata.get("version")
        or "Not provided"
    )

    return {
        "chunk_id": chunk_id,
        "source_id": source_id,
        "document_title": (
            metadata.get("document_title")
            or metadata.get("title")
        ),
        "section": section,
        "version": version,
        "display": (
            f"{title} | Section: {section}"
            f" | Version: {version}"
            f" | Source: {source_id}"
        ),
    }


def build_citations(chunk_ids, evidence):
    evidence_by_id = {
        item["chunk_id"]: item
        for item in evidence
    }

    if not isinstance(chunk_ids, list):
        raise InvalidCitationError(
            "Citations must be a list"
        )

    if not all(
        isinstance(chunk_id, str)
        for chunk_id in chunk_ids
    ):
        raise InvalidCitationError(
            "Citation IDs must be strings"
        )

    invalid = set(chunk_ids) - set(evidence_by_id)

    if invalid:
        raise InvalidCitationError(
            "Citations not present in retrieved evidence: "
            f"{sorted(invalid)}"
        )

    citations = []
    seen = set()

    for chunk_id in chunk_ids:
        if chunk_id in seen:
            continue

        citations.append(
            format_citation(
                evidence_by_id[chunk_id]
            )
        )

        seen.add(chunk_id)

    return citations
