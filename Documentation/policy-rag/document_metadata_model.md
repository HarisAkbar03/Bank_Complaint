# Policy RAG — Document and Chunk Metadata Model

**Project:** Banking Complaint Management System  
**Feature:** Policy RAG Knowledge Service  
**Version:** 1.0 — Draft  
**Related Specification:** `spec/policy-rag/spec.md`

## 1. Overview

The purpose of this metadata model is to ensure that every policy document and retrieved document chunk can be identified, validated, filtered, and traced back to its original source.

The metadata model supports:

- Accurate policy retrieval.
- Document version control.
- Source traceability.
- Citation generation.
- Access control.
- Detection of modified documents.
- Retrieval of approved and effective policy information.

## 2. Document-Level Metadata

Each knowledge-base document must have the following metadata.

| Field | Data type | Required | Description |
|---|---|---|---|
| `source_id` | String | Yes | Unique identifier for a policy document |
| `title` | String | Yes | Official document title |
| `document_type` | String | Yes | Procedure, Matrix, Guidance, or Guide |
| `category` | String | Yes | Business category assigned to the document |
| `version` | String | Yes | Document version |
| `effective_date` | Date | Yes | Date the version becomes effective |
| `access_label` | String | Yes | Internal or Restricted |
| `filename` | String | Yes | Physical source filename |
| `checksum` | String | Yes | SHA-256 checksum of the source file |
| `ingestion_date` | DateTime | Yes | Date and time the document was ingested |
| `approval_status` | String | Yes | Indicates whether the document is approved for retrieval |

### 2.1 Example Document Metadata

The following example uses the known manifest values for POL-001. Unavailable values are explicitly marked as pending.

```json
{
  "source_id": "POL-001",
  "title": "Complaint Handling Procedure",
  "document_type": "Procedure",
  "category": null,
  "version": "2.0",
  "effective_date": "2026-01-01",
  "access_label": "Internal",
  "filename": null,
  "checksum": null,
  "ingestion_date": null,
  "approval_status": null
}
```

The example is an incomplete inventory record, not a valid ingestion-ready record.

## 3. Document Validation Rules

### DR-01 — Source Identifier

- `source_id` must not be empty.
- `source_id` must follow the approved identifier format.
- A source/version combination must uniquely identify a document version.

### DR-02 — Document Title

- `title` must not be empty.
- The title must correspond to the source document.

### DR-03 — Document Type

- `document_type` must be present.
- Allowed values for the supplied inventory are `Procedure`, `Matrix`, `Guidance`, and `Guide`.
- Additional types require approval.

### DR-04 — Category

- `category` must be present before ingestion.
- Category values must follow an approved business taxonomy.
- Missing categories must be flagged for clarification.

### DR-05 — Version

- `version` must not be empty.
- The version must match the approved manifest.
- Version values must be treated as identifiers rather than floating-point numbers.

### DR-06 — Effective Date

- `effective_date` must be a valid date.
- Future-effective versions must not be treated as currently effective.
- Historical eligibility must follow approved versioning rules.

### DR-07 — Access Label

Allowed values:

- `Internal`
- `Restricted`

Any unknown access label must cause the document to be rejected or quarantined until resolved.

### DR-08 — Filename

- `filename` must identify an existing source file.
- The file must be readable.
- The file must correspond to the manifest entry.

### DR-09 — Checksum

- `checksum` must be generated from the source file using SHA-256.
- A checksum must be recorded for every ingested document version.
- If the checksum changes without an approved document update, the document must be flagged for review.

### DR-10 — Approval Status

- Documents must have an explicit approval status.
- Only documents confirmed as approved and eligible may be used to support answers.
- Missing approval status must not be interpreted as approval.

### DR-11 — Ingestion Date

- `ingestion_date` must record when the document was added to the knowledge base.
- It must be stored in a consistent timestamp format.

## 4. Chunk-Level Metadata

A chunk is a retrievable section of a source document.

Each chunk must preserve sufficient information to identify its source, position, version, and access restrictions.

| Field | Data type | Required | Description |
|---|---|---|---|
| `chunk_id` | String | Yes | Unique identifier for the chunk |
| `source_id` | String | Yes | Identifier of the original document |
| `version` | String | Yes | Version of the source document |
| `section_name` | String | Yes | Heading or section represented by the chunk |
| `sequence_number` | Integer | Yes | Position of the chunk within the document version |
| `chunk_text` | String | Yes | Text content of the chunk |
| `access_label` | String | Yes | Access restriction inherited from the source |
| `document_type` | String | Yes | Type inherited from the source document |
| `effective_date` | Date | Yes | Effective date inherited from the source |
| `checksum` | String | Yes | Checksum of the original source file |

