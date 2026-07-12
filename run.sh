#!/usr/bin/env bash
# End-to-end PGenMap pipeline. Resumable: every API response is cached under
# data/cache_cr/, so re-runs replay from disk. Each stage writes to data/ or
# outputs/ and can be run independently.
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python

echo "[1/7] discover researcher universe"
$PY src/01_discover.py

echo "[2/7] harvest publications"
$PY src/02_harvest.py

echo "[3/7] build DuckDB store"
$PY src/build_db.py

echo "[4/7] enrich (method tags + embeddings)"
$PY src/03_enrich.py

echo "[5/7] topic model"
$PY src/04_topics.py

echo "[6/7] collaboration network"
$PY src/05_network.py

echo "[7/10] analyze + export analysis.json"
$PY src/06_analyze.py

echo "[8/10] figures (UMAP + method/topic/growth/community plots)"
$PY src/07_figures.py

echo "[9/10] atlas map + opportunity data"
$PY src/08_atlas.py

echo "[10/10] build dashboard pages (docs/index.html + docs/scientists.html)"
$PY src/build_dashboard.py

echo "done. outputs/ has analysis.json, network.json, figures/, report.md;"
echo "docs/ has the GitHub Pages dashboard."
