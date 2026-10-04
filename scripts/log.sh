#!/usr/bin/env bash
# log.sh - Cross-platform bash wrapper for log_decision.py
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/log_decision.py" "$@"
