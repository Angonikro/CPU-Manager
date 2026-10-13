#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# For source checkout, run as admin while preserving the active graphical session.
exec ./launch_admin.sh "$@"
