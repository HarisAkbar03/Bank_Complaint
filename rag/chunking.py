
import argparse
import json
import math
import re

from collections import Counter
from pathlib import Path


DEFAULT_SIZE = 500
DEFAULT_OVERLAP = 50

INPUT_PATH = Path("reports/ingestion/documents.jsonl")
OUTPUT_DIR = Path("reports/chunking")


# ---------------------------------------------------------
# JSONL utilities
# ---------------------------------------------------------

def load_jsonl(path):
    records = []

    with Path(path).open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {error}"
                ) from error

    return records


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )


def words(text):
    return re.findall(r"\S+", text)


# ---------------------------------------------------------
# Chunk metadata
# ---------------------------------------------------------

def make_chunk(record, text, strategy, sequence):
    chunk = dict(record)

    source = record["source_id"]
    version = record["version"]
    section = record["sequence_number"]

    chunk["parent_section_id"] = record["chunk_id"]

    chunk["chunk_id"] = (
        f"{source}-V{version}-S{section:04d}"
        f"-{strategy}-{sequence:04d}"
    )

    chunk["chunk_text"] = text
    chunk["strategy"] = strategy
    chunk["word_count"] = len(words(text))

    return chunk


# ---------------------------------------------------------
# Strategy 1: Fixed-size baseline chunking
# ---------------------------------------------------------

def fixed_chunk(record, chunk_size=500, overlap=50):
    """
    Split a section into fixed word windows.

    This strategy does not preserve paragraph boundaries.
    """

    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("Require 0 <= overlap < chunk_size")

    tokens = words(record.get("chunk_text", ""))
    chunks = []

    if not tokens:
        return chunks

    step = chunk_size - overlap

    for start in range(0, len(tokens), step):
        part = tokens[start:start + chunk_size]

        if not part:
            break

        chunks.append(
            make_chunk(
                record,
                " ".join(part),
                "baseline",
                len(chunks) + 1
            )
        )

        if start + chunk_size >= len(tokens):
            break

    return chunks


# ---------------------------------------------------------
# Strategy 2: Structure-aware chunking
# ---------------------------------------------------------

def split_long_paragraph(text, chunk_size, overlap):
    """
    Split oversized paragraphs into overlapping word windows.
    """

    tokens = words(text)
    parts = []

    step = chunk_size - overlap

    for start in range(0, len(tokens), step):
        part = tokens[start:start + chunk_size]

        if part:
            parts.append(" ".join(part))

        if start + chunk_size >= len(tokens):
            break

    return parts


def structure_aware_chunk(
    record,
    chunk_size=500,
    overlap=50
):
    """
    Prefer paragraph boundaries and preserve the section
    heading in each resulting chunk.
    """

    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("Require 0 <= overlap < chunk_size")

    text = record.get("chunk_text", "").strip()

    if not text:
        return []

    heading = record.get("section_name", "").strip()

    heading_words = words(heading)
    available = chunk_size - len(heading_words)

    if available <= 0:
        raise ValueError("Heading exceeds chunk size")

    effective_overlap = min(overlap, available - 1)

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n|\n", text)
        if paragraph.strip()
    ]

    units = []

    for paragraph in paragraphs:
        if len(words(paragraph)) <= available:
            units.append(paragraph)
        else:
            units.extend(
                split_long_paragraph(
                    paragraph,
                    available,
                    effective_overlap
                )
            )

    chunks = []
    current = []
    current_count = 0

    def save_current():
        if not current:
            return

        body = "\n".join(current)

        chunk_text = (
            f"{heading}\n{body}"
            if heading else body
        )

        chunks.append(
            make_chunk(
                record,
                chunk_text,
                "structure",
                len(chunks) + 1
            )
        )

    for unit in units:
        unit_count = len(words(unit))

        if current and current_count + unit_count > available:
            save_current()
            current = []
            current_count = 0

        current.append(unit)
        current_count += unit_count

    save_current()

    return chunks


# ---------------------------------------------------------
# Chunk validation
# ---------------------------------------------------------

