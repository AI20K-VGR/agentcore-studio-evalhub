---
id: studio.mini-rfc.TEMPLATE
type: mini-rfc-template
status: template
created: 2026-08-03
created_by: AIE-2 — Lưu Tiến Duy (D11)
---

# Mini-RFC — TEMPLATE

> **Dùng khi nào.** Sau khi một hợp đồng đã `FROZEN`, mọi thay đổi **rename · removal ·
> required-add** trên hợp đồng đó cần một mini-RFC + **4/4 chữ ký** (`contracts/__init__.py:5-12` +
> umbrella-contract §3). Trước freeze thì **không cần** — mở PR thẳng, rẻ hơn 10×.
>
> **KHÔNG dùng khi nào** — bốn ca hay bị định giá quá cao (mỗi ca đã tốn thật ít nhất một lần):
>
> | Ca | Vì sao không cần mini-RFC |
> |---|---|
> | Thêm field **optional** mới | `__init__.py:5-12` cho phép tường minh, không bump |
> | Nới `required` → `optional` | ADR-D11-02: không bump, điều kiện *đếm được 0 reader giả định non-null* |
> | Khoá câu chữ về một field **đã tồn tại** (vd `outputs["chunks"]`) | Shape không đổi ⇒ chỉ là một dòng doc. Đây là ca đã bị định giá thành "4/4 chữ ký" ở `scorecard-v0.md:335-337` rồi phải **rút** |
> | Đổi kiểu **nội bộ quadrant** (không nằm trong `studio_contracts`) | Vd `GoldenCase`, `SmokeResult`, `AgentRunner` — không ai ngoài quadrant import |
>
> **Kiểm trước khi viết:** `grep -rn "<tên field>" packages apps scripts tests`. Nếu ra **0 reader
> ngoài quadrant** thì gần chắc không cần mini-RFC.

---

## 0 · Metadata

| | |
|---|---|
| **Mini-RFC id** | `MRFC-<ngày>-<slug>` |
| **Hợp đồng chạm** | `<recipe \| trace-event \| kb.search \| scorecard>` |
| **Người giữ bút hợp đồng đó** | `<@github-id>` |
| **Người đề xuất** | `<@github-id>` |
| **Loại thay đổi** | `<rename \| removal \| required-add \| khác>` |
| **Bump `SCHEMA_VERSION`?** | `<có → từ X sang Y \| không → vì sao>` |
| **Ngày mở** | `<YYYY-MM-DD>` |
| **Hạn xin đủ 4/4** | `<YYYY-MM-DD>` |

## 1 · Thay đổi cụ thể — diff, không phải mô tả

```diff
# file:line thật, không phải pseudo-code
```

## 2 · Vì sao cần — và vì sao KHÔNG hoãn được

Nêu cái **bị chặn** nếu không làm. Nếu không có gì bị chặn thì đây là dấu hiệu nên hoãn, không phải
dấu hiệu nên viết mini-RFC.

## 3 · Ai vỡ — đếm được, không phải "chắc là ít"

| Consumer (file:line) | Repo | Vỡ thế nào | Ai sửa |
|---|---|---|---|

Lệnh đã chạy để có bảng trên (dán nguyên văn, để người ký chạy lại được):

```bash
grep -rn "<pattern>" packages apps scripts tests
```

## 4 · Phương án đã cân nhắc và bỏ

**Bắt buộc ≥1 phương án bỏ, và phải là phương án mạnh nhất có thật — không phải bù nhìn.**

| Phương án | Vì sao bỏ |
|---|---|

## 5 · Proof consumer — CI KHÔNG chạy hộ

`reusable-domain-ci.yml:100` chỉ chạy `pytest <domain_path>/tests` ⇒ **PR vào `contracts` không bao
giờ chạy test của consumer**. Phải tự chạy và dán số:

```bash
git -C packages/contracts checkout <nhánh-của-RFC-này>
uv run pytest packages apps tests -q
uv run mypy packages apps
uv run lint-imports
git -C packages/contracts checkout <SHA-đang-ghim>   # BẮT BUỘC trả về
git status --short                                    # PHẢI rỗng
```

| Đo | Trước | Sau |
|---|---|---|
| `pytest packages apps tests` | | |
| `mypy packages apps` | | |
| `lint-imports` | | |

## 6 · Chữ ký — 4/4

Chữ ký thật = **bấm Approve trên PR** (ADR-D11-01 lớp 1, xác thực bằng tài khoản GitHub). Bảng dưới
chỉ là **dấu vết**, không phải chỗ ký:

| Vai | GitHub | PR đã Approve | Ngày | `<repo>@<sha>` |
|---|---|---|---|---|
| AIE-1 | @TranBaDat2607 | | | |
| AIE-2 | @dholmes0207 | | | |
| DE | @DongAnh2704 | | | |
| SWE | @Dozyboy | | | |

Verify không cần tin ai:

```bash
gh pr view <N> --repo <repo> --json reviews \
  --jq '.reviews[]|"\(.author.login) \(.state) \(.commit.oid[0:8])"'
```

## 7 · Nếu không đủ 4/4 trước hạn

Ghi trạng thái, **không** ghi sự im lặng của người khác:

```
Trạng thái: ĐÃ NỘP <path>@<sha> lúc <giờ>. Chữ ký: <n>/4 (còn <vai>).
Mặc định sẽ áp nếu không có phản đối trước <hạn>: <mặc định>.
```
