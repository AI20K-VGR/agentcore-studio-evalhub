"""Nhánh judge của `EvalHarness.run` — wiring + tụt nấc. **Tất định, 0 call mạng** (`DEC-D18-02/03`).

Bốn thứ được khoá ở đây, và ba trong bốn nói về *cái KHÔNG xảy ra*:

1. `judge=None` (mặc định) ⇒ **không đổi một dòng** hành vi hôm nay;
2. case trượt exact-match ⇒ đi qua judge — nhánh **chạy thật**, không phải chết;
3. `JudgeUnavailable` ⇒ tụt nấc exact-match, **không** vỡ run;
4. tụt nấc phải **ghi lại kèm `reason`** — một run tụt nấc mà trông y hệt run không tụt là một
   scorecard nói dối về phương pháp của chính nó.

**Judge dùng ở đây là `LLMJudge` THẬT, chỉ `LLM` là double** — không dựng một judge giả. Cap chạm
được bằng `cap=0`, provider hỏng được bằng một `LLM` ném; hai đường đó đi qua đúng code T2 đã cài chứ
không qua một stub mô phỏng lại nó. Một judge giả sẽ khiến bài xanh kể cả khi `JudgeUnavailable` thật
mang hình dạng khác.

**Fixture nằm ngoài golden-30 có chủ đích** (`DEC-D18-07`): 0/30 case production cần judge, nên nhánh
judge được chứng minh bằng case dựng trong test. Định tuyến **không** dùng field mới — xem
`test_case_truot_exact_match_moi_di_qua_judge`.
"""

from __future__ import annotations

import ast
import logging
from collections.abc import Mapping
from pathlib import Path
from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest
from studio_contracts import NodeType, Tokens, TraceEvent
from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
from studio_evalhub.harness import EvalHarness
from studio_evalhub.judge import JudgeUnavailableReason, LLMJudge

_REF = "fx-judge-v1"
_TS = 0.9
_TC = 0.95

# Hai case, **bất đối xứng theo nhánh chấm**: FX-01 khớp exact-match, FX-02 KHÔNG. Cân hai case
# theo cùng một kiểu thì một mutant định tuyến sai vẫn cho ra cùng số lần gọi judge.
_YAML = """\
golden_set_ref: fx-judge-v1
cases:
  - case_id: FX-01
    query: "Nghỉ phép năm bao nhiêu ngày?"
    tenant: ankor
    section_roles: [hr]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "12 ngày"
    expected_citation: []
  - case_id: FX-02
    query: "Duyệt chi phí mất bao lâu?"
    tenant: ankor
    section_roles: [hr]
    expected_tenant: ankor
    expected_section_role: hr
    expected: "ba ngày làm việc"
    expected_citation: []
"""


class _FakeLLM:
    """`LLM` double — `calls` là thứ mọi bài định tuyến assert lên."""

    def __init__(self, reply: str = "PASS") -> None:
        self.calls: list[str] = []
        self._reply = reply

    async def complete(self, prompt: str, **kwargs: object) -> str:
        self.calls.append(prompt)
        return self._reply


class _BoomLLM:
    async def complete(self, prompt: str, **kwargs: object) -> str:
        raise RuntimeError("no API key configured")


def _tenant_ids() -> Mapping[str, UUID]:
    return {"ankor": uuid5(NAMESPACE_DNS, "ankor")}


def _event(tenant_id: UUID) -> TraceEvent:
    return TraceEvent(
        event_id="e1",
        run_id="r1",
        agent_id="a",
        tenant_id=tenant_id,
        node_id="n1",
        node_type=NodeType.KB_RETRIEVE,
        ts="2026-08-12T00:00:00+00:00",
        inputs_hash="h",
        outputs={"chunks": []},
        tokens=Tokens(prompt=0, completion=0),
        cost=0.0,
        citations=[],
    )


def _runner() -> StubAgentRunner:
    """FX-01 trả **đúng cụm** `expected`; FX-02 trả **cùng ý, khác chữ**.

    FX-02 chính là ca mà `judge.py` docstring gọi là *subjective*: `"Khoảng 3 ngày làm việc"` truyền
    tải đúng `"ba ngày làm việc"` nhưng `_contains_phrase` (so token liên tiếp) không bắt được. Đây
    là lý do nhánh judge tồn tại, và là ca duy nhất trong fixture này được định tuyến sang nó.
    """
    tenant_id = _tenant_ids()["ankor"]
    return StubAgentRunner(
        {
            ("Nghỉ phép năm bao nhiêu ngày?", tenant_id, ("hr",)): CaseRun(
                answer=AgentAnswer(answer="Theo tài liệu, nghỉ phép 12 ngày.", citations=[], refused=False),
                events=[_event(tenant_id)],
            ),
            ("Duyệt chi phí mất bao lâu?", tenant_id, ("hr",)): CaseRun(
                answer=AgentAnswer(answer="Khoảng 3 ngày làm việc.", citations=[], refused=False),
                events=[_event(tenant_id)],
            ),
        }
    )