def validate_chunks(chunks, source_records, max_words=500):
    issues = []
    seen = set()

    valid_parents = {
        record["chunk_id"]: record
        for record in source_records
    }

    required_metadata = [
        "source_id",
        "version",
        "access_label",
        "approval_status",
        "checksum",
        "section_name",
        "sequence_number"
    ]

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        parent_id = chunk.get("parent_section_id")
        text = chunk.get("chunk_text", "")

        if chunk_id in seen:
            issues.append({
                "chunk_id": chunk_id,
                "reason": "Duplicate chunk ID"
            })

        seen.add(chunk_id)

        if not text.strip():
            issues.append({
                "chunk_id": chunk_id,
                "reason": "Empty chunk"
            })

        if len(words(text)) > max_words:
            issues.append({
                "chunk_id": chunk_id,
                "reason": "Exceeds maximum word count"
            })

        if parent_id not in valid_parents:
            issues.append({
                "chunk_id": chunk_id,
                "reason": "Unknown parent section"
            })
            continue

        parent = valid_parents[parent_id]

        for field in required_metadata:
            if (
                not chunk.get(field)
                or chunk.get(field) != parent.get(field)
            ):
                issues.append({
                    "chunk_id": chunk_id,
                    "reason": f"Missing or altered metadata: {field}"
                })

    return {
        "chunk_count": len(chunks),
        "issue_count": len(issues),
        "issues": issues
    }


# ---------------------------------------------------------
# BM25 retrieval
# ---------------------------------------------------------

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "what", "when", "where", "why", "how",
    "for", "to", "of", "in", "on", "at",
    "and", "or", "be", "should", "do", "does"
}

# Experimental weights, not official policy authority rules.
AUTHORITY_WEIGHTS = {
    "policy": 1.30,
    "playbook": 1.25,
    "guide": 1.20,
    "bulletin": 1.15,
    "faq": 0.90,
    "casebook": 0.75
}


def tokenize(text):
    return [
        word
        for word in re.findall(r"[a-z0-9]+", text.lower())
        if word not in STOP_WORDS
    ]


def simple_retrieve(query, chunks, top_k=3):
    """
    Retrieve chunks using BM25 and experimental
    document-type weighting.

    This is lexical retrieval, not semantic retrieval.
    """

    query_tokens = tokenize(query)

    if not query_tokens or not chunks or top_k <= 0:
        return []

    documents = []
    document_frequency = Counter()

    for chunk in chunks:
        section_name = chunk.get("section_name", "")
        chunk_text = chunk.get("chunk_text", "")

        searchable_text = (
            section_name + " " +
            section_name + " " +
            chunk_text
        )

        tokens = tokenize(searchable_text)
        frequencies = Counter(tokens)

        documents.append(
            (chunk, frequencies, len(tokens))
        )

        document_frequency.update(frequencies.keys())

    total_documents = len(documents)

    average_length = (
        sum(length for _, _, length in documents)
        / total_documents
    )

    k1 = 1.5
    b = 0.75

    ranked = []

    for chunk, frequencies, length in documents:
        score = 0.0

        for term in set(query_tokens):
            frequency = frequencies.get(term, 0)

            if frequency == 0:
                continue

            df = document_frequency[term]

            idf = math.log(
                1 + (total_documents - df + 0.5) / (df + 0.5)
            )

            numerator = frequency * (k1 + 1)

            denominator = frequency + k1 * (
                1 - b + b * length / max(average_length, 1)
            )

            score += idf * numerator / denominator

        if score > 0:
            document_type = chunk.get(
                "document_type", ""
            ).strip().lower()

            weight = AUTHORITY_WEIGHTS.get(
                document_type, 1.0
            )

            score *= weight

            ranked.append((score, chunk))

    ranked.sort(
        key=lambda item: (
            -item[0],
            item[1]["chunk_id"]
        )
    )

    return [
        chunk
        for score, chunk in ranked[:top_k]
    ]


# ---------------------------------------------------------
# Official FDM retrieval experiment
# ---------------------------------------------------------

