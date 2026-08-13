# D20 · T5 — agreement ba giá trị + đếm định tuyến judge trên run THẬT

> `DEC-D20-04`. Ô DoD `#128`: *"judge-agreement vs nhãn tay **có số** (hoặc exact-match descope)"* —
> đóng **cả hai vế**, vì chúng không loại trừ nhau.

## State lúc chạy — không dùng lại khối SHA nền

| Repo | SHA lúc chạy số dưới đây | `git status --porcelain` |
|---|---|---|
| `apps/studio` | `b866bc2` | rỗng |
| `packages/evalhub` | `7684658` | rỗng |
| `packages/workbench` | `04ca988` | rỗng |
| `packages/kb` | `0194199` | rỗng |
| `packages/engine` | `bfa19cc` | rỗng |

---

## 1. Agreement — ba giá trị, không phải một `rate` trần

```console
$ agreement(*nhan_tu_golden_set(load_golden_set(callisto-golden-30-v1.yaml)))
rate        = 1.0
n_compared  = 10
lech        = []
```

**Một `rate` trần không mẫu số là đúng thứ `kit#134` gọi là bằng chứng dị dạng.** `1.0` đọc một mình
nghe như *"đồng thuận tuyệt đối trên golden-30"*; sự thật là **10/30**, và 20 case còn lại **chưa có
nhãn tay** — chúng bị loại khỏi mẫu số chứ không được tính là khớp (`agreement.py` fail-closed
đường 1: `nhan_tay[case] is None` ⇒ loại khỏi mẫu số, vì *chưa gán nhãn* ≠ *bất đồng*).

## 2. `n_compared = 10` đang đo **CÁI GÌ** — và nó không phải cái ai cũng tưởng

**Đây KHÔNG phải human–machine agreement.** Ba bước để thấy vì sao:

1. Nhãn bộ chấm suy từ `expects_refusal` (evalhub tính, từ hai trục hàng rào T1/T6).
2. Nhãn tay là `manual_label` (kb gán).
3. Trên 10 case có nhãn, `manual_label` trùng khít `expects_refusal` **10/10** — và
   `expects_refusal` là thuộc tính **dẫn xuất từ chính dữ liệu golden**
   (`expected_tenant`/`expected_section_role` so với `tenant`/`section_roles` của câu hỏi).

⇒ Nhãn tay **không mang thông tin độc lập** với thứ nó đang được so. `rate = 1.0` ở đây **không**
nói *"người và máy đồng ý về chất lượng câu trả lời"*.

**Cái nó thật sự đo:** *đồng thuận **ngữ nghĩa hàng rào** giữa `kb` và `evalhub`* — hai bản cài đặt
độc lập, ở hai repo, của cùng một khái niệm *"case này đáng bị từ chối"*. Nó là một **regression
detector cho semantic drift** giữa hai quadrant: ngày DE đổi luật gán nhãn hoặc evalhub đổi luật suy
`expects_refusal` mà hai bên lệch nhau, `rate` tụt và `lech` chỉ đúng case nào.

Đó là một phép đo **có giá trị thật**, chỉ là không phải phép đo mà chữ *"agreement"* gợi ra.

**Điều kiện lật để nó thành human–machine agreement thật** (chủ: AIE-2 + DE, ask ④): DE gán nhãn
**đúng/sai của một `actual`** — tức chấm chính câu trả lời — chứ không phải nhãn **nhánh**
(`pass`/`refuse`). Nhãn nhánh sẽ luôn trùng vì nó dẫn xuất được; nhãn chất lượng thì không.

## 3. Nấc descope — khai bằng SỐ, không bằng lời

`DESCOPE.md` khai nấc *LLM-judge → exact-match scorer*, và evalhub **đang ở nấc đó**. Plan D20 yêu
cầu đếm **bao nhiêu case định tuyến sang judge trên run thật của T3**, và dự đoán **0** (khớp phép đo
D18 *"0/30 case cần judge"*).

Điều kiện định tuyến, nguyên văn `harness.py`:

```python
if judge is not None and not case.expects_refusal and not scored.success:
```

Đếm trên **chính run thật của T3** (`EngineAgentRunner` + `PgKbSearch` + `ExtractiveFakeLLM`,
Postgres thật):

