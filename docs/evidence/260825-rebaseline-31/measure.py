"""Re-baseline evalhub#31 trên stack HÔM NAY (app#48 `run_agent_loop` + workbench#41 `create_recipe`).

Chạy: uv run python <file> <n_runs>
"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from psycopg_pool import AsyncConnectionPool
from studio_app.eval_adapter import EngineAgentRunner
from studio_app.obs.trace_writer import PgTraceWriter
from studio_app.providers.openai import OpenAIProvider
from studio_contracts import Edge, Node, NodeType, Recipe
from studio_evalhub.harness import EvalHarness
from studio_evalhub.judge import LLMJudge
from studio_kb.doc_factory import TENANT_IDS
from studio_kb.postgres import PgKbSearch
from studio_workbench import create_recipe


class RunRow(TypedDict):
    """Một dòng kết quả. `TypedDict` chứ không `dict[str, object]`: bản sau bắt mọi chỗ đọc lại
    phải `cast`, và `len(r["truot"])` trên `object` là lỗi mypy chứ không phải lỗi thật.

    `citation`/`n_cit` khai `| None` vì `Aggregate` khai vậy — `DEC-D16-03`: *chưa đo* khác *đo
    được và bằng 0*. Trong 20 lượt của phép đo này chúng chưa bao giờ `None` (mẫu số giữ nguyên
    22), nhưng khai `float` trần ở đây là dựng lại đúng cái giả định mà luật kia cấm."""

    success: float
    citation: float | None
    n_cit: int | None
    verdict: str
    truot: list[str]
    cache_hit: int
    cache_miss: int
    vi_du_query_llm_tu_viet: list[str]


_KB = Path("packages/kb").resolve()
sys.path.insert(0, str(_KB / "tests" / "embedding-tests"))
# `packages/kb/tests/embedding-tests/` không phải package cài đặt được — nó là dụng cụ đo của kb,
# neo `CACHE_DIR` theo vị trí file của chính nó (xem docstring `ingest_callisto_v2.py`). Vá `sys.path`
# rẻ hơn nhiều so với lôi 9 MB cache vào wheel production.
#
# KHÔNG `type: ignore[import-not-found]` ở đây: gate thật là `uv run mypy packages apps` (gốc kit),
# và ở chế độ đó mypy CÓ phân giải được hai module này vì `packages/kb/tests/` nằm trong tập kiểm.
# Thêm ignore sẽ thành `unused-ignore` và làm CI đỏ. Chạy mypy trên RIÊNG file này thì ngược lại —
# nhưng đó không phải lệnh nào chạy trong CI.
from _vector_cache import VectorCache  # noqa: E402
from providers import GEMINI_DIM, GEMINI_MODEL, GeminiEmbedding  # noqa: E402

GOLDEN = _KB / "src" / "studio_kb" / "golden" / "callisto-2.0-golden-30-v1.yaml"
REF = "callisto-2.0-golden-30-v1"

# Đúng câu canvas thật gửi (apps/web/src/recipe/sample.ts:18).
INSTR_CANVAS = "Hãy tra cứu tài liệu Callisto và trả lời thắc mắc của người dùng."
# Câu khuyến nghị ở evalhub#31 — CHƯA BAO GIỜ được áp vào code.
INSTR_REFUSAL = (
    " Nếu câu hỏi hỏi về một công ty hoặc chủ thể KHÁC với chủ thể của các đoạn tài liệu được "
    "cung cấp, hãy TỪ CHỐI trả lời thay vì suy ra từ tài liệu của chủ thể khác."
)


class CacheThenNetworkEmbedding:
    """Cache trước, mạng sau — và ĐẾM số lần trượt cache.

    Số lần trượt chính là phép đo: cache đã có đủ 22 query phân biệt của golden 2.0 (ghi ở kb#40).
    Một text trượt cache nghĩa là nó KHÔNG phải câu hỏi golden nguyên văn — tức `run_agent_loop`
    đã để LLM tự viết lại câu tra cứu. Đường cũ (`interpreter.run`) không thể trượt: query lấy
    thẳng từ `node.params`.
    """

    def __init__(self) -> None:
        self._cached = GeminiEmbedding(allow_network=False)
        # Bản gọi mạng dùng thư mục cache RIÊNG (`VectorCache(cache_dir=...)`). Dùng chung với
        # `self._cached` sẽ làm hai chuyện, cả hai đều sai:
        #   1. lượt sau trúng cache đúng những query mà lượt trước LLM tự viết ra ⇒ `cache_miss`
        #      (thứ đang đo) tụt xuống vì chính phép đo, không vì hành vi đổi;
        #   2. sửa fixture đã commit ở kb#40, im lặng, ngay trong cây làm việc — đã xảy ra thật ở
        #      lượt chạy thử đầu tiên, phát hiện bằng `git status` chứ không bằng lỗi nào.
        _tmp = Path(tempfile.mkdtemp(prefix="rebaseline-emb-"))
        _live_cache = VectorCache(
            f"{GEMINI_MODEL.rsplit('/', 1)[-1]}-d{GEMINI_DIM}", model=GEMINI_MODEL, dim=GEMINI_DIM, cache_dir=_tmp
        )
        self._live = GeminiEmbedding(allow_network=True)
        # Gán SAU khi dựng, không qua `cache=`. `GeminiEmbedding.__init__` viết
        # `self._cache = cache or VectorCache(...)`, mà `VectorCache.__len__` trả 0 cho cache rỗng
        # ⇒ **falsy** ⇒ bản vừa tiêm bị vứt im lặng và provider quay về `CACHE_DIR` mặc định. Đo
        # được: `GeminiEmbedding(allow_network=True, cache=<cache rỗng ở /tmp>)._cache._bin` trỏ
        # vào `packages/kb/tests/embedding-tests/cache/`. Đó là lý do lượt đo trước ghi thêm 61
        # vector vào fixture đã commit dù đã "tách thư mục". Lỗi thuộc `providers.py` (kb) — nên
        # là `cache if cache is not None else ...`; ở đây chỉ đi vòng, không sửa repo người khác.
        self._live._cache = _live_cache
        self.name = self._cached.name
        self.hits = 0
        self.misses: list[str] = []

    def _embed_one(self, text: str) -> list[float]:
        try:
            v: list[float] = self._cached.embed([text])[0]
        except Exception:
            self.misses.append(text)
            fallback: list[float] = self._live.embed([text])[0]
            return fallback
        self.hits += 1
        return v

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(lambda: [self._embed_one(t) for t in texts])


def _recipe(instructions: str) -> Recipe:
    return create_recipe(
        agent_id="agent-rebaseline",
        tenant_id=TENANT_IDS["ankor"],
        instructions=instructions,
        tool_whitelist=[],
        nodes=[
            Node(id="n1", type=NodeType.KB_RETRIEVE, params={"top_k": 3}),
            Node(id="n2", type=NodeType.LLM_STEP, params={"temperature": 0.0}),
            Node(id="n4", type=NodeType.END, params={}),
        ],
        edges=[Edge(from_="n1", to="n2"), Edge(from_="n2", to="n4")],
    )


async def one_run(pool: Any, instructions: str, tag: str, i: int, outdir: Path) -> RunRow:
    emb = CacheThenNetworkEmbedding()
    llm = OpenAIProvider(api_key=os.environ["STUDIO_OPENAI_API_KEY"], model="gpt-4o-mini")
    runner = EngineAgentRunner(
        kb_search=PgKbSearch(pool, emb),
        llm=llm,
        embedding=emb,
        trace_writer=PgTraceWriter(pool),
        recipe=_recipe(instructions),  # nhánh (a) — đúng như routes/publish.py::_evaluate
    )
    # cache/cap TƯƠI mỗi lượt: judge không được mượn kết quả lượt trước
    judge = LLMJudge(
        llm, cache_path=outdir / f"judge-cache-{tag}-{i}.json", cap_path=outdir / f"judge-cap-{tag}-{i}.json"
    )
    sc = await EvalHarness().run(
        "agent-rebaseline",
        REF,
        golden_set_path=GOLDEN,
        runner=runner,
        tenant_ids=dict(TENANT_IDS),
        threshold_success=0.9,
        threshold_citation_accuracy=0.95,
        recipe_hash="rebaseline-not-published",
        judge=judge,
    )
    (outdir / f"scorecard-{tag}-{i}.json").write_text(sc.model_dump_json(indent=2), encoding="utf-8")
    truot = [r.case_id for r in sc.results if not r.success]
    return {
        "success": sc.aggregate.success_rate,
        "citation": sc.aggregate.citation_accuracy,
        "n_cit": sc.aggregate.n_scored_citation,
        "verdict": sc.gate.verdict,
        "truot": truot,
        "cache_hit": emb.hits,
        "cache_miss": len(emb.misses),
        "vi_du_query_llm_tu_viet": emb.misses[:5],
    }


async def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    outdir = Path(__file__).parent / "raw"
    outdir.mkdir(exist_ok=True)
    dsn = os.environ["STUDIO_DATABASE_URL"]
    ket: dict[str, list[RunRow]] = {}
    async with AsyncConnectionPool(dsn, open=False) as pool:
        await pool.open()
        for tag, instr in [("canvas", INSTR_CANVAS), ("canvas+refusal", INSTR_CANVAS + INSTR_REFUSAL)]:
            ket[tag] = []
            for i in range(1, n + 1):
                r = await one_run(pool, instr, tag.replace("+", "-"), i, outdir)
                print(
                    f"  {tag} lượt {i}: success={r['success']:.4f} citation={r['citation']:.4f} "
                    f"{r['verdict']} truot={len(r['truot'])}",
                    flush=True,
                )
                ket[tag].append(r)

    tong: dict[str, Any] = {"khi": datetime.now(UTC).isoformat(), "n": n, "model": "gpt-4o-mini", "ket": ket}
    for tag, rs in ket.items():
        ss = [r["success"] for r in rs]
        # `None` = trục citation KHÔNG đo được lượt đó (`DEC-D16-03`). Bỏ nó khỏi thống kê thay vì
        # coi là 0: một lượt không đo được kéo trung bình xuống sẽ đọc thành "chất lượng tụt".
        cs = [c for c in (r["citation"] for r in rs) if c is not None]
        tong[f"tomtat_{tag}"] = {
            "success_tb": round(statistics.fmean(ss), 4),
            "success_min": min(ss),
            "success_max": max(ss),
            "success_sd": round(statistics.stdev(ss), 4) if len(ss) > 1 else None,
            "citation_tb": round(statistics.fmean(cs), 4) if cs else None,
            "citation_min": min(cs) if cs else None,
            "citation_max": max(cs) if cs else None,
            "citation_n_do_duoc": len(cs),
            "pass": sum(1 for r in rs if r["verdict"] == "PASS"),
        }
    (outdir / "tong-hop.json").write_text(json.dumps(tong, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in tong.items() if k.startswith("tomtat")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
