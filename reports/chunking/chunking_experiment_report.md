# Chunking Experiment Report

## Configuration

- Unit: whitespace-delimited words (not LLM tokens)
- Maximum size: 500 words
- Baseline overlap: 50 words
- Structure-aware: paragraph-first, with long-paragraph overlap
- Retrieval: BM25 with experimental document-type weighting, top 3

## Chunk Counts

- Baseline: 175
- Structure-aware: 175

## Validation

- Baseline issues: 0
- Structure-aware issues: 0

## Retrieval Comparison

- Evaluated cases: 3
- Baseline source-and-section hits: 1
- Structure-aware source-and-section hits: 0

| Case | Query | Baseline | Structure-aware |
|---|---|---|---|
| CH-001 | When is supervisor approval required? | True | False |
| CH-002 | What evidence is needed for a fee complaint? | False | False |
| CH-003 | When should suspected account takeover be escalated? | False | False |

## Strategy Decision

- Selected strategy: baseline
- Reason: Baseline selected based on retrieval results: 1/3 versus 0/3.

## Trade-offs

- Baseline: predictable word windows, but paragraph boundaries may be lost.
- Structure-aware: preserves paragraph boundaries and headings, but chunk sizes vary.
- Neither strategy guarantees that exceptions remain with governing rules.
- Matching a source and section does not establish that the answer is fully supported.

## Limitations

- Word counts are not tokenizer-specific.
- BM25 is lexical retrieval, not embedding-based semantic retrieval.
- Document-type weights are experimental and require evaluation.
- Human inspection is needed for rules, exceptions and citations.
- Three test cases are insufficient to establish general retrieval quality.
