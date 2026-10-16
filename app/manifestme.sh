#!/bin/bash
# manifestme.sh
#
# Write a Posit deployment manifest for this Shiny for Python app.
# Run from anywhere: ./manifestme.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Use the repo's virtual environment if it is there, else whatever `python` is on the PATH.
if [ -x "$SCRIPT_DIR/../.venv/bin/python" ]; then
  PYTHON="$SCRIPT_DIR/../.venv/bin/python"
else
  PYTHON="python"
fi

echo "Copying the data files next to the app (Connect deploys only this folder)..."
# qc.find_data_dir() looks in app/data first, then in the repo's data/ folder.
if ! ls ../data/*.csv >/dev/null 2>&1; then
  echo "No CSV files in ../data yet. Make them first (see data/README.md)." >&2
  exit 1
fi
mkdir -p data
cp ../data/*.csv data/

echo "Installing rsconnect-python (if needed)..."
"$PYTHON" -m pip install rsconnect-python

# After the install, the rsconnect command sits next to the python that installed it.
RSCONNECT="$(dirname "$PYTHON")/rsconnect"
[ -x "$RSCONNECT" ] || RSCONNECT="rsconnect"

echo "Writing manifest.json for the Shiny app..."
# Entry point is app.py with the Shiny `app` object. The mode is `shiny` (python-shiny).
"$RSCONNECT" write-manifest shiny . --entrypoint app:app --overwrite

echo "Done. manifest.json created in: $SCRIPT_DIR"
