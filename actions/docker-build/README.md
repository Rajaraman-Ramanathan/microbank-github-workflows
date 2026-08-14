# Docker Build

Builds a container image from the application's Dockerfile using a
previously verified JAR artifact.

The action builds the image locally on the GitHub Actions runner and
does not push the image to a container registry.

## Purpose

The Docker Build action establishes the container build boundary between
the verified application JAR and the resulting container image.

The intended flow is:

    Maven Build
        ↓
    JAR Verification
        ↓
    GitHub Actions Artifact
        ↓
    Download JAR
        ↓
    JAR Verification + SHA-256
        ↓
    Docker Build
        ↓
    Container Verification
        ↓
    Container Vulnerability Scan
        ↓
    SBOM Generation
        ↓
    Security Gate
        ↓
    Docker Publish

The action builds the container image once. The same local image is then
used by downstream verification, vulnerability scanning, SBOM generation,
and publication steps within the same workflow job.

## Responsibilities

This action is responsible for:

- Validating the Docker build context.
- Validating the Dockerfile.
- Validating that the verified JAR exists.
- Validating that the JAR is not empty.
- Validating that the Docker CLI is available.
- Building the container image.
- Applying the requested image name and tag.
- Passing the verified JAR to the Docker build as a build argument.
- Exposing the resulting image reference and metadata.

## Non-Responsibilities

This action does not:

- Build the Java application.
- Run Maven.
- Validate the internal structure of the JAR.
- Perform vulnerability scanning.
- Generate an SBOM.
- Authenticate to a container registry.
- Push the image to a registry.
- Sign the image.
- Promote the image between environments.

These responsibilities belong to other actions or to the workflow.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `context` | No | `.` | Docker build context directory. |
| `dockerfile` | No | `Dockerfile` | Dockerfile path relative to the build context. |
| `image-name` | Yes | — | Container image name without registry or tag. |
| `image-tag` | Yes | — | Container image tag. |
| `jar-path` | Yes | — | Path to the previously verified JAR relative to the build context. |
| `build-args` | No | `""` | Additional organization-approved Docker build arguments. |

## Outputs

| Output | Description |
|---|---|
| `image` | Fully qualified local container image reference. |
| `image-name` | Container image name. |
| `image-tag` | Container image tag. |

## Build Contract

The action expects the Dockerfile to consume the application JAR through
the `JAR_FILE` build argument.

For example:

    ARG JAR_FILE
    COPY ${JAR_FILE} /app/application.jar

The JAR is therefore produced outside the Docker build:

    Maven
      ↓
    application.jar
      ↓
    JAR verification
      ↓
    Docker build

The Dockerfile must not execute Maven or rebuild the application.

## Image Naming

The action does not determine the organization's image-tagging strategy.

The calling workflow supplies:

    image-name

and:

    image-tag

For branch CI, the workflow should preferably use a commit-derived tag
rather than relying only on a mutable tag such as `latest`.

Example:

    microbank-account:sha-abc123...

The exact tagging policy belongs to the workflow.

## Usage

```yaml
- name: Build Container Image
  id: docker-build
  uses: ./.github/actions/docker-build
  with:
    context: .
    dockerfile: Dockerfile
    image-name: microbank-account
    image-tag: sha-${{ github.sha }}
    jar-path: artifacts/microbank-account.jar