def run_spot_test(cases, baseline, structured):
    results = []

    for case in cases:
        case_id = case["case_id"]
        query = case["query"]
        expected_source = case["expected_source"]
        expected_section = case["expected_section"]

        baseline_hits = simple_retrieve(
            query, baseline, top_k=3
        )

        structure_hits = simple_retrieve(
            query, structured, top_k=3
        )

        def check_retrieval(hits):
            return any(
                hit["source_id"] == expected_source
                and hit["section_name"].strip().casefold()
                == expected_section.strip().casefold()
                for hit in hits
            )

        def summarize_hits(hits):
            return [
                {
                    "rank": rank,
                    "chunk_id": hit["chunk_id"],
                    "source_id": hit["source_id"],
                    "section_name": hit["section_name"]
                }
                for rank, hit in enumerate(hits, 1)
            ]

        results.append({
            "case_id": case_id,
            "query": query,
            "expected_source": expected_source,
            "expected_section": expected_section,
            "baseline_hit": check_retrieval(baseline_hits),
            "structure_hit": check_retrieval(structure_hits),
            "baseline_results": summarize_hits(baseline_hits),
            "structure_results": summarize_hits(structure_hits)
        })

    return results


# ---------------------------------------------------------
# Strategy selection
# ---------------------------------------------------------

def select_strategy(
    baseline,
    structured,
    baseline_validation,
    structure_validation,
    comparison
):
    """
    Select a default using validation and retrieval results.

    If both strategies tie, prefer structure-aware chunking
    as a documented design preference, not a measured win.
    """

    baseline_valid = baseline_validation["issue_count"] == 0
    structure_valid = structure_validation["issue_count"] == 0

    if not baseline_valid and not structure_valid:
        return None, "Neither strategy passed validation."

    if baseline_valid and not structure_valid:
        return "baseline", (
            "Baseline selected because structure-aware "
            "chunking failed validation."
        )

    if structure_valid and not baseline_valid:
        return "structure", (
            "Structure-aware selected because baseline "
            "chunking failed validation."
        )

    if comparison is None:
        return "structure", (
            "Structure-aware selected provisionally because "
            "both strategies passed validation. Retrieval "
            "evaluation has not been performed."
        )

    baseline_hits = sum(
        item["baseline_hit"] for item in comparison
    )

    structure_hits = sum(
        item["structure_hit"] for item in comparison
    )

    if structure_hits > baseline_hits:
        return "structure", (
            f"Structure-aware selected based on retrieval "
            f"results: {structure_hits}/{len(comparison)} "
            f"versus {baseline_hits}/{len(comparison)}."
        )

    if baseline_hits > structure_hits:
        return "baseline", (
            f"Baseline selected based on retrieval "
            f"results: {baseline_hits}/{len(comparison)} "
            f"versus {structure_hits}/{len(comparison)}."
        )

    return "structure", (
        f"Both strategies tied at "
        f"{structure_hits}/{len(comparison)} retrieval hits. "
        "Structure-aware selected as a design preference "
        "because it preserves paragraph boundaries and "
        "repeats section headings. This is not evidence "
        "of superior retrieval performance."
    )


# ---------------------------------------------------------
# Experiment report
# ---------------------------------------------------------

