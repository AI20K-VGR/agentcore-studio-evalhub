# Tự gieo mutant vào T3 — `render_run_cases` + `answer_from_trace`

**Ngày:** 2026-08-07 (D15) · **Người gieo:** AIE-2 (chủ quadrant tự gieo vào code của chính mình)
**Mục tiêu đo:** suite viết ở T3 có **răng** không, hay chỉ đang mô tả lại code.

> **Khai TRƯỚC khi chạy.** Bảng §1 dưới đây được viết và commit vào file này **trước** khi bất kỳ
> mutant nào được gieo. Không có bước này thì phép đo không có giả thuyết để bác bỏ: nhìn kết quả
> rồi mới nói *"đúng như tôi nghĩ"* là chấm điểm sau khi đã biết đáp án.

## Điều kiện của một mutant hợp lệ

1. Nó là một **failure mode có ý nghĩa** — một cách hàm này có thể sai thật trong đời thật, không
   phải đổi tên biến.
2. Nó được khai **trước**, kèm **bài cụ thể được kỳ vọng sẽ đỏ**. Một mutant không nêu được bài nào
   phải đỏ thì chưa đủ điều kiện gieo.
3. Nó gieo được **sạch** — không `SyntaxError`, không `ImportError`, không lỗi thu thập test.
   **Collection failure KHÔNG BAO GIỜ tính là `caught`**, kể cả khi pytest báo đỏ và kể cả khi đỏ
   đúng số bài mong đợi. Đã trả giá một lần ở `into-engine-d11.md` M5 lượt 1 (comment `# MUTANT M5`
   chèn giữa dict literal ⇒ 13 collection error, phải gieo lại).

**Mutant tương đương và mutant không liên quan được PHÂN LOẠI, không tính vào số.** Không cố đủ một
con số bằng mutation vô nghĩa: 5 là sàn cho *nỗ lực tìm failure mode*, không phải sàn cho *số dòng
trong bảng*.

## Bẫy đo, đã trả giá ở lượt trước

| bẫy | vì sao | cách tránh |
|---|---|---|
| ANSI màu | regex `FAILED` khớp rỗng trên chuỗi có escape code | `--color=no` **và** đọc exit code |
| `.pyc` cũ | bytecode cache khoá theo `(mtime giây, size)` — sửa trong cùng giây, cùng độ dài ⇒ chạy code cũ | `PYTHONDONTWRITEBYTECODE=1` |

---

## §1 · Khai trước — `mutant → bài phải đỏ`

Baseline trước khi gieo: `69 passed, 1 skipped, 2 xfailed, 0 XPASS`.

| ID | Gieo vào | Mutation | Failure mode thật nó mô phỏng | **Khai: bài phải ĐỎ** |
|---|---|---|---|---|
| **M1** | `render.py` `render_run_cases` | dòng đếm success in `f"{n}/{k}"` thay `f"{k}/{n}"` | hoán vị tử/mẫu — `1/5` đọc thành `5/1`, một run trượt gần hết trông như vượt chỉ tiêu | `test_render_case_in_k_tren_n_tho_KHONG_in_ty_le_tong` |
| **M2** | `render.py` `render_run_cases` | bỏ nhánh `expects_refusal`, cột citation luôn in `f"{r.citation_accuracy:.2f}"` | mất `DEC-D12-01`: dòng từ-chối in `1.00`, con số đẹp nhất bảng nằm trên một dòng chưa đo gì | `test_render_case_tu_choi_in_n_a_chu_khong_in_1_00` |
| **M3** | `render.py` `render_run_cases` | `n_citation = len(results)` thay `len(answerable)` | gộp refusal vào mẫu số citation — vi phạm `DEC-S2-134-03`, đúng lỗi `kit#134` mô tả | `test_render_case_mau_so_citation_loai_refusal_chu_khong_dung_tong_case` · `test_render_case_in_k_tren_n_tho_KHONG_in_ty_le_tong` |
| **M4** | `render.py` `_count_or_not_estimable` | bỏ nhánh `n == 0`, luôn trả `f"{k}/{n}"` | `n=0` in `0/0` — mời người đọc chia một phép chia không tồn tại | `test_render_case_rong_la_not_estimable_KHONG_in_0_phan_tram` · `test_render_case_toan_refusal_thi_citation_la_not_estimable` |
| **M5** | `render.py` `render_run_cases` | `k_citation` đếm `>= 0.5` thay `== 1.0` | nới định nghĩa *"trích đủ citation"* — case đạt một nửa được đếm là đạt, tử số phồng im lặng | `test_render_case_in_k_tren_n_tho_KHONG_in_ty_le_tong` |
| **M6** | `run_report.py` `answer_from_trace` | nhiều `llm-step` ⇒ lấy `llm_steps[0]` thay vì raise | chấm nhầm bước trong recipe nhiều bước LLM — bảng điểm trông đúng mà đo sai đối tượng | `test_answer_from_trace_nhieu_llm_step_thi_raise_chu_khong_chon_bua` |
| **M7** | `run_report.py` `answer_from_trace` | thiếu `llm-step` ⇒ trả `AgentAnswer(answer="", ...)` thay vì raise | run **không đọc được** bị đếm vào mẫu số như một run đã đo và trượt | `test_answer_from_trace_thieu_llm_step_thi_raise_chu_khong_tra_chuoi_rong` |
| **M8** | `render.py` `render_run_cases` | gọi `compute_scorecard(...)` trong thân hàm | kéo mốc D16 lên sớm ⇒ `test_gate_blocks_on_fail` (`xfail(strict=True)`) XPASS ⇒ FAIL | `test_render_case_KHONG_goi_compute_scorecard` |

**8 mutant, không phải 5.** Con số không phải mục tiêu — 8 là số failure mode có ý nghĩa tìm được
mà gieo sạch được. Mutant từng cân nhắc rồi **bỏ**, ghi ở §3.

---

## §2 · Kết quả thực đo

*(điền sau khi chạy — xem §2.1)*

---

## §3 · Mutant đã cân nhắc rồi bỏ

*(điền sau khi chạy)*
