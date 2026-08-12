"""LLM-judge seam — spec AIE-2 (R-SPEC A7, INV-4, INV-7).

Scores subjective (non-exact-match) golden-set cases via an LLM judge. Two invariants this seam's
real implementation MUST carry, per R-SPEC A7 and the umbrella-contract invariants:

- **Agreement-check vs hand labels (required, R-SPEC A7)**: a judge that is never checked against
  a human-labeled baseline is not trustworthy alone — every judged case's agreement score
  (`Judge.agreement`, P2 `studio_contracts.scorecard.Judge`) must be derivable from a real
  comparison against a hand label, not a constant/placeholder value.
- **Cap ≤100 calls/day + cache (INV-4)**: the real `judge()` MUST check a cache keyed on
  `(case_id, actual)` before making an LLM call, and MUST refuse (not silently proceed) once the
  day's cap of 100 calls is reached.
- **Descope-guard (INV-7)**: when the daily cap is hit, or the judge provider is unavailable, the
  caller (`harness.py`) falls back to an exact-match scorer instead of failing the whole eval run
  — this module's contract is to make that capped/unavailable state observable (e.g. by raising or
  returning a sentinel the harness can detect), not to implement the fallback itself.

Rubric note (R-SPEC A7 :161): D3·Rigor is NOT activated here — 30 cases + the ≤100/day cap is the
intended DoD; this module does not need deep statistical calibration of judge agreement.

**Đã điền D18/T2** (`kit#118`) — trước đó body là `NotImplementedError`. Ba thứ được cài, và ranh
giới của chúng là nội dung của module:

- **seam** `LLM` tiêm vào (`DEC-D18-02`) — không env, không provider, không biết Gemini tồn tại;
- **cache** khoá `(case_id, actual)` + **cap ≤100/ngày** bền ngoài tiến trình, fail-closed
  (`DEC-D18-05`);
- **descope-sentinel** `JudgeUnavailable(reason=...)` — làm trạng thái *không chấm được* **quan sát
  được kèm danh tính**, và **không** tự thực hiện fallback (đó là việc của `harness.py`, INV-7).

**Cái module này KHÔNG làm, có chủ đích:** không tính `agreement`. Agreement là phép so với **nhãn
tay** trên một **tập** kết quả (`DEC-D18-04`), không phải thứ một lần chấm đơn lẻ sinh ra — xem
`judge()` docstring.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from studio_contracts.protocols import LLM

_PROMPT = """Bạn là bộ chấm. Trả lời DUY NHẤT một từ: PASS hoặc FAIL.

PASS nếu CÂU TRẢ LỜI truyền tải đúng nội dung của ĐÁP ÁN MONG ĐỢI. FAIL nếu không.

