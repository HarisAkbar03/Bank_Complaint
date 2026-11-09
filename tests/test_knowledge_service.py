
import pytest

from rag.knowledge_service import (
    answer_question,
    ABSTENTION_MESSAGE,
)
from rag.citations import (
    build_citations,
    InvalidCitationError,
)


def make_result(
    text,
    score=0.8,
    source_id="KB-002",
    approved=True,
):
    return {
        "rank": 1,
        "chunk_id": f"{source_id}-001",
        "text": text,
        "original_score": score,
        "reranked_score": score,
        "metadata": {
            "source_id": source_id,
            "section_name": "Escalation",
            "version": "1",
            "approval_status": (
                "Approved"
                if approved
                else "Draft"
            ),
            "access_label": "Restricted",
        },
    }


def fake_retriever(results):
    def search(**kwargs):
        return {"results": results}
    return search


def test_relevant_approved_evidence():
    evidence = make_result(
        "Immediate complaint escalation requires "
        "review by the responsible team."
    )

    result = answer_question(
        "What requires immediate complaint escalation?",
        retriever=fake_retriever([evidence]),
    )

    assert result["state"] == "partially_supported"
    assert result["answer"] != ABSTENTION_MESSAGE
    assert result["citations"][0]["source_id"] == "KB-002"


def test_partially_supported_question():
    evidence = make_result(
        "Disputed fees require investigation.",
        score=0.5,
        source_id="KB-003",
    )

    result = answer_question(
        "How are disputed fees investigated?",
        retriever=fake_retriever([evidence]),
    )

    assert result["state"] == "partially_supported"
    assert result["confidence"] == "low"


def test_unsupported_question():
    result = answer_question(
        "What is the policy for extraterrestrial banking?",
        retriever=fake_retriever([]),
    )

    assert result["state"] == "abstained"
    assert result["answer"] == ABSTENTION_MESSAGE
    assert result["citations"] == []


def test_low_similarity_abstains():
    evidence = make_result(
        "Unrelated document passage.",
        score=0.1,
    )

    result = answer_question(
        "What is the escalation policy?",
        retriever=fake_retriever([evidence]),
    )

    assert result["state"] == "abstained"


def test_unapproved_evidence_is_rejected():
    evidence = make_result(
        "Immediate complaint escalation is required.",
        approved=False,
    )

    result = answer_question(
        "When is immediate complaint escalation required?",
        retriever=fake_retriever([evidence]),
    )

    assert result["state"] == "abstained"


def test_fabricated_citation_is_rejected():
    evidence = make_result(
        "Immediate complaint escalation is required."
    )

    with pytest.raises(InvalidCitationError):
        build_citations(
            ["KB-999"],
            [evidence],
        )
