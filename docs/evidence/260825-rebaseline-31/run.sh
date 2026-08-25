#!/usr/bin/env bash
# Tái lập phép đo re-baseline evalhub#31. Xem README.md cho SHA và tiền đề.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# 1. Postgres test + schema + tenant + corpus 2.0 (vector đọc từ cache đã commit, KHÔNG gọi API)
docker compose -f docker-compose.test.yml up -d
export STUDIO_DATABASE_URL=postgresql://studio_app:changeme@localhost:5433/studio_test
export STUDIO_DATABASE_URL_ADMIN=postgresql://studio_owner:changeme@localhost:5433/studio_test
uv run python apps/studio/scripts/seed_demo_tenants.py
uv run python packages/kb/scripts/ingest_callisto_v2.py     # → 800 chunk / 2 tenant

# 2. Khoá API — LLM trả lời + judge (OpenAI), embedding query LLM tự viết (OpenRouter)
export STUDIO_OPENAI_API_KEY="${STUDIO_OPENAI_API_KEY:?}"
export OPEN_ROUTER_API_KEY="${OPEN_ROUTER_API_KEY:?}"

# 3. N=5 lượt × 2 cấu hình. Ghi thẳng vào thư mục tạm rồi mv — `> raw/x` sẽ cắt cụt file cũ
#    TRƯỚC khi biết lệnh có chạy được không.
out="$(mktemp -d)"
uv run python packages/evalhub/docs/evidence/260825-rebaseline-31/measure.py 5 > "$out/run.log" 2>&1
mv "$out/run.log" packages/evalhub/docs/evidence/260825-rebaseline-31/raw/run.log
