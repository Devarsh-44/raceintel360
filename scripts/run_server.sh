#!/usr/bin/env bash
set -e
# Default to SQLite if not set
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./raceintel.db}"
# Prefer ./cache locally; HF Spaces should override to /tmp
export FASTF1_CACHE="${FASTF1_CACHE:-./cache}"

uvicorn api.main:app --host 0.0.0.0 --port 8000
