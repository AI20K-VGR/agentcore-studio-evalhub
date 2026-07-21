# DESCOPE — evalhub (AIE-2)

> **Chủ:** AIE-2 — Lưu Tiến Duy · **Viết:** 2026-07-21 (D2) · **Phạm vi:** nấc của quadrant này.

Thang cắt giảm để khi kẹt thì cắt theo danh sách viết sẵn, không cắt tuỳ hứng. Điều kiện của mọi
nấc: demo 8 bước vẫn chạy.

---

## Nấc của evalhub — LLM-judge → exact-match scorer

**Cắt gì:** bỏ `LLMJudge`, chấm mọi case bằng so khớp trực tiếp.

**Kích hoạt khi** (bất kỳ điều nào):

- chạm trần ≤100 lượt gọi judge/ngày (INV-4);
- nhà cung cấp LLM không dùng được (mất mạng, hết quota, lỗi xác thực);
- đến hạn mốc mà `LLMJudge.judge` chưa có số đo đồng thuận với nhãn tay;
- CI cần chạy tất định, không phụ thuộc phản hồi mô hình.

**Thay đổi cụ thể:**

| | Trước cắt | Sau cắt |
| --- | --- | --- |
| Case khách quan | so khớp trực tiếp | không đổi |
| Case chủ quan | `LLMJudge.judge()` | so khớp trực tiếp |
| `CaseResult.judge` | điểm đồng thuận thật | xem Q1 — `docs/scorecard-v0.md` |
| `aggregate` | — | không đổi |
| `gate.verdict` | — | không đổi |

**Walking-skeleton sau khi cắt:** `gate.verdict` quyết bởi `success` + `citation_accuracy`, không
bởi trường `judge`. Demo bước 6 (gate PASS → publish) và bước 7 (gate FAIL → chặn + rollback) chạy
nguyên vẹn.

**Ảnh hưởng:** case chủ quan bị chấm chặt hơn — câu trả lời đúng ý nhưng khác chữ tính là sai. Điểm
lệch xuống, không lệch lên; gate có thể chặn bản đạt, không cho lọt bản không đạt.

**Đường lùi:** bật lại judge = chuyển case về nhánh judge trong bộ chấm. Không migration dữ liệu,
không đụng `Scorecard`, không đụng quadrant khác.

---

## Trạng thái hiện tại

Bộ 5 smoke-case v0 chốt với DE ngày 2026-07-21 không có case nào cần judge — toàn bộ là so khớp
trực tiếp hoặc kỳ vọng-từ-chối. evalhub đang ở sẵn nấc này từ S1.

Judge chỉ xuất hiện khi bộ case lên 30 câu ở S3. Trình tự dự kiến: chạy thông exact-match trước, đo
đồng thuận với nhãn tay, bật judge khi có số.

---

## Điều kiện chưa gỡ

Nấc này vướng Q1 trong `docs/scorecard-v0.md`: `CaseResult.judge` là trường bắt buộc, case không qua
judge chưa có giá trị hợp lệ để điền, và `judge.py` loại trừ giá trị hằng. Chưa chốt Q1 thì nấc chưa
thực thi được.

Đã đưa vào question-batch gửi mentor ngày 2026-07-21.
