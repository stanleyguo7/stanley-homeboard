#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$REPO_DIR/apps/chat-lite"
PORT="${1:-8790}"
BRANCH="${CHAT_LITE_BRANCH:-main}"

cd "$REPO_DIR"

echo "[chat-lite] syncing latest code from GitHub..."
git fetch origin "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "[chat-lite] starting no-cache server on 0.0.0.0:${PORT}"
exec python3 "$REPO_DIR/scripts/chat_lite_server.py" --bind 0.0.0.0 --port "$PORT" --dir "$APP_DIR"
