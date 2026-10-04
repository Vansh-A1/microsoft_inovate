#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$task_root/.venv/bin/python" "$task_root/scripts/seed/hackathon.py" run "$@"
