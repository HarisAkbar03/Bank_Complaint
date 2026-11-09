
import argparse
import json
import re

from pathlib import Path

from rag.embeddings import (
    get_local_model,
    load_config,
)

from rag.vector_index import (
    VectorIndex,
    VectorStoreUnavailableError,
    FILTER_FIELDS,
)


TEST_FILE = Path(
    "Supporting Documents/Test_Data/retrieval_test_set.json"
)

OUTPUT_FILE = Path(
    "reports/retrieval/semantic_evaluation.json"
)


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at",
    "be", "by", "do", "does", "for",
    "from", "how", "in", "is", "it",
    "of", "on", "or", "should", "the",
    "to", "what", "when", "which", "with",
}


def tokenize(text):
    return {
        word
        for word in re.findall(
            r"[a-z0-9]+",
            text.lower()
        )
        if word not in STOP_WORDS
    }


def lexical_overlap(query, text):
    query_words = tokenize(query)

    if not query_words:
        return 0.0

    text_words = tokenize(text)

    return (
        len(query_words & text_words)
        / len(query_words)
    )


def rerank_results(query, matches):
    """
    Deterministic fallback reranker.

    Original score: pgvector cosine similarity
    Reranked score: 80% similarity + 20% overlap
    """
    results = []

    for match in matches:
        original = match["similarity"]

        overlap = lexical_overlap(
            query,
            match["chunk_text"]
        )

        reranked = (
            0.8 * original
            + 0.2 * overlap
        )

        results.append({
            **match,
            "original_score": original,
            "reranked_score": reranked,
            "lexical_overlap": overlap,
        })

    return sorted(
        results,
        key=lambda item: (
            -item["reranked_score"],
            item["chunk_id"]
        )
    )