async def _chay(path: Path, judge: LLMJudge | None) -> object:
    return await EvalHarness().run(
        "agent-fx",
        _REF,
        golden_set_path=path,
        runner=_runner(),
        tenant_ids=_tenant_ids(),
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        judge=judge,
    )


@pytest.fixture
def golden_fx(tmp_path: Path) -> Path:
    path = tmp_path / "fx-judge.yaml"
    path.write_text(_YAML, encoding="utf-8")
    return path


async def test_judge_none_khong_doi_mot_dong_hanh_vi(golden_fx: Path) -> None:
    """`judge` **additive, default `None`** ⇒ mọi call-site hiện tại chạy nguyên.

    So **hai lần chạy**: một lần không truyền `judge` (đúng cách mọi call-site hôm nay gọi — `cli.py`,
    2 bài integration, `apps/studio`), một lần truyền tường minh `judge=None`. Hai scorecard phải
    **bằng nhau tuyệt đối**, không chỉ cùng verdict.

    Assert bằng `==` trên cả object thay vì so từng field: `Scorecard` là model frozen nên `==` là so
    sâu, và một field mới lặng lẽ khác nhau sẽ lộ ra ở đây chứ không cần bài này biết trước field nào
    đáng ngờ."""
    khong_truyen = await EvalHarness().run(
        "agent-fx",
        _REF,
        golden_set_path=golden_fx,
        runner=_runner(),
        tenant_ids=_tenant_ids(),
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
    )
    truyen_none = await _chay(golden_fx, judge=None)

    assert khong_truyen == truyen_none


async def test_judge_none_moi_case_result_judge_la_none(golden_fx: Path) -> None:
    """`judge=None` ⇒ **mọi** `CaseResult.judge is None` — *"case này chấm KHÔNG qua LLM-judge"*.

    Giá trị trung thực duy nhất trước S3 (`DEC-02`). Một `Judge(...)` hằng số ở đây không phân biệt
    được với một judge thật đồng thuận 100%, và nó hỏng âm thầm mọi aggregate trên `agreement`."""
    scorecard = await _chay(golden_fx, judge=None)

    assert [r.judge for r in scorecard.results] == [None, None]  # type: ignore[attr-defined]


async def test_case_truot_exact_match_moi_di_qua_judge(golden_fx: Path, tmp_path: Path) -> None:
    """**Định tuyến**: chỉ case **trượt** exact-match mới đi qua judge. Case khớp thì không.

    Đây là chỗ khoá lý lẽ `DEC-D18-07` bằng hành vi thay vì bằng lời hứa: định tuyến **không** đọc
    một field mới nào (`match_mode` không tồn tại), nó dẫn xuất từ **chính kết quả chấm exact-match**
    — đúng nguyên văn hai docstring đã có từ trước (`judge.py:3` *"scores subjective (non-exact-match)
    cases"*, `harness.py:420` *"exact-match cases score directly"*).

    Hệ quả đo được: golden-30 với runner tốt ⇒ **0 case** đi qua judge, khớp phép đo *"0/30 case cần
    judge"* của nền D18. Không có tập rỗng nào được dựng đường dẫn riêng.

    Assert `len(llm.calls) == 1`, **không** `>= 1`: judge được gọi cho FX-02 và **chỉ** FX-02. Một
    bản vá gọi judge cho mọi case answer-branch sẽ xanh với `>= 1` và đỏ ở đây — mà đó đúng là bản vá
    biến golden-30 thành 22 lần gọi LLM mỗi lần chạy."""
    llm = _FakeLLM(reply="PASS")
    judge = LLMJudge(llm, cache_path=tmp_path / "c.json", cap_path=tmp_path / "q.json")

    scorecard = await _chay(golden_fx, judge=judge)

    assert len(llm.calls) == 1
    assert "ba ngày làm việc" in llm.calls[0]  # đúng case FX-02, không phải FX-01

    ket_qua = {r.case_id: r.success for r in scorecard.results}  # type: ignore[attr-defined]
    assert ket_qua == {"FX-01": True, "FX-02": True}  # FX-02 PASS nhờ judge, không nhờ exact-match


