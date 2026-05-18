#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "build" ]; then
  python3 -m backend.cli "${@:2}"
else
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
fi

