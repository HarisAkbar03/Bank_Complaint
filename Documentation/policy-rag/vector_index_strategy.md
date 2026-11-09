# Policy RAG — Vector, Text, and Metadata Index Strategy

**Project:** Banking Complaint Management System  
**Feature:** Policy RAG Knowledge Service  
**Version:** 1.0 — Draft  
**Related Specification:** `spec/policy-rag/spec.md`  
**Related Metadata Model:** `document_metadata_model.md`

## 1. Purpose

The index strategy defines how the Policy RAG Knowledge Service will locate relevant policy information while preserving source traceability, document version control, and access restrictions.

The service will support three complementary retrieval capabilities:

1. Vector search for semantic relevance.
2. Text search for exact keywords and terminology.
3. Metadata filtering for document eligibility and access control.

This document describes required search behavior rather than mandating a particular search engine or vector database.

## 2. Vector Index Strategy

### 2.1 Purpose

The vector index supports semantic retrieval.

It helps identify relevant policy sections even when the user's question uses different wording from the source document.

**Example question:**

"How should an analyst handle a complaint that needs escalation?"

The service should identify semantically relevant policy chunks from approved, accessible documents.

### 2.2 Indexed Content

The vector representation shall be generated from:

- `chunk_text`

Each vector entry must retain a reference to:

- `chunk_id`
- `source_id`
- `version`

### 2.3 Requirements

- Each searchable vector must correspond to a valid chunk.
- Vector entries must preserve source traceability.
- Ineligible or unauthorized content must not be returned.
- Retrieval must support relevance ranking.
- Updated or removed source versions must be reflected in the searchable collection.

## 3. Text Index Strategy

### 3.1 Purpose

The text index supports keyword and exact-term retrieval.

It is useful when users search for specific policy names, business terms, or document headings.

### 3.2 Indexed Fields

- `title`
- `section_name`
- `chunk_text`

### 3.3 Example

**Question:** "Where can I find the complaint escalation matrix?"

Text search should be able to identify the document titled "Complaint Escalation Matrix" when it is eligible and accessible to the user.

### 3.4 Requirements

- Exact document titles must be searchable.
- Section headings must be searchable.
- Policy terminology must be searchable.
- Text results must retain source and chunk identifiers.
- Search results must obey the same access and version restrictions as vector results.

## 4. Metadata Index Strategy

### 4.1 Purpose

The metadata index supports filtering, source identification, and compliance.

It ensures the service retrieves only documents that satisfy the required business and security rules.

### 4.2 Indexed Fields

| Field | Purpose |
|---|---|
| `source_id` | Identify the source document |
| `chunk_id` | Identify the retrieved chunk |
| `document_type` | Filter by document type |
| `category` | Filter by business category |
| `version` | Identify the source version |
| `effective_date` | Filter future-effective documents |
| `access_label` | Enforce document access restrictions |
| `approval_status` | Exclude unapproved documents |
| `checksum` | Support source integrity verification |

The `category` and `approval_status` fields are defined at document level and may be made available to retrieval through document-to-chunk metadata association.

### 4.3 Required Filters

The retrieval contract must support:

- `document_type`
- `version`
- `effective_date`
- `access_label`
- `approval_status`

Optional business filtering may use:

- `category`
- `source_id`

These field names must remain consistent across metadata definitions, retrieval requests, and evaluation tests.

## 5. Access Filtering Strategy

### 5.1 Requirement

The service must prevent unauthorized documents from being returned or used as answer evidence.

### 5.2 Filtering Rules

1. Determine the user's authorized document access.
2. Apply the permitted `access_label` values.
3. Exclude chunks with unauthorized labels.
4. Perform retrieval only within the eligible document set.
5. Verify access again before returning source content or citations.

### 5.3 Example

**User authorization:** Internal policy access only.

**Eligible access label:**

`Internal`

**Excluded access label:**

`Restricted`

A user authorized for both Internal and Restricted documents may retrieve both, subject to the approved access-control policy.

A restricted document must never become visible simply because its content has high semantic similarity to the question.

## 6. Effective Version Filtering

