# 24/08 — Wilson 95% trên golden-30: `n` thô vs `n` hiệu dụng

> **Chẩn đoán, KHÔNG phải cổng** (`DEC-S2-134-01`). Bảng này để đọc, không để chặn publish.
>
> Tái lập: `./run.sh` — không cần Postgres, không cần API key. Số thô: [`raw/ci.json`](raw/ci.json).

## Điều kiện đo

| | |
|---|---|
| Lệnh | `./run.sh` → `measure_ci.py` |
| Hàm | `studio_evalhub.wilson.wilson(k, n, z=Z_95)` — stdlib, **không** `scipy`/`numpy` |
| `z` | `1.959963984540054` (ghim literal, không dẫn xuất) |
| Nguồn `n` | đếm từ YAML qua `load_golden_set`, xem [`260824-golden-30-sample`](../260824-golden-30-sample/README.md) |
| `packages/kb` | `72b6133` |
| Phụ thuộc ngoài | không |

**Câu chữ:** *"cận dưới theo **khoảng Wilson 95%**"*. **Không** đọc thành *"95% khả năng tỷ lệ đúng
nằm trong khoảng này"* — sai theo frequentist. Wilson nói về **coverage của quy trình khi lặp lại**,
và coverage thật với `n` nhỏ có thể **dưới** mức danh nghĩa.

---

## Bảng — cùng tỷ lệ chất lượng, hai mẫu số

`n` hiệu dụng = **số query độc lập** (golden-30 có 7 câu bị dùng lại, một câu tới 4 lần). `k` được
tỷ lệ theo `n` để hai cột so đúng *"cùng chất lượng, khác cỡ mẫu"*.

### `callisto-golden-30-v1` — mặc định của `builder.py`

| Tỷ lệ | `n` thô = 30 | cận dưới | `n` hiệu dụng = **21** | cận dưới | chênh |
|---|---|---|---|---|---|
| 100% | 30/30 | **0.8865** | 21/21 | **0.8454** | −0.0411 |
| ~97% | 29/30 | 0.8333 | 20/21 | 0.7733 | −0.0600 |
| 90% | 27/30 | 0.7438 | 19/21 | 0.7109 | −0.0329 |

### `callisto-2.0-golden-30-v1` — mặc định của `RunRequest`

| Tỷ lệ | `n` thô = 30 | cận dưới | `n` hiệu dụng = **22** | cận dưới | chênh |
|---|---|---|---|---|---|
| 100% | 30/30 | **0.8865** | 22/22 | **0.8513** | −0.0352 |
| ~97% | 29/30 | 0.8333 | 21/22 | 0.7820 | −0.0513 |
| 90% | 27/30 | 0.7438 | 20/22 | 0.7219 | −0.0219 |

**Công thức:** Wilson score interval,
`center = (p̂ + z²/2n)/(1 + z²/n)`, `half = z/(1+z²/n)·√(p̂(1−p̂)/n + z²/4n²)`, `p̂ = k/n`.

---

## Ba điều bảng này nói

**1. `n = 30` phẳng cho khoảng HẸP HƠN SỰ THẬT.** Chênh cận dưới **0.02–0.06** — không lớn về con
số, nhưng nó nằm đúng vùng người ta hay đặt ngưỡng. Dùng `n` thô là khai một lượng thông tin mình
không có, vì 30 case chỉ mang 21 (hoặc 22) câu hỏi độc lập.

**2. Cận dưới ở `30/30` là `0.8865` — thấp hơn ngưỡng `0.9` đang dùng.** Đây là **hệ quả cỡ mẫu**,
không phải agent tệ: 30 lần đúng liên tiếp **không** loại trừ tỷ lệ lỗi thật cỡ 11%. Nếu ai đó đổi
gate sang `lower >= 0.90`, golden-30 **FAIL cả khi mọi case pass**, và với `n` hiệu dụng thì càng
xa hơn (`0.8454`). Cần khoảng `35/35` mới vượt.

⇒ Đó chính là lý do `DEC-S2-134-01` chốt CI là **chẩn đoán**. Bảng này **không** đề xuất đổi gate.

**3. Hai bộ golden cho hai `n` hiệu dụng khác nhau (21 vs 22)** ⇒ mọi con số CI công bố **phải khai
`golden_set_ref`**. Xem phát hiện "hai default" ở
[`260824-golden-30-sample`](../260824-golden-30-sample/README.md).

---

## Cái bảng này KHÔNG làm

- **Không** hiệu chỉnh cụm bằng ICC. `kit#134` xếp route ICC/cluster vào *"sau S2, chỉ khi có
  decision và đủ data"* và cấm đích danh việc tự đặt `ICC = 0.3` làm mặc định. Ở đây chỉ **chọn đúng
  đơn vị độc lập** rồi đưa `n` đó vào — không có tham số nào được bịa.
- **Không** vào `studio_contracts.Scorecard`. Thêm `ci_lower`/`ci_upper`/`n_eff` vào contract chạm
  renderer + DB + consumer + roundtrip test, phải qua RFC (`kit#134`).
- **Không** là số của một run cụ thể. `k` ở đây là **kịch bản** để đọc độ nhạy theo mẫu số, không
  phải kết quả đo agent. Số thật của một run nằm ở scorecard của run đó.
- **Không** nói bộ nào "đủ lớn". Nó chỉ nói `n = 30` **không** phải `n` đúng.
