# Application Verification

## Purpose

Verify that a Java application satisfies the organization's engineering quality gates.

---

## Responsibilities

- Validate Maven project structure
- Compile the application
- Execute unit tests
- Generate JaCoCo coverage
- Enforce Maven verification rules
- Perform SonarQube analysis

---

## Non Responsibilities

This action intentionally **does not**:

- Checkout source code
- Install Java
- Scan for secrets
- Execute SAST
- Scan third-party dependencies
- Build Docker images
- Publish artifacts

---

## Inputs

| Name | Required | Default |
|------|----------|---------|
| working-directory | No | `.` |
| sonar-project-key | Yes | - |
| maven-goals | No | `verify` |
| additional-args | No | *(empty)* |

---

## Outputs

- surefire-report-directory
- jacoco-xml-report
- jacoco-html-report-directory
- sonar-report-task-file


---

## Example

```yaml
- uses: ./actions/setup-java
  with:
    java-version: "21"

- uses: ./actions/application-verification
  env:
    SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
  with:
    sonar-project-key: account-service
```