def create_report(
    baseline,
    structured,
    baseline_validation,
    structure_validation,
    comparison=None,
    selected_strategy=None,
    decision_reason=None
):
    lines = [
        "# Chunking Experiment Report",
        "",
        "## Configuration",
        "",
        "- Unit: whitespace-delimited words (not LLM tokens)",
        "- Maximum size: 500 words",
        "- Baseline overlap: 50 words",
        "- Structure-aware: paragraph-first, with long-paragraph overlap",
        "- Retrieval: BM25 with experimental document-type weighting, top 3",
        "",
        "## Chunk Counts",
        "",
        f"- Baseline: {len(baseline)}",
        f"- Structure-aware: {len(structured)}",
        "",
        "## Validation",
        "",
        f"- Baseline issues: {baseline_validation['issue_count']}",
        f"- Structure-aware issues: {structure_validation['issue_count']}",
        "",
        "## Retrieval Comparison",
        ""
    ]

    if comparison is None:
        lines.append(
            "Not run: experiment cases were not supplied."
        )
    else:
        baseline_hits = sum(
            item["baseline_hit"] for item in comparison
        )

        structure_hits = sum(
            item["structure_hit"] for item in comparison
        )

        lines.extend([
            f"- Evaluated cases: {len(comparison)}",
            f"- Baseline source-and-section hits: {baseline_hits}",
            f"- Structure-aware source-and-section hits: {structure_hits}",
            "",
            "| Case | Query | Baseline | Structure-aware |",
            "|---|---|---|---|"
        ])

        for item in comparison:
            query = item["query"].replace("|", "/")

            lines.append(
                f"| {item['case_id']} "
                f"| {query} "
                f"| {item['baseline_hit']} "
                f"| {item['structure_hit']} |"
            )

    lines.extend([
        "",
        "## Strategy Decision",
        "",
        f"- Selected strategy: {selected_strategy or 'None'}",
        f"- Reason: {decision_reason or 'Not evaluated'}",
        "",
        "## Trade-offs",
        "",
        "- Baseline: predictable word windows, but paragraph boundaries may be lost.",
        "- Structure-aware: preserves paragraph boundaries and headings, but chunk sizes vary.",
        "- Neither strategy guarantees that exceptions remain with governing rules.",
        "- Matching a source and section does not establish that the answer is fully supported.",
        "",
        "## Limitations",
        "",
        "- Word counts are not tokenizer-specific.",
        "- BM25 is lexical retrieval, not embedding-based semantic retrieval.",
        "- Document-type weights are experimental and require evaluation.",
        "- Human inspection is needed for rules, exceptions and citations.",
        "- Three test cases are insufficient to establish general retrieval quality."
    ])

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------
# Main execution
# ---------------------------------------------------------

def main():
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
        "--cases",
        default=None
    )

    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE
    )

    parser.add_argument(
        "--overlap",
        type=int,
        default=DEFAULT_OVERLAP
    )

    args = parser.parse_args()

    records = load_jsonl(args.input)

    baseline = []
    structured = []

    for record in records:
        baseline.extend(
            fixed_chunk(record, args.size, args.overlap)
        )

        structured.extend(
            structure_aware_chunk(
                record, args.size, args.overlap
            )
        )

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    write_jsonl(
        output / "chunks_baseline.jsonl",
        baseline
    )

    write_jsonl(
        output / "chunks_structure.jsonl",
        structured
    )

    baseline_validation = validate_chunks(
        baseline, records, args.size
    )

    structure_validation = validate_chunks(
        structured, records, args.size
    )

    validation = {
        "baseline": baseline_validation,
        "structure_aware": structure_validation
    }

    (output / "chunk_validation.json").write_text(
        json.dumps(validation, indent=2),
        encoding="utf-8"
    )

    comparison = None

    if args.cases:
        with open(args.cases, encoding="utf-8") as file:
            cases = json.load(file)

        if not isinstance(cases, list):
            raise ValueError(
                "Expected a list of experiment cases."
            )

        comparison = run_spot_test(
            cases, baseline, structured
        )

        (output / "retrieval_comparison.json").write_text(
            json.dumps(comparison, indent=2),
            encoding="utf-8"
        )

    selected_strategy, decision_reason = select_strategy(
        baseline,
        structured,
        baseline_validation,
        structure_validation,
        comparison
    )

    if selected_strategy == "baseline":
        selected_chunks = baseline
    elif selected_strategy == "structure":
        selected_chunks = structured
    else:
        selected_chunks = []

    if selected_strategy is not None:
        write_jsonl(
            output / "chunks_selected.jsonl",
            selected_chunks
        )

    report = create_report(
        baseline,
        structured,
        baseline_validation,
        structure_validation,
        comparison,
        selected_strategy,
        decision_reason
    )

    (output / "chunking_experiment_report.md").write_text(
        report,
        encoding="utf-8"
    )

    print("Chunking completed")
    print(f"Source sections: {len(records)}")
    print(f"Baseline chunks: {len(baseline)}")
    print(f"Structure-aware chunks: {len(structured)}")
    print(f"Baseline validation issues: {baseline_validation['issue_count']}")
    print(f"Structure validation issues: {structure_validation['issue_count']}")
    print(f"Selected strategy: {selected_strategy}")
    print(f"Report: {output / 'chunking_experiment_report.md'}")


if __name__ == "__main__":
    main()
