# Runbook — từ `git clone` tới bảng per-case của một run thật

**Ngày diễn tập:** 2026-08-07 (D15) · **Người chạy:** AIE-2 · **Kết quả: CHẠY ĐƯỢC, exit 0.**

`kit#74`: *"I clone your repo fresh and run your commands exactly as written. If it does not run from
a clean recursive clone, it does not count as delivered."*

Chưa ai trong nhóm diễn tập việc này trong cả Sprint 2. Trang này là biên bản của lượt đầu tiên —
lệnh nguyên văn đã chạy, cộng **bốn thứ vấp được** mà chỉ lộ ra khi thật sự clone ra chỗ khác.

## Lệnh — nguyên văn, đã chạy

```bash
# 1 · clone (58 giây)
git clone --recursive git@github.com:hieubui2409/agentcore-studio-kit.git kit
cd kit

# 2 · TẠM THỜI: pointer evalhub chưa bump, lấy nhánh D15 thủ công.
#     Bước này BIẾN MẤT sau khi evalhub PR #14 và #15 merge + parent bump pointer.
git -C packages/evalhub fetch origin aie-2/d15-t3-run-cases
git -C packages/evalhub checkout aie-2/d15-t3-run-cases

# 3 · deps (3 giây — cache uv nóng; máy lạ sẽ lâu hơn)
make setup

# 4 · Postgres test. `down -v` là CỐ Ý — xem vấp #2.
docker compose -f docker-compose.test.yml down -v
docker compose -f docker-compose.test.yml up -d --wait

# 5 · DSN. BẮT BUỘC, và không có chỗ nào trong repo nói ra — xem vấp #1.
export STUDIO_DATABASE_URL=postgresql://studio_app:changeme@localhost:5433/studio_test
export STUDIO_DATABASE_URL_ADMIN=postgresql://studio_owner:changeme@localhost:5433/studio_test

# 6 · seed một run THẬT vào obs.trace_events — xem vấp #3.
uv run pytest "apps/studio/tests/test_spine_scored_from_postgres.py::test_score_from_postgres_matches_score_from_memory"

# 7 · MỘT LỆNH → bảng per-case
RUN=$(uv run python -m studio_evalhub.run_report --list | head -1 | cut -f1)
uv run python -m studio_evalhub.run_report --run "$RUN:SC-01"
```

## Kết quả lượt diễn tập

```
RUN CASES — 56261603-371f-4a2d-acef-9ea57a2c73a6
------------------------------------------------------------------------------
golden_set_ref         callisto-smoke-5-v0
trace_source           obs.trace_events (Postgres — trace đã bền hoá qua PgTraceWriter)
------------------------------------------------------------------------------
case_id              expects_refusal  success   citation_accuracy
-----------------------------------------------------------------
SC-01                trả-lời          PASS                   1.00
-----------------------------------------------------------------
success (k/n thô)      1/1
citation (k/n thô)     1/1  — mẫu số đã loại refusal
```

`exit=0`. Suite evalhub trong clone sạch: `71 passed, 1 skipped, 2 xfailed, 0 XPASS`.

**`run_id` sẽ KHÁC ở mỗi lượt chạy** — interpreter sinh `uuid4` mới mỗi run. Cái tái lập được là
**bảng**, không phải chuỗi id. Ai đối chiếu xin so hình dạng bảng và hai dòng `k/n`, đừng so `run_id`.

## SHA của lượt diễn tập

| | |
|---|---|
| kit | `2809cbb` |
| `packages/evalhub` | `4eb4f64` (nhánh `aie-2/d15-t3-run-cases`, **chưa** ở pointer) |
| `packages/contracts` | `79edfb79` |
| `packages/engine` | `f8c36cc6` |
| `packages/kb` | `b57ba78a` |
| `apps/studio` | `03521767` |
| `apps/web` | `a6ec3def` |
| `packages/workbench` | `e8a9899e` |

---

## Bốn thứ vấp được — chỉ lộ ra khi thật sự clone ra chỗ khác

### Vấp #1 · Hai biến DSN là bắt buộc mà không chỗ nào trong repo nói ra

