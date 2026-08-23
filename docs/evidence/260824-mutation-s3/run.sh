#!/usr/bin/env bash
# Tái lập bảng số trong README.md của thư mục này.
#
# Tiền đề (script tự kiểm và DỪNG nếu thiếu):
#   - Postgres test:  docker compose -f docker-compose.test.yml up -d
#   - packages/engine ở con trỏ có agent_loop.py (65731e5, engine#36)
#
# Chạy 6 lượt suite TOÀN WORKSPACE (1 nền + 5 mutant) ≈ 10 phút.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."   # → gốc kit
export STUDIO_DATABASE_URL_ADMIN="${STUDIO_DATABASE_URL_ADMIN:-postgresql://studio_owner:changeme@localhost:5433/studio_test}"
export STUDIO_DATABASE_URL="${STUDIO_DATABASE_URL:-postgresql://studio_app:changeme@localhost:5433/studio_test}"
export STUDIO_DATABASE_URL_SCORER="${STUDIO_DATABASE_URL_SCORER:-postgresql://studio_scorer:changeme@localhost:5433/studio_test}"
python -u packages/evalhub/scripts/mutation_s3.py \
  | tee packages/evalhub/docs/evidence/260824-mutation-s3/raw/sweep.log
