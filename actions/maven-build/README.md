# Maven Build

## Purpose

Build a Java Spring Boot application using the Maven Wrapper and produce a trusted executable JAR.

This action is part of the **Microbank Enterprise CI/CD Platform** and is intended to be consumed by reusable workflows such as:

- PR Validation
- Branch CI
- Production Release
- Hotfix

---

## Responsibilities

- Validate Maven project structure
- Read Maven project metadata
- Compile the application
- Package an executable Spring Boot JAR
- Expose build metadata for downstream jobs

---

## Non-Responsibilities

This action intentionally **does not**:

- Execute unit tests
- Generate code coverage
- Run SonarQube analysis
- Perform secret scanning
- Run dependency vulnerability scans
- Upload GitHub artifacts
- Publish binaries to JFrog Artifactory / Sonatype Nexus
- Build Docker images
- Publish container images

---

## Inputs

| Name | Required | Default |
|------|----------|---------|
| working-directory | No | `.` |
| goals | No | `clean package` |
| additional-args | No | *(empty)* |

---

## Outputs

| Output | Description |
|---------|-------------|
| group-id | Maven groupId |
| artifact-id | Maven artifactId |
| project-version | Maven project version |
| artifact-file | Executable JAR filename |
| artifact-path | Executable JAR path |

---

## Example

```yaml
- name: Build Application
  id: build
  uses: ./actions/maven-build

- name: Display Build Metadata
  shell: bash
  run: |
    echo "Group ID        : ${{ steps.build.outputs.group-id }}"
    echo "Artifact ID     : ${{ steps.build.outputs.artifact-id }}"
    echo "Version         : ${{ steps.build.outputs.project-version }}"
    echo "Artifact Path   : ${{ steps.build.outputs.artifact-path }}"
```
