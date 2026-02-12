#!/usr/bin/env bash
set -euo pipefail

GATEWAY_PORT="8000"
WEBUI_PORT="5173"

echo "==> Stopping gateway on :$GATEWAY_PORT..."
if command -v lsof >/dev/null 2>&1; then
  PIDS="$(lsof -t -iTCP:"$GATEWAY_PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${PIDS}" ]]; then
    echo " - Killing PIDs: $PIDS"
    kill -TERM $PIDS 2>/dev/null || true
    sleep 0.3
    kill -KILL $PIDS 2>/dev/null || true
  else
    echo " - Not running"
  fi
else
  pkill -f "uvicorn.*gateway:app" 2>/dev/null && echo " - Killed" || echo " - Not running"
fi

echo "==> Stopping web UI on :$WEBUI_PORT..."
if command -v lsof >/dev/null 2>&1; then
  PIDS="$(lsof -t -iTCP:"$WEBUI_PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${PIDS}" ]]; then
    echo " - Killing PIDs: $PIDS"
    kill -TERM $PIDS 2>/dev/null || true
    sleep 0.3
    kill -KILL $PIDS 2>/dev/null || true
  else
    echo " - Not running"
  fi
else
  pkill -f "vite" 2>/dev/null && echo " - Killed" || echo " - Not running"
fi

echo "Done."
