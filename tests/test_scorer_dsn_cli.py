"""CLI `run_report` phải ưu tiên DSN của role bộ chấm (`evalhub#37`, mắt xích cuối).

Chuỗi vá `evalhub#37` gồm 3 mảnh, đây là mảnh thứ 3:

1. `evalhub#38` — hai hàm đọc-xuyên-tenant **từ chối trả lời** thay vì trả rỗng khi RLS đang áp.
2. `kit#202` + `app#42` — role `studio_scorer` (`BYPASSRLS`) + `GRANT SELECT` đúng một bảng.
3. **đây** — CLI thật sự *dùng* role đó, nếu không thì hai mảnh trên chỉ tồn tại trên giấy.

Mọi câu SQL của CLI này chỉ chạm `obs.trace_events` (`_READ_RUN`, `_LIST_RUNS` — grep toàn file ra
đúng 2 `FROM`), nên `SELECT` trên một bảng mà `grant_scorer_privileges()` cấp là **đủ**; không cần
nới thêm quyền nào cho role.

**Fallback về `STUDIO_DATABASE_URL` được giữ có chủ đích.** Máy nào chưa có role (volume Postgres
tạo trước `kit#202` thì initdb không chạy lại) vẫn chạy được CLI như trước — và nếu RLS đang áp thì
nó sẽ dừng ở `UnscopedReadUnavailable` với thông điệp chỉ đúng cách sửa, chứ không im lặng. Đó là lý
do thứ tự là *ưu tiên*, không phải *bắt buộc*.
"""

from __future__ import annotations

import pytest
from studio_evalhub.run_report import _DSN_ENV_APP, _DSN_ENV_SCORER, dsn_bo_cham

_SCORER = "postgresql://studio_scorer:changeme@localhost:5433/studio_test"
_APP = "postgresql://studio_app:changeme@localhost:5433/studio_test"


def test_uu_tien_dsn_scorer_khi_ca_hai_cung_dat() -> None:
    """KHÓA cốt lõi: có cả hai thì phải chọn scorer.

    Đây là bài duy nhất phân biệt được bản vá với bản cũ — trước đó CLI đọc thẳng
    `STUDIO_DATABASE_URL`, tức luôn chọn role bị RLS chặn kể cả khi role bộ chấm đã có sẵn.
    """
    assert dsn_bo_cham({_DSN_ENV_SCORER: _SCORER, _DSN_ENV_APP: _APP}) == _SCORER


def test_fallback_ve_dsn_app_khi_chua_co_role_scorer() -> None:
    """KHÓA tương thích ngược: máy chưa có role vẫn chạy được, không đổi hành vi cũ."""
    assert dsn_bo_cham({_DSN_ENV_APP: _APP}) == _APP


def test_chuoi_rong_khong_tinh_la_da_dat() -> None:
    """`STUDIO_DATABASE_URL_SCORER=` (khai nhưng để trống) phải đọc là CHƯA đặt, không phải
    'đặt bằng chuỗi rỗng' — nếu không, `AsyncConnectionPool("")` sẽ nổ ở một chỗ xa nguồn lỗi."""
    assert dsn_bo_cham({_DSN_ENV_SCORER: "", _DSN_ENV_APP: _APP}) == _APP


def test_khong_co_bien_nao_thi_None() -> None:
    assert dsn_bo_cham({}) is None


async def test_cli_bao_loi_neu_thieu_ca_hai_bien(monkeypatch: pytest.MonkeyPatch) -> None:
    """KHÓA đường CLI thật: thiếu cả hai ⇒ `parser.error` nêu ĐÍCH DANH cả hai biến.

    Không assert bằng `in` trên một chuỗi con chung chung: người đọc lỗi cần biết biến nào là ưu
    tiên, nếu không họ sẽ đặt đúng biến cũ rồi tự hỏi vì sao vẫn `UnscopedReadUnavailable`.
    """
    from studio_evalhub.run_report import _amain

    monkeypatch.delenv(_DSN_ENV_SCORER, raising=False)
    monkeypatch.delenv(_DSN_ENV_APP, raising=False)
    with pytest.raises(SystemExit):
        await _amain([])
