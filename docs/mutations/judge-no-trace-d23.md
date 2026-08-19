# Sổ mutation D23 — cổng judge × `DEC-05` (`M-T1` … `M-T4`)

> Bảng khai **trước** khi viết test, ghi **bài nào đỏ** — không chỉ có-đỏ-hay-không. Cùng luật đo với
> [`gate2-d20.md`](gate2-d20.md): dọn `__pycache__` mỗi lần gieo/khôi phục, kiểm giá trị **runtime**
> chứ không chỉ `git diff`, và sau khôi phục thì chạy lại suite.

## Bất biến được đo

`_duoc_hoi_judge` (`harness.py`) — **judge không được hỏi khi case trượt vì một cổng fail-closed cấu
trúc**, cụ thể `case_run.events == []` (`DEC-05` *no-trace-no-proof*). Xem `DEC-D23-01`.

## Bảng khai

| # | Mutant | Dự đoán | Kết quả | Bài nào ĐỎ |
|---|---|---|---|---|
| `M-T1` | Bỏ cổng — `_duoc_hoi_judge` trả `True` (hành vi TRƯỚC bản vá) | DIE cả 3 | ✅ **KILLED** | cả 3 bài |
| `M-T2` | Cổng trả `False` luôn — tắt hẳn nhánh judge | DIE ở đối chứng dương | ✅ **KILLED** | cả 3 bài |
| `M-T3` | Đảo cổng — `return not case_run.events` | DIE cả 3 | ✅ **KILLED** | cả 3 bài |
| `M-T4` | **Cổng đặt sai chỗ**: vẫn hỏi judge, chỉ bỏ verdict cho ca no-trace | DIE **chỉ** ở bài đếm số lần gọi | ✅ **KILLED** | `test_no_trace_judge_khong_he_duoc_goi` **(1 bài duy nhất)** |

**4/4 killed. 0 survivor.** Bài: [`tests/test_judge_khong_lat_duoc_no_trace.py`](../../tests/test_judge_khong_lat_duoc_no_trace.py).

---

## `M-T4` — mutant duy nhất trong sổ nói được điều gì mới

`M-T1`/`M-T2`/`M-T3` đều bị **cả ba** bài giết, nên xét riêng chúng thì ba bài trông như dư hai. Ghi
ra thay vì để người đọc tự suy: **ba mutant đó không chứng minh được là ba bài độc lập.**

`M-T4` mới là chỗ tách chúng ra. Nó giữ cổng đúng về **kết quả** — `Scorecard` trùng khít bản có bản
vá — nhưng đặt cổng **sau** lời gọi judge thay vì trước:

```python
if judge is not None and not case.expects_refusal and not scored.success:
    ket = await _hoi_judge(judge, case, scored)
    scored = ket if case_run.events else scored      # ← hỏi rồi bỏ
```

Kết quả gieo: **2 passed, 1 failed** — chỉ `test_no_trace_judge_khong_he_duoc_goi` đỏ. Tức bài đếm số
lần gọi **không suy ra được** từ bài assert kết quả, và nếu sổ này chỉ có `M-T1..M-T3` thì bỏ bài đó
đi vẫn thấy "3/3 killed".

Vế bị mất nếu bỏ bài đó có giá thật: `cap ≤100/ngày` (`INV-4`, `DEC-D18-05`) là quota **chia sẻ, bền
ngoài tiến trình**. Tiêu một lần gọi cho một case mà verdict chắc chắn bị bỏ là tiêu mất hẳn, không
phải tiêu vào một chỗ vô hại — và không dòng nào sai để ai nhìn ra.

---

## Phép đo kèm — và nó nói ngược lại điều dễ tưởng

Chạy golden-30 qua spine thật (`EngineAgentRunner` + `PgKbSearch` + `PgTraceWriter` + Postgres,
`ExtractiveFakeLLM`), phân lớp **lý do trượt** của 22 case nhánh trả-lời:

| Lý do trượt | Số case |
|---|---|
| content-miss (`_contains_phrase` không khớp) | **17** |
| `answer.refused is True` | **0** |
| no-trace (`events == []`) | **0** |

Hai kết luận, cả hai phải nói ra:

1. **Cổng này hôm nay chưa chặn một case nào.** `no-trace = 0/22` với runner hiện tại, nên bản vá
   **không đổi một con số nào** của golden-30 — nó không sửa một điểm sai đang quan sát được. Giá trị
   của nó là: `DEC-05` tồn tại đúng cho ca **runner hỏng** (trace writer chết, engine đoản mạch), và
   trước bản vá thì judge sẽ lặng lẽ tháo `DEC-05` **đúng vào lúc `DEC-05` có việc**. Một fence cho ca
   chưa xảy ra, khai đúng là fence, không khai là bug-fix.
2. **Trục `refused` để mở là quyết định có số đỡ**, không phải bỏ sót: `0/22`. Ghi honest-TODO ở
   `DEC-D23-01`, không thêm cổng cho một trục chưa có case nào chạm.

Con số `17` khớp đúng con số đã ghi trong docstring `EvalHarness.run` từ D20 — dùng làm đối chứng cho
chính cách dựng phép đo này.
