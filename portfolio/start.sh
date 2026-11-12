#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MODE=${PORTFOLIO_MODE:-local}
PORT=${PORTFOLIO_PORT:-8765}
exec python3 "$SCRIPT_DIR/hub.py" serve --mode "$MODE" --port "$PORT" --open
