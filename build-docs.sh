#!/usr/bin/env bash

set -euo pipefail

echo "📦 Building static MkDocs documentation..."

# Ensure uv is installed
python3 -m pip install --user uv

# Sync only mkdocs dependencies
python3 -m uv sync --python 3.11 --group mkdocs --frozen

# Build the site
python3 -m uv run mkdocs build
