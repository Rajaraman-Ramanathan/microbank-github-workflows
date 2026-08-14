# Container Scan

Scans a locally built container image for known vulnerabilities using
Trivy and enforces the organization's container vulnerability threshold.

The action operates on the container image produced by the Docker Build
action and does not publish the image.

## Purpose

The Container Scan action establishes the vulnerability-management
boundary for the container image.

The intended flow is:

    Docker Build
        ↓
    Container Verification
        ↓
    Container Scan
        ↓
    SBOM Generation
        ↓
    Security Gate
        ↓
    Docker Publish

The scan is performed before the image is published to Amazon ECR.

## Responsibilities

This action is responsible for:

- Validating that Docker is available.
- Validating that the target image exists locally.
- Running Trivy against the container image.
- Scanning operating-system packages.
- Scanning application/library dependencies.
- Applying the configured vulnerability severity threshold.
- Generating a SARIF report when enabled.
- Verifying the generated SARIF report.
- Enforcing the container vulnerability security gate.
- Exposing the SARIF report location and scan result.

## Non-Responsibilities

This action does not:

- Build the container image.
- Build the Java application.
- Verify the JAR.
- Generate the SBOM.
- Authenticate to Amazon ECR.
- Push the image to ECR.
- Sign the image.
- Promote the image.
- Perform runtime/container integration testing.

These responsibilities belong to other actions or workflow stages.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `image` | Yes | — | Local container image reference to scan. |
| `severity-threshold` | No | `HIGH,CRITICAL` | Vulnerability severities that cause the security gate to fail. |
| `ignore-unfixed` | No | `false` | Whether vulnerabilities without a known fix should be excluded. |
| `report-directory` | No | `.github/reports` | Directory where the SARIF report is generated. |
| `generate-sarif` | No | `true` | Whether to generate a SARIF report. |
| `trivy-version` | No | `v0.36.0` | Approved Trivy version. Pin the underlying action to an immutable SHA for production. |
| `additional-args` | No | `""` | Additional organization-approved Trivy arguments. |

## Outputs

| Output | Description |
|---|---|
| `sarif-file` | Absolute path to the generated SARIF report. |
| `scan-result` | `passed`, `failed`, or `error`. |

## Scan Scope

The action performs vulnerability scanning for:

    os
    library

This allows the scan to identify vulnerabilities in both the container
operating-system packages and application/library dependencies.

The scan is performed against the actual built image rather than the
Maven project source tree.

## Severity Gate

The default policy is:

    HIGH
    CRITICAL

A vulnerability at or above the configured threshold causes the security
gate to fail.

For example:

    severity-threshold: "HIGH,CRITICAL"

means:

    LOW       → report
    MEDIUM    → report
    HIGH      → fail
    CRITICAL  → fail

The organization's policy can change the threshold through the action
input without modifying the action implementation.

## Unfixed Vulnerabilities

By default:

    ignore-unfixed: "false"

This means vulnerabilities without an available upstream fix are not
silently excluded from the scan.

If the organization explicitly approves ignoring unfixed vulnerabilities,
the workflow can set:

    ignore-unfixed: "true"

This should be treated as an explicit security-policy decision.

## SARIF Reporting

When SARIF generation is enabled, the action produces:

    .github/reports/trivy-container.sarif

The report is verified before the action completes.

The workflow can subsequently upload the SARIF report to GitHub Code
Scanning using the organization's approved SARIF upload action.

## Security Gate

The Trivy scan uses a non-zero exit code when vulnerabilities meet the
configured security threshold.

The action deliberately captures the scan result before enforcing the
security gate.

This allows the report to be generated and verified even when the scan
finds blocking vulnerabilities.

The effective sequence is:

    Trivy Scan
        ↓
    Report Generation
        ↓
    Report Verification
        ↓
    Security Gate
        ↓
    PASS / FAIL

## Usage

```yaml
- name: Scan Container Image
  id: container-scan
  uses: ./.github/actions/container-scan
  with:
    image: ${{ steps.docker-build.outputs.image }}
    severity-threshold: "HIGH,CRITICAL"
    ignore-unfixed: "false"