async def test_judge_noi_fail_thi_case_van_fail(golden_fx: Path, tmp_path: Path) -> None:
    """Judge trả `FAIL` ⇒ case **trượt**. Bài đối trọng của bài trên.

    Không có nó thì `test_case_truot_exact_match_moi_di_qua_judge` không phân biệt được *"judge được
    hỏi và trả lời"* với *"harness bỏ qua judge rồi cho PASS bừa"* — cả hai đều cho FX-02 xanh."""
    llm = _FakeLLM(reply="FAIL")
    judge = LLMJudge(llm, cache_path=tmp_path / "c.json", cap_path=tmp_path / "q.json")

    scorecard = await _chay(golden_fx, judge=judge)

    ket_qua = {r.case_id: r.success for r in scorecard.results}  # type: ignore[attr-defined]
    assert ket_qua == {"FX-01": True, "FX-02": False}


async def test_cham_cap_thi_tut_nac_chu_khong_vo_run(golden_fx: Path, tmp_path: Path) -> None:
    """`JudgeUnavailable(CAP_REACHED)` ⇒ **tụt nấc exact-match**, run vẫn ra `Scorecard` đủ 2 case.

    `cap=0` ⇒ `LLMJudge` THẬT chạm trần ngay lần gọi đầu, nên đường đi qua đúng code T2 đã cài chứ
    không qua một stub mô phỏng exception.

    Kết quả phải **trùng khít** run không có judge: tụt nấc nghĩa là *quay về* nấc exact-match, không
    phải *một nấc thứ ba* nào đó. So với `judge=None` thay vì assert từng field là cách khoá điều đó
    mà không phải liệt kê trước cái gì có thể lệch."""
    judge = LLMJudge(_FakeLLM(), cache_path=tmp_path / "c.json", cap_path=tmp_path / "q.json", cap=0)

    tut_nac = await _chay(golden_fx, judge=judge)
    khong_judge = await _chay(golden_fx, judge=None)

    assert tut_nac == khong_judge


async def test_provider_hong_cung_tut_nac(golden_fx: Path, tmp_path: Path) -> None:
    """`PROVIDER_UNAVAILABLE` cũng tụt nấc — **cùng một nhánh xử lý** với `CAP_REACHED`.

    `DEC-D18-05` chốt: fallback đi cùng một nhánh cho cả ba `reason`, cái khác nhau **chỉ là thứ được
    ghi lại**. Bài này khoá vế thứ nhất (gộp nhánh xử lý); bài dưới khoá vế thứ hai (tách nhãn ghi
    nhận). Tách hai vế ra hai bài vì chúng hỏng độc lập với nhau."""
    judge = LLMJudge(_BoomLLM(), cache_path=tmp_path / "c.json", cap_path=tmp_path / "q.json")

    tut_nac = await _chay(golden_fx, judge=judge)
    khong_judge = await _chay(golden_fx, judge=None)

    assert tut_nac == khong_judge


