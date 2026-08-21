"""eval.* schema DDL seam (schema-per-quadrant, Decision #4).

P1 stub filled at Phase 8 (Evalhub, AIE-2 owner) — `ensure_all_schemas()` (Phase 3,
`apps/studio/src/studio_app/core/schema.py`) direct-imports this module and calls `ddl()`. This
file is edited ONLY here, never `apps/studio` (antichain, plan.md "Dependency matrix &
file-ownership").

`eval.golden_sets` — one row per golden-set (produced by DE's doc-factory, consumed by AIE-2's
`harness.py`): `cases` is a JSONB array of the 30 `{case_id, expected}` pairs the eval-harness
runs against an agent recipe.

`eval.scorecards` — one row per **successful publish**, shaped to match the `Scorecard` contract
(P2, R-SPEC A1#4): `results` (per-case `CaseResult`s), `aggregate` (success_rate/citation_accuracy),
`gate` (threshold + verdict — the field SWE's publish/rollback pipeline reads, INV-6), plus
`recipe_hash` + `recipe_version` để nối ngược về hàng `wb.recipes` mà scorecard này chứng nhận.

**Sửa lại từ *"one row per eval run"* (review `workbench#28` mục 🟡3).** Câu cũ tả một bảng không
tồn tại: writer duy nhất (`studio_workbench.publish`) chỉ ghi trên **đường PASS**, và route
`/api/agents/{id}/evaluate` chạy đủ một eval run rồi trả `Scorecard` mà **không** gọi `publish()` ⇒
phần lớn eval run không để lại hàng nào, còn publish bị chặn (`verdict=FAIL`, hash lệch, graph-lint)
cũng không. Lựa chọn "chỉ PASS" là hợp lý — một publish bị chặn không sinh ra bản certify nào để
audit — nhưng khi đó **mô tả phải nói đúng thứ bảng chứa**, không thì người đọc `count(*)` ở đây sẽ
đọc thành số lần chấm.

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
    kb_id UUID,
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
    recipe_hash TEXT,
    recipe_version INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Đường thứ hai cho DB đã tồn tại trước T6: `CREATE TABLE IF NOT EXISTS` ở trên là no-op trên bảng
-- đã có, nên không có hai câu này thì cột chỉ xuất hiện ở fresh clone.
--
-- ⚠️ FAILURE MODE, cố ý KHÔNG vá hôm nay (finding review AIE-1, evalhub#23): `ADD COLUMN … NOT NULL`
-- **không có `DEFAULT`** sẽ **raise** nếu bảng đã có row. Hôm nay rủi ro đo được = **0** — hai bảng
-- này chưa có writer thật nào ngoài test. Land NOT NULL trần lúc bảng còn rỗng là đúng chỗ rẻ nhất.
--
-- Bản trước còn viện thêm lý do *"`recipe_hash` (`DEC-03`) chưa tồn tại"* — **hết đúng từ D22/D23**:
-- producer là `studio_workbench.publish.recipe_hash()` (`workbench#27`), call-site là
-- `apps/studio/routes/publish.py::_evaluate` (`app#26`). Vế còn đứng là vế *"chưa có writer"*, và
-- chính nó giữ cho `ADD COLUMN` bên dưới còn rẻ — nên khi mục 2 của `evalhub#28` land (SWE ghi
-- `INSERT INTO eval.scorecards` trong `publish()`), lý do này mất, và luật đọc tripwire ở dưới
-- (*"đúng 1 hit"*) phải được sửa **trong cùng PR đó**.
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

-- `kb_id` — nối ngược golden-set này tới đúng KB phòng ban đã sinh ra nó (ERD
-- `G:\\My Drive\\ERD.drawio`, target schema `agentcore-studio-kit#DATABASE-DESIGN-DAY30.md` chưa vẽ,
-- land SỚM dưới dạng cột shell — cùng lý do `kb.knowledge_bases`/`kb.documents`/`kb.chunk_pointers`
-- phía `agentcore-studio-kb` land shell trước, chưa có writer).
--
-- NULLABLE (khác `tenant_id` ngay trên, GIỐNG `recipe_hash`/`recipe_version` bên dưới): `kb_id` trỏ
-- sang `kb.knowledge_bases` — bảng đó CHÍNH NÓ cũng vừa land dạng shell, chưa ai ghi được `kb_id`
-- thật. `NOT NULL` trần ở đây sẽ khoá cứng writer tương lai phải biết KB trước khi biết `tenant_id`
-- có sẵn hay không — chặt hơn cần thiết cho một liên kết chưa ai tiêu thụ. `NULL` đọc đúng nghĩa
-- "golden-set này chưa gắn KB nào" — không phải giá trị bịa.
--
-- KHÔNG `REFERENCES kb.knowledge_bases(id)`: cross-schema FK (eval → kb) vi phạm luật "không FK
-- xuyên schema" đã áp dụng cho mọi `tenant_id` trong file này (Decision #4) — `kb_id` theo đúng
-- khuôn đó, một cột UUID trần, ràng buộc join ở tầng ứng dụng khi có writer thật.
ALTER TABLE eval.golden_sets ADD COLUMN IF NOT EXISTS kb_id UUID;

-- `recipe_hash` NULLABLE, và đó là chỗ khác `tenant_id` ngay trên: kiểu Python là
-- `Scorecard.recipe_hash: str | None` (`DEC-03` cho phép `None`, consumer `publish()` fail-closed
-- trên `None` chứ không cấm nó tồn tại), nên `NOT NULL` ở đây sẽ **chặt hơn hợp đồng** — và cũng là
-- thứ raise trên bảng đã có row mà không cần bàn migration. Không `DEFAULT`: một hash bịa ra tệ hơn
-- một hash vắng mặt, vì `NULL` đọc được thành *"scorecard này không khai recipe nào"* còn một chuỗi
-- rác thì đọc thành *"khai một recipe không tồn tại"*.
ALTER TABLE eval.scorecards ADD COLUMN IF NOT EXISTS recipe_hash TEXT;

-- `recipe_version` — vế thứ hai của khoá audit, và một mình `recipe_hash` KHÔNG thay được nó.
-- Đo được (review `workbench#28`): publish lại một recipe **nội dung y nguyên** cho ra version mới
-- nhưng **cùng** `recipe_hash` ⇒ nối `eval.scorecards → wb.*` bằng hash là **một-nhiều**, và câu mà
-- `evalhub#28` mở ra để hỏi — *"scorecard nào đã chứng nhận VERSION nào của agent này"* — vẫn treo.
--
-- Nối vào `wb.recipes`, KHÔNG phải `wb.recipe_versions`: `wb.recipes` có `UNIQUE (agent_id,
-- tenant_id, version)` còn `wb.recipe_versions` **không có** (`workbench/schema.py:61` vs `:64-70`,
-- và `publish.py` tự khai điều đó khi giải thích vì sao `rollback()` phải đọc theo NỘI DUNG). Nên
-- khoá nối duy nhất đúng là `(agent_id, tenant_id, recipe_version)` **cộng** điều kiện `agent_id` của
-- hàng audit khớp `agent_id` của recipe được publish — vế sau là finding riêng ở `workbench#28`, và
-- thiếu nó thì cột này chỉ là trang trí.
--
-- NULLABLE, cùng lý do `recipe_hash`: hàng ghi trước khi writer biết truyền version (và mọi hàng của
-- một writer tương lai chọn không truyền) phải ghi được. `NOT NULL` ở đây vừa chặt hơn cần thiết vừa
-- raise trên bảng đã có row.
ALTER TABLE eval.scorecards ADD COLUMN IF NOT EXISTS recipe_version INT;

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
