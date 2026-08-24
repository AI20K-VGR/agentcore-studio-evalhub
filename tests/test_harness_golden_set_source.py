"""`EvalHarness.run` — nguồn case: **đúng một** trong `golden_set_path` / `golden_set`.

Mở thêm nguồn thứ hai (đối tượng `GoldenSet`, thường từ `golden_store.read_golden_set`) là điều kiện
của cutover golden-set **file → DB**: nguồn thật từ nay là `eval.golden_sets` **theo tenant**, và một
hàm chỉ nhận `Path` sẽ bắt caller ghi bộ ra file tạm rồi đọc lại — một vòng qua đĩa chỉ để thoả chữ
ký, cộng một chỗ nữa để hai bản lệch nhau.

Thay đổi **additive**: 10 call-site `golden_set_path=` hiện có (evalhub tests · apps/studio tests +
scripts + route · kit e2e) không đổi một dòng. Bán kính được đo **trước** khi chọn hướng — một
breaking change ở chữ ký này chạm **ba** repo.

## Vì sao vẫn giữ tinh thần `DEC-D16-01`

`DEC-D16-01` chốt *"`golden_set_path` KHÔNG default, vì một default là chỗ để ai đó điền đường dẫn
kb cho tiện ở lần sửa sau"*. Sau thay đổi này **cả hai** tham số default `None` — nhưng chúng không
phải "tuỳ chọn": thân hàm raise khi nhận **cả hai** hoặc **không cái nào**. Thứ `DEC-D16-01` cấm là
**rơi vào một nguồn mặc định**, không phải việc tồn tại hai nguồn.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest
from studio_evalhub.agent_runner import AgentAnswer, CaseRun, StubAgentRunner
from studio_evalhub.golden_case import GoldenCase, GoldenSet
from studio_evalhub.harness import EvalHarness

_REF = "fx-source-v1"
_TS = 0.9
_TC = 0.95
_QUERY = "Nghỉ phép năm bao nhiêu ngày?"


def _tenant_ids() -> Mapping[str, UUID]:
    return {"ankor": uuid5(NAMESPACE_DNS, "ankor")}


def _golden(ref: str = _REF) -> GoldenSet:
    return GoldenSet(
        golden_set_ref=ref,
        cases=[
            GoldenCase(
                case_id="U-01",
                query=_QUERY,
                tenant="ankor",
                section_roles=["hr"],
                expected_tenant="ankor",
                expected_section_role="hr",
                expected="12 ngày",
                expected_citation=[],
            )
        ],
    )


def _runner() -> StubAgentRunner:
    tenant_id = _tenant_ids()["ankor"]
    return StubAgentRunner(
        {
            (_QUERY, tenant_id, ("hr",)): CaseRun(
                answer=AgentAnswer(answer="Theo tài liệu, nghỉ phép 12 ngày.", citations=[], refused=False),
                events=[],
            )
        }
    )


async def _chay(**nguon: object) -> object:
    return await EvalHarness().run(
        "agent-fx",
        _REF,
        runner=_runner(),
        tenant_ids=_tenant_ids(),
        threshold_success=_TS,
        threshold_citation_accuracy=_TC,
        **nguon,  # type: ignore[arg-type]
    )


async def test_truyen_golden_set_doi_tuong_chay_duoc(tmp_path: Path) -> None:
    """Nhánh mới: truyền thẳng `GoldenSet` — không chạm đĩa, không cần file nào tồn tại.

    `tmp_path` cố ý **không dùng**: có mặt trong chữ ký để nói rõ bài này chạy được kể cả khi không
    có một file golden nào trên hệ thống, đúng trạng thái của một tenant lấy bộ từ `eval.golden_sets`."""
    del tmp_path
    scorecard = await _chay(golden_set=_golden())

    assert scorecard.golden_set_ref == _REF  # type: ignore[attr-defined]
    assert len(scorecard.results) == 1  # type: ignore[attr-defined]


async def test_khong_truyen_nguon_nao_thi_raise() -> None:
    """**Không nguồn nào ⇒ raise.** Đây là vế giữ `DEC-D16-01` sống sau khi `golden_set_path` có
    default `None`: nếu thiếu phép kiểm này, một caller quên truyền sẽ đi tiếp và vỡ ở chỗ khác —
    hoặc tệ hơn, ai đó "vá" bằng cách cho nó rơi về một đường dẫn mặc định."""
    with pytest.raises(ValueError, match="ĐÚNG MỘT"):
        await _chay()


async def test_truyen_ca_hai_nguon_thi_raise() -> None:
    """**Cả hai ⇒ raise**, không im lặng ưu tiên một cái.

    Một bản cài đặt "path thắng" (hoặc "object thắng") sẽ chạy đúng ở mọi bài test hôm nay và sai
    đúng một lần: hôm ai đó truyền cả hai vì tưởng cái kia là tuỳ chọn, rồi chấm bằng bộ không định
    chấm. Raise là câu trả lời duy nhất không phải đoán ý caller."""
    with pytest.raises(ValueError, match="ĐÚNG MỘT"):
        await _chay(golden_set=_golden(), golden_set_path=Path("/khong/ton/tai.yaml"))


async def test_golden_set_ref_lech_thi_raise() -> None:
    """Nhánh object chịu **cùng** phép kiểm chéo mà nhánh path nhận từ `load_golden_set(expect_ref=…)`.

    Không có vế này thì hai nguồn có **hai mức bảo đảm khác nhau** — và cái yếu hơn chính là cái
    được dùng ở production (đường DB). Một bộ khai `ref` khác đi lọt nghĩa là `Scorecard.golden_set_ref`
    nói một đằng còn case được chấm là một nẻo, và `recipe_hash` không bắt được chuyện đó."""
    with pytest.raises(ValueError, match="khác golden_set_ref"):
        await _chay(golden_set=_golden(ref="mot-ref-khac"))