```text
n_routed_to_judge = 17   (trên 22 case nhánh trả-lời)

HB-01 HB-02 HB-03 HB-06 HB-07 HB-08 HB-09 HB-10 HB-11 HB-12
HB-13 HB-14 HB-16 HB-18 HB-20 HB-21 HB-22
```

### ⚠️ FINDING — `17`, không phải `0`. Giữ nguyên con số, không sửa cho khớp dự đoán

Plan viết sẵn: *"Dự đoán **0** … nếu ra khác 0 thì con số đó là **finding**, không phải nhiễu."*
Đây là nó.

**Vì sao hai con số cùng đúng mà khác nhau:** D18 đo `0/30` với **`runner_tot`** — một
`StubAgentRunner` sinh từ chính golden-set, tức trả lời đúng **theo định nghĩa**, nên không case nào
trượt exact-match và không case nào cần judge. Hôm nay runner là `ExtractiveFakeLLM` đi qua engine
thật: 17/22 case nhánh trả-lời **trượt** `_contains_phrase` ⇒ **sẽ** đi judge nếu `judge` được truyền.

**Hệ quả phải nói ra:** câu *"thêm selector production hôm nay là dựng đường dẫn cho một tập rỗng"*
(nền D18) **chỉ đúng trên đường stub**. Trên đường thật tập đó có **17 phần tử**. Nấc descope
*exact-match* vì thế **không** miễn phí như con số D18 gợi ra — nó đang che 17/22 case mà bộ chấm
exact-match không kết luận được, và cả 17 case đó hôm nay bị tính `success=False`.

Con số `17` **không** nói judge sẽ cứu được bao nhiêu case — `ExtractiveFakeLLM` trả câu canned, nên
phần lớn 17 case đó nhiều khả năng vẫn sai. Nó nói đúng một điều, và điều đó là điều cần: **mẫu số
của quyết định descope là 17, không phải 0.**

| | D18 (nền) | D20 (run thật) |
|---|---|---|
| Runner | `StubAgentRunner` sinh từ golden-set | `ExtractiveFakeLLM` + engine thật + Postgres |
| Case đi judge | **0/30** | **17/22** nhánh trả-lời |
| Kết luận rút ra được | *"selector cho tập rỗng"* | *"selector cho 17 case"* — kết luận cũ **không** còn đứng |

**Chủ + điều kiện lật:** AIE-2. Đo lại khi có một LLM **sinh prose thật, không biết trước nhãn**
(cùng điều kiện lật của `DEC-D17-04` cho ngưỡng). Trước đó, mọi con số ở trục này là số của một
double, và phải được đọc như vậy.

---

## 4. Ba con số này KHÔNG đóng ô DoD nào một mình

- `rate = 1.0` đóng vế *"có số"* của `#128`, kèm bắt buộc câu ở `§2` nói nó đo gì. Không có câu đó,
  con số bị đọc thành human–machine agreement và **báo cáo sai** dù số đúng.
- `n_compared = 10` là **trạng thái của dữ liệu**, không phải của bộ chấm: 20/30 case chưa có nhãn
  (`kb` `0194199` trên `main`). Nợ hai phía, ask ④.
- `17` là finding mở, chưa có kết luận — và nó đang **mâu thuẫn với một tiền đề đã dùng để hoãn
  việc** ở D18. Nêu ra thay vì để nó tự trôi.

## Lưới test đang giữ ba giá trị này

| Bất biến | Bài giữ |
|---|---|
| `n_compared == 0` ⇒ `rate is None`, **không** `0.0` | `test_mau_so_rong_tra_none_khong_phai_khong_phay_khong` (`M-G5`) |
| lệch toàn bộ ⇒ `rate == 0.0`, **không** `None` | `test_lech_toan_bo_tra_0_0_chu_khong_phai_none` |
| mẫu số khớp số nhãn đếm **độc lập** bằng `yaml.safe_load` | `test_agreement_tren_golden_30_khop_so_nhan_thuc_te` |
| `rate == (n_compared − len(lech)) / n_compared` | cùng bài trên |

Bài thứ ba là bài đáng giá nhất: nó đếm nhãn bằng **oracle độc lập** với loader, nên ngày
`manual_label` hỏng theo hướng nuốt câm, mẫu số tụt về 0 trong khi file vẫn có nhãn — và bài đó bắt
được, còn một bài chỉ đọc qua loader thì không.
