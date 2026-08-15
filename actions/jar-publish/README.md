# Publish JAR

Publishes a previously verified Java application JAR to JFrog
Artifactory using Maven-compatible repository coordinates.

The action can optionally associate the uploaded artifact with JFrog
Build Info for CI/CD traceability.

## Purpose

The Publish JAR action provides the durable Java artifact publication
boundary in branch CI.

The intended flow is:

    Maven Build
        ↓
    JAR Verification
        ↓
    GitHub Actions Artifact
        ↓
    Download Artifact
        ↓
    JAR Verification
        ↓
    Docker Build
        ↓
    Container Security Controls
        ↓
    Security Gate
        ↓
    Publish JAR
        ↓
    JFrog Artifactory

The action publishes the exact JAR produced and verified by the
pipeline. It does not rebuild the application.

## Responsibilities

This action is responsible for:

- Validating that JFrog CLI is available.
- Validating the configured JFrog server.
- Validating connectivity to Artifactory.
- Validating the JAR artifact.
- Constructing the Maven-compatible repository path.
- Uploading the JAR to Artifactory.
- Verifying that the uploaded artifact exists remotely.
- Optionally associating the artifact with JFrog Build Info.
- Optionally publishing JFrog Build Info.
- Exposing the published artifact path and URL.

## Non-Responsibilities

This action does not:

- Build the Java application.
- Execute Maven.
- Run unit tests.
- Perform JAR security verification.
- Perform SCA.
- Build the Docker image.
- Scan the Docker image.
- Generate an SBOM.
- Publish the Docker image.
- Sign artifacts.
- Promote artifacts between environments.

These responsibilities belong to other actions or workflow stages.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `artifact-path` | Yes | — | Path to the verified executable JAR. |
| `repository` | Yes | — | JFrog Artifactory Maven repository key. |
| `group-id` | Yes | — | Maven groupId. |
| `artifact-id` | Yes | — | Maven artifactId. |
| `version` | Yes | — | Maven project version. |
| `server-id` | No | `setup-jfrog-cli-server` | JFrog CLI server configuration identifier. |
| `build-name` | No | `""` | JFrog Build Info name. |
| `build-number` | No | `""` | JFrog Build Info number. |
| `project-key` | No | `""` | JFrog project key. |

## Outputs

| Output | Description |
|---|---|
| `repository-path` | Repository-relative path of the published JAR. |

## JFrog CLI Prerequisite

The calling workflow is responsible for installing and configuring the
approved JFrog CLI version.

The recommended workflow pattern is:

```yaml
- name: Setup JFrog CLI
  uses: jfrog/setup-jfrog-cli@v4
  env:
    JF_URL: ${{ vars.JF_URL }}
    JF_ACCESS_TOKEN: ${{ secrets.JF_ACCESS_TOKEN }}