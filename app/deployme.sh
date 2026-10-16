#!/bin/bash
# deployme.sh

# Deploy the Response Watch Shiny app to Posit Connect.
# This script targets Posit Connect (not Connect Cloud).
# It never contains a key: set CONNECT_SERVER and CONNECT_API_KEY in your shell
# (or in an untracked .env file) before running it.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Use the repo's virtual environment if it is there, else whatever `python` is on the PATH.
if [ -x "$SCRIPT_DIR/../.venv/bin/python" ]; then
  PYTHON="$SCRIPT_DIR/../.venv/bin/python"
else
  PYTHON="python"
fi

"$PYTHON" -m pip install rsconnect-python

# After the install, the rsconnect command sits next to the python that installed it.
RSCONNECT="$(dirname "$PYTHON")/rsconnect"
[ -x "$RSCONNECT" ] || RSCONNECT="rsconnect"

# Optional: load CONNECT_SERVER and CONNECT_API_KEY from .env (keep .env out of git)
if [ -f ".env" ]; then
  # shellcheck disable=SC1091
  source .env
fi

# The data files must travel with the app: copy them next to app.py first.
if ! ls ../data/*.csv >/dev/null 2>&1; then
  echo "No CSV files in ../data yet. Make them first (see data/README.md)." >&2
  exit 1
fi
mkdir -p data
cp ../data/*.csv data/

# If CONNECT_SERVER and CONNECT_API_KEY are set, use explicit auth.
# Otherwise this will use your existing rsconnect account configuration.
"$RSCONNECT" deploy shiny \
  ${CONNECT_SERVER:+--server "$CONNECT_SERVER"} \
  ${CONNECT_API_KEY:+--api-key "$CONNECT_API_KEY"} \
  --entrypoint app:app \
  .
