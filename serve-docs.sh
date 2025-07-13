#!/usr/bin/env bash

set -euo pipefail

echo "🚀 Serving MkDocs locally on http://localhost:8001"

# Ensure uv is available
python3 -m pip install --user uv

# Sync only docs dependencies from pyproject.toml
python3 -m uv sync --python 3.11 --group mkdocs --frozen

# Serve docs at specified host:port
python3 -m uv run mkdocs serve -a localhost:8001
