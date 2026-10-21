# Clarification Log

**Project:** Banking Complaint Resolution Agent  
**Feature:** Complaint intake, Human approval, investigation, AI supported recommendations,  
**Log owner:** Unknown  
**Status values:** Open, Answered, Deferred, Rejected, Superseded

## **CL-001: Human Approval Rules**

- **Category:** Workflow
- **Question:** Can the AI approve a refund or fee reversal?
- **Why it matters:** Important financial decisions should be done by human approval rather than AI
- **Source/owner:** Project Brief
- **Decision:** No, the Ai should be able to recommend an action, but an authorized human must approve it
- **Impact:** requires a human to review all sensitive financial remedies and liability determinations.
- **Affected requirements:** Decision Workflow
- **Status:** Answered
- **Decision date:** 2026-10-15

Unclear Categories:

## **CL-002: Evidence Scope**

- **Category:** Workflow
- **Question:** How should the AI assistant distinguish between customer claims, verified system facts, and retrieval policies?
- **Why it matters:** Later recommendations need to clearly separate facts, evidence, and generated phrasing to prevent hallucinated citations.
- **Source/owner:** Classification, Extraction, and Evidence
- **Decision:** The evidence must separate customer assertions, verify system facts (SQL/API), retrieve policy statements, identify missing information, and generate summary text.
- **Impact:** Makes sure there is audit compliance and strict traceability without mixing unstructured text with verified records in the system.
- **Affected requirements:** Classification, Extraction, and Evidence.
- **Status:** Answered
- **Decision date:** 2026-10-15

## **CL-003: Missing Data**

- **Category: Intake**
- **Question:** What system state must be triggered if an intake field is absent during validation?
- **Why it matters:** The incomplete submissions cannot be classified without having identifiers like transaction IDs or amounts.
- **Source/owner:** End-to-end processing
- **Decision:** If the required field (complaint ID, transaction ID, amount date, merchant, or authorization statement) is absent, the system sets the state to Information Needed.
- **Impact:** Prevents premature routing of malformed complaint submissions.
- **Affected requirements:** Intake Validation
- **Status:** Answered
- **Decision date:** 2026-10-15

## **CL-004: Evidence & Expectations**

- **Category:** AI Recommendations
- **Question:** What metadata needs to be attached when retrieving approved guidance with RAG?
- **Why it matters:** The audit trails require exact versions and source tracking to verify that the recommendations align with current bank procedures.
- **Source/owner:** Core Data Entities & RAG
- **Decision:** Policy evidence has to include metadata, including the document source ID, title, version, date, and section.
- **Impact:** Guarantees the recommendations point to a valid operational reference.
- **Affected requirements:** RAG Policy Retrieval & Citation Standards
- **Status:** Answered
- **Decision date:** 2026-10-15

## **CL-005: Failure Behavior**

- **Category:** Failure Behavior
- **Question:** How would the system respond when document retrieval returns 0 evidence or when external dependencies are unavailable?
- **Why it matters:** Unexamined fallback answers or silent services compromise compliance and safety.
- **Source/owner:** Quality & Safety Principles
- **Decision:** The system needs to decline to answer when evidence is insufficient and clearly communicate in unverified states.
- **Impact:** Stops baseless answers and makes sure operators are alerted immediately to the system.
- **Affected requirements:** System Error Handling
- **Status:** Answered
- **Decision date:** 2026-10-15

## **Decision summary**

| **ID** | **Outcome**               | **Specification effect**                                                                                              |
| ------ | ------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| CL-001 | Workflow                  | Established explicit status milestones to route complaints efficiently.                                               |
| CL-002 | Classification & Evidence | Mandates separation of claims from verified system facts and policy records for audits.                               |
| CL-003 | Intake Validation         | Triggers "Information Needed" state if the transaction field is empty or absent.                                      |
| CL-004 | RAG Policy Retrieval      | Requires attaching full metadata (source ID, title, version, date, and section) to all guidance.                      |
| CL-005 | System Error Handling     | Forces the system to decline answers and flag operators when the evidence is insufficient, or external services fail. |

**Domain Rules**

**DR-1** - **Verified Facts:**

Only information retrieved from approved banking systems may be treated as verified facts.

**DR-2 - Policy Governance:**

Only approved complaint policies may be used during recommendation generation.

**DR-3 - Human Approval;**

Refunds, fee reversals, compensation, and case closure require human approval.

**DR-4 - Evidence Requirement:**

Recommendations must include supporting facts and policy evidence.

**DR-5 Escalation**

Cases matching escalation criteria must be flagged for human review.

**DR-6 Auditability**

All investigation actions, recommendations, and approvals must be recorded.

**Measurable Success Criteria**

- 90% of investigations retrieve applicable policy evidence.
- 100% of generated recommendations contain source attribution.
- 100% of financial decisions receive human approval.
- Investigation summaries generated within 10 seconds for normal workloads.
- 100% of case actions recorded in the audit trail.

**Positive Scenarios**

**PS-1 Successful Investigation**

- Complaint exists.
- Customer data exists.
- Relevant policy found.
- Recommendation generated with supporting evidence.

**PS-2 Successful Escalation**

- Escalation criteria met.
- System recommends escalation.
- Reviewer approves escalation.

**PS-3 Successful Resolution**

- Evidence supports complaint outcome.
- Reviewer approves recommendation.
- Case is closed.

**Negative Scenarios**

**NS-1 Customer Not Found**

- Customer record unavailable.
- Investigation halted.

**NS-2 No Matching Policy**

- No policy found.
- Recommendation withheld.
- Manual review required.

**NS-3 Unauthorized Access**

- Unauthorized user attempts access.
- Access denied and logged.

**NS-4 Insufficient Evidence**

- Investigation lacks necessary information.
- Recommendation not produced.

**Edge Scenarios:**

**ES-1 Conflicting Information:**

Two systems provide different account or complaint details.

Expected Outcome:

- Flag inconsistency.
- Require analyst review.

**ES-2 Multiple Applicable Policies:**

Expected Outcome:

- Display all relevant policies.
- Allow reviewer assessment.

**ES-3 High Complaint Volume:**

Expected Outcome:

- System remains operational.
- Investigations continue within performance targets.

**ES-4 Policy Update During Investigation**

Expected Outcome:

- Active investigation records policy version used.
- Audit trail preserved.

**Security Constraints:**

- Users shall authenticate before accessing the system.
- Role-based access shall restrict visibility of complaint information.
- Only authorized users may approve financial decisions.
- Sensitive customer information shall be protected during storage and access.

**Privacy Constraints:**

- Only required customer data shall be displayed.
- Personal information shall only be visible to authorized personnel.
- Customer data shall only be used for complaint-handling purposes.

**Audit Constraints:**

- All investigation activities shall be logged.
- All evidence sources shall be recorded.
- All approvals, rejections, and overrides shall be recorded.
- Override actions require justification.

**Reliability Constraints:**

- System failures shall not cause loss of complaint records.
- Manual investigation shall remain available if AI services fail.
- Investigation progress shall be recoverable after temporary outages.
- System shall preserve integrity of facts, evidence, and audit records throughout the investigation lifecycle.