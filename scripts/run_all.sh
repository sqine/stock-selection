#!/usr/bin/env bash
# 전체 재현: 테스트 → 노트북 생성·실행
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest -q
python scripts/build_notebooks.py
for nb in notebooks/01_weekly_picks.ipynb notebooks/02_ga_kospi200.ipynb; do
  python -m jupyter nbconvert --to notebook --execute --inplace "$nb" 2>/dev/null \
    || python - "$nb" <<'PY'
import sys, nbformat
from nbclient import NotebookClient
nb = nbformat.read(sys.argv[1], as_version=4)
NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": "notebooks"}}).execute()
nbformat.write(nb, sys.argv[1])
PY
done
