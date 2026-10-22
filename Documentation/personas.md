# Personas

## Persona 1: Complaint Analyst

### Responsibilities

- Receive and investigate customer complaints.
- Review customer account and transaction history.
- Identify and assess relevant policies.
- Evaluate AI-generated recommendations.
- Escalate cases when required.

### Goals

- Resolve complaints accurately and efficiently.
- Ensure recommendations comply with bank policies and regulations.
- Maintain complete and traceable evidence for review.
- Reduce investigation time while maintaining quality.

### Tasks

- Search customer and complaint records.
- Review supporting evidence and documents.
- Review applicable policy guidance.
- Validate retrieved information.
- Review and adjust AI-generated recommendations.
- Submit completed investigations for approval.

### Information Needs

- Complaint details
- Customer information
- Account and transaction history
- Applicable policy excerpts
- Investigation status
- AI recommendation rationale
- Escalation criteria and requirements

### Permissions

- View complaint records
- View customer records
- View transaction and account history
- View policy evidence
- Create and update investigation notes
- Submit cases for review

### Constraints

- Cannot approve refunds, fee reversals, or compensation decisions.
- Cannot close complaints requiring reviewer approval.
- Must provide supporting evidence for recommendations.
- Must use approved policy sources during investigations.

---

## Persona 2: Supervisor / Reviewer

### Responsibilities

- Review complaint investigations.
- Approve or reject recommendations.
- Review escalated cases.
- Ensure compliance with bank policies and regulations.
- Provide final approval for complaint resolutions.

### Goals

- Ensure complaint outcomes are accurate, fair, and compliant.
- Verify that evidence supports all recommendations.
- Minimize compliance and regulatory risk.
- Maintain consistency in complaint-handling decisions.

### Tasks

- Review verified facts and evidence.
- Review AI-generated analysis and recommendations.
- Approve or reject recommendations.
- Request additional investigation when required.
- Approve escalation outcomes.
- Review audit trails and investigation history.
- Justify overrides of analyst or AI recommendations.

### Information Needs

- Verified facts
- Policy evidence
- Investigation summary
- Analyst notes
- AI recommendation rationale
- Audit history
- Escalation details

### Permissions

- View all assigned complaint cases
- View investigation details and supporting evidence
- Approve recommendations
- Reject recommendations
- Modify recommendations
- Escalate complaints
- View audit records
- Close approved complaint cases

### Constraints

- Must justify recommendation overrides.
- Must review evidence before making a decision.
- Responsible for final complaint outcome.
- Cannot approve decisions without sufficient supporting evidence.
- Must comply with regulatory and policy requirements.

---

# Persona Summary

| Persona | Primary Responsibility | Key Decision Authority |
|----------|------------------------|-------------------------|
| Complaint Analyst | Investigate complaints and prepare recommendations | Can recommend and escalate cases |
| Supervisor / Reviewer | Review and approve complaint outcomes | Final approval and closure authority |

# Relationship Between Personas

### Complaint Analyst
- Conducts investigations.
- Collects and evaluates evidence.
- Reviews AI-assisted recommendations.
- Prepares proposed resolutions.

### Supervisor / Reviewer
- Validates investigation quality.
- Reviews evidence and recommendations.
- Makes final complaint decisions.
- Approves, rejects, modifies, or escalates cases.

This separation ensures that AI and analysts support the investigation process while final complaint outcomes remain under authorized human control.
