"""Eval-harness seam — spec AIE-2 (R-SPEC A7).

Runs the 30-case golden set (produced by DE's doc-factory, consumed here — AIE-2 does NOT
generate golden sets) through an agent recipe's DAG (executed by AIE-1's interpreter, consumed
here — AIE-2 does NOT own the interpreter), scores each case (subjective cases via `judge.py`,
exact-match cases directly), then hands the per-case results to `compute.py` to aggregate into a
`Scorecard` (P2 contract). P9's SWE-owned publish/rollback pipeline is the consumer of the
resulting `Scorecard.gate.verdict` — this module produces the verdict, never wires the gate
itself (R-SPEC A4 ownership fence).

`EvalHarness.run()` (đích cuối `-> Scorecard`) vẫn `NotImplementedError`: nó cần `compute_scorecard`
(Day 4–5) và nguồn golden-set thật (Q5, `docs/scorecard-v0.md`). Building-block skeleton D3 nằm ở
`run_smoke()` + `score_case()` bên dưới — chạy case qua seam `AgentRunner`, chấm 2 nhánh, trả
`SmokeResult` (kiểu nội bộ, chưa lên `CaseResult` vì Q1 chưa chốt).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from studio_contracts import CaseResult, NodeType, Scorecard, TraceEvent

from studio_evalhub.agent_runner import AgentAnswer, AgentRunner, CaseRun
from studio_evalhub.compute import compute_scorecard
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.golden_loader import load_golden_set
from studio_evalhub.judge import JudgeUnavailable, LLMJudge

# Logger đầu tiên của quadrant, và nó tồn tại vì đúng một lý do: tụt nấc judge phải **quan sát được**
# mà `Scorecard` thì không đổi được một byte (`DEC-D18-06`). Log là kênh cho tín hiệu vận hành —
# không phải chỗ chứa kết quả đo, và không có gì khác trong module này ghi log.
_logger = logging.getLogger(__name__)


class SmokeResult(BaseModel):
    """Kết quả chấm một case ở tầng skeleton — output của `score_case`/`run_smoke`.

    Cố ý KHÔNG phải `studio_contracts.CaseResult`: `CaseResult.judge` là trường bắt buộc, còn
    smoke-case toàn exact-match/refusal nên không có judge (Q1, `docs/scorecard-v0.md`). Điền một
    `Judge` hằng số là thứ `judge.py` cấm; sửa contract cho `judge` optional cần mentor-approval —
    cả hai để D11. Đến lúc đó, `SmokeResult` là kiểu riêng của quadrant (như `RunResult` của engine),
    đổi shape không cần mini-RFC.
    """

    model_config = ConfigDict(frozen=True)

    case_id: str
    expected: str
    actual: str
    success: bool
    citation_accuracy: float
    expects_refusal: bool = False
    """Case này thuộc nhánh **từ-chối** hay nhánh **trả-lời** — dẫn xuất từ
    `GoldenCase.expects_refusal` (`golden_case.py:88`), copy sang đây để **tầng render đọc được nhánh
    mà không phải join lại với golden-set** (DEC-D12-01, D12 `kit#88`).

    Vì sao cần field thay vì suy ra: `citation_accuracy == 1.0` trên nhánh từ-chối là **quy ước
    vacuous-truth**, và `expected_citation == []` ở nhánh trả-lời **cũng** trả `1.0`
    (`harness.py:167`) ⇒ suy nhánh từ con số là không phân biệt được, đúng lớp lỗi breakpoint `#14`
    (suy một cờ ngữ nghĩa từ một giá trị số ⇒ **xanh-giả**).

    Vì sao thêm được mà không cần mini-RFC: xem docstring class — `SmokeResult` là kiểu riêng của
    quadrant. `citation_accuracy` **giữ `float`** nên 3 renderer format `:.2f` không đổi một dòng.
    Default `False` để mọi constructor cũ vẫn dựng được (additive)."""


class _NotProvided:
    """Sentinel cho `score_case(retrieved_chunks=...)` — **"caller không đi đường chunks"**.

    Phải khác `None`, và đây là chỗ mà một `Optional` trần sẽ nói dối: `None` có nghĩa riêng
    (*"đã đọc trace nhưng không quan sát được event `kb-retrieve`"* ⇒ fail-closed). Gộp hai nghĩa
    vào một giá trị thì hoặc 6 call-site cũ (`apps/studio` ×4, `run_report`, `score_run_from_trace`)
    đột nhiên chấm FAIL mọi case từ-chối, hoặc ca không-quan-sát-được được cho qua im lặng — cả hai
    đều là lỗi nặng hơn cái đang vá."""

    __slots__ = ()


_NOT_PROVIDED = _NotProvided()


def _citation_tenant(chunk_id: str) -> str | None:
    """Tenant của chunk suy từ tiền tố id (định dạng DE `ankor-leave-001#c1` → `ankor`).

    Trả `None` khi id không đúng dạng (thiếu dấu `-` hoặc tiền tố rỗng) — nhánh từ-chối coi
    None là fail-closed (không parse được ⇒ không chứng minh được là an toàn)."""
    prefix, sep, _rest = chunk_id.partition("-")
    if not sep or not prefix:
        return None
    return prefix


class RetrievedChunk(TypedDict):
    """Một chunk RETRIEVAL trả về, đúng shape `KbSearchResultItem.model_dump(mode="json")` mà
    `interpreter.py:347` ghi vào `outputs["chunks"]` của event `kb-retrieve`.

    **Giữ đủ 5 khoá, không rút gọn.** `tenant_id` và `section_role` là hai field mà `no_leak` chấm
    trên đó (`DEC-D17-03`); rút thành `chunk_id` là quay lại đoán tenant bằng tiền tố slug
    (`_citation_tenant`) — đúng heuristic mà `F-6` tồn tại để bỏ."""

    chunk_id: str
    tenant_id: str
    section_role: str
    score: float
    text: str


def chunks_from_trace(events: Sequence[TraceEvent]) -> list[RetrievedChunk] | None:
    """Chunk RETRIEVAL trả về (`kb-retrieve` → `outputs["chunks"]`) — KHÁC `citations` (`llm-step`,
    thứ câu trả lời thật sự dựa vào). `trace.py:39-45` tách sẵn hai fact này: *"retrieved
    (kb-retrieve, scope-filtered, may be irrelevant) and cited/grounded (llm-step, what the answer
    actually used) are different facts"*.

    Vì sao `F-6` cần nó: nhánh từ-chối chấm `no_leak` trên `citations`, mà mọi runner phát **0
    citation** khi từ chối ⇒ luật đúng và luật sai cho **cùng** kết quả (vacuous). Hàng rào lọc ở
    tầng *retrieved*, nên bộ chấm phải nhìn đúng tầng đó mới có dữ liệu để một luật sai **sai được**.

    Ba giá trị trả về, ba nghĩa KHÁC nhau — đây là chỗ dễ chọn sai nhất:

    - `None` ⇒ **không quan sát được** — không event `kb-retrieve` nào, **hoặc** có event nhưng
      `outputs["chunks"]` không đọc được (thiếu khoá · không phải list · có phần tử không phải
      dict). Fail-closed: không chứng minh được thì không phải là đạt (cùng luật
      `tenant_scope_ok:130`, `DEC-05`).
    - `[]` ⇒ có event nhưng retrieval trả rỗng ⇒ **hàng rào chặn sạch**, bằng chứng TỐT.
    - non-empty ⇒ có chunk rời khỏi retrieval; `no_leak` xét từng cái theo đúng trục đã kích refusal.

    Gom theo `node_type is NodeType.KB_RETRIEVE` chứ **không** node-agnostic như
    `citations_from_trace`: `outputs["chunks"]` là khoá của riêng node đó (`interpreter.py:218`),
    trong khi `citations` từng bị hai bề mặt khai khác nhau nên phải gom rộng cho robust."""
    retrieve_events = [event for event in events if event.node_type is NodeType.KB_RETRIEVE]
    if not retrieve_events:
        return None
    out: list[RetrievedChunk] = []
    for event in retrieve_events:
        raw = event.outputs.get("chunks")
        if not isinstance(raw, list) or not all(isinstance(chunk, dict) for chunk in raw):
            # Có event `kb-retrieve` nhưng payload KHÔNG đọc được ⇒ `None`, không phải `[]`.
            # Vá sau review `evalhub#18` (DE): bản đầu `continue` qua event hỏng rồi trả `[]`, mà
            # `[]` ở tầng trên nghĩa là *"hàng rào chặn sạch"* — một bằng chứng TỐT. Tức một
            # retrieval LỖI được chấm nhẹ hơn một run KHÔNG CÓ retrieval, ngược hẳn fail-closed.
            # Một phần tử hỏng cũng làm cả lô `None`: lọc lặng phần tử là **báo thiếu**, và bộ chấm
            # sẽ kết luận "không rò" trên tập nhỏ hơn thứ retrieval thật sự trả về.
            return None
        out.extend(cast("RetrievedChunk", chunk) for chunk in raw)
    return out


def citations_from_trace(events: list[TraceEvent]) -> list[str]:
    """Tập chunk **quan sát được** của một run: gom `.citations` từ **mọi** trace event có
    (bỏ `None`), **không phụ thuộc `node_type`** (D5 #24 — chấm điểm theo trace, mặt quan sát thật).

    **API công khai từ D7** (trước là `_retrieved_citations`). Lý do đổi: nó là *phép đo* mà mọi
    consumer của scorecard cần — `apps/studio` dùng ở cả script e2e lẫn test chấm-từ-Postgres, và
    `scripts/smoke_eval_d6.py` ở repo cha import nó **xuyên repo**. Một hàm có người ngoài quadrant
    phụ thuộc thì không còn là chi tiết nội bộ; giữ dấu gạch dưới chỉ khiến người dùng phải phá
    quy ước để làm việc đúng. Alias `_retrieved_citations` giữ cuối module suốt D7→D18 để không
    consumer nào vỡ khi đổi; **gỡ ở D18/T6** (`T9c` bước 2) sau khi đo bằng AST ra **0 consumer
    thật** trên toàn workspace. Bài `test_alias_retrieved_citations_da_go` giữ cho nó không quay lại.

    Vì sao tên là `citations_from_trace` chứ không phải `retrieved_citations`: `score_case` đã có
    **tham số** tên `retrieved_citations`, và 14 call-site truyền nó bằng keyword nên tên tham số
    không đổi được. Đặt hàm cùng tên sẽ che tham số trong thân `score_case` — ai sau này gọi
    `retrieved_citations(events)` ở đó sẽ gặp `list is not callable`. Tên hiện tại nói đúng việc
    (trích citation TỪ trace) và không đụng gì.

    Node nào mang citations là do engine quyết: thực tế (interpreter AIE-1, branch day5) nâng
    citations từ output **`llm-step`** lên trace event của node đó (chunk agent thực sự trích —
    grounded ∩ retrieved); event `kb-retrieve` để `citations=None` (output là list, không có key).
    Contract lại chú thích `TraceEvent.citations  # from kb-retrieve`. Vì thế gom **node-agnostic** để
    robust với cả hai (đã xác nhận qua thread-check franken-workspace 2026-07-24); v0 smoke chỉ một
    node mang citations nên không trộn retrieved/cited. Chốt carrier chính xác với AIE-1 → siết theo
    node cụ thể nếu cần. Đây là nguồn cho citation-accuracy (nhánh trả-lời-được) và leak-check (nhánh
    từ-chối), thay cho `AgentAnswer.citations` mà agent tự khai."""
    retrieved: list[str] = []
    for event in events:
        if event.citations is not None:
            retrieved.extend(event.citations)
    return retrieved


def tenant_scope_ok(events: list[TraceEvent], expected: UUID) -> bool:
    """Mọi trace event của một run có mang ĐÚNG `expected` ở `tenant_id` hay không (D8 #39).

    **API công khai từ D8.** Bất biến này trước đó chỉ tồn tại dưới dạng một dòng trong *script*
    `apps/studio/scripts/e2e_smoke_eval.py` (`tenant_consistent = all(...)`). Script không chạy thì
    bất biến không được kiểm, và script đó lại nằm trong một PR chưa merge — nên nó được nâng lên
    thành hàm thuần ở đây để sống độc lập với việc PR kia có vào `main` hay không.

    **Fail-closed: `events` rỗng ⇒ `False`.** Không có trace thì không CHỨNG MINH được scope đúng, và
    "không chứng minh được" phải đọc là chưa đạt, không phải mặc định đạt. Đây là chỗ dễ chọn sai:
    `all([])` trong Python là `True`, nên viết thẳng `all(...)` sẽ cho một run **không có event nào**
    điểm hợp lệ — đúng loại xanh-giả mà `_LeakyKb` được dựng ra để phát hiện.

    Quan hệ với DoD *"`tenant_id` NOT NULL"* (`day-08.md`): `TraceEvent.tenant_id` đã là `UUID`
    non-optional trong `studio_contracts`, nên NOT NULL đúng sẵn **ở mức kiểu** — pydantic chặn
    `None` trước khi event tồn tại. Thứ *chưa* ai đo là **nhất quán**: mọi event trong CÙNG một run
    trỏ về cùng một tenant. Một run mà node đầu mang ankor còn node sau mang borea vẫn thoả NOT NULL
    từng dòng mà vỡ hoàn toàn ở mức run. Hàm này đo đúng khoảng trống đó.

    **Observe-only — KHÔNG gate `success`.** Bộ chấm quan sát hàng rào, không tạo ra hàng rào: fence
    thật là mandatory filter server-side (`StaticKbSearch` so UUID) cộng RLS. Hàm này chỉ báo. Vì thế
    nó nằm ngoài `score_case` chứ không thêm vào luật chấm — và cũng vì `score_case` không nhận
    `events` (chỉ nhận `retrieved_citations`), nên nó cấu trúc mà nói không đọc được `tenant_id`.
    Đổi chữ ký `score_case` để nhét vào là chuyện khác: 3 consumer ngoài quadrant đang gọi nó.
    """
    if not events:
        return False
    return all(event.tenant_id == expected for event in events)


def _tokenize(text: str) -> list[str]:
    r"""Tách `text` thành token cho so token-contains: lowercase + cắt theo `\w+` (unicode — chữ có
    dấu tiếng Việt và chữ số giữ nguyên thành một token). So theo token nguyên vẹn nên `"1 ngày"`
    KHÔNG khớp `"11 ngày"` (token `"11"` ≠ `"1"`) như substring thô sẽ mắc."""
    return re.findall(r"\w+", text.lower())


def _contains_phrase(answer_text: str, expected_phrase: str) -> bool:
    """True khi token của `expected_phrase` xuất hiện LIÊN TIẾP trong token của `answer_text`.

    Luật nhánh trả-lời-được (`docs/scorecard-v0.md` §2.3): `answer` CHỨA cụm `expected` là đúng, không
    bắt khớp cả câu / đúng chính tả / dấu câu. So token (không substring thô) để `"1 ngày"` không lọt
    vào `"11 ngày"`, mà `"1 ngày/tuần"`, `"...1 ngày."`, đầu/cuối câu vẫn khớp.

    Fail-closed: `expected_phrase` token hoá ra rỗng ⇒ False (không coi "cụm rỗng" là luôn khớp)."""
    expected_tokens = _tokenize(expected_phrase)
    if not expected_tokens:
        return False
    answer_tokens = _tokenize(answer_text)
    n = len(expected_tokens)
    return any(answer_tokens[i : i + n] == expected_tokens for i in range(len(answer_tokens) - n + 1))


def _no_leak_from_chunks(
    case: GoldenCase, chunks: list[RetrievedChunk], tenant_ids: Mapping[str, UUID]
) -> tuple[bool, bool]:
    """`(all_parseable, no_leak)` cho nhánh từ-chối, chấm trên **chunk RETRIEVAL** (`F-6`).

    Rẽ theo đúng trục đã kích refusal, y như luật `citations` nó thay thế — chỉ đổi **nguồn dữ
    liệu**, không đổi số conjunct (`DEC-D17-02`):

    | Trục | Điều kiện kích | `no_leak` đúng |
    |---|---|---|
    | **T1** chéo-tenant | `expected_tenant != tenant` (đáp án ở kho KHÁC) | mọi chunk thuộc kho NGƯỜI HỎI |
    | **T6** chéo-vai | `expected_tenant == tenant` (cùng kho, khác VAI) | mọi chunk đúng kho người hỏi
      **VÀ** vai họ giữ |

    **Khác bản `citations` ở đúng một điểm, và điểm đó là toàn bộ giá trị của `F-6`:** tenant so
    bằng **UUID thật** (`RetrievedChunk.tenant_id`) chứ không đoán bằng tiền tố `chunk_id`
    (`_citation_tenant`) — ngày DE đổi quy ước đặt tên là heuristic kia sai im lặng. Và trục T6 kiểm
    được **đúng thứ nó nói về** nhờ `section_role` có sẵn trong chunk, thay vì chỉ kiểm hộ trục
    tenant rồi ghi chú *"vai không đọc được"*.

    **Vì sao T1 so với kho NGƯỜI HỎI chứ không phải "cấm kho `expected_tenant`"** (khác chữ ở bảng
    T2 của plan, khớp bảng `DEC-D17-03`): với case T1, `expected_tenant` đúng là kho caller **không
    có quyền**, nên nó KHÔNG nằm trong `tenant_ids` của run — `tenant_ids[case.expected_tenant]` ném
    `KeyError` (đo được: 4 bài đỏ khi thử). Và "mọi chunk thuộc kho người hỏi" **mạnh hơn**: nó chặn
    cả rò từ kho thứ ba mà luật cũ không nhắc tới.

    `all_parseable` = mọi chunk khai đủ hai field định danh. Thiếu ⇒ không chứng minh được là an
    toàn ⇒ fail-closed, cùng quy ước `_citation_tenant` trả `None`."""
    all_parseable = all(bool(chunk.get("tenant_id")) and bool(chunk.get("section_role")) for chunk in chunks)
    caller_tenant = str(tenant_ids[case.tenant])
    in_caller_tenant = all(chunk.get("tenant_id") == caller_tenant for chunk in chunks)
    if case.expected_tenant is not None and case.expected_tenant != case.tenant:
        no_leak = in_caller_tenant
    else:
        allowed_roles = set(case.section_roles)
        no_leak = in_caller_tenant and all(chunk.get("section_role") in allowed_roles for chunk in chunks)
    return all_parseable, no_leak


def score_case(
    case: GoldenCase,
    answer: AgentAnswer,
    retrieved_citations: list[str],
    *,
    retrieved_chunks: list[RetrievedChunk] | None | _NotProvided = _NOT_PROVIDED,
    tenant_ids: Mapping[str, UUID] | None = None,
) -> SmokeResult:
    """Chấm một case theo luật v0 (`docs/scorecard-v0.md` §2.3), rẽ nhánh qua
    `GoldenCase.expects_refusal` (xét cả T1 chéo-tenant lẫn T6 chéo-vai).

    `retrieved_citations` = chunk đã trích **theo TRACE** (event `kb-retrieve`, từ
    `citations_from_trace`) — nguồn chấm citation, KHÔNG dùng `answer.citations` (agent tự khai):

    - **trả-lời-được**: `success` khi agent KHÔNG từ chối VÀ `answer` CHỨA cụm `expected`
      (`_contains_phrase` — so token liên tiếp, không bắt khớp cả câu/chính tả). `citation_accuracy`
      = |`expected_citation` ∩ `retrieved_citations`| / |`expected_citation`| (set-semantics, ≤1.0
      kể cả trace trùng; rỗng ⇒ 1.0). **`citation_accuracy` là metric riêng, KHÔNG gate `success`** —
      trace sai/rỗng ⇒ accuracy 0.0 nhưng vẫn PASS nếu answer đúng. Giới hạn: token-contains không
      bắt phủ định/ngữ cảnh — chỉ judge (S3).
    - **từ-chối**: **fail-closed** — `success` chỉ khi cả ba: agent thực sự từ chối (`refused`), mọi
      citation TRACE parse được tenant, và **không rò** theo luật của **đúng trục** đã kích refusal.
      Vi phạm bất kỳ ⇒ fail. Đây là **leak SANITY** (D-13, *sanity thứ cấp*): KHÔNG chứng minh fence
      RLS-UUID — nó **quan sát** thứ retrieval đã trả, không chứng minh retrieval không thể trả thứ
      khác; fence thật là mandatory filter + RLS server-side (`#110`/`#112`).
      `citation_accuracy` = 1.0 (quy ước vacuous-truth, `DEC-04`).

      **Nguồn của `no_leak` rẽ theo `retrieved_chunks` — `F-6` / `DEC-D17-02` (D17):**

      - **không truyền** (`_NOT_PROVIDED`) ⇒ đường CŨ, chấm trên `retrieved_citations`. Giữ cho 6
        call-site chưa đổi. Đường này **vacuous trên mọi runner thật**: đo trên golden-30 qua
        interpreter, 8/8 case từ-chối phát **0 citation** ⇒ luật đúng và luật sai cho cùng kết quả.
        Chữ *"theo chunk-id slug"* mô tả đúng đường này và **chỉ** đường này.
      - **`None`** ⇒ đã đọc trace nhưng không có event `kb-retrieve` ⇒ **fail-closed** (`success`
        False). `None` ≠ `[]`: `[]` là *hàng rào chặn sạch*, bằng chứng TỐT.
      - **list** ⇒ đường MỚI, chấm trên chunk RETRIEVAL qua `_no_leak_from_chunks`: tenant so bằng
        **UUID thật**, vai so bằng **`section_role` thật** — hết đoán tiền tố `chunk_id`, và trục T6
        kiểm được đúng thứ nó nói về. Đòi `tenant_ids`; thiếu ⇒ `ValueError`, không im lặng.

      **Luật `no_leak` rẽ theo trục — vá D16 sau review `kb#18` (N1).** Bản trước dùng **một** biểu
      thức `_citation_tenant(c) != expected_tenant` cho cả hai trục. Đúng cho T1, **sai cho T6**:

      | Trục | Điều kiện kích | `no_leak` đúng |
      |---|---|---|
      | **T1** chéo-tenant | `expected_tenant != tenant` — đáp án ở kho KHÁC | không chunk nào thuộc `expected_tenant` |
      | **T6** chéo-vai | `expected_tenant == tenant` — cùng kho, khác VAI | mọi chunk phải thuộc đúng `tenant` |

      Với T6 thì `expected_tenant == tenant`, nên biểu thức cũ đọc thành *"cấm trích mọi chunk của
      chính kho người hỏi"* — kể cả chunk `public` họ **có quyền** thấy. Một agent từ chối hoàn toàn
      đúng nhưng có retrieval hợp lệ bị chấm FAIL. Đo trên golden-30: **4/8** case từ-chối là T6
      thuần (`HB-24/26/27/30`) ⇒ trần `success_rate` của agent hoàn hảo kẹt ở **26/30 = 0.867**, và
      con số đó bị đọc thành *"agent tệ"* chứ không phải *"bộ chấm sai"*.

      Chiều ngược lại còn nặng hơn và cũng do cùng một dòng: với T6, một chunk của **kho khác** thoả
      `!= expected_tenant` nên **lọt** — tức agent rò dữ liệu kho khác rồi từ chối vẫn được chấm
      PASS. Bản vá đóng cả hai chiều.

      **Giới hạn phải nói ra, không vá được ở tầng này:** `chunk_id` **không mã hoá vai**
      (`golden_case.py:69-71`), và case từ-chối có `expected_citation = []` nên cũng không có danh
      sách chunk cấm. ⇒ **T6 không kiểm được đúng thứ nó nói về**: một agent trích đúng chunk vai
      `hr` mà người hỏi không giữ, rồi từ chối, vẫn PASS. Thứ kiểm được chỉ là **sanity theo slug
      tenant**. Đóng thật cần vai đi kèm citation ở tầng contract — chưa có producer.

      Ca `expected_tenant is None` (*"không kho nào chứa đáp án"*) đi cùng nhánh T6: không có kho
      nào để cấm riêng, nên luật đúng vẫn là *"mọi chunk phải thuộc kho người hỏi"*. Bản cũ cho ca
      này một `no_leak` **vacuous** (`_citation_tenant(c) != None` luôn đúng với chunk parse được).
    """
    if not case.expects_refusal:
        success = (answer.refused is False) and _contains_phrase(answer.answer, case.expected)
        expected = set(case.expected_citation)
        citation_accuracy = len(expected & set(retrieved_citations)) / len(expected) if expected else 1.0
    elif isinstance(retrieved_chunks, _NotProvided):
        # Đường CŨ (`citations`) — giữ nguyên cho 6 call-site chưa đi đường chunks. Nhánh này
        # vacuous trên mọi runner thật (0 citation khi từ chối); đó chính là lý do `F-6` tồn tại.
        all_parseable = all(_citation_tenant(c) is not None for c in retrieved_citations)
        if case.expected_tenant is not None and case.expected_tenant != case.tenant:
            # T1 chéo-tenant: đáp án nằm ở kho KHÁC ⇒ cấm trích bất kỳ chunk nào thuộc kho đó.
            no_leak = all(_citation_tenant(c) != case.expected_tenant for c in retrieved_citations)
        else:
            # T6 chéo-vai (và ca `expected_tenant is None`): đáp án nằm CÙNG kho người hỏi, chỉ khác
            # VAI — nên "cấm trích kho `expected_tenant`" là cấm chính kho của họ. Thứ kiểm được
            # bằng `chunk_id` là: mọi chunk trích phải thuộc ĐÚNG kho người hỏi.
            no_leak = all(_citation_tenant(c) == case.tenant for c in retrieved_citations)
        success = (answer.refused is True) and all_parseable and no_leak
        citation_accuracy = 1.0
    elif retrieved_chunks is None:
        # Đã đọc trace nhưng KHÔNG có event `kb-retrieve` ⇒ không quan sát được ⇒ fail-closed.
        # Cùng luật `tenant_scope_ok` (`events` rỗng ⇒ False) và `DEC-05`.
        success = False
        citation_accuracy = 1.0
    else:
        if tenant_ids is None:
            msg = (
                "score_case: đi đường `retrieved_chunks` thì BẮT BUỘC truyền `tenant_ids` — "
                "tenant so bằng UUID thật, không đoán tiền tố chunk_id (DEC-D17-03)"
            )
            raise ValueError(msg)
        all_parseable, no_leak = _no_leak_from_chunks(case, retrieved_chunks, tenant_ids)
        success = (answer.refused is True) and all_parseable and no_leak
        citation_accuracy = 1.0

    return SmokeResult(
        case_id=case.case_id,
        expected=case.expected,
        actual=answer.answer,
        success=success,
        citation_accuracy=citation_accuracy,
        expects_refusal=case.expects_refusal,
    )


def _score_case_run(case: GoldenCase, case_run: CaseRun, tenant_ids: Mapping[str, UUID]) -> SmokeResult:
    """Chấm một `CaseRun` — `score_case` cộng bất biến **`no-trace-no-proof`** (`DEC-05`).

    > **`CaseRun.events == []` ⇒ case FAIL**, bất kể `answer` nói gì. Không có trace quan sát được
    > thì không chứng minh được gì.

    **Vì sao cưỡng chế ở đây chứ không trong `score_case`** — nguyên nhân là **TẦNG**, không phải
    cẩu thả: `score_case` chỉ nhận `retrieved_citations: list[str]` (`harness.py:158`), nên cấu trúc
    mà nói nó **không phân biệt được** *"chưa có run nào"* với *"có run, không trích gì"*. Cả hai
    đều tới nó dưới dạng `[]`. Đòi `score_case` fail-closed cho `[]` là đòi nó phân biệt bằng dữ
    liệu nó không được đưa — và sẽ làm mọi refusal trung thực đỏ oan. `tenant_scope_ok` phân biệt
    được **vì nó nhận `events`** (`harness.py:130`); hàm này ở đúng tầng đó.

    Chữ ký `score_case` **không đổi** (`DEC-05`): 3 consumer ngoài quadrant đang gọi nó.

    Chỉ hạ `success`, **không** đụng `citation_accuracy`: trục citation là metric riêng, không gate
    `success` (`score_case` docstring). Một case no-trace ở nhánh trả-lời đằng nào cũng ra `0.0` vì
    không trích được gì; ở nhánh từ-chối nó giữ `1.0` quy ước và bị loại khỏi mẫu số — cả hai đều là
    hành vi đã chốt, không phải hệ quả tình cờ của bản vá này."""
    result = score_case(
        case,
        case_run.answer,
        citations_from_trace(case_run.events),
        retrieved_chunks=chunks_from_trace(case_run.events),
        tenant_ids=tenant_ids,
    )
    if not case_run.events:
        return result.model_copy(update={"success": False})
    return result


async def _hoi_judge(judge: LLMJudge, case: GoldenCase, scored: SmokeResult) -> SmokeResult:
    """Hỏi judge cho một case đã trượt exact-match; `JudgeUnavailable` ⇒ **giữ nguyên** kết quả cũ.

    Giữ nguyên `scored` chính là *tụt nấc*: nấc exact-match đã chấm xong trước khi judge được hỏi, nên
    fallback không phải tính lại cái gì — nó là **không ghi đè**. Cách này làm cho *"tụt nấc"* và
    *"chưa từng có judge"* cho ra **đúng cùng một `Scorecard`**, và đó là thứ bài test khoá bằng phép
    so `==` giữa hai lần chạy: tụt nấc là **quay về** nấc dưới, không phải rẽ sang một nấc thứ ba.

    Chỉ ghi đè `success`, **không** đụng `citation_accuracy`: trục citation là metric riêng, không
    gate `success`, và judge không quan sát gì về trích dẫn để có ý kiến về nó.

    Ba `reason` gộp chung **một** nhánh xử lý, tách nhau ở **một** dòng log (`DEC-D18-05`) — gộp
    nhánh xử lý mà tách nhãn ghi nhận là đúng mức trừu tượng cần thiết. Log ở mức `WARNING` kèm cả
    `case_id`: *"đã tụt nấc"* mà không nói **case nào** và **vì sao** là vứt đúng phần thông tin
    hành động được.
    """
    try:
        verdict = await judge.judge(case_id=case.case_id, expected=case.expected, actual=scored.actual)
    except JudgeUnavailable as exc:
        _logger.warning(
            "judge descope → exact-match: case_id=%s reason=%s",
            case.case_id,
            exc.reason.value,
        )
        return scored
    return scored.model_copy(update={"success": verdict})


class EvalHarness:
    """Runs the golden-set eval loop for one agent recipe.

    Contract (fill at implementation time):
    - `run()` fetches the 30 cases for `golden_set_ref` from `eval.golden_sets` (schema.py),
      executes each case's input through the agent's recipe DAG, and collects a `CaseResult`
      per case (P2 `studio_contracts.CaseResult` — success/citation_accuracy/judge fields).
    - Subjective cases (no exact string match) delegate scoring to `judge.py`'s `LLMJudge`;
      exact-match cases score directly, and are also the descope-guard fallback (INV-7) when the
      judge's daily cap is hit.
    - The collected results are handed to `compute.compute_scorecard()` to produce the final
      `Scorecard`, including `gate.verdict` (PASS|FAIL) against the recipe's `ScorecardThreshold`.
    """

    async def run(
        self,
        agent_id: str,
        golden_set_ref: str,
        *,
        golden_set_path: Path,
        runner: AgentRunner,
        tenant_ids: Mapping[str, UUID],
        threshold_success: float,
        threshold_citation_accuracy: float,
        judge: LLMJudge | None = None,
    ) -> Scorecard:
        """Chạy **mọi** case của `golden_set_ref` qua `agent_id` rồi trả `Scorecard` có verdict thật.

        **`golden_set_path` bắt buộc, keyword-only, KHÔNG default** (`DEC-D16-01`). `golden_set_ref`
        vừa là khoá tra cứu vừa là **assert nội dung file**: thân hàm gọi
        `load_golden_set(golden_set_path, expect_ref=golden_set_ref)`, nên không có chỗ nào để hai
        thứ lệch nhau âm thầm. Một default `None` ở đây là chỗ để ai đó điền đường dẫn kb *"cho
        tiện"* ở lần sửa sau, và khi đó `DEC-D16-01` chỉ còn là một câu chữ.

        **Ngưỡng cũng bắt buộc, cũng không default.** `EvalHarness` **không sở hữu** `0.9/0.95` —
        ngưỡng thuộc recipe (`workbench/builder.py:169`), và một default ở đây là nguồn sự thật thứ
        hai cạnh nó. `DEC-D16-05` giữ ngưỡng ở recipe đúng vì lý do đó.

        Ghép ba thứ đã có, không phát minh gì mới: `load_golden_set` (`DEC-D16-01`) → vòng lặp giống
        `run_smoke` → `compute_scorecard`. `scored_case_ids` đếm từ `case.expects_refusal` — caller
        **biết** nhánh vì nó cầm `GoldenCase`, còn `CaseResult` thì không mang cờ nhánh
        (`DEC-D16-03`).

        ## `judge` — additive, default `None` (D18/T4)

        **`judge=None` ⇒ không đổi một dòng** hành vi: mọi call-site hôm nay (`cli.py`, 2 bài
        integration, `apps/studio`) chạy nguyên vì chúng không truyền tham số này.

        **Định tuyến không đọc field mới nào.** `DEC-D18-07` từ chối thêm `match_mode`, nên nhánh
        judge dẫn xuất từ **chính kết quả chấm exact-match**: case nhánh trả-lời mà `_contains_phrase`
        không bắt được ⇒ hỏi judge. Đúng nguyên văn hai docstring có sẵn từ trước (`judge.py`
        *"subjective (non-exact-match) cases"*, và mô tả của chính lớp này *"exact-match cases score
        directly"*).

        **Số case đi qua judge phụ thuộc RUNNER, và đoạn này từng khai thiếu vế đó** (sửa D20, finding
        của DE trên `kit#125`). Hai phép đo, cả hai đúng, khác nhau ở runner:

        | Runner | Case đi judge | Đo ở |
        |---|---|---|
        | `StubAgentRunner` sinh từ chính golden-set (đúng **theo định nghĩa**) | **0/30** | nền D18 |
        | `ExtractiveFakeLLM` qua engine thật + `PgKbSearch` + Postgres | **17/22** nhánh trả-lời | D20 `DEC-D20-04` |

        Bản trước chỉ ghi vế đầu kèm kết luận *"không có selector production nào được dựng cho một tập
        rỗng"* — và câu đó **đã được dùng làm căn cứ hoãn việc**. Nó **chỉ đúng trên đường stub**: trên
        đường thật tập đó có **17 phần tử**, và cả 17 hôm nay bị tính `success=False` mà bộ chấm
        exact-match **không kết luận được** — nó chỉ biết *"không khớp chuỗi"*, không biết *"sai"*.

        Con số `17` **không** nói judge sẽ cứu được bao nhiêu case (`ExtractiveFakeLLM` trả câu canned
        nên phần lớn nhiều khả năng vẫn sai). Nó nói đúng một điều: **mẫu số của quyết định descope là
        17, không phải 0.** Điều kiện lật để đo lại: một LLM **sinh prose thật, không biết trước nhãn**,
        trên ≥30 case — cùng điều kiện lật của `DEC-D17-04`.

        **Judge chỉ được hỏi ở nhánh trả-lời-được.** Nhánh từ-chối chấm bằng luật hàng rào (`refused`
        + `no_leak`), không bằng so khớp văn bản — không có gì *subjective* để hỏi, và hỏi LLM ở đó là
        để một mô hình phủ quyết một bằng chứng cấu trúc.

        **`JudgeUnavailable` ⇒ tụt nấc exact-match, KHÔNG vỡ run** (INV-7). Cả ba `reason` đi **cùng
        một nhánh xử lý** — cái khác nhau chỉ là **thứ được ghi lại** (`DEC-D18-05`). Tụt nấc ghi ra
        log kèm `reason` và `case_id`: `Scorecard` không đổi được một byte (`DEC-D18-06`) nên log là
        kênh đúng cho một tín hiệu vận hành, và một run tụt nấc mà trông y hệt run không tụt là một
        scorecard **nói dối về phương pháp của chính nó**.

        **`CaseResult.judge` vẫn `None` kể cả với case đã qua judge** — hạn chế phải nói ra, không
        phải sơ suất: `Judge` (contract) đòi `agreement: float`, mà agreement là phép so với **nhãn
        tay** trên một **tập** kết quả (`DEC-D18-04`); `judge()` không nhận nhãn tay nên mọi số điền
        vào đó chỉ có thể là **hằng số**, đúng thứ bị cấm ở ba chỗ. Ô DoD *"agreement của judge"*
        **không đóng trong D18** (§7 ô 2), và để trống trung thực hơn là điền một hằng số.
        """
        golden = load_golden_set(golden_set_path, expect_ref=golden_set_ref)

        results: list[CaseResult] = []
        scored_case_ids: set[str] = set()
        for case in golden.cases:
            case_run = await runner.run_case(
                agent_id=agent_id,
                query=case.query,
                tenant_id=tenant_ids[case.tenant],
                section_roles=case.section_roles,
            )
            scored = _score_case_run(case, case_run, tenant_ids)
            if judge is not None and not case.expects_refusal and not scored.success:
                scored = await _hoi_judge(judge, case, scored)
            results.append(
                CaseResult(
                    case_id=scored.case_id,
                    expected=scored.expected,
                    actual=scored.actual,
                    success=scored.success,
                    citation_accuracy=scored.citation_accuracy,
                    # `judge=None` = *"case này chấm KHÔNG qua LLM-judge"* — giá trị trung thực duy
                    # nhất trước S3 (`DEC-02`). Một `Judge(...)` hằng số ở đây không phân biệt được
                    # với một judge thật đồng thuận 100%.
                )
            )
            if not case.expects_refusal:
                scored_case_ids.add(case.case_id)

        return compute_scorecard(
            agent_id,
            golden_set_ref,
            results,
            threshold_success,
            threshold_citation_accuracy,
            scored_case_ids=scored_case_ids,
        )

    async def run_smoke(
        self,
        agent_id: str,
        golden_set: GoldenSet,
        runner: AgentRunner,
        tenant_ids: Mapping[str, UUID],
    ) -> list[SmokeResult]:
        """Phác skeleton smoke-eval (D3 #14; D5 #24 đọc trace): duyệt `golden_set.cases`, chạy mỗi
        case qua `runner` (seam `AgentRunner`), chấm bằng `score_case` với citations lấy từ TRACE
        (`citations_from_trace` trên `CaseRun.events`), trả danh sách `SmokeResult`.

        `tenant_ids` map slug (`GoldenCase.tenant`) → `tenant_id` UUID: **resolve tường minh ở đây,
        phía trên seam** (D-13) — golden giữ slug làm nhãn, runner nhận UUID; thiếu slug ⇒ `KeyError`
        (fail-closed). Thật thì map đến từ `core.tenants` (`studio_app`); CLI/test dựng map stand-in.

        Nhận `golden_set` in-memory + `runner` tiêm vào (chưa đọc từ DB, chưa gọi interpreter thật):
        đây là chỗ nối sẽ thay stub bằng adapter engine của AIE-1 (D5–6, #29). KHÔNG dựng `Scorecard`
        (cần `compute_scorecard`, Q1 treo)."""
        results: list[SmokeResult] = []
        for case in golden_set.cases:
            tenant_id = tenant_ids[case.tenant]
            case_run = await runner.run_case(
                agent_id=agent_id,
                query=case.query,
                tenant_id=tenant_id,
                section_roles=case.section_roles,
            )
            # `no-trace-no-proof` cưỡng chế ở ĐÂY, tầng giữ `events` (DEC-05) — cùng một helper với
            # `run`, để hai đường không trôi ra hai luật chấm khác nhau.
            results.append(_score_case_run(case, case_run, tenant_ids))
        return results
