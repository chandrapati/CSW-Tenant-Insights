#!/usr/bin/env bash
# One-command demo: venv + install + render synthetic tenant reports.
# Usage (from repo root):  ./scripts/demo.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"

if [[ ! -d .venv ]]; then
  echo "Creating .venv …"
  "$PYTHON" -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

pip install -q --upgrade pip
pip install -q -e .

echo ""
csw-insights doctor
echo ""
csw-insights demo

echo ""
echo "Next:"
echo "  open out/acme/"
echo "  open out/customer1/"
echo "  PDF without building:  examples/sample-reports/"
echo "  export HTML/DOCX/PDF:  make export"
