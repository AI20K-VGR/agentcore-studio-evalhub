"""Ghi lại rồi phát lại lời gọi `LLM.complete()` — làm một lượt eval qua model thật trở thành
**tái lập được**, mà không thay bất kỳ tầng nào khác của spine.

## Vì sao ở seam này, không ở seam `AgentRunner`

`StubAgentRunner` (`agent_runner.py`) đã replay được `CaseRun` sẵn, nhưng nó thay luôn
**interpreter · retrieval · trace** — đúng những tầng mà một buổi demo tồn tại để trình. Ghi ở
`LLM.complete()` thì engine thật, `PgKbSearch` thật, `PgTraceWriter` thật, `EvalHarness` thật đều
giữ nguyên; **chỉ** lời gọi model được phát lại (`DEC-D22-01`, plan `day-22-aie2.md` §1).

Số đo buộc phải làm việc này (D21, golden-30 qua `o4-mini`): cùng model, cùng prompt, cùng
retrieval, hai lượt cho nhánh từ-chối `6/8` rồi `5/8` — biên độ nhiễu **±1 case**, tức `1/30 = 0.033`
điểm `success_rate`. Một lượt gọi sống không so được với một lượt gọi sống khác, nên `INV-4`
(*"CI không phụ thuộc model"*) và mọi phép quy-tác-dụng đều đòi một bản ghi phát lại được.

## `DEC-D22-01` — khoá là `(prompt, kwargs)`, không chỉ `prompt`

`executors.py:351` gọi `complete(prompt, **kwargs)`, và `kwargs["model"]` được tiêm từ
`recipe.agent_config.model` (`:349-350`); recipe còn khai được `params["kwargs"]` (`:324`). Hôm nay
mọi impl đều bỏ qua kwargs (`FixtureLLM.complete` mở đầu bằng `del prompt, kwargs`;
`GeminiProvider` dùng `self._model`), nên hành vi không đổi — nhưng ngày một gateway đọc
`kwargs["model"]`, *cùng prompt + khác model* sẽ được phục vụ **cùng một response đã ghi**: một đáp
án sai không có gì báo. Đưa kwargs vào khoá thì lệch thành **miss ⇒ raise**, không thành câu trả lời
im lặng.

`json.dumps(..., sort_keys=True)` sắp khoá **đệ quy** nên thứ tự khai không vào khoá; `float` dùng
repr ngắn nhất round-trip; `ensure_ascii` mặc định ⇒ escaping tất định. `Node.params` là
`dict[str, object]` (**không** validate giá trị), nên một recipe dựng bằng Python vẫn có thể nhét
`set`/`UUID`/object vào — khi đó `json.dumps` raise `TypeError` và **`TypeError` đó được để thoát
ra**, không bọc, không coerce. **Cấm `default=str`**: `__repr__` mặc định mang địa chỉ bộ nhớ (đo 3
tiến trình liên tiếp ra 3 khoá khác nhau) ⇒ mọi replay ở tiến trình khác thành miss.

## `DEC-D22-02` — miss là lỗi, không phải đường lùi

`ReplayLLM` **không** rơi về một fake, **không** gọi mạng, **không** trả rỗng. Cùng luật `_doc_json`
của `judge.py`: *đọc được nhưng không dùng được ≡ không đọc được*. Một replay lặng lẽ lùi về fake
vẫn ra một con số, và không ai biết con số đó đến từ đâu — đúng lớp xanh-giả mà `app#20` đã bắt ở
nhánh judge.

## Hai thứ CỐ Ý không có ở đây

**Không ghi token.** `Tokens` không đến từ provider mà do engine tự tính từ text:
`Tokens(prompt=len(prompt.split()), completion=len(answer.split()))` (`executors.py:362`). Phát lại
đúng chuỗi `answer` là tự ra đúng token, và do đó đúng cost. Ghi thêm token vào fixture là dựng
**nguồn thứ hai** cho một giá trị đã có nguồn — đúng thứ `DEC-D19-01` (*đọc, không tính lại*) cấm,
chỉ khác trục.

**Không cố làm `llm_source` thành `"stub"`.** Engine phân loại bằng allowlist tên class
(`_KNOWN_STUB_LLM_CLASS_NAMES`, `executors.py:219`, bút AIE-1), nên một run replay sẽ mang
`llm_source="gateway"`. Không consumer nào ngoài test của engine đọc field đó, và nhãn `"gateway"`
**đúng hơn** `"stub"`: giá trị đang phát lại là giá trị gateway đã ghi, không phải một double sinh
ra tại chỗ như `ExtractiveFakeLLM`. Một nhãn thứ ba (`"replay"`) sẽ là thay đổi hợp đồng ở engine —
ngoài phạm vi.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from studio_contracts.protocols import LLM


class ReplayError(Exception):
    """Gốc cho mọi đường không phát lại được. Tách hai nhánh con vì **hành động của người đọc khác
    nhau**: miss ⇒ ghi lại fixture (hoặc tìm ra vì sao prompt đổi); file hỏng ⇒ dọn file."""


class ReplayMiss(ReplayError):
    """Không có bản ghi cho `(prompt, kwargs)` này.

    Ba nguyên nhân thật, và cả ba đều đáng biết chứ không đáng nuốt: fixture ghi thiếu lượt (vd ghi
    khi judge TẮT rồi phát lại khi judge BẬT — `judge.py` phát prompt riêng theo template của nó);
    prompt đổi vì `instructions`/retrieval đổi; hoặc `kwargs` đổi."""


class FixtureUnreadable(ReplayError):
    """File fixture thiếu/hỏng/sai hình dạng. **Fail-closed**, không coi như rỗng: một fixture rỗng
    làm mọi lời gọi thành miss, còn một fixture *sai hình dạng* đọc thành rỗng thì im lặng biến một
    file rác thành "chưa ghi gì" — mất luôn tín hiệu cần dọn file."""


def call_key(prompt: str, kwargs: dict[str, object]) -> str:
    """Khoá của một lời gọi = `sha256(prompt + NUL + json.dumps(kwargs, sort_keys=True))`.

    `NUL` làm phân tách vì nó không xuất hiện trong prompt văn bản. Nói cho đúng: với cách
    serialize hôm nay **không** dựng được cặp đụng khoá kể cả khi nối trần, vì `json.dumps` của một
    `dict` luôn mở `{` và đóng `}` nên không có cách tách nào khác. Dấu phân tách ở đây là để ranh
    giới hai thành phần không phụ thuộc vào tính chất đó — không phải để vá một va chạm đang có.

    Xem `DEC-D22-01` ở docstring module cho lý do kwargs phải vào khoá, và vì sao `TypeError` của
    `json.dumps` được để thoát ra."""
    canonical = f"{prompt}\0{json.dumps(kwargs, sort_keys=True)}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _doc_fixture(path: Path) -> dict[str, Any]:
    """Đọc + kiểm hình dạng. Thiếu file / JSON hỏng / shape lạ ⇒ `FixtureUnreadable`.

    **Kiểm shape SAU khi parse, không chỉ kiểm parse được** (cùng bài học `judge.py:_doc_cache`):
    JSON hợp lệ mà cấu trúc khác thì lọt tới chỗ khác rồi mới nổ, xa chỗ gây lỗi — `calls` là một
    `str` sẽ cho `.get()` chạy trên `str` ⇒ `AttributeError` thoát ra ngoài `ReplayError` và người
    gọi không bắt được bằng thứ họ được bảo là phải bắt."""
    if not path.is_file():
        raise FixtureUnreadable(f"fixture không tồn tại: {path}")
    try:
        noi_dung = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureUnreadable(f"fixture đọc không được: {path}") from exc
    if not isinstance(noi_dung, dict):
        raise FixtureUnreadable(f"fixture không phải object JSON: {path}")
    calls = noi_dung.get("calls")
    if not isinstance(calls, dict):
        raise FixtureUnreadable(f"fixture thiếu khoá 'calls' dạng object: {path}")
    for khoa, muc in calls.items():
        if not isinstance(muc, dict) or not isinstance(muc.get("response"), str):
            raise FixtureUnreadable(
                f"fixture: mục {khoa!r} phải là object có 'response' dạng str — `LLM.complete` khai "
                "`-> str`, nên một bản ghi sai kiểu là một bản ghi hỏng, không phải một đáp án lạ."
            )
    return noi_dung


def _ghi_fixture(path: Path, noi_dung: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(noi_dung, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


class RecordingLLM:
    """Bọc một `LLM` thật, trả nguyên văn response của nó và **ghi lại** vào `path`.

    Ghi **sau từng lời gọi**, không gom tới cuối run: một lượt golden-30 là ~60 lời gọi tốn tiền
    thật, và mất sạch vì process chết ở case thứ 58 là mất không cần thiết. Cùng lý do `judge.py`
    ghi counter ngay khi call trả về.

    `path` do **bên gọi** chọn (composition root / script), module này không đọc env và không tự
    quyết chỗ ghi — cùng seam `DEC-D18-02` đã đặt cho `LLMJudge(cache_path=…)`.
    """

    def __init__(self, inner: LLM, path: Path, *, model: str, golden_set_ref: str | None = None) -> None:
        self._inner = inner
        self._path = path
        self._model = model
        self._golden_set_ref = golden_set_ref

    async def complete(self, prompt: str, **kwargs: object) -> str:
        response = await self._inner.complete(prompt, **kwargs)
        try:
            noi_dung = _doc_fixture(self._path)
        except FixtureUnreadable:
            if self._path.is_file():
                raise
            noi_dung = {
                "meta": {
                    "model": self._model,
                    "recorded_at": datetime.now(UTC).isoformat(),
                    "golden_set_ref": self._golden_set_ref,
                },
                "calls": {},
            }
        calls = cast("dict[str, Any]", noi_dung["calls"])
        calls[call_key(prompt, kwargs)] = {"response": response}
        _ghi_fixture(self._path, noi_dung)
        return response


class ReplayLLM:
    """Phát lại từ `path`; **không** có đường lùi (`DEC-D22-02`).

    Nạp fixture một lần rồi giữ trong bộ nhớ: fixture là hiện vật bất biến trong một lượt phát lại,
    nên đọc lại mỗi lời gọi chỉ tốn I/O mà không phát hiện thêm gì.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._calls: dict[str, Any] | None = None

    def _tra(self) -> dict[str, Any]:
        if self._calls is None:
            self._calls = cast("dict[str, Any]", _doc_fixture(self._path)["calls"])
        return self._calls

    async def complete(self, prompt: str, **kwargs: object) -> str:
        khoa = call_key(prompt, kwargs)
        muc = self._tra().get(khoa)
        if muc is None:
            raise ReplayMiss(
                f"không có bản ghi cho khoá {khoa[:16]}… trong {self._path} — "
                f"{len(self._tra())} bản ghi đang có. Prompt/kwargs đã đổi so với lúc ghi, hoặc "
                "lượt ghi thiếu nhánh này (vd ghi khi judge TẮT rồi phát lại khi judge BẬT)."
            )
        return cast("str", muc["response"])
