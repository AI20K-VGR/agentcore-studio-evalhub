"""Đo hình dạng MẪU của golden set — dính chùm, lệch trục, phủ nhãn tay.

Không đo chất lượng agent. Đo xem 30 case có phải 30 quan sát ĐỘC LẬP không, và
mẫu số thật của `Judge.agreement` là bao nhiêu.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_ROOT / "packages" / "evalhub" / "src"))

from studio_evalhub.golden_loader import load_golden_set  # noqa: E402

_GOLDEN_DIR = _ROOT / "packages" / "kb" / "src" / "studio_kb" / "golden"


def do(ref: str) -> dict[str, object]:
    golden = load_golden_set(_GOLDEN_DIR / f"{ref}.yaml", expect_ref=ref)
    cases = list(golden.cases)
    dem_query = Counter(c.query for c in cases)
    dung_lai = {q: n for q, n in dem_query.items() if n > 1}
    return {
        "golden_set_ref": ref,
        "n_case": len(cases),
        "n_query_doc_lap": len(dem_query),
        "n_query_dung_lai": len(dung_lai),
        "query_dung_lai": sorted(dung_lai.items(), key=lambda kv: (-kv[1], kv[0])),
        "theo_tenant": dict(sorted(Counter(c.tenant for c in cases).items())),
        "theo_role_nguoi_hoi": dict(sorted(Counter(r for c in cases for r in c.section_roles).items())),
        "n_refusal": sum(1 for c in cases if c.expects_refusal),
        "ty_le_refusal": round(sum(1 for c in cases if c.expects_refusal) / len(cases), 4),
        "n_manual_label": sum(1 for c in cases if c.manual_label is not None),
    }


if __name__ == "__main__":
    ket_qua = [do(ref) for ref in ("callisto-golden-30-v1", "callisto-2.0-golden-30-v1")]
    print(json.dumps(ket_qua, ensure_ascii=False, indent=2))