def retrieve(
    query,
    top_k=3,
    filters=None,
    rerank=False,
    candidate_k=None,
    index=None,
    model=None,
    config=None,
):
    """
    Public retrieval interface for later agents.

    Args:
        query: Nonempty natural-language question
        top_k: Number of final matches
        filters: Approved metadata filters
        rerank: Enable deterministic reranking
        candidate_k: Initial candidates before reranking

    Returns:
        Dictionary containing query, filters,
        retrieval settings and ranked matches.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError(
            "Query cannot be empty"
        )

    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError(
            "top_k must be a positive integer"
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

    for field, value in filters.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Invalid filter value: {field}"
            )

    if candidate_k is None:
        candidate_k = max(top_k, 10) if rerank else top_k

    if (
        not isinstance(candidate_k, int)
        or candidate_k < top_k
    ):
        raise ValueError(
            "candidate_k must be >= top_k"
        )

    if config is None:
        config = load_config()

    if config["mode"] != "local":
        raise ValueError(
            "Semantic retrieval requires "
            "EMBEDDING_MODE=local"
        )

    if model is None:
        model = get_local_model(
            config["model"]
        )

    query = query.strip()

    vector = model.encode(
        [query],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0].tolist()

    owns_index = index is None

    if owns_index:
        index = VectorIndex(
            model_name=config["model"],
            dimensions=config["dimensions"]
        )

    try:
        index.check_model()

        matches = index.search_similar(
            query_vector=vector,
            limit=candidate_k,
            filters=filters,
        )

    finally:
        if owns_index:
            index.close()

    # Preserve the baseline similarity score.
    baseline = [
        {
            **match,
            "original_score": match["similarity"],
            "reranked_score": None,
        }
        for match in matches
    ]

    if rerank:
        ranked = rerank_results(
            query,
            matches
        )
    else:
        ranked = baseline

    final_matches = []

    for rank, match in enumerate(
        ranked[:top_k],
        start=1
    ):
        final_matches.append({
            "rank": rank,
            "chunk_id": match["chunk_id"],
            "text": match["chunk_text"],
            "original_score": round(
                match["original_score"], 6
            ),
            "reranked_score": (
                round(match["reranked_score"], 6)
                if match["reranked_score"] is not None
                else None
            ),
            "metadata": match["metadata"],
        })

    return {
        "query": query,
        "top_k": top_k,
        "filters": filters,
        "reranking_enabled": rerank,
        "candidate_k": candidate_k,
        "results": final_matches,
        "result_count": len(final_matches),
    }


def load_test_cases(path):
    with Path(path).open(
        encoding="utf-8-sig"
    ) as file:
        cases = json.load(file)

    if not isinstance(cases, list):
        raise ValueError(
            "Test cases must be a JSON array"
        )

    for case in cases:
        for field in (
            "case_id",
            "query",
            "expected_source_ids",
        ):
            if field not in case:
                raise ValueError(
                    f"Missing test field: {field}"
                )

        if (
            not isinstance(
                case["expected_source_ids"],
                list
            )
            or not case["expected_source_ids"]
        ):
            raise ValueError(
                f"Invalid expected sources: "
                f"{case['case_id']}"
            )

    return cases


def evaluate(
    test_file=TEST_FILE,
    output_file=OUTPUT_FILE,
    top_k=3,
    rerank=False,
    candidate_k=None,
):
    cases = load_test_cases(test_file)

    config = load_config()
    model = get_local_model(
        config["model"]
    )

    results = []

    with VectorIndex(
        model_name=config["model"],
        dimensions=config["dimensions"]
    ) as index:

        for case in cases:
            response = retrieve(
                query=case["query"],
                top_k=top_k,
                filters=case.get("filter", {}),
                rerank=rerank,
                candidate_k=candidate_k,
                index=index,
                model=model,
                config=config,
            )

            retrieved_sources = [
                result["metadata"].get(
                    "source_id"
                )
                for result in response["results"]
            ]

            expected = set(
                case["expected_source_ids"]
            )

            passed = bool(
                expected.intersection(
                    retrieved_sources
                )
            )

            results.append({
                "case_id": case["case_id"],
                "expected_source_ids": sorted(expected),
                "retrieved_source_ids": retrieved_sources,
                "hit_at_k": passed,
                "retrieval": response,
            })

            print(
                f"{case['case_id']}: "
                f"{'PASS' if passed else 'FAIL'}"
            )
            print(
                f"  Expected: {sorted(expected)}"
            )
            print(
                f"  Retrieved: {retrieved_sources}"
            )

    passed_count = sum(
        item["hit_at_k"]
        for item in results
    )

    summary = {
        "method": (
            "MiniLM + pgvector + lexical reranking"
            if rerank
            else "MiniLM + pgvector"
        ),
        "metric": f"Hit@{top_k}",
        "total_cases": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        "hit_rate": (
            round(passed_count / len(results), 4)
            if results else 0
        ),
        "results": results,
    }

    output = Path(output_file)
    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("\nSemantic Retrieval Evaluation")
    print("-----------------------------")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Hit@{top_k}: {summary['hit_rate']:.2%}")
    print(f"Report: {output}")

    return summary


def main():
    parser = argparse.ArgumentParser()

    source = parser.add_mutually_exclusive_group()

    source.add_argument(
        "--question",
        type=str
    )

    source.add_argument(
        "--test-file",
        default=None
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3
    )

    parser.add_argument(
        "--candidate-k",
        type=int,
        default=None
    )

    parser.add_argument(
        "--document-type",
        type=str
    )

    parser.add_argument(
        "--version",
        type=str
    )

    parser.add_argument(
        "--access-label",
        type=str
    )

    parser.add_argument(
        "--rerank",
        action="store_true"
    )

    parser.add_argument(
        "--output",
        type=str
    )

    args = parser.parse_args()

    filters = {}

    if args.document_type:
        filters["document_type"] = args.document_type

    if args.version:
        filters["version"] = args.version

    if args.access_label:
        filters["access_label"] = args.access_label

    try:
        if args.question is not None:
            result = retrieve(
                query=args.question,
                top_k=args.top_k,
                filters=filters,
                rerank=args.rerank,
                candidate_k=args.candidate_k,
            )

            print(json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            ))

            if args.output:
                output = Path(args.output)
                output.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )
                output.write_text(
                    json.dumps(
                        result,
                        indent=2,
                        ensure_ascii=False
                    ),
                    encoding="utf-8"
                )

        else:
            if filters:
                parser.error(
                    "CLI metadata filters apply to "
                    "--question. Test-file mode "
                    "uses each case's own filter."
                )

            evaluate(
                test_file=(
                    args.test_file or TEST_FILE
                ),
                output_file=(
                    args.output or OUTPUT_FILE
                ),
                top_k=args.top_k,
                rerank=args.rerank,
                candidate_k=args.candidate_k,
            )

    except (
        ValueError,
        VectorStoreUnavailableError,
        RuntimeError
    ) as error:
        parser.exit(
            status=1,
            message=f"Retrieval error: {error}\n"
        )


if __name__ == "__main__":
    main()
