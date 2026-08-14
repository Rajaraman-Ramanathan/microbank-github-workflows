
# Container Verification

Verifies a locally built container image before vulnerability scanning,
SBOM generation, and publication.

The action performs deterministic image-level validation without running
a vulnerability scanner or publishing the image.

## Purpose

The Container Verification action establishes a validation boundary
between the Docker build and the container security controls.

The intended flow is:

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

The action verifies that the expected image exists locally and that its
basic container configuration is valid before downstream security
controls operate on it.

## Responsibilities

This action is responsible for:

- Validating that the Docker CLI is available.
- Verifying that the expected image exists locally.
- Retrieving the image ID.
- Verifying that the image has a non-zero size.
- Retrieving the image digest when available.
- Optionally validating the expected runtime user.
- Verifying that the image has an ENTRYPOINT or CMD.
- Exposing image metadata for downstream workflow steps.

## Non-Responsibilities

This action does not:

- Build the container image.
- Run Maven.
- Validate the JAR.
- Perform vulnerability scanning.
- Generate an SBOM.
- Push the image to a registry.
- Sign the image.
- Promote the image.
- Perform application integration testing.

Those responsibilities belong to other actions or workflow stages.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `image` | Yes | — | Local container image reference to verify. |
| `expected-user` | No | `""` | Expected container runtime user. When provided, the image must specify this user. |

## Outputs

| Output | Description |
|---|---|
| `image-id` | Docker image ID. |
| `image-digest` | Image content digest when available locally. |
| `image-size` | Image size in bytes. |

## Verification Checks

### Docker CLI

The action first verifies that Docker is available:

    command -v docker

The action then reports the Docker version.

The action does not install Docker.

The workflow or runner environment is responsible for providing Docker.

### Image Existence

The action verifies that the requested image exists locally:

    docker image inspect "$IMAGE"

The action fails if the image cannot be inspected.

### Image ID

The action retrieves the image ID:

    docker image inspect --format '{{.Id}}' "$IMAGE"

An empty image ID causes the action to fail.

### Image Size

The action verifies that the image has a non-zero size.

A zero-byte image is considered invalid and causes the action to fail.

### Image Digest

The action retrieves the repository digest when available.

The digest is useful because it represents the immutable content identity
of a container image.

Example:

    sha256:abc123...

The digest output may be empty for a locally built image that has not yet
been associated with a registry repository digest.

The action therefore does not fail solely because a local image has no
repository digest.

### Runtime User

The workflow can optionally provide:

    expected-user

For example:

```yaml
- name: Verify Container Image
  uses: ./.github/actions/container-verification
  with:
    image: ${{ steps.docker-build.outputs.image }}
    expected-user: "10001"