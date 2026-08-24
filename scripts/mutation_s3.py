"""Mutation **chéo** cho 5 hàng rào Sprint 3 — AIE-2 gieo vào `src/` của quadrant KHÁC.

    docker compose -f docker-compose.test.yml up -d
    export STUDIO_DATABASE_URL_ADMIN=postgresql://studio_owner:changeme@localhost:5433/studio_test
    export STUDIO_DATABASE_URL=postgresql://studio_app:changeme@localhost:5433/studio_test
    uv run python packages/evalhub/scripts/mutation_s3.py

## Vì sao có script này thay vì thêm mutant vào `packages/kb/scripts/mutation_check.py`

Script của DE là **file của DE**. Bộ mutant dưới đây là phép đo của AIE-2 cho 5 cờ đỏ Sprint 3, và
nó nhắm vào `src/` của **ba** quadrant (engine · kb · evalhub) — thêm vào script DE sẽ trộn hai bộ
đo có chủ khác nhau vào một bảng, và mỗi lần một trong hai người đổi bộ của mình thì người kia phải
đọc lại. Khuôn `Mutant` bên dưới chép đúng của DE (cùng `anchor` phải-duy-nhất, cùng `try/finally`),
nên hai bảng đọc được như nhau — chỉ tách chủ sở hữu.

## "Chéo" nghĩa là gì, và vì sao nó là điều kiện

Không ai chấm bài của chính mình. 4/5 mutant dưới đây nằm ở `src/` của người khác (engine: 3, kb: 1),
và thứ được đo là **test của họ** có cắn không. Mutant còn lại (`M4`) nằm ở evalhub — giữ lại vì nó
là hàng rào mà chính AIE-2 sở hữu và là chỗ đã trả giá một lần (`evalhub#18`).

## Đọc bảng kết quả

`bắt` = số test đỏ dưới mutant đó, đo trên **toàn workspace từ gốc kit** (không phải suite của một
repo con — CI repo con mù với 5 repo còn lại). Một mutant `bắt == 0` nghĩa là hành vi đó **không bài
test nào khoá** — đó là **phát hiện**, không phải điều đáng mừng, và phải mở issue.

## Tiền đề bắt buộc

`packages/engine` phải ở con trỏ có `agent_loop.py` (`65731e5`, `engine#36`) — 3/5 mutant nhắm vào
vòng lặp mới. Script **dừng và nói rõ** nếu thiếu, thay vì lặng lẽ bỏ qua rồi in một bảng trông đủ.

Script tự hoàn nguyên qua `try/finally`, kể cả khi pytest vỡ hoặc bị Ctrl-C. Kiểm lại bằng
`git status --short` **ở cả submodule** sau khi chạy — phải sạch (đo được: một mutant `ALTER TABLE`
từng để lại cột thật trong DB test dù `src/` đã sạch, cùng lớp lỗi `kb#48`).
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_EVALHUB = Path(__file__).resolve().parent.parent
_ROOT = _EVALHUB.parent.parent
_ENGINE_SRC = _ROOT / "packages" / "engine" / "src" / "studio_engine"
_KB_SRC = _ROOT / "packages" / "kb" / "src" / "studio_kb"
_EVALHUB_SRC = _EVALHUB / "src" / "studio_evalhub"


@dataclass(frozen=True)
class Mutant:
    """Một phép làm-hỏng-có-chủ-đích.

    `anchor` phải xuất hiện **đúng một lần** trong file — script khẳng định điều đó và dừng nếu
    không, vì một anchor trùng nghĩa là đang sửa chỗ mình không định sửa, và kết quả đo sẽ vô nghĩa.
    """

    name: str
    description: str
    fence: str
    path: Path
    anchor: str
    replacement: str
    zero_means: str


_MUTANTS = (
    Mutant(
        name="M1 kb-search-tenant-from-recipe",
        description="`kb_search` trong vòng lặp bỏ qua `session_context`, lấy tenant/roles LLM tự khai",
        fence="INV-1 Tenant-Wall (engine — AIE-1)",
        path=_ENGINE_SRC / "agent_loop.py",
        anchor='            fenced_params = fenced_kb_params({**signal.params, "top_k": top_k}, session_context)',
        replacement='            fenced_params = {**signal.params, "top_k": top_k}  # MUTANT M1',
        zero_means="Hàng rào công ty KHÔNG được khoá — INV-1 chỉ còn là quy ước, một prompt-injection "
        "khai tenant khác sẽ đọc được kho của họ mà không test nào đỏ.",
    ),
    Mutant(
        name="M2 drop-section-role-clause",
        description="Bỏ `AND section_role = ANY(%s)` khỏi câu SQL truy xuất",
        fence="T6 hàng rào phòng ban (kb — DE)",
        path=_KB_SRC / "postgres.py",
        anchor="  AND section_role = ANY(%s)\n",
        replacement="  -- MUTANT M2: menh de section_role da bi xoa\n",
        zero_means="Hàng rào phòng ban **không được DB đỡ** — nó chỉ là một mệnh đề WHERE trong "
        "câu SQL của ứng dụng. Ngày ai đó viết truy vấn mới quên mệnh đề đó, mọi phòng ban lộ hết.",
    ),
    Mutant(
        name="M3 remove-c1-citations-gate",
        description="Bỏ cổng *chỉ `llm-step` mới được mang `citations`* ở interpreter",
        fence="C-1 (engine — AIE-1)",
        path=_ENGINE_SRC / "interpreter.py",
        anchor='            raw_citations = raw_outputs.get("citations") if node_type is NodeType.LLM_STEP else None',
        replacement='            raw_citations = raw_outputs.get("citations")  # MUTANT M3',
        zero_means="Một tool tự khai `citations` sẽ đi thẳng vào trace thành trích dẫn thật và "
        "ăn điểm `citation_accuracy` giả — fail-open đúng vào trục chấm điểm.",
    ),
    Mutant(
        name="M4 chunks-from-trace-returns-empty",
        description="`chunks_from_trace` trả `[]` thay vì `None` khi không quan sát được",
        fence="3 nghĩa `None`/`[]`/`list` (evalhub — AIE-2)",
        path=_EVALHUB_SRC / "harness.py",
        anchor="    if not retrieve_events:\n        return None\n",
        replacement="    if not retrieve_events:\n        return []  # MUTANT M4\n",
        zero_means="`None` (*không quan sát được*, fail-closed) bị đọc thành `[]` (*hàng rào chặn "
        "sạch*, bằng chứng TỐT) ⇒ **mọi case từ-chối xanh giả**. Đúng lớp lỗi `evalhub#18` đã trả giá.",
    ),
    Mutant(
        # Bản đầu gieo vào cận `range(1, max_turns + 1)` → `range(1, 10_000)` và **sống sót 0/1686**.
        # Đó KHÔNG phải phát hiện, đó là **mutant sai**: cap thật không nằm ở cận vòng lặp mà ở câu
        # `if i == max_turns: raise AgentLoopExhausted(...)` BÊN TRONG thân — nới cận không đổi hành
        # vi nào vì `i == max_turns` vẫn bắn. Một mutant no-op sống sót rồi được báo là *"test không
        # khoá"* chính là loại báo động giả mà cả bộ đo này sinh ra để chống. Giữ lại ghi chú vì đó
        # là bài học đọc kết quả: `bắt == 0` chỉ là phát hiện khi mutant **thật sự đổi hành vi**.
        name="M5 remove-max-turns-cap",
        description="Gỡ câu raise `AgentLoopExhausted` — vòng lặp mất trần lượt thật",
        fence="Cap `max_turns` (engine — AIE-1)",
        path=_ENGINE_SRC / "agent_loop.py",
        anchor="        if i == max_turns:\n            raise AgentLoopExhausted(",
        replacement="        if False:  # MUTANT M5\n            raise AgentLoopExhausted(",
        zero_means="Một agent không bao giờ chịu dừng sẽ chạy tới khi hết tiền/hết thời gian, và "
        "không bài test nào bắt được — `AgentLoopExhausted` thành code chết.",
    ),
)


def _count_failing_tests() -> int:
    """Chạy suite **toàn workspace từ gốc kit** rồi đếm số test đỏ.

    Từ gốc kit chứ không phải từ repo con: CI của repo con mù với 5 repo còn lại, nên một mutant ở
    engine có thể được **test của evalhub** bắt, và ngược lại. Đó chính là thứ *"chéo"* đo."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    summary_lines = [d for d in result.stdout.splitlines() if " passed" in d or " failed" in d]
    if not summary_lines:
        print(result.stdout[-2000:], file=sys.stderr)
        raise RuntimeError("không đọc được dòng tổng kết của pytest — xem stderr ở trên")
    summary = summary_lines[-1]
    print(f"      {summary.strip()}")
    if " failed" not in summary:
        return 0
    return int(summary.split(" failed")[0].strip().split()[-1])


