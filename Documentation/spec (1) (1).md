**Banking Specification**

**Problem Statement:**

The system will help employees of the bank manage customer complaints and develop an appropriate response based on the complaint.

**Functional Requirements/Scope:**

1-Customer Complaints:

The system shall retrieve customer complaints and information.

2-Fact Verification:

The system should distinguish operational facts from the generated content.

3-Evidecne Retrieval:

The system should retrieve document/complaints from all the sources (mobile app, portal etc.).

4- Detailed Overview:

The system should give a detailed overview of the analyst to review.

5-Escalation Recommendation:

The system should identify conditions that require escalation according to business rules and regulations.

7-Recommendation:

The system should generate a draft recommendation using verified facts and policy evidence.

**Non-goals:**

1-Automated Decision-Making:

The assistant will not execute any final financial compensation, refunds, or account adjustments without review and approval by a human.

2-Direct customer-facing communication:

The assistant will not interact directly with customers with any outward-facing communications; it should only act as an internal advisory tool for analysts.

3-Replacing the core banking transaction systems:

Cannot replace core systems, transaction processing, or serve as a permanent system of record for bank transactions.

4-No Use of Production or Real Customer Data:

The system will only use synthetic datasets (customers, accounts, complaints, transactions, and service requests).

5\. No Exhaustive Product Line Scope:

Implementation is scoped to specifically target complaint patterns such as fee-review processing.

**Actors:**  
<br/>1- Complaint Analyst – Investigates complaints and prepares recommendations

2- Supervisor/Reviewer - Reviews and approves, rejects or requests changes

3- Customer – Submits complaints and receives the final response

4- Specialists – Handle escalated issues requiring a specialized review  
<br/>

**Preconditions:**

Before the AI assistant can investigate a complaint:

- Only synthetic or approved training data is used in this project
- A complaint must have been submitted and recorded in the system and all information must be provided before being investigated, missing information but be facts and not fabricated by the AI
- Only authorized employees can access information or perform certain actions; the AI Assistant has limited access.
- The AI Assistant must use approved banking policy documents and how where the information came from
- Actions that require supervisor approval cannot happen until that approval has been recorded and verified.

**Core Flows:**

1\. Case Initialization & Ingestion

2\. Automated Triage & Policy Retrieval

3\. Analyst Review & Modification

4\. Human Overview & Approval Gate

5\. Final Resolution & Audit Logging

**Business Rules:**

- The system should give recommendations based on business policy(s).
- The system should retrieve verified facts only.
- Every recommendation should mention the supporting facts and policy sources.
- The system shall not make final complaint decisions.
- A case cannot be closed until review is completed.
- Certain complaints must be escalated automatically.

**Error conditions:**

- Customer data not found.
- Complaint ID does not exist.
- No policy documents can be retrieved.
- Multiple systems provide contradictory information.
- AI service fails while generating analysis.
- Attempt to close case without reviewer approval.

**NFRs**

- Secure audit logging for every interaction, retrieved document reference, and analyst override.
- The security & privacy of customer PII and financial data need to be handled in accordance with banking data privacy regulations.
- The reliability of viewing core case management views needs to be accessible even after AI-generated services experience degradation.

**High-level interface expectations:**

- IE-1: The system shall provide a dashboard displaying complaint investigation details.

Complaint ID

Customer Information

Complaint Status

Investigation Progress

Assigned Analyst

- IE-2: Evidence Separation: The interface shall clearly separate information into four sections:

Plain Text

Verified Facts

Policy Evidence

System Analysis

Human Decisions

- IE-3: Investigation Workflow Guidance: The interface shall indicate the current step of the investigation process.

- IE-4: Missing Information Alerts: The interface shall prominently display missing or incomplete information.

- IE-5: Recommendation View: The interface shall display system-generated recommendations separately from human decisions.
- IE-6: Review and Approval Controls: Reviewers shall be able to:

Approve recommendation

Reject recommendation

Modify recommendation

Request additional investigation

- IE-7: Search and Case Retrieval: Users shall be able to search for cases using:

Complaint ID

Customer ID

Case Status

Date Range