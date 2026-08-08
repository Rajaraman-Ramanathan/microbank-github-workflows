# Checkmarx SAST

## Purpose

Runs a Checkmarx One Static Application Security Testing (SAST)
scan against the application source code and enforces the
organization-defined security threshold.

The action is intended to be used as a mandatory security gate
in enterprise CI/CD workflows.

---

## Responsibilities

This action:

- Validates the configured source directory.
- Executes a Checkmarx One SAST scan.
- Scans source code without requiring a packaged JAR.
- Applies the configured SAST vulnerability threshold.
- Generates a SARIF report when enabled.
- Exposes the Checkmarx scan ID.
- Exposes the generated SARIF report path.

---

## Non-Responsibilities

This action intentionally does not:

- Checkout the repository.
- Install or configure Git.
- Build the application.
- Compile the application.
- Build a JAR.
- Run unit tests.
- Run SonarQube.
- Perform dependency/SCA scanning.
- Build Docker images.
- Upload SARIF reports.
- Upload workflow artifacts.
- Generate GitHub workflow summaries.
- Publish notifications.

Repository checkout and report publication are responsibilities
of the calling workflow.

---

## Directory Structure

```text
actions/
└── checkmarx-sast/
    ├── action.yml
    └── README.md
```

The Checkmarx action is centrally maintained in the
`microbank-github-workflows` repository and is consumed by
application repositories through the reusable PR validation workflow.

---

## Authentication

The action uses Checkmarx One OAuth client credentials.

The credentials must be supplied through environment variables:

```text
CX_CLIENT_ID
CX_CLIENT_SECRET
```

These values must be stored as GitHub Actions secrets or supplied
through an approved enterprise secret-management mechanism.

The credentials must never be passed as plain-text workflow inputs
or committed to source control.

Example:

```yaml
env:
  CX_CLIENT_ID: ${{ secrets.CX_CLIENT_ID }}
  CX_CLIENT_SECRET: ${{ secrets.CX_CLIENT_SECRET }}
```

---

## Inputs

| Input | Required | Default | Description |
|---|---:|---|---|
| `project-name` | No | Repository name | Checkmarx One project name |
| `branch` | No | PR head/current branch | Checkmarx project branch |
| `base-uri` | Yes | — | Checkmarx One base URI |
| `tenant` | Yes | — | Checkmarx One tenant |
| `source-directory` | No | `.` | Source directory to scan |
| `sast-threshold` | No | `sast-critical=1;sast-high=1` | Blocking SAST threshold |
| `incremental` | No | `false` | Whether to use incremental SAST scanning |
| `generate-sarif` | No | `true` | Generate a SARIF report |
| `report-directory` | No | `.github/reports` | Report output directory |
| `additional-scan-params` | No | Empty | Organization-approved additional parameters |

---

## Outputs

| Output | Description |
|---|---|
| `scan-id` | Checkmarx One scan identifier |
| `sarif-file` | Path to the generated SARIF report |

Example:

```yaml
- id: checkmarx
  uses: ./actions/checkmarx-sast

- name: Display Checkmarx Scan ID
  run: |
    echo "Checkmarx Scan ID: ${{ steps.checkmarx.outputs.scan-id }}"
```

---

## SAST Threshold

The default policy blocks the pipeline when at least one
Critical or High SAST finding is detected:

```text
sast-critical=1;sast-high=1
```

The threshold can be overridden only when an approved workflow
requires a different policy.

Example:

```yaml
with:
  sast-threshold: "sast-critical=1;sast-high=5"
```

Any threshold override should be governed through the organization's
security review and exception process.

---

## Full Scan vs Incremental Scan

The default behavior is a full SAST scan:

```yaml
with:
  incremental: "false"
```

Full scans are preferred as the initial enterprise baseline because
they provide complete project analysis.

Incremental scanning can be enabled later when scan duration becomes
a meaningful CI optimization requirement and the Checkmarx project has
the required scan history.

Example:

```yaml
with:
  incremental: "true"
```

---

## SARIF Reports

SARIF generation is enabled by default:

```yaml
with:
  generate-sarif: "true"
```

The report is generated under:

```text
.github/reports/
```

The action exposes its location through:

```text
sarif-file
```

The action does not upload the SARIF file.

The calling workflow is responsible for deciding whether the report
should be:

- Uploaded to GitHub Code Scanning.
- Archived as a workflow artifact.
- Published to an enterprise security platform.

---

## Example Usage

```yaml
- name: Run Checkmarx SAST
  id: checkmarx
  uses: ./actions/checkmarx-sast
  env:
    CX_CLIENT_ID: ${{ secrets.CX_CLIENT_ID }}
    CX_CLIENT_SECRET: ${{ secrets.CX_CLIENT_SECRET }}
  with:
    base-uri: ${{ vars.CX_BASE_URI }}
    tenant: ${{ vars.CX_TENANT }}
    project-name: account-service
    source-directory: .
    sast-threshold: "sast-critical=1;sast-high=1"
    generate-sarif: "true"
```

---

## PR Validation Usage

Within the enterprise PR validation workflow, Checkmarx runs after
application verification and the SonarQube Quality Gate:

```text
Gitleaks
    ↓
Application Verification
    ├── Compile
    ├── Unit Tests
    ├── Coverage
    └── SonarQube Analysis
    ↓
SonarQube Quality Gate
    ↓
Checkmarx SAST
    ↓
OWASP Dependency Check
    ↓
Workflow Summary
```

A blocking Checkmarx finding causes the PR validation workflow to fail.

---

## Security Considerations

### Credentials

Never commit Checkmarx credentials to source control.

Use:

```text
CX_CLIENT_ID
CX_CLIENT_SECRET
```

through GitHub Actions secrets or an approved enterprise secret
management mechanism.

### Action Pinning

The third-party Checkmarx GitHub Action must be pinned to an immutable
commit SHA before the reusable workflow repository is promoted to
production.

Development may temporarily use a version tag while the approved
commit is being established.

### Policy Changes

Changes to:

- SAST thresholds
- Scan types
- Checkmarx configuration
- Security exceptions

should go through normal pull-request review and the organization's
security governance process.

---

## Why Checkmarx Does Not Receive a JAR

Checkmarx SAST analyzes the application's source code and project
context.

The PR validation workflow therefore does not build or publish a
JAR for Checkmarx.

The packaged JAR becomes important later in the CI/CD lifecycle,
particularly in Branch CI, where the verified binary is promoted
toward artifact repositories and container image creation.

---

## Production Hardening

Before production rollout:

1. Pin the Checkmarx GitHub Action to an approved commit SHA.
2. Store Checkmarx credentials in GitHub Actions secrets or the
   enterprise-approved secret-management system.
3. Establish organization-wide SAST severity thresholds.
4. Define the vulnerability exception process.
5. Configure SARIF publishing to GitHub Code Scanning if required.
6. Establish Checkmarx project naming and branch conventions.