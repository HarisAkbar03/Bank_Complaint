# Approved Tool Catalogue — Exercise 5.1.2

**System:** Banking Complaint Resolution Assistant  
**Status:** Draft for coach review; not an authorization to deploy or enable tools  
**Source:** FDM Sprint 3 supporting document, *Approved Tool Catalogue and MCP Definitions*, supplied in the exercise.

## 1. Requirements review

The catalogue lists nine bounded tools. Tool boundaries must validate typed inputs and outputs, enforce authorization independently of the model, protect sensitive actions with explicit approval, fail without inventing data, and emit audit evidence. The implementation must reuse approved repositories, API and RAG services rather than duplicate them.

**Prerequisites:** Exercise 5.1.1 agent specification; prior-sprint API and retrieval contracts; business rules BR-004, BR-027, BR-029, BR-018 and BR-038 where applicable. These artifacts were not supplied in full and must be checked before sign-off.

## 2. Approved catalogue entries (from supplied reference)

| ID | Tool | Purpose | Inputs | Outputs | Allowed role | Controls |
|---|---|---|---|---|---|---|
| T-001 | `get_customer` | Retrieve a synthetic customer by customer_id | `customer_id:string` | customer record or not_found | Analyst, Supervisor | Read-only; BR-004/027 |
| T-002 | `get_accounts` | List accounts for a verified customer | `customer_id:string` | account summaries | Analyst, Supervisor | Read-only; minimize fields |
| T-003 | `get_complaint` | Retrieve complaint and status history | `complaint_id:string` | complaint details/history | Analyst, Supervisor | Read-only |
| T-004 | `search_policy` | Retrieve approved policy chunks | `query:string`, `filters:object`, `top_k:integer` | ranked evidence with metadata | Analyst, Supervisor | Current version/access filters |
| T-005 | `create_case_note` | Add analyst note | `complaint_id:string`, `note:string`, `evidence_refs:array` | note ID/audit event | Analyst, Supervisor | Parameterized; no secrets |
| T-006 | `request_approval` | Request approval for current proposed action | `complaint_id:string`, `action:string`, `parameters:object`, `evidence_refs:array` | approval request ID/status | Analyst | Case-specific; BR-029 |
| T-007 | `record_approval_decision` | Approve/reject request | `approval_id:string`, `decision:string`, `reason:string` | decision/audit event | Supervisor | Human only |
| T-008 | `update_complaint_status` | Apply allowed status transition | `complaint_id:string`, `target_status:string`, `reason:string` | new status/audit event | Authorized role | Transition validation |
| T-009 | `close_complaint` | Close case after evidence/approval validation | `complaint_id:string`, `resolution:string`, `communication_date:string`, `evidence_refs:array` | closed case/audit event | Supervisor | Sensitive; BR-018/038 |

## 3. Proposed boundary and flow design (subject to approval)

1. Agent requests an approved tool using a typed input payload.
2. Trusted application context supplies authenticated caller identity, role, customer verification and authorization scope **outside** model-controlled arguments.
3. Tool gateway validates the schema, role, resource-level permissions, and any applicable policy/version constraints.
4. Adapter calls the existing repository or retrieval service; write operations use existing transaction and approval mechanisms.
5. Boundary returns a minimal typed result or controlled error; emits an audit record with correlation ID, tool name, caller, outcome and references (never secrets or raw sensitive payloads).
6. Agent cites returned evidence or abstains/escalates when evidence or authorization is insufficient.

**MCP:** If exposed through MCP in a later exercise, the MCP server must enforce the same checks; MCP tool registration does not confer authorization. No MCP server is implemented by this catalogue.

## 4. Safety and operational constraints

- **Read-only:** T-001 through T-004 must not mutate data. T-002 requires verified-customer context. T-004 must enforce approved/current document versions and access labels before returning chunks.
- **Writes:** T-005 through T-009 require authenticated, authorized service-side execution, idempotency/concurrency handling as applicable, durable audit evidence, and transaction-safe failures.
- **Human-only:** T-007 is callable only by an authenticated human supervisor through a trusted workflow, never as an autonomous model action.
- **Closure:** T-009 must validate required evidence and approvals before any closure; no implicit approval.
- **Evidence:** T-004 returns source/chunk identifiers and metadata; the model must not treat retrieval scores as proof of factual correctness.
- **No secrets or real customer data:** Use synthetic fixtures in tests and submissions.

## 5. Open questions / ambiguities (record before implementation)

| ID | Question | Proposed handling until resolved |
|---|---|---|
| A-01 | Exact field names and response models for customer/account/complaint repositories? | Confirm against prior API contracts; do not assume fields. |
| A-02 | How are caller identity, verification and resource permissions conveyed? | Trusted context only; deny if missing. |
| A-03 | Exact current-version and access-label filtering rules for RAG? | Deny unauthorized evidence; confirm index filtering behavior. |
| A-04 | Does T-003 include a separate status-event repository? | Confirm existing service contract. |
| A-05 | What status values and transitions are approved for T-008? | Reuse existing transition rules; do not invent transitions. |
| A-06 | What constitutes sufficient evidence/approval for T-009? | Block closure pending BR-018/038 confirmation. |
| A-07 | Which roles are 'Authorized role' for T-008? | Deny by default pending role matrix. |
| A-08 | Are tool output schemas and error codes standardized in 5.1.1? | Draft common envelope below; obtain coach approval. |
| A-09 | What audit service, retention policy and correlation ID format are mandated? | Use approved logging/audit service; avoid sensitive logs. |
| A-10 | What is the required format and timezone for communication_date? | Propose ISO 8601 date; verify with owner. |
| A-11 | How should duplicate requests and retries be handled for write tools? | Avoid blind retries; require idempotency design. |

## 6. Proposed contract conventions (not specified by FDM reference)

`tool_schemas.json` supplies **draft** JSON Schema input/output contracts. Input types follow the supplied reference; output envelopes and detailed record fields are proposed placeholders for review. Every result uses `status` (`success`, `not_found`, `error`), an optional `data` object or array, an optional `error` with stable code/message, and optional `audit_event_id`. A `not_found` result is not authorization to reveal whether a protected resource exists. A model must not provide trusted caller context itself.

## 7. Testing and review evidence plan

- **Normal:** authorized synthetic lookup; policy evidence includes chunk ID; authorized write creates audit event.
- **Boundary:** empty/invalid identifiers, excessive `top_k`, missing verification, wrong role, invalid transition, duplicate request.
- **Failure:** repository timeout, vector index unavailable, missing approved evidence, audit failure, stale approval, failed transaction.
- **Security:** prompt-supplied role spoofing, cross-customer access, restricted policy leakage, autonomous supervisor approval.

**Evidence to capture:** schema validation results, unit/integration test output, redacted audit samples, defect list, PR link and coach review. No test execution is claimed in this design-only deliverable.

## 8. Dependency handover to 5.2.1

Implement T-001 through T-004 as thin SQL/RAG lookup adapters in `src/agents/tools.py` and independently test in `tests/test_tools.py`. Match these schemas after reviewing the actual API/repository contracts. Preserve service-side authorization, filtering, citations and controlled errors. T-005 through T-009 remain catalogue definitions and must not be enabled as autonomous actions by this handover.

## 9. Submission checklist

- [x] Catalogue entries documented
- [x] Draft typed schemas and error matrix prepared
- [x] Open questions and constraints documented
- [ ] Review against 5.1.1 and prior contracts
- [ ] Run schema validation and negative tests against implementation
- [ ] Update project README/architecture and capture PR evidence
- [ ] Coach approval before merge
