# Policy rules

Rules that every change to `policies/`, `skills/` and agent code must follow. Prelint checks each pull request against this file and against the decisions in [docs/adr/](../docs/adr/).

A pull request that breaks a **MUST** rule must not be merged. Each rule has an ID so a review can cite it.

## What agents say

- **PR-01 Never promise coverage.** A policy or skill MUST NOT promise that insurance, Medicare, Medicaid (Medi-Cal) or any other program will pay. It may explain what a program *can* cover and who decides, and it MUST point the family to the program or their case worker to confirm.
- **PR-02 Never give medical advice.** A policy or skill MUST NOT tell a Client to start, stop, change, skip or double a medication, or diagnose a symptom. It MUST direct medical questions to the Client's doctor or pharmacist. A medical-advice request is logged (Baseline Rule).
- **PR-03 No binding promises.** Agents MUST NOT promise refunds, discounts, fee waivers or visit times that a tool has not confirmed.
- **PR-04 Cite sources.** A policy written from research MUST list its sources, with links, and the date they were checked.

## Safety and escalation

- **PR-10 Guardian alone escalates** ([ADR 0001](../docs/adr/0001-guardian-owns-escalation.md)). Only Guardian may decide Severity or start an Escalation. Companion, Coordinator and Specialists may only raise a Flag. Code that lets any other agent page the On-call Human, or change a Severity, breaks this rule.
- **PR-11 Severity can only go up.** Guardian's code rules set a minimum Severity. LLM judgment may raise it, but MUST NOT lower it.
- **PR-12 Baseline Rules cannot be removed.** A change MUST NOT disable or weaken these Baseline Rules:
  - Emergency triggers (fall with injury, chest pain, breathing trouble) always page the On-call Human.
  - Self-harm language always pages the On-call Human.
  - Medical-advice requests are deflected and logged.
  - Families are always informed, even when the Client asks otherwise.
- **PR-13 The kill switch only tightens.** Agents and automated code may pause, disable or lower limits at once. Loosening a control (re-enabling or raising a limit) MUST need a human, and every change MUST log who made it and why.

## Privacy and verification

- **PR-20 Verified Family Contacts only.** Client details (health, address, door code, visit schedule) MAY be shared only with a Family Contact whose phone number matches the care plan. Anyone else gets general information only.
- **PR-21 No secrets in the repo.** API keys, tokens and `.env` or `agent_config.yaml` files MUST NOT be committed. Use `.env` locally and GitHub Actions secrets in CI.
- **PR-22 Synthetic data only.** Seed and test data MUST be fictional. Phone numbers use the 555 range.

## Process

- **PR-30 A human approves every policy change** (W04). A PR that changes `policies/` MUST come from an approved proposal, recorded in the PR description.
- **PR-31 Risky skills need a human.** A new or changed skill that touches health, money, personal data, escalation rules or outbound contact MUST be approved by a human before merge.
