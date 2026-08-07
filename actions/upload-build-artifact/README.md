# Upload Build Artifact

## Purpose

Uploads artifacts for consumption by downstream jobs within the same GitHub Actions workflow.

---

## Responsibilities

- Validate artifact existence
- Upload artifact to GitHub Actions
- Configure retention period
- Configure compression

---

## Non Responsibilities

This action intentionally **does not**:

- Build artifacts
- Scan artifacts
- Publish to JFrog Artifactory
- Publish to Sonatype Nexus
- Publish Docker images
- Rename artifacts
- Compress artifacts manually

---

## Inputs

| Name | Required | Default |
|------|----------|---------|
| artifact-name | Yes | - |
| artifact-path | Yes | - |
| retention-days | No | 1 |
| compression-level | No | 6 |

---

## Outputs

None.

---

## Example

```yaml
- name: Upload Trusted Binary
  uses: ./actions/upload-build-artifact
  with:
    artifact-name: account-service-jar
    artifact-path: target/account-service-1.0.0.jar
```