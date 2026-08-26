#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${ECR_REPOSITORY:-}" ]]; then
  echo "::error::ECR repository must not be empty."
  exit 1
fi

if [[ -z "${IMAGE_DIGEST:-}" ]]; then
  echo "::error::Image digest must not be empty."
  exit 1
fi

if [[ ! "$IMAGE_DIGEST" =~ ^sha256:[a-f0-9]{64}$ ]]; then
  echo "::error::Invalid image digest."
  echo "::error::Digest: $IMAGE_DIGEST"
  exit 1
fi

echo "Checking DEV ECR image..."

IMAGE_COUNT="$(
  aws ecr describe-images \
    --repository-name "$ECR_REPOSITORY" \
    --image-ids imageDigest="$IMAGE_DIGEST" \
    --query 'length(imageDetails)' \
    --output text
)"

if [[ "$IMAGE_COUNT" != "1" ]]; then
  echo "::error::Expected image digest was not found in DEV ECR."
  echo "::error::Repository: $ECR_REPOSITORY"
  echo "::error::Digest: $IMAGE_DIGEST"
  exit 1
fi

ACTUAL_DIGEST="$(
  aws ecr describe-images \
    --repository-name "$ECR_REPOSITORY" \
    --image-ids imageDigest="$IMAGE_DIGEST" \
    --query 'imageDetails[0].imageDigest' \
    --output text
)"

if [[ "$ACTUAL_DIGEST" != "$IMAGE_DIGEST" ]]; then
  echo "::error::DEV ECR returned an unexpected image digest."
  echo "::error::Expected: $IMAGE_DIGEST"
  echo "::error::Received: $ACTUAL_DIGEST"
  exit 1
fi

echo "DEV ECR image verified successfully."
echo "Repository: $ECR_REPOSITORY"
echo "Digest:     $ACTUAL_DIGEST"