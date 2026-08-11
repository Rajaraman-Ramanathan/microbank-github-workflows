# Gitleaks Scan

## Purpose

Scans the repository for hardcoded secrets using the organization's
standard Gitleaks configuration.

---

## Responsibilities

- Validate repository structure
- Execute Gitleaks
- Generate SARIF report
- Expose report location

---

## Non Responsibilities

This action intentionally does not:

- Checkout the repository
- Upload SARIF to GitHub
- Upload artifacts
- Generate workflow summaries

---

## Inputs

| Name | Required | Default |
|------|----------|---------|
| working-directory | No | `.` |
| config-path | No | `.gitleaks.toml` |
| report-format | No | `sarif` |

---

## Outputs

| Name | Description |
|------|-------------|
| report-file | Generated SARIF report |

---

## Example

```yaml
- uses: ./actions/gitleaks-scan

- uses: actions/upload-artifact@v4
  with:
    name: gitleaks-report
    path: ${{ steps.gitleaks.outputs.report-file }}