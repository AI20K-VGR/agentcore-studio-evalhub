#!/usr/bin/env bash
# Tái lập bảng số trong README.md. Không cần Postgres, không cần API key.
set -euo pipefail
cd "$(dirname "$0")"
python measure_ci.py | tee raw/ci.json