The retrieval service must exclude ineligible policy versions.

For current-policy questions:

1. Filter to approved documents.
2. Exclude versions with a future `effective_date`.
3. Apply the approved current-version rule.
4. Exclude superseded documents unless historical retrieval is permitted.
5. Preserve the exact `version` in the returned metadata.

### Example

If a document has versions 1.0 and 2.0, and 2.0 is the approved current version, a current-policy answer must not rely on version 1.0.

The actual current-version designation must come from approved source metadata, not an assumption that the numerically highest version is always current.

## 7. Retrieval Contract

### 7.1 Retrieval Input

The retrieval operation shall accept:

| Field | Description |
|---|---|
| `question` | User's natural-language question |
| `document_type` | Optional document-type filter |
| `category` | Optional category filter |
| `source_id` | Optional source filter |
| `version` | Optional version filter, subject to eligibility rules |
| `effective_date` | Applicable policy reference date |
| `access_label` | Authorized access-label set, derived from trusted authorization context |
| `approval_status` | Eligibility restriction enforced by the service |

A client must not be able to grant itself higher access by submitting an arbitrary `access_label`.

### 7.2 Retrieval Output

Each returned result shall contain:

- `chunk_id`
- `source_id`
- `version`
- `section_name`
- `sequence_number`
- `chunk_text`
- `document_type`
- `effective_date`
- `access_label`
- Relevance rank or score
- Source reference sufficient for citation resolution

### 7.3 Retrieval Count

The proposed retrieval target is the top three eligible chunks.

The count is subject to approval in the clarification log.

If fewer than three eligible chunks exist, the service may return fewer results.

Retrieval count alone does not determine whether evidence is sufficient to answer.

## 8. Retrieval Workflow

1. Receive a valid policy question.
2. Determine authorized document access.
3. Establish applicable document and version filters.
4. Search eligible policy content using semantic and text retrieval.
5. Rank relevant results.
6. Return the highest-ranked eligible chunks.
7. Verify source metadata and traceability.
8. Provide evidence to the answer-generation process.
9. Attach citations to supported answers.
10. Abstain when evidence is insufficient.

## 9. Citation Requirements

Every substantive answer must include at least one citation referencing actual retrieved evidence.

A citation must identify:

- Document title.
- `source_id`.
- `version`.
- `section_name` or equivalent source locator.

The system must be able to resolve each citation to its supporting `chunk_id`.

### Example

**Illustrative citation:**

Complaint Escalation Matrix — POL-002 — Version 1.4 — Section: Escalation Timelines.

This section label is illustrative; it must be verified against the source before use as a real citation.

## 10. Index Maintenance

The service must support:

- Adding newly approved document versions.
- Detecting changed source files using `checksum`.
- Updating searchable content after approved changes.
- Removing or excluding ineligible versions.
- Maintaining document-to-chunk relationships.
- Preventing orphaned chunk records.
- Preserving source traceability after reindexing.

## 11. Index Acceptance Criteria

**IAC-01:** Every vector entry maps to a valid `chunk_id`.

**IAC-02:** Every retrieved chunk maps to an existing `source_id` and `version`.

**IAC-03:** Text search can retrieve eligible documents by exact title or section terminology.

**IAC-04:** Metadata filtering excludes all unauthorized `access_label` values.

**IAC-05:** Unapproved documents are excluded from retrieval.

**IAC-06:** Future-effective versions are excluded from current-policy searches.

**IAC-07:** Superseded versions are excluded according to approved version rules.

**IAC-08:** Retrieved results preserve citation metadata.

**IAC-09:** A missing or invalid source reference prevents a chunk from being used as answer evidence.

**IAC-10:** Index updates do not leave searchable chunks pointing to missing source versions.

## 12. Open Decisions

The following remain unresolved:

- Approved search technology.
- Retrieval-ranking approach.
- Final top-k retrieval count.
- Current-version eligibility rule.
- Category taxonomy.
- Authorized access-label mapping.
- Historical policy retrieval rules.
- Reindexing and retention requirements.

These decisions must be finalized before implementation.