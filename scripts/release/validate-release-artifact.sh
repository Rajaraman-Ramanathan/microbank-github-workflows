#!/usr/bin/env bash

set -euo pipefail

echo "Validating release artifact..."

# ----------------------------------------------------------------
# Required values
# ----------------------------------------------------------------

if [[ -z "${IMAGE_REPOSITORY:-}" ]]; then
  echo "::error::Image repository must not be empty."
  exit 1
fi

if [[ -z "${IMAGE_REFERENCE:-}" ]]; then
  echo "::error::Image reference must not be empty."
  exit 1
fi

if [[ -z "${IMAGE_DIGEST:-}" ]]; then
  echo "::error::Image digest must not be empty."
  exit 1
fi

if [[ -z "${SOURCE_SHA:-}" ]]; then
  echo "::error::Source SHA must not be empty."
  exit 1
fi

if [[ -z "${DEV_ECR_REPOSITORY:-}" ]]; then
  echo "::error::DEV ECR repository must not be empty."
  exit 1
fi

# ----------------------------------------------------------------
# Validate image digest
# ----------------------------------------------------------------

if [[ ! "$IMAGE_DIGEST" =~ ^sha256:[a-f0-9]{64}$ ]]; then
  echo "::error::Invalid image digest."
  echo "::error::Digest: $IMAGE_DIGEST"
  exit 1
fi

# ----------------------------------------------------------------
# Validate immutable image reference
# ----------------------------------------------------------------

if [[ "$IMAGE_REFERENCE" != *@sha256:* ]]; then
  echo "::error::Image reference must use an immutable digest."
  echo "::error::Reference: $IMAGE_REFERENCE"
  exit 1
fi

METADATA_DIGEST="${IMAGE_REFERENCE##*@}"

if [[ "$METADATA_DIGEST" != "$IMAGE_DIGEST" ]]; then
  echo "::error::Image reference digest does not match image digest."
  echo "::error::Reference digest: $METADATA_DIGEST"
  echo "::error::Image digest: $IMAGE_DIGEST"
  exit 1
fi

# ----------------------------------------------------------------
# Validate source Git SHA
# ----------------------------------------------------------------

if [[ ! "$SOURCE_SHA" =~ ^([a-f0-9]{40}|[a-f0-9]{64})$ ]]; then
  echo "::error::Invalid source Git SHA."
  echo "::error::Source SHA: $SOURCE_SHA"
  exit 1
fi

# ----------------------------------------------------------------
# Extract repository from immutable image reference
#
# Example:
#
# 123456789012.dkr.ecr.ap-south-1.amazonaws.com/
# microbank/account-service@sha256:...
#
# becomes:
#
# microbank/account-service
# ----------------------------------------------------------------

IMAGE_REFERENCE_WITHOUT_DIGEST="${IMAGE_REFERENCE%@*}"

if [[ -z "$IMAGE_REFERENCE_WITHOUT_DIGEST" ]]; then
  echo "::error::Unable to extract repository from image reference."
  echo "::error::Image reference: $IMAGE_REFERENCE"
  exit 1
fi

IMAGE_REFERENCE_REPOSITORY="${IMAGE_REFERENCE_WITHOUT_DIGEST#*/}"

if [[ -z "$IMAGE_REFERENCE_REPOSITORY" ||
      "$IMAGE_REFERENCE_REPOSITORY" == "$IMAGE_REFERENCE_WITHOUT_DIGEST" ]]; then
  echo "::error::Unable to determine ECR repository from image reference."
  echo "::error::Image reference: $IMAGE_REFERENCE"
  exit 1
fi

# ----------------------------------------------------------------
# Validate metadata repository against image reference
# ----------------------------------------------------------------

if [[ "$IMAGE_REFERENCE_REPOSITORY" != "$IMAGE_REPOSITORY" ]]; then
  echo "::error::Image repository does not match image reference."
  echo "::error::Metadata repository: $IMAGE_REPOSITORY"
  echo "::error::Reference repository: $IMAGE_REFERENCE_REPOSITORY"
  exit 1
fi

# ----------------------------------------------------------------
# Validate release repository against expected DEV repository
# ----------------------------------------------------------------

if [[ "$IMAGE_REPOSITORY" != "$DEV_ECR_REPOSITORY" ]]; then
  echo "::error::Release image repository does not match DEV ECR repository."
  echo "::error::Release repository: $IMAGE_REPOSITORY"
  echo "::error::DEV ECR repository: $DEV_ECR_REPOSITORY"
  exit 1
fi

# ----------------------------------------------------------------
# Export validated outputs
# ----------------------------------------------------------------

echo "image-repository=$IMAGE_REPOSITORY" >> "$GITHUB_OUTPUT"
echo "image-reference=$IMAGE_REFERENCE" >> "$GITHUB_OUTPUT"
echo "image-digest=$IMAGE_DIGEST" >> "$GITHUB_OUTPUT"
echo "source-sha=$SOURCE_SHA" >> "$GITHUB_OUTPUT"

echo
echo "Release artifact validated successfully."
echo "Repository: $IMAGE_REPOSITORY"
echo "Image:      $IMAGE_REFERENCE"
echo "Digest:     $IMAGE_DIGEST"
echo "Source SHA: $SOURCE_SHA"