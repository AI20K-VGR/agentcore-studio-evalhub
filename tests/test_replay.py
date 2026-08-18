"""`studio_evalhub.replay` — ghi/phát lại lời gọi `LLM.complete()` (plan `day-22-aie2.md` T1).

Mỗi bài dưới đây khoá một quyết định đã ghi trong docstring của module, không phải khoá một chi tiết
cài đặt. Ba mutant mà bộ này phải giết:

- **M-R1** — bỏ `kwargs` khỏi khoá (chỉ băm `prompt`) ⇒ `test_kwargs_khac_thi_khoa_khac` đỏ.
- **M-R2** — miss trả `""` (hoặc lùi về một fake) thay vì raise ⇒ `test_miss_thi_raise` đỏ.
- **M-R3** — fixture hỏng đọc thành `{}` ⇒ `test_fixture_hong_khong_duoc_coi_nhu_rong` đỏ.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from studio_contracts.protocols import LLM
from studio_evalhub.replay import (
    FixtureUnreadable,
    RecordingLLM,
    ReplayLLM,
    ReplayMiss,
    call_key,
)


class _LLMDem:
    """`LLM` double đếm số lần bị gọi — dùng để chứng minh replay KHÔNG chạm provider."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.so_lan = 0

    async def complete(self, prompt: str, **kwargs: object) -> str:
        self.so_lan += 1
        return self.response


def _fixture(tmp_path: Path) -> Path:
    return tmp_path / "replay.json"


async def test_ghi_roi_phat_lai_tra_dung_byte(tmp_path: Path) -> None:
    """Vòng tròn ghi → đọc phải trả **đúng byte**, kể cả dấu tiếng Việt và ký tự xuống dòng.

    Không assert bằng `in`/`startswith`: một replay trả "gần đúng" là thứ tệ hơn một replay lỗi, vì
    nó vẫn chấm được và sai âm thầm ở tầng `_contains_phrase`."""
    path = _fixture(tmp_path)
    goc = "Nhân viên được nghỉ **3 ngày mỗi tuần**.\n\n[ankor-remote-001#c1]"
    that = _LLMDem(goc)

    ghi = RecordingLLM(that, path, model="o4-mini", golden_set_ref="callisto-golden-30-v1")
    assert await ghi.complete("câu hỏi", model="o4-mini") == goc
    assert that.so_lan == 1

    phat = ReplayLLM(path)
    assert await phat.complete("câu hỏi", model="o4-mini") == goc
    assert that.so_lan == 1, "phát lại mà vẫn chạm provider thì fixture không phục vụ mục đích nào"


async def test_miss_thi_raise(tmp_path: Path) -> None:
    """`DEC-D22-02` — miss là **lỗi**, không phải đường lùi.

    Mutant M-R2 (trả `""`, hoặc lùi về `ExtractiveFakeLLM`) làm bài này xanh nếu chỉ assert "không
    trả về response cũ" — nên phải assert đúng loại exception."""
    path = _fixture(tmp_path)
    await RecordingLLM(_LLMDem("A"), path, model="m").complete("prompt đã ghi")

    with pytest.raises(ReplayMiss):
        await ReplayLLM(path).complete("prompt CHƯA ghi")


async def test_kwargs_khac_thi_khoa_khac(tmp_path: Path) -> None:
    """`DEC-D22-01` — `(prompt, kwargs)` mới là danh tính một lời gọi, không phải `prompt`.

    Đây là bài giết mutant M-R1. Ca thật đứng sau nó: `executors.py:349-350` tiêm
    `kwargs["model"]` từ `recipe.agent_config.model`, nên *cùng prompt + khác model* là chuyện
    thường ngày. Nếu khoá bỏ kwargs, lời gọi thứ hai được phục vụ response của model khác — một đáp
    án sai mà không có gì báo."""
    path = _fixture(tmp_path)
    await RecordingLLM(_LLMDem("của o4-mini"), path, model="o4-mini").complete("q", model="o4-mini")

    phat = ReplayLLM(path)
    assert await phat.complete("q", model="o4-mini") == "của o4-mini"
    with pytest.raises(ReplayMiss):
        await phat.complete("q", model="gemini-2.5-flash")


def test_thu_tu_khai_kwargs_khong_vao_khoa() -> None:
    """`sort_keys=True` sắp **đệ quy**: hai dict cùng nội dung, khác thứ tự khai ⇒ cùng khoá.

    Nếu ai đó đổi sang `json.dumps(kwargs)` trần, bài này đỏ — và nó đỏ vì đúng lý do: khoá lúc đó
    phụ thuộc thứ tự chèn của caller, không phụ thuộc nội dung."""
    assert call_key("q", {"b": 1, "a": {"z": 1, "y": 2}}) == call_key("q", {"a": {"y": 2, "z": 1}, "b": 1})


