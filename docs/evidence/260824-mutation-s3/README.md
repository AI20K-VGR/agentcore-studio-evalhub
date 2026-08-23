# 24/08 — mutation **chéo**: 5 hàng rào Sprint 3 có được test khoá không

> Suite xanh là **điều kiện cần**, không phải bằng chứng. Bằng chứng là: làm hỏng `src/` rồi xem
> test có đỏ không. 4/5 mutant nằm ở `src/` của quadrant **khác** — không ai chấm bài của chính mình.
>
> Tái lập: `./run.sh` (≈10 phút, 6 lượt suite toàn workspace). Số thô: [`raw/sweep.log`](raw/sweep.log).

## Điều kiện đo

| | |
|---|---|
| Lệnh | `./run.sh` → `packages/evalhub/scripts/mutation_s3.py` |
| Phạm vi chạy | `pytest` **từ gốc kit** (toàn workspace), không phải suite repo con |
| Nền (không mutant) | **1686 passed**, 7 skipped, 1 xpassed, 0 failed |
| `packages/engine` | `65731e5` (`engine#36` — cần `agent_loop.py`) |
| `packages/kb` | `72b6133` |
| `packages/evalhub` | nhánh `fix/answer-from-trace-multi-turn` @ `24fabad` |
| Postgres | `docker-compose.test.yml`, pgvector pg17 @ `5433` |

**Chạy từ gốc kit, không từ repo con** — CI repo con mù với 5 repo còn lại, nên một mutant ở `engine`
có thể được **test của evalhub** bắt và ngược lại. Đó chính là thứ *"chéo"* đo được.

---

## Bảng kết quả

| # | Mutant | Hàng rào | Chủ `src/` | **bắt** |
|---|---|---|---|---|
| **M1** | `kb_search` bỏ qua `session_context`, lấy tenant/roles LLM tự khai | INV-1 Tenant-Wall | engine — AIE-1 | **26** |
| **M2** | Xoá `AND section_role = ANY(%s)` khỏi câu SQL truy xuất | T6 hàng rào phòng ban | kb — DE | **17** |
| **M3** | Bỏ cổng *chỉ `llm-step` mới được mang `citations`* | C-1 | engine — AIE-1 | **1** |
| **M4** | `chunks_from_trace` trả `[]` thay vì `None` | 3 nghĩa `None`/`[]`/`list` | evalhub — AIE-2 | **3** |
| **M5** | Gỡ câu `raise AgentLoopExhausted` | Cap `max_turns` | engine — AIE-1 | **3** |

**Không mutant nào `bắt == 0`.** Cả 5 hàng rào đều có ít nhất một bài khoá.

`bắt` = số test đỏ dưới mutant đó. Công thức: `bắt = (số failed dưới mutant) − (số failed ở nền)`,
và nền = 0 nên `bắt` đọc thẳng từ dòng tổng kết pytest.

---

## ⚠️ M3 — khoá được, nhưng **lưới mỏng nhất** trong 5

Cổng C-1 là thứ chặn một tool tự khai `citations` đi thẳng vào trace thành trích dẫn thật rồi ăn
điểm `citation_accuracy` giả — fail-open đúng vào trục chấm điểm. Cả workspace **1686 bài** chỉ có
**một** bài khoá nó.

Chưa phải phát hiện chặn (`bắt > 0`), nhưng đáng nêu: một bài bị xoá/đổi vì lý do không liên quan là
cổng đó về `0` mà không ai biết. Có tiền lệ trong repo — `M-T4` (`judge-no-trace-d23.md`) cũng chỉ bị
1 bài giết và đã được ghi là *"vế đó cần lưới riêng"*.

**Đề nghị:** thêm một bài ở evalhub khoá phía **consumer** (`citations_from_trace` gom `.citations`
từ **mọi** event, cố ý node-agnostic ⇒ nó không tự phân biệt được nguồn). Hôm nay lưới nằm hết ở
phía producer.

---

## ⛔ Bài học đọc kết quả: M5 vòng 1 **sống sót**, và đó là mutant SAI chứ không phải lỗ hổng

Vòng 1 gieo vào **cận vòng lặp**:

```
range(1, max_turns + 1)  →  range(1, 10_000)
bắt = 0/1686        ← trông y hệt một phát hiện
```

Nhưng cap **không** được cưỡng chế ở cận. Nó nằm ở câu **bên trong** thân:

```python
if i == max_turns:
    raise AgentLoopExhausted(...)
```

Nới cận là **no-op** — `i == max_turns` vẫn bắn, hành vi không đổi một chút nào. Gieo lại đúng câu
raise (`if False:`) ⇒ **bắt = 3**.

Số thô của cả hai vòng giữ lại: [`raw/sweep-v1-mutant-M5-sai.log`](raw/sweep-v1-mutant-M5-sai.log)
và [`raw/sweep.log`](raw/sweep.log).

**Luật rút ra, đã ghi vào `mutation_s3.py`:** `bắt == 0` chỉ là phát hiện khi mutant **thật sự đổi
hành vi**. Một mutant no-op sống sót rồi được báo là *"test không khoá"* chính là loại báo động giả
mà cả bộ đo này sinh ra để chống — và nó tốn của người đọc đúng một vòng điều tra vào chỗ không có gì.

---

## Cái bộ đo này KHÔNG nói

- Không nói 5 hàng rào **đúng** — chỉ nói chúng **được khoá**. Một hàng rào sai mà có test khoá cái
  sai đó vẫn cho `bắt > 0`.
- Không phủ hết bề mặt: 5 mutant chọn theo 5 cờ đỏ Sprint 3, không phải một phép quét đầy đủ.
- `bắt` **không** là thước đo chất lượng test. M1 = 26 không có nghĩa nó tốt gấp 26 lần M3 = 1 — nó
  chỉ nói hàng rào M1 chạm nhiều đường hơn.
