#!/usr/bin/env bash
# Start the Atlas Copco Intervention Report local server.
#
# Portable/offline layout:
#   ./serve.sh                    # serves on port 8000 and opens the browser
#   ./serve.sh 3000               # serves on port 3000 and opens the browser
#   ./serve.sh --no-browser       # serves on port 8000 without opening the browser
#   INTERVENTION_PYTHON=/path/to/python ./serve.sh
#
# The SQLite database is stored in ./data/ so the whole folder can live on a USB stick.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PORT=8000
OPEN_BROWSER=true
DATA_DIR="${INTERVENTION_DATA_DIR:-$SCRIPT_DIR/data}"
DB_PATH="${INTERVENTION_DB:-$DATA_DIR/intervention_reports.sqlite3}"
PYTHON_HINT="${INTERVENTION_PYTHON:-}"

for arg in "$@"; do
    case "$arg" in
        --no-browser) OPEN_BROWSER=false ;;
        -h|--help)
            sed -n '1,14p' "${BASH_SOURCE[0]:-$0}"
            exit 0
            ;;
        *)
            if [[ "$arg" =~ ^[0-9]+$ ]]; then
                PORT="$arg"
            else
                echo "Unknown argument: $arg"
                echo "Usage: $0 [port] [--no-browser]"
                exit 1
            fi
            ;;
    esac
done

PYTHON="${PYTHON_HINT}"
if [ -z "$PYTHON" ]; then
    for candidate in \
        "$SCRIPT_DIR/runtime/python/bin/python3" \
        "$SCRIPT_DIR/runtime/python/bin/python" \
        python3 python py; do
        if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import sqlite3, http.server" >/dev/null 2>&1; then
            PYTHON="$candidate"
            break
        fi
    done
fi

if [ -z "$PYTHON" ]; then
    cat <<'EOF'
Python 3 with sqlite3 was not found.
For a fully portable offline stick, place a Python runtime under:
  runtime/python/bin/python3
or set INTERVENTION_PYTHON to a local interpreter path.
EOF
    exit 1
fi

cd "$SCRIPT_DIR"
mkdir -p "$DATA_DIR"

ARGS=(server.py --host 127.0.0.1 --port "$PORT" --db "$DB_PATH")
if [ "$OPEN_BROWSER" = true ]; then
    ARGS+=(--open-browser)
fi

exec "$PYTHON" "${ARGS[@]}"
