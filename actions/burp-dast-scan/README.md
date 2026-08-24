
# Burp Suite DAST Scan

Runs a Burp Suite DAST CI-driven scan against a deployed application and
exposes the generated JUnit report for downstream release validation.

This action provides the standardized DAST integration point for the
Microbank reusable release workflow.

The action does not contain application-specific DAST rules or test logic.
Burp Suite owns the vulnerability scanning engine while the reusable
workflow owns orchestration and release gating.

---

## Purpose

DAST is executed against the deployed application in STAGE.

The release workflow uses the following sequence:

```text
Deploy to STAGE
      │
      ▼
Integration Tests
      │
      ▼
System / E2E Tests
      │
      ▼
Burp Suite DAST
      │
      ▼
STAGE Release Gate