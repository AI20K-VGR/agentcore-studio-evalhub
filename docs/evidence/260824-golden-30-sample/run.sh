#!/usr/bin/env bash
# Tái lập mọi con số trong README.md của thư mục này.
# Không cần Postgres, không cần key — chỉ đọc file YAML golden set và AST của source.
#
# `uv run python` chứ không phải `python` trần: `scan_defaults.py` dùng cú pháp `except A, B:`
# (PEP 758, hợp lệ từ Python 3.14 — bản mà workspace này ghim). Gọi bằng interpreter mặc định của
# máy người chạy thì 3.12 báo `SyntaxError: multiple exception types must be parenthesized`, và
# người đọc sẽ tưởng bằng chứng hỏng thay vì tưởng mình đang chạy sai Python. Phát hiện qua review
# evalhub#43 (@Dozyboy) — họ chạy thật và trúng đúng lỗi đó.
#
# Ghi ra file tạm rồi mới `mv` vào `raw/`: `... | tee raw/x.json` cắt cụt file ĐÍCH trước khi biết
# lệnh có chạy nổi không, nên một lần chạy hỏng sẽ để lại `raw/` RỖNG — xoá mất chính số thô mà
# thư mục này tồn tại để giữ. (Đo được, không phải phòng xa: một lần thử với PATH tối thiểu đã làm
# đúng thế.)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p raw
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

uv run python measure_sample.py > "$tmp/sample.json"
uv run python scan_defaults.py  > "$tmp/defaults.json"

mv "$tmp/sample.json"   raw/sample.json
mv "$tmp/defaults.json" raw/defaults.json
cat raw/sample.json raw/defaults.json
