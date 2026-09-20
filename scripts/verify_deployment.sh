#!/usr/bin/env bash
set -euo pipefail
: "${BACKEND_URL:?Set BACKEND_URL, for example http://host/health}"
curl --fail --show-error --silent "${BACKEND_URL%/}/health"