@pytest.mark.parametrize(
    ("dung_llm_hong", "cap", "reason_mong_doi"),
    [
        (True, 100, JudgeUnavailableReason.PROVIDER_UNAVAILABLE),
        (False, 0, JudgeUnavailableReason.CAP_REACHED),
    ],
    ids=["provider-hong", "cham-cap"],
)
async def test_tut_nac_phai_duoc_ghi_lai_kem_reason(
    golden_fx: Path,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    *,
    dung_llm_hong: bool,
    cap: int,
    reason_mong_doi: JudgeUnavailableReason,
) -> None:
    """Tụt nấc **không được nuốt câm** — phải ghi lại, và ghi kèm **`reason`**.

    **Phủ CẢ HAI đường tụt nấc, và đó là bản vá do mutation ép ra.** Bản đầu chỉ chạy đường
    `PROVIDER_UNAVAILABLE`, và `M-J3` (*chạm cap ⇒ trả `False` thay vì raise*) **SỐNG SÓT** ở phía
    harness. Lý do đáng ghi vì nó không hiển nhiên:

    - đúng: judge raise ⇒ harness giữ nguyên kết quả exact-match của FX-02 ⇒ `success=False`;
    - `M-J3`: judge trả `False` ⇒ harness ghi đè `success=False`;
    - ⇒ **hai `Scorecard` trùng khít**. Không assert nào trên kết quả phân biệt được chúng.

    Thứ duy nhất phân biệt được là **dòng log**, nên đường `CAP_REACHED` bắt buộc phải có mặt ở đây
    chứ không chỉ ở bài so `Scorecard`. Bài so `==` vẫn giữ (nó khoá *gộp nhánh xử lý*), nhưng nó
    **không đủ** để canh *"không nuốt câm"* — hai bất biến khác nhau cần hai lưới khác nhau.

    Ba `reason` đòi ba hành động khác nhau của con người (đợi mai · cần người cấp key · cần dọn file
    hỏng), nên assert **giá trị** `reason`, không chỉ assert *có một dòng log* — đường lọt của `M-J6`.

    Một run tụt nấc mà trông y hệt run không tụt là một scorecard **nói dối về phương pháp của chính
    nó**: cùng một `Scorecard`, hai phương pháp chấm khác nhau, và người đọc không có cách nào biết.
    `Scorecard` không đổi được một byte (`DEC-D18-06`), nên chỗ ghi là **log** — kênh đúng cho một
    tín hiệu vận hành.
    """
    llm = _BoomLLM() if dung_llm_hong else _FakeLLM()
    judge = LLMJudge(llm, cache_path=tmp_path / "c.json", cap_path=tmp_path / "q.json", cap=cap)

    with caplog.at_level(logging.WARNING):
        await _chay(golden_fx, judge=judge)

    ghi_nhan = [r.getMessage() for r in caplog.records if "descope" in r.getMessage().lower()]
    assert ghi_nhan, "tụt nấc bị nuốt câm — không dòng log nào ghi lại"
    assert any(reason_mong_doi.value in m for m in ghi_nhan)
    assert any("FX-02" in m for m in ghi_nhan)  # ghi cả case nào bị tụt, không chỉ "có tụt"


def test_conftest_khong_dung_provider_that() -> None:
    """**Ô DoD "CI deterministic"**: không file test nào trong quadrant dựng provider thật.

    Bài quét nguồn, không quét hành vi — nó chặn **vi phạm tương lai**, không chứng minh hôm nay
    đúng. Ai đó thêm `GeminiProvider` vào một fixture sẽ làm CI phụ thuộc key + mạng, và nó hỏng theo
    kiểu tệ nhất: xanh trên máy có `.env`, đỏ trên CI, và **tốn tiền thật** mỗi lần chạy suite.

    `DEC-D18-02` làm điều này thành hệ quả **cấu trúc**: judge nhận `LLM` tiêm vào, nên không có chỗ
    nào trong test cần biết provider thật tồn tại.

    **Quét AST, KHÔNG quét văn bản thô** — bài học đã trả giá hai lần: bản đầu của chính bài này quét
    chuỗi và **tự bắt chính nó** (tên cấm nằm ngay trong danh sách cấm), y hệt lần
    `test_src_khong_hardcode_duong_dan_kb` bắt oan một docstring ở T1. Quét AST tránh hẳn: ở đây
    `GeminiProvider` là một `Constant` trong mẫu match, còn thứ bị quét là node `Name`/`Attribute`.

    **Phạm vi hẹp đúng bằng thứ `DEC-D18-02` cấm — provider LLM thật, không phải `studio_app` nói
    chung.** Bản đầu cấm mọi import `studio_app` và mọi truy cập env, rồi bắt đúng hai ca **hợp lệ**:
    `test_scorecard_roundtrip.py` import `studio_app.core._db` và `test_determinism.py` đọc env — cả
    hai là bài **Postgres**, chẳng liên quan gì tới mạng LLM. Cấm chúng là bắt oan, và một bài bắt oan
    sẽ bị nới lỏng, kéo theo cả cái lưới thật. `studio_app.providers.fakes` cũng **không** bị cấm: nó
    là double, đúng thứ `DEC-D18-02` muốn người ta dùng."""
    tests_dir = Path(__file__).resolve().parent
    vi_pham: list[str] = []

    for file in sorted(tests_dir.rglob("*.py")):
        cay = ast.parse(file.read_text(encoding="utf-8"))
        ten = file.relative_to(tests_dir)

        for node in ast.walk(cay):
            match node:
                case ast.ImportFrom(module=str(mod)) if mod.startswith("studio_app.providers.gemini"):
                    vi_pham.append(f"{ten}:{node.lineno} → from {mod} import ...")
                case ast.Name(id="GeminiProvider") | ast.Attribute(attr="GeminiProvider"):
                    vi_pham.append(f"{ten}:{node.lineno} → dựng provider LLM thật")
                case _:
                    pass

    assert not vi_pham, "CI phải tất định: test không được dựng provider LLM thật.\n" + "\n".join(vi_pham)
