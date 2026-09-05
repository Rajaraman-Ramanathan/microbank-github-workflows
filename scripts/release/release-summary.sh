#!/usr/bin/env bash

set -euo pipefail

result_icon() {
  case "$1" in
    success)
      echo "✅ Passed"
      ;;
    failure)
      echo "❌ Failed"
      ;;
    cancelled)
      echo "⚠️ Cancelled"
      ;;
    skipped)
      echo "⏭️ Skipped"
      ;;
    *)
      echo "❓ Unknown"
      ;;
  esac
}

echo "Generating release summary..."

{
  echo "# Release Summary"
  echo

  echo "## Release Artifact"
  echo
  echo "| Property | Value |"
  echo "|---|---|"
  echo "| Source SHA | ${SOURCE_SHA} |"
  echo "| Image Repository | ${IMAGE_REPOSITORY} |"
  echo "| Image Digest | ${IMAGE_DIGEST} |"
  echo

  echo "## Promotion"
  echo
  echo "| Environment | Result |"
  echo "|---|---|"
  echo "| DEV Image Verification | $(result_icon "$VERIFY_DEV_RESULT") |"
  echo "| DEV → STAGE Promotion | $(result_icon "$PROMOTE_STAGE_RESULT") |"
  echo "| STAGE → PROD Promotion | $(result_icon "$PROMOTE_PROD_RESULT") |"
  echo

  echo "## Deployment"
  echo
  echo "| Environment | Result |"
  echo "|---|---|"
  echo "| DEV Deployment | $(result_icon "$DEPLOY_DEV_RESULT") |"
  echo "| DEV Smoke Test | $(result_icon "$DEV_SMOKE_RESULT") |"
  echo "| STAGE Deployment | $(result_icon "$DEPLOY_STAGE_RESULT") |"
  echo "| PROD Deployment | $(result_icon "$DEPLOY_PROD_RESULT") |"
  echo

  echo "## STAGE Validation"
  echo
  echo "| Validation | Result |"
  echo "|---|---|"
  echo "| Integration Tests | $(result_icon "$INTEGRATION_RESULT") |"
  echo "| System / E2E Tests | $(result_icon "$SYSTEM_E2E_RESULT") |"
  echo "| Burp Suite DAST | $(result_icon "$DAST_RESULT") |"
  echo

  echo "## PROD Validation"
  echo
  echo "| Validation | Result |"
  echo "|---|---|"
  echo "| Argo Rollout Validation | $(result_icon "$VALIDATE_PROD_RESULT") |"
  echo "| PROD Smoke Tests | $(result_icon "$PROD_SMOKE_RESULT") |"
  echo

  echo "## Immutable Release"
  echo
  echo "| Property | Value |"
  echo "|---|---|"
  echo "| PROD Image Reference | ${PROD_IMAGE_REFERENCE} |"
  echo "| PROD Image Digest | ${PROD_IMAGE_DIGEST} |"
  echo

  echo "## Release Outcome"
  echo

  if [[ "$RELEASE_STATUS" == "success" ]]; then
    echo "### ✅ Release Successful"
    echo
    echo "The release passed all required promotion, deployment, and validation stages."
  else
    echo "### ❌ Release Failed"
    echo
    echo "One or more required release stages did not complete successfully."
  fi

} >> "$GITHUB_STEP_SUMMARY"

echo "Release summary generated successfully."