### 4.1 Example Chunk Metadata

This is an illustrative chunk record, not evidence that the section exists in POL-001.

```json
{
  "chunk_id": "POL-001-V2.0-CHUNK-002",
  "source_id": "POL-001",
  "version": "2.0",
  "section_name": "Escalating Complaints",
  "sequence_number": 2,
  "chunk_text": "[Extracted policy text]",
  "access_label": "Internal",
  "document_type": "Procedure",
  "effective_date": "2026-01-01",
  "checksum": "[SHA-256 checksum]"
}
```

## 5. Chunk Validation Rules

### CR-01 — Chunk Identifier

- Every chunk must have a unique `chunk_id`.
- The identifier must remain associated with the correct source version.
- Duplicate chunk identifiers must be rejected.

### CR-02 — Source Traceability

- Every chunk must reference an existing document using `source_id` and `version`.
- Orphaned chunks must not be indexed.

### CR-03 — Section Information

- `section_name` must identify the source section or a reliable equivalent locator.
- Missing source headings must be handled using a documented fallback locator.

### CR-04 — Sequence Number

- `sequence_number` must be a positive integer.
- Sequence numbers must preserve chunk order within a document version.
- Duplicate sequence numbers within the same document version must be rejected.

### CR-05 — Chunk Content

- `chunk_text` must not be empty.
- Chunk text must originate from the referenced source.
- Unsupported or fabricated content must not be indexed.

### CR-06 — Access Label

- Chunk `access_label` must match the source document's `access_label`.
- A chunk must not have weaker restrictions than its source.

### CR-07 — Version Consistency

- Chunk `version` must match the corresponding source document version.
- Chunk `checksum` must match the referenced source-file checksum.

## 6. Access Filtering

Access filtering must occur before retrieved content is made available for answer generation.

### 6.1 Internal Documents

Documents labeled `Internal` may be retrieved by users authorized for internal policy access.

### 6.2 Restricted Documents

Documents labeled `Restricted` may only be retrieved by users explicitly authorized for restricted policy access.

### 6.3 Access Rules

1. The service must verify user authorization.
2. Retrieval must apply the permitted `access_label` values.
3. Unauthorized chunks must not be returned.
4. Unauthorized chunks must not be used to generate answers.
5. The service must not reveal restricted content through citations or metadata.

Access filtering must use authorization-approved label sets, not simply compare one user label for exact equality.

## 7. Effective Version Filtering

Retrieval must use policy versions eligible for the requested context.

For questions about current policy:

- The document must be approved.
- `effective_date` must not be later than the applicable reference date.
- The version must be designated as current or otherwise eligible under approved versioning rules.
- Superseded versions must be excluded unless historical retrieval is authorized.

An effective date alone does not prove that a document is still current.

## 8. Citation Mapping

Every citation must be traceable to an actual retrieved chunk.

The citation process must support:

1. Identifying the retrieved `chunk_id`.
2. Resolving the chunk's `source_id` and `version`.
3. Identifying the document title.
4. Identifying the section using `section_name`.
5. Verifying that the cited evidence is accessible to the user.
6. Confirming that the citation corresponds to the answer's supporting evidence.

### Example Citation

**Illustrative format:**

Complaint Handling Procedure, Version 2.0, Section: Escalating Complaints.

The example section name is not verified against the actual source document.

## 9. Metadata Acceptance Criteria

**MAC-01:** Every indexed document has a valid `source_id`, `version`, `effective_date`, `access_label`, and `checksum`.

**MAC-02:** Every indexed chunk references an existing source document version.

**MAC-03:** Every chunk has a unique `chunk_id`.

**MAC-04:** Every chunk preserves its source `access_label`.

**MAC-05:** Every retrieved chunk can be traced to its source document and version.

**MAC-06:** No unauthorized document or chunk is returned during retrieval.

**MAC-07:** No unapproved document is used to generate an answer.

**MAC-08:** A checksum mismatch is detected and flagged before changed content is accepted.

**MAC-09:** A citation can be resolved to its source document, version, and section.

**MAC-10:** Missing required metadata prevents ingestion into the approved retrieval index.

## 10. Outstanding Decisions

The following must be confirmed:

- Business category taxonomy.
- Physical filenames for the five manifest entries.
- Actual document checksums.
- Approval-status source.
- Current-version designation.
- Handling of historical policy questions.
- Authorized role-to-access-label mapping.
- Fallback locators for documents without headings.

These items must be resolved before the metadata model is considered final.