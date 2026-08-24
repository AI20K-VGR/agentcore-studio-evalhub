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
    golden_set_ref TEXT NOT NULL,
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
-- ⚠️ FAILURE MODE (finding review AIE-1, `evalhub#23`): `ADD COLUMN … NOT NULL` **không có
-- `DEFAULT`** sẽ **raise** nếu bảng đã có row.
--
-- ## Tripwire ĐÃ ĐỎ — writer thật đã land (cập nhật D23, `evalhub#41`)
--
-- Bản trước dạy: *"kết quả sạch = đúng 1 hit"* của
--
--     grep -rn "INSERT INTO eval" packages/*/src apps/*/src
--
-- và tự ràng buộc rằng luật đó *"phải được sửa **trong cùng PR** land writer"*. Writer đã land
-- (`studio_workbench/publish.py`, `INSERT INTO eval.scorecards` trong `publish()`) nhưng luật đọc
-- **không** được sửa cùng lúc ⇒ grep giờ trả **3 hit** và comment vẫn nói *"chưa có writer"*. Một
-- phép kiểm dạy sai còn tệ hơn không có phép kiểm: nó mời người sau kết luận ngược.
--
-- ## Vì sao `ADD COLUMN … NOT NULL` VẪN an toàn — lý do MỚI, không phải lý do cũ
--
-- Lý do cũ (*"chưa ai ghi nên bảng rỗng"*) đã hết đúng. Lý do đang đỡ hôm nay là **thứ tự land**,
-- và nó bền hơn:
--
-- 1. `tenant_id` vào DDL ở **D20**, trước writer đầu tiên (**D23**);
-- 2. `ensure_all_schemas()` chạy **mỗi lần boot**, tức `ALTER` áp trước mọi lần ghi của tiến trình đó;
-- 3. writer khai `tenant_id` **tường minh** trong danh sách cột của `INSERT` — một DB thiếu cột thì
--    **chính câu INSERT** đỏ, không phải chờ tới `ALTER`.
--
-- ⇒ Không tồn tại đường nào sinh ra **row có trước cột**. Rủi ro đo được vẫn **0**, nhưng vì tính
-- chất (1)+(3), không vì *"bảng rỗng"*.
--
-- Bất biến đó được **khoá bằng bài test**, không chỉ bằng comment này — comment vừa tự chứng minh nó
-- trôi được: `tests/test_eval_schema_rls.py::test_ddl_is_safe_on_populated_table`.
--
-- ## Điều kiện lật (thứ thay cho luật "đúng 1 hit")
--
-- Câu `ALTER` dưới đây thành nguy hiểm khi có **một** trong hai:
--
-- - một writer `eval.*` **không** khai `tenant_id` trong danh sách cột (phá tính chất 3); hoặc
-- - một cột `NOT NULL` **mới** được thêm vào đây **sau** khi bảng đã có dữ liệu thật (phá tính chất 1).
--
-- Ngày đó câu này **fail loud**, và đó là hành vi ĐÚNG — nó buộc người migrate trả lời *"row cũ
-- thuộc tenant nào"* thay vì lấp bằng một `DEFAULT` bịa ra. Một `DEFAULT gen_random_uuid()` hay
-- `DEFAULT '00000000-…'` sẽ gán tenant SAI cho dữ liệu thật mà không ai biết — đúng lớp lỗi
-- `DEC-D20-05` viết ra để tránh. Đường vá đúng lúc đó là **backfill có chủ đích**, không phải nới
-- DDL này.
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

-- `golden_set_ref` UNIQUE **toàn cục** → UNIQUE **theo cặp `(tenant_id, golden_set_ref)`**.
--
-- Bản đầu khai `golden_set_ref TEXT NOT NULL UNIQUE` ngay trong `CREATE TABLE`, tức duy nhất trên
-- toàn bảng. Sai ngữ nghĩa: bảng này có `tenant_id NOT NULL` và RLS `FORCE` theo tenant — nó **đã
-- là** bảng per-tenant ở mọi mặt khác. Ràng buộc toàn cục nói rằng Ankor đặt tên bộ là
-- `"handbook-v1"` thì Borea **vĩnh viễn** không được dùng tên đó, dù RLS làm hai bên không bao giờ
-- nhìn thấy nhau.
--
-- Hệ quả thật (không phải chuyện gọn gàng): cutover golden-set từ file sang DB đòi mỗi tenant một
-- bộ. Với ràng buộc cũ, tenant thứ hai trở đi phải **bịa tên khác cho cùng một khái niệm** — và
-- `recipe.golden_set_ref` là thứ người dùng khai trong recipe, nên cái tên bịa rò ra tận UI. Cách
-- vá hay gặp (nhồi tenant vào chuỗi: `"borea/handbook-v1"`) đẩy một khoá HAI phần vào MỘT cột
-- chuỗi, không ai cưỡng chế cấu trúc ngầm đó, và nó sẽ lệch.
--
-- **`CREATE UNIQUE INDEX IF NOT EXISTS` chứ không `ADD CONSTRAINT`**: Postgres không có
-- `ADD CONSTRAINT IF NOT EXISTS`, nên đường kia bắt buộc phải bọc `DO $$ … pg_constraint … $$` —
-- một khối procedural trong một file DDL vốn thuần khai báo, chỉ để mua lại tính idempotent mà
-- `CREATE INDEX` cho sẵn. Về **cưỡng chế** hai dạng tương đương; `ON CONFLICT (tenant_id,
-- golden_set_ref)` (dạng danh sách cột) hoạt động với unique index như với constraint, nên writer
-- tương lai không mất gì.
--
-- `DROP CONSTRAINT IF EXISTS` dùng tên Postgres tự sinh cho `UNIQUE` inline
-- (`{table}_{column}_key`, không mang tiền tố schema) — đã kiểm trên DB test thật, không đoán:
-- lệnh `psql` mô tả bảng → `"golden_sets_golden_set_ref_key" UNIQUE CONSTRAINT, btree (golden_set_ref)`.
-- DB dựng mới sau thay đổi này không có constraint đó ⇒ `IF EXISTS` biến câu thành no-op; DB cũ thì
-- nó gỡ đúng ràng buộc sai. Hai đường hội tụ về cùng một hình dạng.
--
-- An toàn trên bảng có dữ liệu: cùng lý lẽ khối `tenant_id` ở trên, cộng một quan sát đo được —
-- `eval.golden_sets` hiện **0 row** (`SELECT count(*)` trên DB test), và chưa có writer nào. Nếu
-- ngày nào đó bảng đã có hai row cùng `golden_set_ref` trong CÙNG một tenant, `CREATE UNIQUE INDEX`
-- sẽ **fail loud** — đúng hành vi mong muốn: nó buộc người migrate trả lời *"bộ nào là bộ thật"*
-- thay vì im lặng giữ lại một cái.
ALTER TABLE eval.golden_sets DROP CONSTRAINT IF EXISTS golden_sets_golden_set_ref_key;
CREATE UNIQUE INDEX IF NOT EXISTS eval_golden_sets_tenant_ref_uidx
    ON eval.golden_sets (tenant_id, golden_set_ref);

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
