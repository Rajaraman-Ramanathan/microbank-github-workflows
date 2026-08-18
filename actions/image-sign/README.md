# Sign Container Image

Signs an immutable container image digest using Cosign and an AWS KMS-backed
signing key, then verifies the resulting signature.

## Purpose

This action establishes cryptographic trust for container images entering the
release promotion lifecycle.

The action:

1. Validates that the image reference uses an immutable SHA256 digest.
2. Validates the AWS KMS Cosign key URI.
3. Installs the approved Cosign version.
4. Verifies registry access.
5. Signs the image using the AWS KMS-backed key.
6. Verifies the generated signature.
7. Exposes the signed image reference and digest.

The action does not build, scan, publish, or deploy container images.

## Prerequisites

The calling workflow must:

- Authenticate to the target container registry.
- Authenticate to AWS using an appropriate IAM role.
- Provide permission to use the configured AWS KMS signing key.

The workflow is responsible for AWS authentication. This action does not
configure AWS credentials.

## Inputs

| Input | Required | Default | Description |
|---|---:|---|---|
| `image` | Yes | — | Immutable image reference including SHA256 digest. |
| `kms-key-uri` | Yes | — | AWS KMS URI used by Cosign. |
| `cosign-version` | No | `3.0.2` | Approved Cosign version. |
| `additional-args` | No | `""` | Additional organization-approved Cosign arguments. |

## Outputs

| Output | Description |
|---|---|
| `image` | Immutable image reference that was signed. |
| `image-digest` | SHA256 digest of the signed image. |
| `verification` | Signature verification result. |

## AWS KMS

Cosign supports AWS KMS keys using an `awskms:///` URI.

Example:

```text
awskms:///arn:aws:kms:ap-south-1:123456789012:key/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx