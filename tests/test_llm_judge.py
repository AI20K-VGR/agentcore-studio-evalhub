"""Test `LLMJudge` — cache + cap + descope-sentinel. **Tất định, 0 call mạng** (`DEC-D18-02/03/05`).

Mọi bài chạy bằng `LLM` **double** dựng ngay trong file. Đó không phải tiện tay: `DEC-D18-02` chốt
judge nhận `LLM` qua seam **tiêm vào**, nên nhánh judge test được hoàn toàn tất định mà không cần key,
không chạm mạng — ô DoD *"CI deterministic"* đóng như **hệ quả cấu trúc**, không phải một việc riêng.

**Mỗi bài raise phải assert `reason`, không chỉ assert loại exception.** Một bài
`pytest.raises(JudgeUnavailable)` trần xanh với **mọi** `reason` ⇒ nó không canh được gì về **danh
tính** của trigger, chỉ canh được *có-một-trigger-nào-đó*. Ba `reason` tồn tại vì chúng đòi **ba hành
động khác nhau của con người** (`DEC-D18-05`): `CAP_REACHED` ⇒ đợi mai · `PROVIDER_UNAVAILABLE` ⇒ cần
người cấp key · `STATE_UNREADABLE` ⇒ cần dọn file hỏng. Gộp lại là biến tín hiệu vận hành thành tiếng
ồn. Đây cũng là đường lọt đích danh của mutant `M-J6`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from studio_evalhub.judge import JudgeUnavailable, JudgeUnavailableReason, LLMJudge


class _FakeLLM:
    """`LLM` double — đếm số lần bị gọi. Bộ đếm đó là thứ bài cache assert lên."""

    def __init__(self, reply: str = "PASS") -> None:
        self.calls: list[str] = []
        self._reply = reply

    async def complete(self, prompt: str, **kwargs: object) -> str:
        self.calls.append(prompt)
        return self._reply


class _BoomLLM:
    """`LLM` double luôn ném — mô hình hoá thiếu key / lỗi xác thực / mất mạng."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def complete(self, prompt: str, **kwargs: object) -> str:
        self.calls.append(prompt)
        raise RuntimeError("no API key configured")


def _paths(tmp_path: Path) -> dict[str, Any]:
    return {"cache_path": tmp_path / "judge-cache.json", "cap_path": tmp_path / "judge-cap.json"}


async def test_cache_hit_khong_goi_lai_llm(tmp_path: Path) -> None:
    """Case đã chấm rồi ⇒ lần sau đọc cache, **không** gọi lại LLM.

    Assert trên `len(llm.calls)` chứ không trên giá trị trả về: hai lần cùng trả `True` là điều xảy ra
    **dù** cache có hoạt động hay không — một bài chỉ so kết quả sẽ xanh với một cache hỏng hoàn toàn.
    Thứ duy nhất phân biệt được là **số lần provider bị chạm**."""
    llm = _FakeLLM()
    judge = LLMJudge(llm, **_paths(tmp_path))

    lan_1 = await judge.judge(case_id="HB-01", expected="12 ngày", actual="Nghỉ phép 12 ngày.")
    lan_2 = await judge.judge(case_id="HB-01", expected="12 ngày", actual="Nghỉ phép 12 ngày.")

    assert lan_1 == lan_2
    assert len(llm.calls) == 1


async def test_cache_hit_khong_ton_quota(tmp_path: Path) -> None:
    """Cache hit **không** tăng counter — nếu tăng thì cache không tiết kiệm gì và cap sai đơn vị.

    Bất biến này tách hẳn với bài trên: một bản vá vẫn đọc cache đúng (không gọi LLM) mà **vẫn** cộng
    counter sẽ xanh ở bài trên và đỏ ở đây. Đây là mutant `M-J2`."""
    paths = _paths(tmp_path)
    llm = _FakeLLM()
    judge = LLMJudge(llm, **paths)

    await judge.judge(case_id="HB-01", expected="x", actual="y")
    sau_lan_dau = json.loads(paths["cap_path"].read_text(encoding="utf-8"))["count"]
    await judge.judge(case_id="HB-01", expected="x", actual="y")
    sau_cache_hit = json.loads(paths["cap_path"].read_text(encoding="utf-8"))["count"]

    assert sau_lan_dau == 1
    assert sau_cache_hit == 1


async def test_counter_ben_qua_hai_instance(tmp_path: Path) -> None:
    """Counter **bền ngoài tiến trình**: instance thứ hai đọc tiếp số của instance thứ nhất.

    `INV-4` nói *"≤100 call/**ngày**"* — một đơn vị **thời gian**, không phải một đơn vị **tiến
    trình**. Counter in-memory sẽ reset mỗi lần khởi động: chạy harness 5 lần trong ngày là cap thật
    ≤500, và **không dòng code nào sai** để ai đó nhìn ra. Bài này là chỗ khác biệt đó lộ ra.

    Hai instance dùng **hai** `_FakeLLM` khác nhau, cố ý: nếu counter sống trong instance thì mỗi con
    tự đếm từ 0 và bài xanh giả."""
    paths = _paths(tmp_path)

    await LLMJudge(_FakeLLM(), **paths).judge(case_id="A", expected="x", actual="a")
    await LLMJudge(_FakeLLM(), **paths).judge(case_id="B", expected="x", actual="b")

    assert json.loads(paths["cap_path"].read_text(encoding="utf-8"))["count"] == 2


async def test_goi_thu_101_raise_cap_reached(tmp_path: Path) -> None:
    """Chạm cap ⇒ **raise** `JudgeUnavailable(reason=CAP_REACHED)`, KHÔNG trả `(False, 0.0)`.

    Đây là bất biến nặng nhất của T2. Trả một giá trị hợp lệ là biến *"không chấm được"* thành *"chấm
    và trượt"* — **cùng đúng lớp lỗi fail-open** mà DE tìm ra ở `chunks_from_trace` (`[]` đọc thành
    *"hàng rào chặn sạch"*), bị bắt trong code của chính quadrant này 24h trước. Lặp lại nó ở module
    kế bên là không học được gì.

    `cap=3` thay vì 100: bài đo **luật**, không đo con số. Chạy 100 lần double chỉ làm bài chậm hơn
    mà không canh thêm bất biến nào — còn `cap` là tham số nên 3 và 100 đi qua đúng một nhánh code."""
    llm = _FakeLLM()
    judge = LLMJudge(llm, **_paths(tmp_path), cap=3)

    for i in range(3):
        await judge.judge(case_id=f"C-{i}", expected="x", actual=f"a-{i}")

    with pytest.raises(JudgeUnavailable) as excinfo:
        await judge.judge(case_id="C-3", expected="x", actual="a-3")

    assert excinfo.value.reason is JudgeUnavailableReason.CAP_REACHED
    # Provider KHÔNG được chạm ở lần bị từ chối — cap phải chặn TRƯỚC khi tiêu tiền.
    assert len(llm.calls) == 3


async def test_cache_hit_van_tra_duoc_sau_khi_cham_cap(tmp_path: Path) -> None:
    """Cache hit **sau** khi chạm cap vẫn trả được — cache không cần quota.

    Chiều ngược của bài trên, và nó chặn một bản vá "an toàn quá đà": đặt kiểm cap **trước** kiểm
    cache sẽ làm mọi case đã chấm rồi cũng bị từ chối khi hết quota, tức vứt đúng phần việc đã trả
    tiền. Thứ tự đúng là **cache trước, cap sau**, và bài này là chỗ thứ tự đó bị khoá."""
    llm = _FakeLLM()
    judge = LLMJudge(llm, **_paths(tmp_path), cap=1)

    lan_dau = await judge.judge(case_id="HB-01", expected="x", actual="y")

    # Case MỚI ⇒ hết quota thật.
    with pytest.raises(JudgeUnavailable) as excinfo:
        await judge.judge(case_id="HB-02", expected="x", actual="z")
    assert excinfo.value.reason is JudgeUnavailableReason.CAP_REACHED

    # Case CŨ ⇒ vẫn trả được, và vẫn không chạm provider.
    assert await judge.judge(case_id="HB-01", expected="x", actual="y") == lan_dau
    assert len(llm.calls) == 1


async def test_counter_hong_fail_closed_state_unreadable(tmp_path: Path) -> None:
    """Counter đọc **không được** ⇒ coi như đã chạm trần ⇒ raise `STATE_UNREADABLE`. **Fail-closed.**

    Luật này đã áp ở **bốn** chỗ khác trong quadrant: `tenant_scope_ok` (`events` rỗng ⇒ `False`),
    `chunks_from_trace` (payload không đọc được ⇒ `None`), `_citation_tenant` (không parse được ⇒
    `None`), `compute_scorecard` (`results` rỗng ⇒ raise). Một counter hỏng mà cho phép gọi tiếp là
    chỗ **duy nhất** trong quadrant fail-**open**, và nó fail-open về phía **tốn tiền thật**.

    `reason` riêng chứ không gộp vào `CAP_REACHED`: hai trạng thái này đòi hai hành động khác nhau —
    chạm cap thì mai reset và số của run vẫn tin được; state hỏng thì cần **dọn file** và số của run
    này **không** tin được. Đây là mutant `M-J4` (fail-open) và `M-J6` (gộp reason)."""
    paths = _paths(tmp_path)
    paths["cap_path"].write_text("{ khong phai json", encoding="utf-8")
    llm = _FakeLLM()

    with pytest.raises(JudgeUnavailable) as excinfo:
        await LLMJudge(llm, **paths).judge(case_id="HB-01", expected="x", actual="y")

    assert excinfo.value.reason is JudgeUnavailableReason.STATE_UNREADABLE
    assert len(llm.calls) == 0


async def test_provider_loi_raise_provider_unavailable(tmp_path: Path) -> None:
    """Provider ném ⇒ raise `PROVIDER_UNAVAILABLE`, không nuốt thành một verdict.

    `reason` này là cái **duy nhất** trong ba cái cần **người** cấp phát (ask ③ — key Gemini). Gộp nó
    vào `CAP_REACHED` sẽ khiến báo cáo nói *"hết quota, mai chạy lại"* trong khi sự thật là *"chưa bao
    giờ có key"* — một tín hiệu vận hành sai hướng hoàn toàn."""
    llm = _BoomLLM()

    with pytest.raises(JudgeUnavailable) as excinfo:
        await LLMJudge(llm, **_paths(tmp_path)).judge(case_id="HB-01", expected="x", actual="y")

    assert excinfo.value.reason is JudgeUnavailableReason.PROVIDER_UNAVAILABLE
    assert len(llm.calls) == 1


async def test_judge_khong_biet_gemini_ton_tai(tmp_path: Path) -> None:
    """**Bất biến cưỡng chế `DEC-D18-02`:** `judge.py` không import `studio_app`, không đọc env,
    không dựng provider.

    Bài này không chứng minh judge hôm nay đúng — nó chặn **vi phạm tương lai**. Không có nó thì
    `DEC-D18-02` chỉ là một câu trong decision-log, và lần sửa nào đó thấy tiện sẽ `import
    studio_app` hoặc `os.environ["STUDIO_GEMINI_API_KEY"]` cho nhanh: chạy tốt trong workspace,
    `ImportError` trong fresh clone của `kit#74` (clone riêng evalhub thì `apps/studio` không tồn
    tại), và kéo mạng vào CI."""
    nguon = (Path(__file__).resolve().parent.parent / "src" / "studio_evalhub" / "judge.py").read_text(encoding="utf-8")

    assert "studio_app" not in nguon
    assert "environ" not in nguon
    assert "getenv" not in nguon
