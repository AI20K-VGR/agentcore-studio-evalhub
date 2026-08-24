"""Wilson 95% trên golden-30, đối chiếu `n` thô (30) với `n` hiệu dụng (số query độc lập).

Chẩn đoán, KHÔNG phải cổng (`DEC-S2-134-01`). Các mức `k` ở đây là **kịch bản** để đọc độ nhạy theo
mẫu số — không phải kết quả đo của một run cụ thể nào.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_ROOT / "packages" / "evalhub" / "src"))

from studio_evalhub.golden_loader import load_golden_set  # noqa: E402
from studio_evalhub.wilson import wilson  # noqa: E402

_GOLDEN_DIR = _ROOT / "packages" / "kb" / "src" / "studio_kb" / "golden"
_REFS = ("callisto-golden-30-v1", "callisto-2.0-golden-30-v1")
_PASS_RATES = (1.0, 29 / 30, 27 / 30)


def _sample_sizes(ref: str) -> tuple[int, int]:
    """`(n thô, n hiệu dụng)` — hiệu dụng = số **query độc lập**, vì golden-30 lặp câu hỏi."""
    golden = load_golden_set(_GOLDEN_DIR / f"{ref}.yaml", expect_ref=ref)
    cases = list(golden.cases)
    return len(cases), len(Counter(c.query for c in cases))


def _row(k: int, n: int) -> dict[str, object]:
    interval = wilson(k, n)
    return {
        "k": k,
        "n": n,
        "point": None if interval.point is None else round(interval.point, 4),
        "lower": None if interval.lower is None else round(interval.lower, 4),
        "upper": None if interval.upper is None else round(interval.upper, 4),
        "status": interval.status,
    }


def main() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for ref in _REFS:
        n_raw, n_effective = _sample_sizes(ref)
        scenarios = [
            {
                "target_pass_rate": round(rate, 4),
                "raw_n": _row(round(rate * n_raw), n_raw),
                "effective_n": _row(round(rate * n_effective), n_effective),
            }
            for rate in _PASS_RATES
        ]
        out.append(
            {
                "golden_set_ref": ref,
                "n_raw": n_raw,
                "n_effective": n_effective,
                "scenarios": scenarios,
            }
        )
    return out


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
