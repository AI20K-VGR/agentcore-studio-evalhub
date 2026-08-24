#!/usr/bin/env bash
# Tái lập mọi con số trong README.md của thư mục này. Không cần Postgres, không cần key.
#
# `uv run python` (không phải `python` trần) + ghi file tạm rồi `mv`: xem run.sh của
# `260824-golden-30-sample` cho lý do đầy đủ — tóm tắt: interpreter mặc định của máy người chạy
# không nhất thiết là bản workspace ghim, và `| tee raw/x.json` cắt cụt file đích TRƯỚC khi biết
# lệnh có chạy nổi không (một lần chạy hỏng xoá mất số thô đã commit).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p raw
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

uv run python measure_ci.py > "$tmp/ci.json"
mv "$tmp/ci.json" raw/ci.json
cat raw/ci.json
