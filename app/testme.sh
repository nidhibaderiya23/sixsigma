#!/bin/bash

# testme.sh
# A helper script to test the Response Watch Shiny app locally.
# Run from anywhere: ./testme.sh   then open http://localhost:8000

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Use the repo's virtual environment if it is there, else whatever `python` is on the PATH.
if [ -x "$SCRIPT_DIR/../.venv/bin/python" ]; then
  PYTHON="$SCRIPT_DIR/../.venv/bin/python"
else
  PYTHON="python"
fi

"$PYTHON" -m shiny run app.py --port 8000
