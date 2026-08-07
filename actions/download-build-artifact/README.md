# Download Build Artifact

## Purpose

Download a previously uploaded GitHub Actions artifact.

---

## Responsibilities

- Download workflow artifacts
- Verify download
- Make artifacts available for downstream jobs

---

## Non Responsibilities

- Build artifacts
- Validate artifacts
- Publish artifacts
- Rename files
- Scan artifacts

---

## Inputs

| Name | Required | Default |
|------|----------|---------|
| artifact-name | Yes | - |
| destination-path | No | artifacts |

---

## Outputs

None.