# Policy RAG Knowledge Service — Clarification Log

**Project:** Banking Complaint Management System  
**Feature:** Policy RAG Knowledge Service  
**Status:** Open for clarification

## 1. Purpose

This document records unclear requirements, proposed interpretations, unresolved decisions, and stakeholder responses.

Requirements must not be treated as approved simply because a possible implementation has been suggested.

## 2. Clarification Questions

| ID | Question | Current understanding / proposed decision | Status |
|---|---|---|---|
| CL-01 | Which policy documents are approved for retrieval? | Only approved documents may be used. The approved document list has not been supplied. | Open |
| CL-02 | Can archived or expired policies be searched? | Current approved documents are preferred; historical access requires a business decision. | Open |
| CL-03 | How many citations must an answer contain? | At least one valid citation for each substantive policy answer. | Proposed |
| CL-04 | What information must a citation include? | Document title and section or equivalent source locator. | Proposed |
| CL-05 | How many document chunks should retrieval return? | Three relevant chunks are proposed. | Proposed |
| CL-06 | What defines sufficient evidence? | Evidence must directly support the answer; the precise decision rule is unresolved. | Open |
| CL-07 | What happens when evidence is insufficient? | The service abstains instead of inventing an answer. | Defined in exercise |
| CL-08 | Should the service answer questions outside complaint policy? | No; unsupported questions receive a safe response. | Defined in exercise |
| CL-09 | What happens when approved policies conflict? | Abstain if no approved conflict-resolution rule exists. | Proposed |
| CL-10 | What is the performance requirement? | Five seconds is an illustrative target; measurement conditions are unconfirmed. | Open |
| CL-11 | Which users can access which documents? | Authorization must restrict access to protected documents. | Open |
| CL-12 | What metadata is mandatory? | Document ID, title, source locator, approval status, and chunk ID are proposed. | Proposed |
| CL-13 | What happens when the retrieval service is unavailable? | Return a controlled error without generating unsupported guidance. | Proposed |
| CL-14 | How should errors be represented? | Reuse the existing API's standardized error structure where applicable. | Proposed |
| CL-15 | Should the service retain questions and answers? | Logging, retention, and privacy requirements are not yet confirmed. | Open |
| CL-16 | How should updated policies replace older versions? | A version-management rule is required. | Open |

## 3. Decisions Supported by the Exercise

The following requirements are explicitly supported by the supplied exercise:

**Decision D-01 — Grounded Answers**

Answers must be based on approved policy documents.

**Decision D-02 — Citations**

Policy answers must show their supporting sources.

**Decision D-03 — Safe Abstention**

When sufficient evidence is unavailable, the service must not invent an answer.

**Decision D-04 — Unsupported Questions**

The service must not invent company policy for questions outside the approved information.

**Decision D-05 — Specification Before Implementation**

The specification must describe required behavior without prescribing technologies such as a specific vector database or language model.

## 4. Unresolved Decisions Requiring Approval

### CL-01 — Approved Documents

**Question:** Which policy documents are allowed?

**Impact:** Without an approved source list, retrieval eligibility cannot be finalized.

**Required decision:** Identify the approved policy collection and responsible owner.

### CL-02 — Archived Documents

**Question:** Can expired or archived documents be retrieved?

**Impact:** Historical documents may contradict current policies.

**Required decision:** Define whether archived policies are excluded or available for explicitly historical questions.

### CL-06 — Evidence Sufficiency

**Question:** How should the service determine whether evidence is sufficient?

**Impact:** This affects hallucination prevention and abstention behavior.

**Required decision:** Approve an evidence-sufficiency rule and corresponding evaluation cases.

### CL-10 — Performance

**Question:** Is a five-second response-time requirement acceptable?

**Impact:** Performance targets affect acceptance testing and service design.

**Required decision:** Confirm response-time target, percentile, workload, and test environment.

### CL-11 — Authorization

**Question:** Which roles may access which policy documents?

**Impact:** Incorrect access rules could expose restricted company information.

**Required decision:** Approve the access-control requirements.

### CL-16 — Policy Versioning

**Question:** How should superseded policy documents be handled?

**Impact:** The service may otherwise return outdated guidance.

**Required decision:** Define policy-version eligibility and historical access rules.

## 5. Decision Recording Template

When a coach or business stakeholder provides a decision, record:

- Clarification ID:
- Decision:
- Decision owner:
- Date:
- Related specification section:
- Impact on acceptance criteria:
- Status: Approved / Rejected / Deferred

## 6. Clarification Completion Criteria

The clarification process is complete when:

1. All blocking questions have an approved decision.
2. Approved decisions are reflected in `spec.md`.
3. Acceptance criteria reflect the final decisions.
4. Deferred items are clearly marked.
5. No proposed interpretation is presented as an approved requirement.