Không có `.env.example`, không có dòng nào trong `README.md` gốc, và `make setup` không đặt chúng.
Người clone mới chạy thẳng bước 7 sẽ nhận `thiếu DSN: đặt $STUDIO_DATABASE_URL hoặc truyền --dsn` —
thông báo đủ rõ để không mất thời gian, nhưng vẫn là một bước phải **đoán ra**.

Giá trị `studio_app:changeme` / `studio_owner:changeme` / port `5433` không suy được từ
`docker-compose.test.yml` (file đó chỉ khai `POSTGRES_USER=postgres`); chúng đến từ script trong
`docker/postgres-init/`. Hôm nay nơi duy nhất chép được là `packages/kb/scripts/ingest_callisto.py`
docstring và plan D11 của AIE-2 — hai chỗ mà người mới không có lý do gì để mở.

**Đề nghị:** một `.env.example` ở gốc kit. **Chủ: chưa có** (gốc kit CODEOWNERS = mentor). Ghi là
vô-chủ-có-hạn, xin chốt D16. Trong lúc chờ, trang này là chỗ chép được.

### Vấp #2 · "Fresh clone" KHÔNG có nghĩa là "fresh database"

Đây là thứ đắt nhất tìm được hôm nay, và nó âm thầm.

Volume Postgres tên **toàn cục**: `studio_pgdata_test` (khai cứng ở `docker-compose.test.yml`, mục
`volumes.name`). Nó **không** thuộc thư mục clone. Nghĩa là clone repo ra một chỗ hoàn toàn mới rồi
`docker compose up` sẽ **gắn lại đúng volume cũ** — kèm mọi row của lượt chạy hôm trước.

Hệ quả cụ thể cho bộ chấm: `--list` sẽ liệt kê cả `run_id` của hôm qua, và `| head -1` (sắp theo
`min(ts)`, cũ nhất trước) sẽ chọn đúng cái cũ nhất — tức **một run không phải run vừa seed**. Bảng in
ra trông hoàn toàn hợp lệ. Không có lỗi nào nổi lên.

⇒ **`down -v` ở bước 4 là bắt buộc**, không phải cho gọn. Đây cùng một lớp lỗi với `.pyc` khoá theo
`(mtime giây, size)` mà mutation sweep đã trả giá: một cái cache mà mình quên là nó tồn tại.

### Vấp #3 · Bước seed đang là một **test**, không phải một script

Bước 6 chạy `pytest` trên `apps/studio/tests/test_spine_scored_from_postgres.py` để có trace bền hoá.
Nó chạy được, nhưng dùng một test làm bước dựng dữ liệu là mượn tạm:

- test có thể được đổi tên hoặc gộp bất cứ lúc nào — nó không phải bề mặt công khai;
- `conftest.py::_truncate_all` **TRUNCATE trước mỗi test**, nên chạy cả file thay vì một hàm sẽ để
  lại run của test **cuối** — và test cuối là bài negative control cố tình **bơm citation sai**. Chạy
  nhầm cả file thì bảng ra `citation 0/1` mà không sai ở đâu cả;
- nó nằm ở `apps/studio` — CODEOWNERS **mentor**, tức AIE-2 không sửa được nếu nó vỡ.

Đường đúng là `#101` (AIE-1): batch thật chạy 6 executor, emit trace đúng schema. Khi có nó thì bước
6 thay bằng lệnh của `#101` và runbook này ngắn đi một dòng. **Chủ: AIE-1 · mốc: `#101`.**

### Vấp #4 · Pointer chưa bump nên còn bước 2

Bước 2 tồn tại **chỉ vì** evalhub PR chưa merge tại thời điểm diễn tập. Ghi ra thay vì giấu: một
runbook có bước *"checkout nhánh"* là runbook chưa xong. Xoá bước 2 ngay sau khi `#14`/`#15` merge và
parent bump `packages/evalhub`.

---

## Vì sao diễn tập hôm nay chứ không phải D20

Vấp #1 và #2 đều **không** thể tìm ra bằng cách đọc lại code trên máy mình: máy mình đã có sẵn biến
môi trường trong shell và đã có sẵn volume với dữ liệu. Cả hai chỉ lộ ra khi đứng ở vị trí người thứ
hai. Vấp ở D15 còn 5 ngày để sửa; vấp ở D20 là mất trắng.
