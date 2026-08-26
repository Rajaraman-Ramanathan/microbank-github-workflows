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

INTEGRATION_STATUS="$(result_icon "$INTEGRATION_RESULT")"
SYSTEM_STATUS="$(result_icon "$SYSTEM_RESULT")"
DAST_STATUS="$(result_icon "$DAST_RESULT")"

{
  echo "# STAGE Release Validation"
  echo
  echo "| Validation | Result |"
  echo "|---|---|"
  echo "| Integration Tests | ${INTEGRATION_STATUS} |"
  echo "| System / E2E Tests | ${SYSTEM_STATUS} |"
  echo "| Burp Suite DAST | ${DAST_STATUS} |"
  echo
} >> "$GITHUB_STEP_SUMMARY"

FAILED=false

if [[ "$INTEGRATION_RESULT" != "success" ]]; then
  echo "::error::STAGE integration tests did not pass."
  FAILED=true
fi

if [[ "$SYSTEM_RESULT" != "success" ]]; then
  echo "::error::STAGE system/E2E tests did not pass."
  FAILED=true
fi

if [[ "$DAST_RESULT" != "success" ]]; then
  echo "::error::STAGE DAST validation did not pass."
  FAILED=true
fi

if [[ "$FAILED" == "true" ]]; then
  echo "## STAGE Release Gate: FAILED" >> "$GITHUB_STEP_SUMMARY"
  exit 1
fi

echo "## STAGE Release Gate: PASSED" >> "$GITHUB_STEP_SUMMARY"