ĐÁP ÁN MONG ĐỢI: {expected}
CÂU TRẢ LỜI: {actual}
"""


def _hom_nay() -> str:
    """Ngày theo **UTC**, không theo giờ máy.

    Cap là một hạn mức chia sẻ; mốc reset của nó phải giống nhau ở mọi máy chạy, nếu không hai người
    ở hai múi giờ sẽ bất đồng về việc hôm nay đã hết quota chưa.
    """
    return datetime.now(UTC).date().isoformat()


def _dung_prompt(expected: str, actual: str) -> str:
    return _PROMPT.format(expected=expected, actual=actual)


def _doc_verdict(phan_hoi: str) -> bool:
    """`PASS`/`FAIL` ⇒ `bool`. Bất kỳ thứ gì khác ⇒ `PROVIDER_UNAVAILABLE`, **không** ⇒ `False`.

    Đây là chỗ fail-open dễ lọt nhất của cả module: đọc "thứ không phải PASS" thành `False` biến một
    phản hồi **rác** thành một case **trượt** — tức lại đúng lớp lỗi *"không chấm được"* bị đọc thành
    *"chấm và trượt"* mà cả `JudgeUnavailable` sinh ra để chặn, chỉ khác là nó lọt qua cửa sau.
    """
    chuan = phan_hoi.strip().upper()
    if chuan.startswith("PASS"):
        return True
    if chuan.startswith("FAIL"):
        return False
    raise JudgeUnavailable(JudgeUnavailableReason.PROVIDER_UNAVAILABLE)


def _doc_json(path: Path, *, mac_dinh: dict[str, Any]) -> dict[str, Any]:
    """File **thiếu** ⇒ mặc định (chưa chạy lần nào). File **hỏng** ⇒ `STATE_UNREADABLE`.

    Phân biệt hai ca này là bắt buộc: gộp "thiếu" vào "hỏng" thì judge không bao giờ chạy được lần
    đầu; gộp "hỏng" vào "thiếu" thì một file rác lặng lẽ reset quota về 0 — fail-open về phía **tốn
    tiền thật**, đúng chỗ duy nhất trong quadrant này không được phép fail-open.
    """
    if not path.is_file():
        return dict(mac_dinh)
    try:
        noi_dung = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise JudgeUnavailable(JudgeUnavailableReason.STATE_UNREADABLE) from exc
    if not isinstance(noi_dung, dict):
        raise JudgeUnavailable(JudgeUnavailableReason.STATE_UNREADABLE)
    return noi_dung


def _ghi_json(path: Path, noi_dung: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(noi_dung, ensure_ascii=False, sort_keys=True), encoding="utf-8")


class JudgeUnavailableReason(StrEnum):
    """Vì sao judge không chấm được — **danh tính** của trigger, không chỉ sự tồn tại của nó.

    Đúng **ba** giá trị vì có đúng **ba hành động khác nhau của con người** (`DEC-D18-05`). Thêm giá
    trị thứ tư chỉ khi có hành động thứ tư — không phải khi có tình huống thứ tư.
    """

    CAP_REACHED = "CAP_REACHED"
    """Hết quota ngày. Người đọc **không phải làm gì** — mai reset, và run vẫn hợp lệ."""

    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    """Không dựng/gọi được provider (thiếu key, lỗi xác thực, mất mạng, phản hồi không dùng được).
    Cần **người** cấp phát — đây là `reason` duy nhất trong ba cái chặn bằng thứ ngoài tầm code."""

    STATE_UNREADABLE = "STATE_UNREADABLE"
    """Counter/cache đọc không được ⇒ fail-closed. Cần **dọn file hỏng**, và số của run này **không
    tin được** — khác hẳn `CAP_REACHED` nơi số vẫn tin được."""


class JudgeUnavailable(Exception):
    """Judge không chấm được — `harness.py` bắt cái này rồi tụt nấc exact-match (INV-7).

    **Raise chứ không trả `(False, 0.0)`**, và đây là điểm dễ làm sai nhất của module: trả một giá trị
    hợp lệ biến *"không chấm được"* thành *"chấm và trượt"* — cùng đúng lớp lỗi fail-open mà DE tìm ra
    ở `chunks_from_trace` (`[]` đọc thành *"hàng rào chặn sạch"*), bị bắt trong code của chính quadrant
    này 24h trước.

    Đúng **một** field enum, không hierarchy exception con, không mã lỗi số, không payload tự do
    (`DEC-D18-05` ranh giới không-over-engineer).
    """

    def __init__(self, reason: JudgeUnavailableReason) -> None:
        self.reason = reason
        super().__init__(reason.value)


class LLMJudge:
    """LLM-judge for subjective eval cases — cap ≤100 calls/day + cache (INV-4), required
    agreement-check against hand labels (R-SPEC A7), descope-guard to exact-match (INV-7)."""

    def __init__(self, llm: LLM, *, cache_path: Path, cap_path: Path, cap: int = 100) -> None:
        """`llm` **tiêm vào**, không tự dựng (`DEC-D18-02`).

        Module này không đọc env, không dựng provider, không biết `GeminiProvider` tồn tại.
        Composition root (CLI · `apps/studio` · fixture test) là chỗ **duy nhất** biết provider thật
        nào được dựng. Ba lý do, không phải một sở thích:

        1. **Layering** — `.importlinter` xếp 4 quadrant là sibling; provider thật sống ở
           `apps/studio`, tức phía **trên** evalhub. Import ngược lên là vi phạm lint, và một đường
           vòng (`importlib`, đọc env trực tiếp) là **cùng một phụ thuộc, chỉ né được lint**.
        2. **Fresh clone** — `kit#74` chấm bằng clone sạch; clone riêng evalhub thì `apps/studio`
           không tồn tại.
        3. **Tiền lệ trong repo** — `AgentRunner` đã là seam tiêm vào đúng hình này.

        Hệ quả: judge test được **hoàn toàn tất định** bằng một `LLM` double — không mạng, không key.
        Ô DoD *"CI deterministic"* đóng như hệ quả **cấu trúc**, không phải một việc riêng phải làm.

        `cap` là tham số chứ không phải hằng số module để test đo **luật** bằng `cap=3` thay vì chạy
        100 lần double — cùng một nhánh code, bài nhanh hơn, bất biến không đổi.
        """
        self._llm = llm
        self._cache_path = cache_path
        self._cap_path = cap_path
        self._cap = cap

    async def judge(self, case_id: str, expected: str, actual: str) -> bool:
        """Chấm một case: `actual` có thoả `expected` không.

        **Thứ tự ba bước là một phần của hợp đồng, không phải chi tiết cài đặt:**

        1. **cache trước** — khoá `(case_id, actual)`. Hit ⇒ trả ngay, **không** chạm counter, và
           **vẫn trả được kể cả khi đã chạm cap**: cache không cần quota. Đặt kiểm cap lên trước sẽ
           vứt đúng phần việc đã trả tiền.
        2. **cap sau** — chạm trần ⇒ `CAP_REACHED`, và provider **không** được chạm.
        3. **gọi provider cuối** — ném ⇒ `PROVIDER_UNAVAILABLE`.

        Trả `bool`, **không** trả `(success, agreement)` như chữ ký spec cũ. Lý do là ranh giới
        `DEC-D18-04`: `agreement` là phép so với **nhãn tay**, mà `judge()` không nhận nhãn tay —
        nên mọi giá trị nó bịa ra ở vị trí đó là **hằng số**, đúng thứ `judge.py` docstring đầu file,
        `ADR B5` và §7 ô DoD 2 cấm bằng ba chỗ khác nhau: *một `agreement` hằng không phân biệt được
        với một judge thật đồng thuận 100%*. Agreement là **hàm thuần riêng** trên tập kết quả, không
        phải thứ một lần chấm đơn lẻ sinh ra.

        Không nuốt lỗi thành verdict: mọi đường không-chấm-được đều `raise JudgeUnavailable` kèm
        `reason`, để `harness.py` tụt nấc **và ghi lại đã tụt vì gì** (INV-7).
        """
        cache = self._doc_cache()
        da_cham = cache.get(case_id, {}).get(actual)
        if da_cham is not None:
            return da_cham

        so_da_goi = self._doc_counter()
        if so_da_goi >= self._cap:
            raise JudgeUnavailable(JudgeUnavailableReason.CAP_REACHED)

        try:
            phan_hoi = await self._llm.complete(_dung_prompt(expected, actual))
        except Exception as exc:
            raise JudgeUnavailable(JudgeUnavailableReason.PROVIDER_UNAVAILABLE) from exc

        # Ghi counter NGAY khi call trả về, TRƯỚC khi parse: quota đã bị tiêu ở thời điểm này rồi.
        # Chỉ cộng khi parse thành công là tự cho mình gọi lại miễn phí mỗi lần mô hình trả rác.
        self._ghi_counter(so_da_goi + 1)

        verdict = _doc_verdict(phan_hoi)
        cache.setdefault(case_id, {})[actual] = verdict
        self._ghi_cache(cache)
        return verdict

    def _doc_cache(self) -> dict[str, dict[str, bool]]:
        """Cache lồng hai tầng `{case_id: {actual: verdict}}` — đó CHÍNH là khoá `(case_id, actual)`.

        Lồng thay vì nối chuỗi (`f"{case_id}|{actual}"`) vì `actual` là **văn bản tự do do mô hình
        sinh ra**: bất kỳ ký tự phân tách nào cũng có thể xuất hiện trong đó, và một `case_id` chứa
        ký tự phân tách sẽ đụng khoá của case khác. Lỗi đó chỉ hiện ra dưới dạng *"cache trả verdict
        của case khác"* — sai âm thầm, không exception.

        **Kiểm shape SAU khi parse, không chỉ kiểm parse được.** `_doc_json` fail-closed khi file
        không phải JSON; nhưng JSON **hợp lệ mà cấu trúc khác** thì lọt, và lọt theo hai kiểu đều tệ:

        - `{"HB-01": "pass"}` ⇒ `.get(actual)` chạy trên một `str` ⇒ `AttributeError` **thoát ra ngoài
          `JudgeUnavailable`** ⇒ `harness._hoi_judge` không bắt được ⇒ **vỡ cả run**, đúng thứ INV-7
          sinh ra để chống;
        - `{"HB-01": {"y": "pass"}}` ⇒ trả thẳng một `str` ra khỏi một hàm khai `-> bool`.
        """
        noi_dung = _doc_json(self._cache_path, mac_dinh={})
        for muc in noi_dung.values():
            if not isinstance(muc, dict) or any(not isinstance(v, bool) for v in muc.values()):
                raise JudgeUnavailable(JudgeUnavailableReason.STATE_UNREADABLE)
        return cast("dict[str, dict[str, bool]]", noi_dung)

    def _ghi_cache(self, cache: dict[str, dict[str, bool]]) -> None:
        _ghi_json(self._cache_path, cache)

    def _doc_counter(self) -> int:
        """Số call đã dùng **trong ngày hôm nay**, đọc từ file — bền ngoài tiến trình.

        **Không để trong RAM:** `INV-4` nói *"≤100 call/**ngày**"* — một đơn vị **thời gian**, không
        phải một đơn vị **tiến trình**. Counter in-memory reset mỗi lần khởi động, nên chạy harness 5
        lần trong ngày là cap thật ≤500 mà không dòng code nào sai để ai đó nhìn ra.

        **Ngày khác ⇒ đếm lại từ 0**, và đó là lý do file mang `date` chứ không chỉ mang `count`: một
        counter không có ngày là cap **trọn đời**, tức khoá cứng judge sau 100 call đầu tiên và không
        bao giờ mở lại — sai theo chiều ngược nhưng vẫn sai.

        **Hai lớp kiểm shape, và cả hai chặn đúng một hướng hỏng: fail-OPEN về phía tiêu tiền thật.**
        Đây là điều đáng ghi nhất của hàm này, vì cả hai ca đều **không ném gì và không trả gì lạ** —
        chúng chỉ lặng lẽ mở lại hạn mức đã dùng hết:

        - `date` **sai kiểu** (vd `123`) ⇒ `123 != "2026-08-12"` là `True` ⇒ rơi vào nhánh *"ngày
          khác"* ⇒ **quota reset về 0**. Một file rác biến cap ≤100/ngày thành **không cap**.
        - `count` là `bool` ⇒ `isinstance(True, int)` là `True` trong Python, nên nó **lọt qua đúng
          lớp kiểm `int`** đã có, rồi đếm thành `1`.

        `DEC-D18-05` chốt counter là chỗ **duy nhất** trong quadrant không được phép fail-open, nên
        cả hai ca phải thành `STATE_UNREADABLE` — *đọc được nhưng không dùng được* ≡ *không đọc được*.
        """
        state = _doc_json(self._cap_path, mac_dinh={})
        ngay = state.get("date")
        if ngay is not None and not isinstance(ngay, str):
            raise JudgeUnavailable(JudgeUnavailableReason.STATE_UNREADABLE)
        if ngay != _hom_nay():
            return 0
        so = state.get("count", 0)
        if not isinstance(so, int) or isinstance(so, bool):
            raise JudgeUnavailable(JudgeUnavailableReason.STATE_UNREADABLE)
        return so

    def _ghi_counter(self, so: int) -> None:
        _ghi_json(self._cap_path, {"date": _hom_nay(), "count": so})
