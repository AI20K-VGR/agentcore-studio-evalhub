"""eval.* schema DDL seam (schema-per-quadrant, Decision #4).

P1 stub filled at Phase 8 (Evalhub, AIE-2 owner) — `ensure_all_schemas()` (Phase 3,
`apps/studio/src/studio_app/core/schema.py`) direct-imports this module and calls `ddl()`. This
file is edited ONLY here, never `apps/studio` (antichain, plan.md "Dependency matrix &
file-ownership").

`eval.golden_sets` — one row per golden-set (produced by DE's doc-factory, consumed by AIE-2's
`harness.py`): `cases` is a JSONB array of the 30 `{case_id, expected}` pairs the eval-harness
runs against an agent recipe.

`eval.scorecards` — one row per eval run, shaped to match the `Scorecard` contract (P2, R-SPEC
A1#4): `results` (per-case `CaseResult`s), `aggregate` (success_rate/citation_accuracy), `gate`
(threshold + verdict — the field SWE's publish/rollback pipeline reads, INV-6).

## RLS trên cả hai bảng — `DEC-D20-05` (D20)

`kb#24` lật `eval.scorecards` từ *KHÔNG CẦN* sang **CẦN RLS**, và tiêu chí là **bản chất data**,
không phải *ai đọc*: `harness.py:463` đổ `actual`/`expected` vào `results JSONB` ⇒ bảng chứa
**answer-text của tenant**. `eval.golden_sets` cùng hạng: `cases` mang `query` + `expected` của
tenant, chỉ trông vô hại vì nó tên là *"đề bài"*.

Cùng khuôn `wb.recipes`/`kb.chunks`: `ENABLE` + **`FORCE`** ROW LEVEL SECURITY, policy `USING` +
`WITH CHECK` khoá vào `NULLIF(current_setting('app.tenant_id', true), '')::uuid`. Session chưa set
biến ⇒ `NULL` ⇒ `tenant_id = NULL` không bao giờ đúng ⇒ **fail-closed thấy/ghi 0 row**, không raise
và không rò. `FORCE` để policy cắn cả `studio_owner` — cần, vì `ensure_all_schemas()` chạy DDL này
bằng admin pool.

**Vì sao land hôm nay** chứ không phải *"khi có writer"*: trước writer đầu tiên đây là một dòng DDL
trên bảng rỗng; sau đó là migration trên bảng đã có dữ liệu nhiều tenant, cộng câu hỏi không trả lời
được *"dữ liệu đã ghi trước đó thuộc tenant nào"*. D20 là ngày `Scorecard` thật đầu tiên tồn tại ⇒
ngày cuối món này còn rẻ.

**Hai đường thêm cột, cả hai đều cần:** `CREATE TABLE` mang sẵn `tenant_id` cho fresh clone, và
`ALTER TABLE … ADD COLUMN IF NOT EXISTS` cho DB đã tồn tại từ trước T6 — `CREATE TABLE IF NOT
EXISTS` là **no-op** trên bảng đã có, nên thiếu đường thứ hai thì máy đồng đội không bao giờ có cột.
"""

_EVAL_DDL = """
CREATE SCHEMA IF NOT EXISTS eval;

CREATE TABLE IF NOT EXISTS eval.golden_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    golden_set_ref TEXT NOT NULL UNIQUE,
    cases JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval.scorecards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    agent_id TEXT NOT NULL,
    golden_set_ref TEXT NOT NULL,
    results JSONB NOT NULL,
    aggregate JSONB NOT NULL,
    gate JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Đường thứ hai cho DB đã tồn tại trước T6: `CREATE TABLE IF NOT EXISTS` ở trên là no-op trên bảng
-- đã có, nên không có hai câu này thì cột chỉ xuất hiện ở fresh clone.
--
-- ⚠️ FAILURE MODE, cố ý KHÔNG vá hôm nay (finding review AIE-1, evalhub#23): `ADD COLUMN … NOT NULL`
-- **không có `DEFAULT`** sẽ **raise** nếu bảng đã có row. Hôm nay rủi ro đo được = **0** — hai bảng
-- này chưa có writer thật nào ngoài test, và `recipe_hash` (`DEC-03`) chưa tồn tại. Land NOT NULL
-- trần lúc bảng còn rỗng là đúng chỗ rẻ nhất.
--
-- Kiểm lại từ **gốc kit**, và đọc kết quả cho đúng (finding review DE, evalhub#24):
--
--     grep -rn "INSERT INTO eval" packages/*/src apps/*/src
--
-- Kết quả sạch = **đúng 1 hit, và hit đó là CHÍNH DÒNG NÀY**. Nhiều hơn 1 ⇒ đã có writer thật ⇒
-- `ADD COLUMN … NOT NULL` bên dưới không còn an toàn trên môi trường có dữ liệu.
--
-- Bản trước viết `*/src` — **glob 1 cấp, không với tới `packages/*/src`** (sâu 2 cấp) nên nó trả
-- rỗng vì **hụt đường dẫn**, không vì "không có writer", và sẽ **vẫn rỗng kể cả sau khi có writer
-- thật**. Một lệnh verify chỉ-trông-có-vẻ-verify thì tệ hơn không có lệnh nào: nó mời người sau tin
-- vào một phép đo không chạy. Đúng lớp lỗi mà chính commit kia đang vá ở premise judge-routing.
--
-- Ngày có writer thật + môi trường nào đó đã có row: câu này **fail loud**, và đó là hành vi ĐÚNG —
-- nó buộc người migrate trả lời *"row cũ thuộc tenant nào"* thay vì lấp bằng một `DEFAULT` bịa ra.
-- Một `DEFAULT gen_random_uuid()` hay `DEFAULT '00000000-…'` ở đây sẽ gán tenant SAI cho dữ liệu
-- thật mà không ai biết — đúng lớp lỗi `DEC-D20-05` viết ra để tránh. Đường vá đúng lúc đó là
-- backfill có chủ đích, không phải nới DDL này.
ALTER TABLE eval.golden_sets ADD COLUMN IF NOT EXISTS tenant_id UUID NOT NULL;
ALTER TABLE eval.scorecards ADD COLUMN IF NOT EXISTS tenant_id UUID NOT NULL;

ALTER TABLE eval.golden_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE eval.golden_sets FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS eval_golden_sets_tenant_isolation ON eval.golden_sets;
CREATE POLICY eval_golden_sets_tenant_isolation ON eval.golden_sets
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

ALTER TABLE eval.scorecards ENABLE ROW LEVEL SECURITY;
ALTER TABLE eval.scorecards FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS eval_scorecards_tenant_isolation ON eval.scorecards;
CREATE POLICY eval_scorecards_tenant_isolation ON eval.scorecards
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
"""


def ddl() -> str:
    """Return this quadrant's idempotent DDL — `eval.golden_sets` + `eval.scorecards`."""
    return _EVAL_DDL
