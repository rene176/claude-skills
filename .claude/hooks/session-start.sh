#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install Node.js dependencies for the docs site (prettier, astro, etc.)
cd "${CLAUDE_PROJECT_DIR}/site"
npm install

# Install Python linting tools if not already present
if ! command -v ruff &> /dev/null; then
  pip install --quiet ruff
fi

if ! command -v pyright &> /dev/null; then
  pip install --quiet pyright
fi