def test_kwargs_khong_serialize_duoc_thi_TypeError() -> None:
    """Giá trị không JSON ⇒ `TypeError` **thoát ra**, không bọc, không `default=str`.

    `Node.params` là `dict[str, object]` (không validate giá trị) nên ca này dựng được thật. Lý do
    cấm `default=str`, đo được: `__repr__` mặc định mang địa chỉ bộ nhớ ⇒ ba tiến trình cho ba khoá
    khác nhau ⇒ mọi replay ở tiến trình khác thành miss. Thà `TypeError` ồn ào."""
    with pytest.raises(TypeError):
        call_key("q", {"khong_json": {1, 2}})


async def test_fixture_hong_khong_duoc_coi_nhu_rong(tmp_path: Path) -> None:
    """Mutant M-R3 — `except: return {}` biến một file rác thành "chưa ghi gì".

    Hai ca, hai kiểu hỏng khác nhau, cùng một hướng fail-closed: JSON vỡ hẳn, và JSON **hợp lệ mà
    shape lạ** (ca thứ hai mới là ca lọt qua một phép kiểm chỉ `try: json.loads`)."""
    vo = tmp_path / "vo.json"
    vo.write_text("{ khong phai json", encoding="utf-8")
    with pytest.raises(FixtureUnreadable):
        await ReplayLLM(vo).complete("q")

    shape_la = tmp_path / "shape.json"
    shape_la.write_text(json.dumps({"calls": "đáng ra phải là object"}), encoding="utf-8")
    with pytest.raises(FixtureUnreadable):
        await ReplayLLM(shape_la).complete("q")


async def test_response_sai_kieu_la_ban_ghi_hong(tmp_path: Path) -> None:
    """`LLM.complete` khai `-> str`; một bản ghi `response: 123` là bản ghi **hỏng**, không phải một
    đáp án lạ để `str()` cho xong. Cùng bài học `FixtureLLM` của engine đã phải vá ở D9: coerce một
    bản ghi sai kiểu là chuyển rác xuống hạ nguồn dưới dạng một câu trả lời thật."""
    path = tmp_path / "sai_kieu.json"
    path.write_text(json.dumps({"calls": {call_key("q", {}): {"response": 123}}}), encoding="utf-8")
    with pytest.raises(FixtureUnreadable):
        await ReplayLLM(path).complete("q")


async def test_fixture_thieu_file_thi_raise_chu_khong_im_lang(tmp_path: Path) -> None:
    """Phát lại từ một fixture chưa tồn tại là lỗi cấu hình, không phải "chưa có bản ghi nào"."""
    with pytest.raises(FixtureUnreadable):
        await ReplayLLM(tmp_path / "chua_co.json").complete("q")


def test_ca_hai_class_thoa_protocol_LLM(tmp_path: Path) -> None:
    """Khoá **hình dạng seam**, không khoá lời hứa: cả hai phải là `LLM` để tiêm được vào đúng chỗ
    `EngineAgentRunner`/`LLMJudge` đang nhận. Đỏ ngay nếu ai đổi chữ ký `complete`."""
    path = _fixture(tmp_path)
    assert isinstance(RecordingLLM(_LLMDem("x"), path, model="m"), LLM)
    assert isinstance(ReplayLLM(path), LLM)


async def test_ghi_nhieu_luot_khong_de_mat_luot_truoc(tmp_path: Path) -> None:
    """Ghi **sau từng lời gọi** và cộng dồn, không ghi đè: một lượt golden-30 là ~60 lời gọi tốn
    tiền thật, mất sạch vì process chết ở case cuối là mất không cần thiết. Bài này đỏ nếu ai đổi
    sang gom-rồi-ghi-một-lần hoặc ghi đè `calls` mỗi lần."""
    path = _fixture(tmp_path)
    ghi = RecordingLLM(_LLMDem("R1"), path, model="m")
    await ghi.complete("q1")
    RecordingLLM(_LLMDem("R2"), path, model="m")  # instance mới, cùng file
    await RecordingLLM(_LLMDem("R2"), path, model="m").complete("q2")

    phat = ReplayLLM(path)
    assert await phat.complete("q1") == "R1"
    assert await phat.complete("q2") == "R2"
