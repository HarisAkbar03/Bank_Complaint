
import math
import os

from dotenv import load_dotenv

from rag.retrieval import retrieve
from rag.local_llm import generate_answer, LocalLLMError
from rag.citations import (
    build_citations,
    InvalidCitationError,
)


load_dotenv()


ABSTENTION_MESSAGE = (
    "I could not find sufficient approved evidence "
    "to answer this question."
)


def abstain(query, retrieved_count=0, reason=None):
    response = {
        "query": query,
        "answer": ABSTENTION_MESSAGE,
        "state": "abstained",
        "confidence": "low",
        "evidence": [],
        "citations": [],
        "retrieved_count": retrieved_count,
        "used_evidence_count": 0,
    }

    if reason:
        response["reason"] = reason

    return response


def answer_question(
    query,
    top_k=5,
    filters=None,
    rerank=True,
    min_similarity=None,
    retriever=None,
    generator=None,
):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty")

    if min_similarity is None:
        min_similarity = float(
            os.getenv("RAG_MIN_SIMILARITY", "0.35")
        )

    if (
        not math.isfinite(min_similarity)
        or not 0 <= min_similarity <= 1
    ):
        raise ValueError(
            "min_similarity must be between 0 and 1"
        )

    search = retriever if retriever is not None else retrieve
    generate = generator if generator is not None else generate_answer

    retrieval = search(
        query=query,
        top_k=top_k,
        filters=filters,
        rerank=rerank,
    )

    results = retrieval["results"]

    approved_evidence = [
        item
        for item in results
        if (
            item.get("metadata", {})
            .get("approval_status", "")
            .casefold() == "approved"
            and item.get("original_score", -1)
            >= min_similarity
            and item.get("text", "").strip()
        )
    ]

    if not approved_evidence:
        return abstain(
            query,
            retrieved_count=len(results),
            reason="Insufficient approved evidence",
        )

    try:
        generated = generate(
            query,
            approved_evidence,
        )

        state = generated["state"]
        confidence = generated["confidence"]
        answer = generated["answer"].strip()
        chunk_ids = generated["cited_chunk_ids"]

        if state == "abstained":
            return abstain(
                query,
                retrieved_count=len(results),
                reason="Generator found insufficient evidence",
            )

        if not answer or not chunk_ids:
            return abstain(
                query,
                retrieved_count=len(results),
                reason="Missing answer or citations",
            )

        citations = build_citations(
            chunk_ids,
            approved_evidence,
        )

    except (InvalidCitationError, KeyError, TypeError):
        return abstain(
            query,
            retrieved_count=len(results),
            reason="Invalid generated citations or response",
        )

    supporting_ids = {
        citation["chunk_id"]
        for citation in citations
    }

    supporting_evidence = [
        item
        for item in approved_evidence
        if item["chunk_id"] in supporting_ids
    ]

    return {
        "query": query,
        "answer": answer,
        "state": state,
        "confidence": confidence,
        "evidence": supporting_evidence,
        "citations": citations,
        "retrieved_count": len(results),
        "used_evidence_count": len(supporting_evidence),
    }
