# Publish Docker Image

Publishes a previously built, verified, scanned, and security-gated
container image to Amazon Elastic Container Registry (ECR).

The action does not build or modify the container image contents.

## Purpose

The Publish Docker Image action provides the container publication
boundary in branch CI.

The intended flow is:

    Maven Build
        ↓
    JAR Verification
        ↓
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
    Publish Docker Image
        ↓
    Amazon ECR

The image supplied to this action must already have passed the required
CI security controls.

## Responsibilities

This action is responsible for:

- Validating that Docker is available.
- Validating the ECR registry configuration.
- Validating the local container image.
- Applying the target ECR repository and tag.
- Publishing the image to ECR.
- Extracting the immutable image digest.
- Exposing the published image reference.
- Exposing the immutable image digest.

## Non-Responsibilities

This action does not:

- Build the Docker image.
- Build the Java application.
- Verify the JAR.
- Scan the image for vulnerabilities.
- Generate an SBOM.
- Authenticate to AWS.
- Configure AWS credentials.
- Sign the image.
- Promote the image between environments.
- Deploy the image to Kubernetes.

These responsibilities belong to other actions or workflow stages.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `image` | Yes | — | Local container image reference to publish. |
| `registry` | Yes | — | Amazon ECR registry hostname. |
| `repository` | Yes | — | Amazon ECR repository name. |
| `tag` | Yes | — | Container image tag to publish. |

## Outputs

| Output | Description |
|---|---|
| `image` | Fully qualified ECR image reference including the tag. |
| `image-digest` | Immutable ECR image digest. |
| `image-reference` | Fully qualified immutable image reference using the digest. |

## AWS Authentication

The calling workflow is responsible for configuring AWS credentials
and authenticating Docker against ECR.

The action does not receive AWS access keys or AWS session credentials
as inputs.

A typical workflow sequence is:

```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-region: ap-south-1
    role-to-assume: ${{ secrets.CI_ECR_ROLE_ARN }}

- name: Login to Amazon ECR
  id: ecr-login
  uses: aws-actions/amazon-ecr-login@v2