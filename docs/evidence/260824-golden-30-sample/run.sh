#!/usr/bin/env bash
# Tái lập mọi con số trong README.md của thư mục này.
# Không cần Postgres, không cần key — chỉ đọc file YAML golden set.
set -euo pipefail
cd "$(dirname "$0")"
python measure_sample.py | tee raw/sample.json