def main() -> int:
    if not (_ENGINE_SRC / "agent_loop.py").is_file():
        print(
            "DỪNG: packages/engine chưa ở con trỏ có `agent_loop.py`.\n"
            "3/5 mutant nhắm vào vòng lặp mới (engine#36, 65731e5). Chạy khi thiếu sẽ in một bảng\n"
            "trông đủ nhưng bỏ qua đúng 3 hàng rào — tệ hơn không đo.\n"
            "  git -C packages/engine checkout 65731e5",
            file=sys.stderr,
        )
        return 2

    print("Đo nền (không mutant):")
    baseline = _count_failing_tests()
    if baseline != 0:
        print(
            f"DỪNG: suite đã đỏ sẵn {baseline} bài trước khi gieo — mọi con số sau đó không đọc được.",
            file=sys.stderr,
        )
        return 2

    result: list[tuple[Mutant, int]] = []
    for mutant in _MUTANTS:
        original = mutant.path.read_text(encoding="utf-8")
        occurrences = original.count(mutant.anchor)
        if occurrences != 1:
            filename = mutant.path.name
            print(f"DỪNG: anchor của {mutant.name} xuất hiện {occurrences} lần trong {filename}", file=sys.stderr)
            return 2
        print(f"\n{mutant.name} — {mutant.description}")
        try:
            mutant.path.write_text(original.replace(mutant.anchor, mutant.replacement), encoding="utf-8")
            result.append((mutant, _count_failing_tests()))
        finally:
            mutant.path.write_text(original, encoding="utf-8")

    print("\n" + "=" * 92)
    print(f"{'mutant':<38} {'hàng rào':<34} {'bắt':>5}")
    print("-" * 92)
    for mutant, hits in result:
        flag = "  ⚠️ PHÁT HIỆN" if hits == 0 else ""
        print(f"{mutant.name:<38} {mutant.fence:<34} {hits:>5}{flag}")
    print("=" * 92)

    survivors = [mutant for mutant, hits in result if hits == 0]
    if survivors:
        print("\nMutant SỐNG SÓT — mỗi cái là một hành vi không test nào khoá, phải mở issue:")
        for mutant in survivors:
            print(f"\n  {mutant.name} ({mutant.fence})\n    {mutant.zero_means}")
    print("\nKiểm `git status --short` ở gốc kit VÀ ở từng submodule — phải sạch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
