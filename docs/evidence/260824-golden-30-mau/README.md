# 24/08 — hình dạng MẪU của golden-30: dính chùm · lệch trục · phủ nhãn tay

> Đo **mẫu**, không đo chất lượng agent. Câu hỏi: *30 case có phải 30 quan sát độc lập không, và
> mẫu số thật của `Judge.agreement` là bao nhiêu?*
>
> Tái lập: `./run.sh` — không cần Postgres, không cần API key. Số thô: [`raw/mau.json`](raw/mau.json).

## Điều kiện đo

| | |
|---|---|
| Lệnh | `./run.sh` (gọi `do_mau.py`, đọc YAML qua `load_golden_set`) |
| Nguồn | `packages/kb/src/studio_kb/golden/{callisto-golden-30-v1,callisto-2.0-golden-30-v1}.yaml` |
| Con trỏ `packages/kb` | `72b6133` |
| Con trỏ `packages/evalhub` | nhánh `fix/answer-from-trace-multi-turn` @ `24fabad` |
| Phụ thuộc ngoài | không (không DB, không mạng, không LLM) |

---

## ⛔ Phát hiện trước khi đọc số: **hệ thống có HAI golden set mặc định khác nhau**

```console
$ grep -n "callisto" packages/workbench/src/studio_workbench/builder.py
111:    golden_set_ref: str = "callisto-golden-30-v1",
213:        golden_set_ref="callisto-golden-30-v1",
227:    golden_set_ref: str = "callisto-golden-30-v1",

$ grep -rn "callisto" apps/studio/src/studio_app/routes/runs.py
64:    golden_set_ref: str = "callisto-2.0-golden-30-v1"
```

`RunRequest` (`runs.py:64`) là body **dùng chung** cho `/api/runs`, `/evaluate` và `/publish`. Nên:

- đi qua **HTTP** mà không khai `golden_set_ref` ⇒ chấm bằng **2.0**;
- dựng recipe qua **`builder.py`** mà không khai ⇒ chấm bằng **v1**.

Hai bộ **không cùng số**, và chênh lệch rơi đúng vào hai đại lượng mà sổ bằng chứng phải công bố:
`n` hiệu dụng (cho khoảng tin cậy) và mẫu số `agreement` (nhãn tay).

⇒ **Mọi con số CI/agreement phải khai rõ đo trên `golden_set_ref` NÀO.** Ghi `n = 22` mà không nói
bộ nào là một con số không tái lập được — người chạy lại qua đường khác sẽ ra `21`.

---

## 1. Dính chùm — 30 case KHÔNG phải 30 quan sát độc lập

| Đại lượng | `callisto-golden-30-v1` (mặc định `builder.py`) | `callisto-2.0-golden-30-v1` (mặc định `RunRequest`) |
|---|---|---|
| `n_case` | 30 | 30 |
| **query độc lập** | **21** | **22** |
| query bị dùng lại | 7 | 7 |
| lần lặp nhiều nhất | **4×** — *"Thang lương của công ty gồm những bậc nào?"* | 3× |

**Công thức:** `n_query_doc_lap = |{c.query : c ∈ cases}|`, `n_query_dung_lai = |{q : đếm(q) > 1}|`.
Số thô đầy đủ (kèm từng query và số lần lặp) ở [`raw/mau.json`](raw/mau.json).

**Vì sao đây là chuyện thống kê, không phải chuyện gọn gàng:** lặp là **cố ý** — header file ghi
*"cặp chéo-tenant khác-số (leak-mimic)"*: cùng câu hỏi, hai công ty, hai đáp án khác nhau, để bắt rò
dữ liệu. Thiết kế tốt cho mục đích đó. Nhưng hệ quả phải khai:

- retrieval hỏng ở đúng câu lặp 4× ⇒ **4 case trượt cùng lúc** — một nguyên nhân, bốn điểm trừ,
  `success_rate` sụt `0.133` vì đúng **một** lỗi;
- khoảng tin cậy tính với `n = 30` phẳng sẽ **hẹp hơn sự thật**. Bậc tự do thật gần **21** (v1) /
  **22** (2.0) hơn 30.

⇒ Khoảng tin cậy phải hoặc (a) bootstrap **gom theo `query`**, hoặc (b) khai `n` hiệu dụng kèm lý do.
Không được im lặng dùng `n = 30`.

## 2. Lệch trục — cả hai bộ đều chưa cân

```
tenant   v1 : ankor 19 · borea 11              2.0: ankor 19 · borea 11
role     v1 : public 10 · hr 9 · finance 6 · engineering 5
         2.0: hr 13 · public 6 · finance 6 · engineering 5
```

Một agent giỏi phần đông mẫu và kém phần ít mẫu vẫn được điểm tốt: ở 2.0, `hr` chiếm **43%**; ở v1,
`public` chiếm **33%**. ⇒ hoặc cân lại mẫu, hoặc **báo điểm tách ô** (tenant × role) thay vì một số gộp.

## 3. Nhãn tay — mẫu số thật của `agreement`

| | v1 | 2.0 |
|---|---|---|
| `manual_label` có giá trị | **10 / 30** | **12 / 30** |

`Judge.agreement` chỉ so được ở những case có nhãn tay ⇒ mọi con số agreement đang tính trên **10**
(v1) hoặc **12** (2.0), **không phải 30**. Con số đó **phải đi kèm mẫu số** khi công bố, nếu không
người đọc mặc định hiểu là 30.

## 4. Tỷ lệ case từ-chối — cả hai bộ giống nhau

| | v1 | 2.0 |
|---|---|---|
| `expects_refusal` | 8 / 30 = **0.2667** | 8 / 30 = **0.2667** |

Nằm trong khoảng 20–30% mà thiết kế mẫu đề ra. Đây là đại lượng **duy nhất** trong báo cáo này khớp
nhau ở cả hai bộ.

---

## Việc kéo theo

1. **Chốt một `golden_set_ref` mặc định**, hoặc khai tường minh ở mọi call-site. Hai default là hai
   phép đo, và không ai đang khai mình dùng cái nào.
2. Mọi số công bố kèm `golden_set_ref` + `n` hiệu dụng + mẫu số nhãn tay — không dùng `30` trần.
3. `evidence-requirements.md` §2 ghi *"22 câu hỏi độc lập"* và *"nhãn tay 12/30"*: **đúng cho 2.0**,
   **sai cho v1** (21 và 10). Bản đó không nói đo trên bộ nào ⇒ chính nó là ví dụ của vấn đề mục này
   nêu ra.
