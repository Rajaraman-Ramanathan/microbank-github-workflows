#!/usr/bin/env bash

set -euo pipefail

ARTIFACT_ID="$1"
COMMIT_SHA="$2"

echo "${ARTIFACT_ID}-${COMMIT_SHA}"