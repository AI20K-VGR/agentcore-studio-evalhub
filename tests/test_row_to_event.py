"""Test `_row_to_event` — tầng đọc DB của bộ chấm. D15, `kit#103`.

## Vì sao tầng này cần bài riêng

`answer_from_trace` và `render_run_cases` đã có 21 bài. Nhưng cả 21 bài đều nhận `TraceEvent` **đã
dựng sẵn** — không bài nào đi qua chỗ `list[tuple]` của psycopg trở thành `list[TraceEvent]`. Tức
đường thật *"đọc lại trace của một run đã bền hoá"* mà `kit#103` yêu cầu đang có một đoạn không lưới.

Đoạn đó nguy hiểm hơn vẻ ngoài vì nó **hỏng im lặng**: `_row_to_event` đọc theo **chỉ số**
(`row[0]`…`row[11]`), còn thứ tự chỉ số đó do **chuỗi SQL `_READ_RUN`** quyết. Hai thứ nằm cách nhau
30 dòng, không có gì buộc chúng khớp. Hoán `agent_id` với `tenant_id` thì `TraceEvent` vẫn dựng được,
bảng per-case vẫn in ra đẹp, và `tenant_scope_ok` bắt đầu đối chiếu nhầm trường — không exception nào
nổi lên.

## Bất biến được cưỡng chế ở đây

Bài chính **không chép tay** thứ tự cột. Nó parse danh sách cột ra từ chính `_READ_RUN`, dựng row
theo đúng thứ tự đọc được, rồi đòi mỗi field của `TraceEvent` mang đúng giá trị mốc của **tên cột
cùng tên**. Hệ quả:

| ai đổi | kết quả |
|---|---|
| chỉ đổi thứ tự trong `_READ_RUN` | **ĐỎ** — hàm còn đọc theo chỉ số cũ |
| chỉ đổi chỉ số trong `_row_to_event` | **ĐỎ** — hàm đọc lệch so với SQL |
| đổi **cả hai** cho khớp nhau | XANH — đúng, vì đó là một thay đổi hợp lệ |

Đó là điều một bảng giá trị chép tay không làm được: nó chỉ khoá được *"hôm nay ra số này"*, không
khoá được *"hai chỗ này phải khớp nhau"*.

**Fixture bất đối xứng theo thiết kế** — mọi cột mang một giá trị **khác nhau và nhận dạng được**.
`tokens` dùng `137/42` chứ không phải `0/0`: hoán `prompt` với `completion` là một failure mode có
thật (vừa bắt được đúng lỗi này khi review `kb#16`), và một fixture `0/0` sẽ nuốt nó.

**Ghi thẳng về "đỏ trước":** `_row_to_event` đã land sáng nay, nên bài này **không** viết được trước
hiện thực. Bù lại bằng vế kiểm chứng còn lại của cùng kỷ luật — gieo mutant để chứng minh bài có
răng, kết quả ghi ở `docs/mutations/self-render-d15.md` §5.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from studio_contracts import NodeType

from studio_evalhub.run_report import _READ_RUN, _row_to_event

_TENANT = UUID("6b1f4c7a-0d2e-4a91-9c3b-5e8f2a7d1b04")

# Một giá trị MỐC cho mỗi cột, cố ý khác nhau từng đôi một: hoán bất kỳ hai cột nào cũng lộ.
# Ba cột `*_id` đều là `str` nên nếu chúng đổi chỗ cho nhau thì pydantic KHÔNG kêu — chỉ giá trị
# khác nhau mới bắt được. Đây là lý do không cột nào dùng giá trị chung chung như "x".
_CELL: dict[str, Any] = {
    "event_id": "ev-row-7",
    "run_id": "run-row-d15",
    "agent_id": "agent-row-callisto",
    "tenant_id": _TENANT,
    "node_id": "n-row-3",
    "node_type": "llm-step",
    "ts": "2026-08-07T00:00:03+00:00",
    "inputs_hash": "sha256:row-fixture",
    "outputs": {"answer": "Nhân viên cần báo trước tối thiểu 3 ngày làm việc.", "refused": False},
    "tokens": {"prompt": 137, "completion": 42},
    "cost": Decimal("0.25"),
    "citations": ["ankor-leave-001#c1"],
}


def _columns() -> list[str]:
    """Danh sách cột của `_READ_RUN`, đúng thứ tự SQL sẽ trả về.

    Đọc từ chính chuỗi SQL thay vì chép tay — chép tay là tạo ra **chỗ thứ ba** phải giữ đồng bộ,
    tức đúng cái bệnh mà bài này sinh ra để chữa."""
    body = re.search(r"SELECT\s+(.*?)\s+FROM", _READ_RUN, re.S | re.I)
    assert body, "không parse được danh sách cột từ _READ_RUN"
    return [c.strip() for c in body.group(1).split(",")]


def _row() -> tuple[Any, ...]:
    """Row giả lập psycopg trả về: xếp theo **thứ tự cột thật của `_READ_RUN`**, không phải thứ tự
    field của `TraceEvent`."""
    return tuple(_CELL[c] for c in _columns())


def test_row_to_event_khop_thu_tu_cot_cua_READ_RUN() -> None:
    """Mỗi field của `TraceEvent` mang đúng giá trị mốc của cột **cùng tên** trong `_READ_RUN`.

    Đây là bài giữ mối nối SQL ↔ chỉ số. Hoán hai cột bất kỳ ở một trong hai phía là bài đỏ."""
    cols = _columns()
    assert len(cols) == 12, f"_READ_RUN đổi số cột ({len(cols)}) — cập nhật _CELL trước khi sửa bài này"
    assert set(cols) == set(_CELL), f"cột lạ hoặc thiếu mốc: {set(cols) ^ set(_CELL)}"

    event = _row_to_event(_row())

    assert event.event_id == _CELL["event_id"]
    assert event.run_id == _CELL["run_id"]
    assert event.agent_id == _CELL["agent_id"]
    assert event.tenant_id == _TENANT
    assert event.node_id == _CELL["node_id"]
    assert event.node_type is NodeType.LLM_STEP
    assert event.ts == _CELL["ts"]
    assert event.inputs_hash == _CELL["inputs_hash"]
    assert event.outputs == _CELL["outputs"]
    assert event.citations == _CELL["citations"]


def test_row_to_event_tokens_khong_hoan_prompt_va_completion() -> None:
    """`tokens` dựng từ JSONB phải giữ đúng vai của từng số.

    Tách khỏi bài trên vì nó là một failure mode riêng và **rất im lặng**: `Tokens(**row[9])` vẫn
    dựng được khi hai số đổi chỗ, không kiểu nào sai. D19 (`kit#120`) sẽ dựng cost-lineage
    `tokens → cost` trên đúng hai số này, nên hoán ở tầng đọc bây giờ thành sai tiền về sau."""
    event = _row_to_event(_row())

    assert event.tokens.prompt == 137
    assert event.tokens.completion == 42


def test_row_to_event_cost_Decimal_thanh_float() -> None:
    """`cost` là `NUMERIC` ⇒ psycopg trả `Decimal`; contract đòi `float`.

    Không phải chuyện thẩm mỹ: `TraceEvent.cost: float` và pydantic sẽ ép — nhưng nếu lớp ép đó biến
    mất thì mọi phép cộng cost sau này trộn `Decimal` với `float` và `TypeError` nổ ở chỗ khác hẳn,
    xa nguyên nhân."""
    event = _row_to_event(_row())

    assert isinstance(event.cost, float)
    assert event.cost == 0.25


def test_row_to_event_citations_NULL_giu_None_chu_khong_thanh_list_rong() -> None:
    """`citations` `NULL` ⇒ `None`, **không** phải `[]`.

    Hai thứ khác nhau và `citations_from_trace` phân biệt được: `None` là *"không áp dụng"*
    (`kb-retrieve` không mang citations theo clause C-1), `[]` là *"đã trích, kết quả rỗng"* — tức
    một `llm-step` **không grounded**, một dấu hiệu chất lượng thật. Đổi `None` thành `[]` ở tầng đọc
    là xoá mất sự phân biệt đó trước khi bộ chấm kịp nhìn thấy."""
    cells = {**_CELL, "citations": None}
    row = tuple(cells[c] for c in _columns())

    event = _row_to_event(row)

    assert event.citations is None


def test_row_to_event_node_type_la_khong_biet_thi_raise() -> None:
    """`node_type` không thuộc `NodeType` ⇒ `ValueError`, không im lặng bỏ qua event.

    Fail-closed: một event có `node_type` lạ nghĩa là engine đã emit thứ bộ chấm chưa biết đọc. Nuốt
    nó đi sẽ cho ra một run **thiếu event** mà trông vẫn hợp lệ — và `answer_from_trace` sẽ chấm trên
    một timeline không đầy đủ."""
    cells = {**_CELL, "node_type": "quantum-step"}
    row = tuple(cells[c] for c in _columns())

    with pytest.raises(ValueError, match="quantum-step"):
        _row_to_event(row)
