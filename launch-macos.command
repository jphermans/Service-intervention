#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PORT="${INTERVENTION_PORT:-8000}"
DATA_DIR="${INTERVENTION_DATA_DIR:-$SCRIPT_DIR/data}"
DB_PATH="${INTERVENTION_DB:-$DATA_DIR/intervention_reports.sqlite3}"
mkdir -p "$DATA_DIR"

PYTHON="${INTERVENTION_PYTHON:-}"
if [ -z "$PYTHON" ]; then
    for candidate in \
        "$SCRIPT_DIR/runtime/python/bin/python3" \
        "$SCRIPT_DIR/runtime/python/bin/python" \
        /opt/homebrew/bin/python3 \
        /usr/local/bin/python3 \
        python3 python; do
        if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import sqlite3, http.server" >/dev/null 2>&1; then
            PYTHON="$candidate"
            break
        fi
    done
fi

if [ -z "$PYTHON" ]; then
    osascript -e 'display alert "Intervention Report" message "Python 3 with sqlite3 was not found. Install Python 3 or place a runtime under runtime/python/bin/python3." buttons {"OK"}' >/dev/null 2>&1 || true
    echo "Python 3 with sqlite3 was not found."
    echo "Install Python 3 or place a runtime under runtime/python/bin/python3."
    exit 1
fi

cd "$SCRIPT_DIR"
exec "$PYTHON" server.py --host 127.0.0.1 --port "$PORT" --db "$DB_PATH" --open-browser
