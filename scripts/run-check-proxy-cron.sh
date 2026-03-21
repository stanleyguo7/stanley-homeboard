#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/check-proxy-and-recover.env}"
LOG_FILE="${LOG_FILE:-$SCRIPT_DIR/check-proxy-and-recover.log}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

mkdir -p "$(dirname "$LOG_FILE")"
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') run ==="
  "$SCRIPT_DIR/check-proxy-and-recover.sh"
  rc=$?
  echo "exit_code=$rc"
  echo
  exit $rc
} >> "$LOG_FILE" 2>&1
