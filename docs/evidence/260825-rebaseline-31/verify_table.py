"""Tái dựng MỌI con số trong bảng §1 của `README.md` từ scorecard gốc, rồi đối chiếu.

Bảng đó từng sai vì chép tay: cột `citation tb` mang `0.9727`/`0.8536` trong khi số thật là
`0.9773`/`0.8091` (`0.9727` là trung bình riêng của `raw-mau-2/`, N=5; `0.8536` thì không khớp
BẤT KỲ tổ hợp con nào của 10 lượt — không truy được nguồn). Phát hiện khi AIE-1 review evalhub#51.

Bài học không phải "cẩn thận hơn": số dẫn xuất chép tay vào tài liệu thì không có gì canh. Script
này đọc thẳng `aggregate` của 20 scorecard — hiện vật sơ cấp, không qua `tong-hop.json` (bản thân
nó cũng là số dẫn xuất) — và so với con số đang nằm trong README. Chạy trước mỗi lần sửa bảng.
"""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
SAMPLES = ("raw", "raw-mau-2")
CONFIGS = {"canvas": "scorecard-canvas-%d.json", "canvas+refusal": "scorecard-canvas-refusal-%d.json"}


def aggregates(config: str) -> list[dict[str, float]]:
    """`aggregate` của cả 10 lượt cho một cấu hình, theo thứ tự raw/ rồi raw-mau-2/."""
    out = []
    for sample in SAMPLES:
        for run in range(1, 6):
            out.append(json.loads((HERE / sample / (CONFIGS[config] % run)).read_text())["aggregate"])
    return out


def readme_row(config: str) -> list[str]:
    """Ô của dòng `config` trong bảng §1 — khớp cả tên có backtick lẫn phần in đậm."""
    for line in (HERE / "README.md").read_text().splitlines():
        if line.startswith("|") and re.search(rf"`{re.escape(config)}`", line):
            return [c.strip().strip("*") for c in line.strip("|").split("|")]
    raise AssertionError(f"không thấy dòng {config!r} trong bảng README")


def main() -> int:
    failures = 0
    for config in CONFIGS:
        success = [a["success_rate"] for a in aggregates(config)]
        citation = [a["citation_accuracy"] for a in aggregates(config)]
        computed = {
            "success range": f"{min(success):.4f} – {max(success):.4f}",
            "success mean": f"{statistics.fmean(success):.4f}",
            "success sd": f"{statistics.stdev(success):.4f}",
            "success spread": f"{max(success) - min(success):.4f}",
            "citation mean": f"{statistics.fmean(citation):.4f}",
        }
        cells = readme_row(config)
        for (label, value), cell in zip(computed.items(), cells[1:], strict=False):
            mark = "ok " if cell == value else "SAI"
            if cell != value:
                failures += 1
            print(f"  {mark} {config:16} {label:16} README={cell:16} tính lại={value}")
    print("\nĐỒNG BỘ" if not failures else f"\n{failures} ô LỆCH — sửa README trước khi dùng")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
