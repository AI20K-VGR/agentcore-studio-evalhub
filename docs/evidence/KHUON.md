# Khuôn sổ bằng chứng — mọi con số công bố phải đi qua đây

> Yêu cầu mentor: *"bất cứ con số nào đưa ra, cần công thức và số liệu thô để tính lại phải ra được
> số đó"*. Chiếm **50% điểm bài cuối khoá**.
>
> **Luật vàng:** mentor chạy `run.sh` phải ra **đúng** con số trong `README.md`. Ra số khác = bằng
> chứng hỏng, **không phải** *"sai số chấp nhận được"*.

## Hình thư mục

```
docs/evidence/<YYMMDD>-<chủ-đề>/
├── README.md      bảng số + công thức + điều kiện đo + kết luận
├── run.sh         chạy lại → ra ĐÚNG số trong README
└── raw/           dữ liệu THÔ (json/log/csv), không tổng hợp sẵn
```

`raw/` là **thô**, không phải bản đã gọt. Một file `raw/` chỉ chứa con số cuối thì nó không phải dữ
liệu thô, nó là README viết lại một lần nữa — và người kiểm không tính lại được gì từ đó.

## Sáu ô cho mỗi con số công bố

Thiếu ô nào thì con số đó **chưa** được tính là có bằng chứng.

| Ô | Nội dung | Sai ở đâu nếu thiếu |
|---|---|---|
| **Giá trị** | `0.9889` | — |
| **Công thức** | `success_rate = k_success / n_case` | người đọc không biết mẫu số là gì |
| **Số thô** | `k=89, n=90` — **trỏ file trong `raw/`** | không tính lại được |
| **Điều kiện đo** | golden_set_ref · corpus · embedding · SHA từng repo · có/không Postgres | số đúng ở máy này, khác ở máy kia, không ai biết vì sao |
| **Lệnh tái lập** | `./run.sh` | "tin tôi đi" |
| **Khoảng tin cậy** | `[0.9394, 0.9981]` Wilson 95%, **`n` hiệu dụng = 21** | `n=30` phẳng cho khoảng **hẹp hơn sự thật** khi mẫu dính chùm |

### Hai ô hay bị bỏ nhất, và cả hai đều đã cắn thật

**Điều kiện đo — phải ghi `golden_set_ref`.** Hệ thống hiện có **hai** mặc định khác nhau
(`builder.py` → `callisto-golden-30-v1`, `RunRequest` → `callisto-2.0-golden-30-v1`) và chúng cho
**`n` hiệu dụng khác nhau** (21 vs 22) và **mẫu số nhãn tay khác nhau** (10 vs 12). Ghi `n = 22` mà
không nói bộ nào là một con số không tái lập được. Đo được ở
[`260824-golden-30-mau`](260824-golden-30-mau/README.md).

**Khoảng tin cậy — phải khai `n` hiệu dụng.** Golden-30 **không** phải 30 quan sát độc lập: 7 câu
hỏi bị dùng lại (một câu tới 4 lần). `kit#134` chốt Wilson là **chẩn đoán, KHÔNG phải cổng** — nên
nó xuất hiện để đọc, không để chặn publish.

## Ba thứ đã có sẵn — nêu trong mọi báo cáo, không dựng lại

| Thứ | Ở đâu | Chứng minh gì |
|---|---|---|
| Test tất định | `evalhub/tests/test_determinism.py` | đổi `run_id`/`ts` ⇒ điểm **không đổi** ⇒ cùng đầu vào cho cùng điểm |
| `recipe_hash` | `workbench/publish.py::recipe_hash` | scorecard này chứng nhận **đúng recipe nào** |
| Mutation | [`260824-mutation-s3`](260824-mutation-s3/README.md) | test có **cắn thật** không, không phải suite xanh |

## Luật viết

1. **Ghi SHA của CHÍNH LÚC CHẠY**, không dùng lại khối SHA nền của ngày — số chạy giữa ngày, repo
   còn đổi tiếp trước khi merge. Neo `file:line` neo được **nội dung**, không neo được **phiên bản**.
2. **Số đo được ≠ số mong muốn.** Một báo cáo tự đánh ❌ vào ô của mình đọc **mạnh hơn** một báo cáo
   im lặng — Sprint 2 đã được chấm đúng như vậy.
3. **Chưa đo thì viết "chưa đo", kèm bị chặn bởi gì.** Không để trống, không suy ra.
4. **Số bất lợi vẫn ghi.** Hạ ngưỡng/đổi mẫu cho số đẹp lên là đúng thứ `DEC-D20-03` cấm.
5. **Mutant `bắt == 0` chỉ là phát hiện khi mutant thật sự đổi hành vi.** Một mutant no-op sống sót
   rồi được báo là *"test không khoá"* là báo động giả — xem M5 ở
   [`260824-mutation-s3`](260824-mutation-s3/README.md).

## Đang có

| Thư mục | Nội dung | `run.sh` |
|---|---|---|
| [`260824-golden-30-mau`](260824-golden-30-mau/) | dính chùm · lệch trục · phủ nhãn tay, **hai** golden set | ✅ không cần DB |
| [`260824-mutation-s3`](260824-mutation-s3/) | 5 mutant chéo trên 5 hàng rào S3 | ✅ cần Postgres + engine `65731e5` |
| `day14/`, `day20/` | bộ cũ — có bảng SHA + console block, **chưa có** `run.sh`/`raw/` | ❌ |

`day14`/`day20` **không** viết lại: chúng là bản ghi của ngày đó và đã được chấm. Khuôn này áp cho
số **mới**.
