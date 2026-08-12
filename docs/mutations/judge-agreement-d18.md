# Sổ gieo mutant D18 — `LLMJudge` (cache + cap + sentinel) · harness wiring · agreement-check

**Ngày:** 2026-08-12 (D18) · **Bút:** AIE-2 · **Ref:** `kit#118` · `DEC-D18-01/02/04/05`
**Phạm vi:** T1 (`GoldenCase`) · T2 (`judge.py`) · T3 (`agreement.py`) · T4 (`harness.py`)

## §1 · Sáu mutant khai TRƯỚC, 6/6 chết

Bộ này được **khai trong plan ở §T7a, trước khi có bài test nào được viết**
(`docs/plans/day-18-aie2.md`). Thứ tự đó là điều kiện để con số có nghĩa: một bộ mutant viết sau khi
nhìn test là bộ mutant kiểm lại danh sách của chính người viết.

Bảng dưới là **một lượt gieo hợp nhất**, chạy lại toàn bộ 6 mutant trên cây sạch sau khi T1–T4 xong —
không phải bản chép lại kết quả rời rạc của từng checkpoint.

| # | Gieo vào | Bất biến bị tấn công | Dự đoán bài đỏ | Thực tế | KQ |
|---|---|---|---|---|---|
| `M-J1` | `golden_case.py` — `extra="forbid"` → `"ignore"` | Field lạ phải **ồn**, không được câm | bài nhãn-sai-tên của T1 | **3 bài** | **DIE** |
| `M-J2` | `judge.py` — cache hit **có** tăng counter | Cache không tiêu quota | bài cache-không-tốn-quota | **1 bài** | **DIE** |
| `M-J3` | `judge.py` — chạm cap ⇒ trả giá trị thay vì raise | *không chấm được* ≠ *chấm và trượt* | bài descope-sentinel + bài harness-tụt-nấc | **3 bài** | **DIE** |
| `M-J4` | `judge.py` — counter đọc lỗi ⇒ coi như `0` (fail-open) | State hỏng ⇒ **fail-closed** | bài counter-hỏng-fail-closed | **1 bài** | **DIE** |
| `M-J5` | `agreement.py` — `n_compared == 0` ⇒ `0.0` thay vì `None` | *chưa đo* ≠ *đo được và bằng 0* | bài agreement-mẫu-số-rỗng | **2 bài** | **DIE** |
| `M-J6` | `judge.py` — mọi đường raise dùng **một** `reason` hằng | **Danh tính** trigger, không chỉ sự tồn tại | bài counter-hỏng + bài provider-lỗi | **3 bài** | **DIE** |

Bài đỏ, ghi **tên** chứ không chỉ số lượng (luật rút từ D17 — script chỉ so `DIE`/`SURVIVE` nên không
tự bắt được sai lệch dự đoán):

```text
M-J1  test_manual_label_sai_ten_phai_do · test_field_la_khong_lien_quan_cung_phai_do
      test_loader_manual_label_sai_ten_do_tai_loader
M-J2  test_cache_hit_khong_ton_quota
M-J3  test_goi_thu_101_raise_cap_reached · test_cache_hit_van_tra_duoc_sau_khi_cham_cap
      test_tut_nac_phai_duoc_ghi_lai_kem_reason[cham-cap]
M-J4  test_counter_hong_fail_closed_state_unreadable
M-J5  test_mau_so_rong_tra_none_khong_phai_khong_phay_khong
      test_agreement_tren_golden_30_khop_so_nhan_thuc_te
M-J6  test_counter_hong_fail_closed_state_unreadable · test_provider_loi_raise_provider_unavailable
      test_tut_nac_phai_duoc_ghi_lai_kem_reason[provider-hong]
```

**`M-J3` được điều chỉnh một chỗ, khai ra thay vì lặng lẽ:** nguyên văn plan là *"trả `(False, 0.0)`"*.
Vì `judge()` chốt trả `bool` (`DEC-D18-04` cấm bịa `agreement`), mutant thi hành là `return False` —
**cùng bất biến**, khác kiểu.

## §2 · `M-J3` SỐNG ở lượt đầu — và đó là dữ liệu đắt nhất của ngày

Lượt gieo đầu tiên ở T4, `M-J3` **sống ở nửa harness**: chết 2 bài của T2, **0 bài của T4**, trong khi
plan dự đoán có *"bài harness-tụt-nấc"*.

Nguyên nhân không hiển nhiên, nên ghi đủ:

| | FX-02 `success` |
|---|---|
| Đúng | judge raise ⇒ harness **giữ nguyên** kết quả exact-match ⇒ `False` |
| `M-J3` | judge trả `False` ⇒ harness **ghi đè** ⇒ `False` |

⇒ **hai `Scorecard` trùng khít**. Case bị tụt nấc đằng nào cũng đã trượt exact-match, nên **không
assert nào trên kết quả** phân biệt được hai đường. Thứ duy nhất phân biệt là **dòng log**, mà bài
ghi-nhận lúc đó chỉ chạy đường `PROVIDER_UNAVAILABLE`.

Vá: parametrize bài ghi-nhận qua **cả hai** đường tụt nấc (`provider-hong` · `cham-cap`). Gieo lại ⇒
chết, thêm đúng `test_tut_nac_phai_duoc_ghi_lai_kem_reason[cham-cap]`.

**Bài học, khác với bài học D17:** D17 dạy *bảng phải ghi bài nào đỏ*. D18 thêm một tầng —
**hai bất biến khác nhau cần hai lưới khác nhau, kể cả khi chúng cùng nói về một sự kiện.** Bài so
`Scorecard == Scorecard` khoá *"gộp nhánh xử lý"*; nó **không** khoá được *"không nuốt câm"*, vì hai
nhánh cho ra cùng một `Scorecard` theo đúng thiết kế. Không có mutation thì lỗ này không lộ ra: cả 8
bài của T4 đều xanh, và `M-J3` đã được đánh dấu DIE ở checkpoint T2 nên rất dễ coi là xong.

## §3 · Ba dự đoán rộng hơn thực tế — lệch theo hướng an toàn, vẫn là lệch

| Mutant | Dự đoán | Thực tế | Đọc đúng |
|---|---|---|---|
| `M-J1` | 1 họ bài | 3 bài | Bất biến là *"field lạ phải ồn"*, không riêng `manual_label` — bài field-lạ-không-liên-quan và bài tầng loader cùng canh nó |
| `M-J5` | 1 bài | 2 bài | golden-30 hôm nay **đang ở đúng trạng thái mẫu số rỗng** (0/30 nhãn), nên mutant bị bắt trên **cả đường dữ liệu thật** |
| `M-J6` | 2 bài | 3 bài | Bài log của T4 cũng assert **giá trị** `reason`, nên nó canh `M-J6` mà plan không tính tới |

Lệch dày hơn dự đoán không phải tin tốt vô điều kiện: nó nghĩa là **bản đồ lưới trong đầu người viết
chưa khớp lưới thật**, và lần sau chỗ lệch có thể rơi về phía mỏng.

## §4 · Môi trường chạy — kiểm lỗ `M-L3` (bài học D16)

D16 mất một mutant vì suite chạy trong môi trường thiếu `packages/kb` ⇒ bài canh nó **skip im lặng**
⇒ mutant sống mà không ai biết. Đo lại cho bộ D18:

| Môi trường | `packages/evalhub` |
|---|---|
| CÓ `packages/kb`, không DSN | `162 passed, 1 skipped` |
| KHÔNG `packages/kb` (bỏ `tests/integration`) | `157 passed, 1 skipped` |
| Riêng 3 file T2+T3+T4 | `26 passed` — không cần DB, không cần `packages/kb` |

Hai mutant có bài canh nằm ở tầng integration (`M-J5`, `M-J3`) được **gieo lại trong môi trường thiếu
`packages/kb`**:

```text
M-J5  (thiếu kb) → DIE, test_mau_so_rong_tra_none_khong_phai_khong_phay_khong
M-J3  (thiếu kb) → DIE, 3 bài
```

⇒ Bộ `M-J1…M-J6` **không** có lỗ `M-L3`: mọi mutant còn ít nhất một bài canh là **unit thuần**. Lượt
gieo ở §1 chạy **có** `packages/kb`, **không** DSN (`162 passed, 1 skipped` baseline).

Skip duy nhất là bài DB có sẵn (`STUDIO_DATABASE_URL_ADMIN not set`), không liên quan bộ này.

## §5 · Gieo chéo — `kb#21` (DE), 5 mutant, **1 sống**

`kit#74`: *"mutation chéo 5 bug"*. Tự gieo không thay được gieo chéo.

Đích: `kb#21` (nhãn tay `manual_label` cho subset golden-30). Chạy trên bản sao cục bộ tại `bdcbcdb`,
baseline **95 passed**. Ba mutant đầu là **kiểm chứng lại claim của DE** (*"Self-mutation 3/3 bắt
được"*), hai mutant sau nhắm vào chỗ đọc tĩnh thấy nghi.

| # | Mutant | Kết quả | Bài đỏ |
|---|---|---|---|
| `X-1` | Nhãn ngược — HB-23 `refuse` → `pass` | DIE | 2 |
| `X-2` | Tắt nhánh render `manual_label` | DIE | 1 (byte-identical) |
| `X-3` | Vocab sai — `"pass"` → `"PASS"` | DIE | 2 |
| `X-4` | Lệch tỷ lệ 9 `pass` / 1 `refuse`, **không** re-emit yaml | DIE | byte-identical |
| **`X-4b`** | Lệch tỷ lệ 9/1 **+ re-emit yaml** (đúng quy trình) | **SURVIVE** | **0** |
| `X-5` | Proxy lệch — HB-23 thêm citation ⇒ `is_refusal=False`, nhãn ép `pass` | DIE | 3 (**đều là bài cũ**) |

**`X-1…X-3` xác nhận DE không khai khống** — claim self-mutation 3/3 tái hiện đúng.

**`X-4b` là bug tìm được.** Subset lệch tới 9/1 — đúng cái mà `format.md` §11 tự lập luận là **phá sức
phân biệt của agreement** — đi qua **cả 3 guard mới** và toàn bộ 95 bài. Guard chỉ bảo vệ *"có ít nhất
1 `refuse`"*, trong khi tài liệu hứa 6/4. `X-4` (quên re-emit) chết, nhưng lưới bắt nó là
byte-identical — một lưới **không liên quan gì tới nhãn**, và nó biến mất ngay khi làm đúng quy trình.

**`X-5` chết nhưng đáng ghi:** cả 3 bài giết nó đều là bài **có sẵn từ trước**, không phải guard của
PR. Rủi ro proxy (`is_refusal := not expected_citation` ≠ ngữ nghĩa hàng rào hai trục của evalhub) đã
được lưới cũ chặn — nhưng sự phụ thuộc đó không được ghi ở đâu, nên ai nới khoá tỷ lệ 22/8 sau này sẽ
vô tình mở lại lỗ.

Đã gửi thành review: [kb#21 comment](https://github.com/AI20K-VGR/agentcore-studio-kb/pull/21#issuecomment-5263795288).

## §6 · Khiếm khuyết TÌM RA khi viết sổ này — state shape sai làm **vỡ cả run** · ĐÃ VÁ

Không phải mutant, và cũng không phải *"chưa đo được"* — **đã đo, và nó hỏng**.

`_doc_json` fail-closed đúng khi file **không parse được**. Nhưng file parse được mà **shape sai**
(JSON hợp lệ, cấu trúc khác) thì lọt qua mọi lớp phòng thủ:

```text
cache_path = {"HB-01": "pass"}        # hợp lệ JSON, nhưng phải là dict LỒNG
LLMJudge(...).judge("HB-01", ...)  →  AttributeError: 'str' object has no attribute 'get'
```

Và vì `harness._hoi_judge` chỉ bắt `JudgeUnavailable`, exception này đi thẳng ra ngoài:

```text
EvalHarness.run(..., judge=judge)   →  RUN VỠ: AttributeError
```

**Đây là vi phạm INV-7 đo được**: hợp đồng nói *"cap chạm hoặc provider không dùng được ⇒ caller tụt
nấc exact-match **thay vì làm hỏng cả eval run**"*. Một file cache rác — thứ hoàn toàn có thể xảy ra
khi một lượt chạy bị giết giữa chừng — làm sập đúng cái mà descope-guard sinh ra để chống.

Nó **không** bị `M-J1…M-J6` bắt vì cả sáu mutant đều tấn công *quyết định* của code, còn đây là một
*hình dạng dữ liệu* chưa ai dựng. Đúng loại điểm mù mà gieo chéo tồn tại để tìm — chỉ khác là lần này
người viết tự vấp phải khi đang viết mục *"chỗ tự biết là mỏng"* ở dưới.

### §6.1 · ĐÃ VÁ — và lỗ rộng hơn ca đầu tiên: **4 hình dạng**, hai trong đó fail-OPEN

Khi dựng ca tái hiện thì lộ ra ca ban đầu chỉ là một trong bốn. Đo trên code trước khi vá:

| Ca | Trước khi vá | Hướng hỏng |
|---|---|---|
| cache value là `str` — `{"HB-01": "pass"}` | `AttributeError` **lọt ra ngoài** | vỡ cả run |
| verdict không `bool` — `{"HB-01": {"y": "pass"}}` | trả `'pass'` (**str**) | phá hợp đồng `-> bool` |
| `date` sai kiểu — `{"date": 123, ...}` | `123 != "2026-08-12"` ⇒ **quota reset về 0** | **fail-OPEN** |
| `count` là `bool` — `{"count": true}` | `isinstance(True, int)` là `True` ⇒ đếm thành `1` | **fail-OPEN** |

Hai ca cuối nguy hiểm hơn ca đầu dù trông hiền hơn: chúng **không ném gì, không trả gì lạ**, chỉ lặng
lẽ mở lại hạn mức đã dùng hết. Ca `count: true` còn lọt **đúng qua lớp kiểm `int` đã có**, vì `bool`
là lớp con của `int` trong Python. `DEC-D18-05` chốt counter là chỗ **duy nhất** trong quadrant không
được phép fail-open, và nó đang fail-open theo hai đường.

**Vá:** `_doc_cache`/`_doc_counter` kiểm **shape sau khi parse**, lệch ⇒ `STATE_UNREADABLE` —
*đọc được nhưng không dùng được* ≡ *không đọc được*.

**Cố ý KHÔNG vá bằng cách nới `harness._hoi_judge` thành `except Exception`.** Bắt rộng sẽ nuốt luôn
lỗi lập trình thật thành *"tụt nấc"* im lặng, biến descope từ một tín hiệu vận hành thành một cái
thùng rác. Chỗ vá đúng là phía sinh ra tín hiệu; harness giữ nguyên hợp đồng hẹp.

**Hai mutant mới cho bất biến mới**, khai trước khi gieo:

| # | Gieo vào | Bất biến | Dự đoán | Thực tế | KQ |
|---|---|---|---|---|---|
| `M-J7` | `_doc_cache` bỏ kiểm shape | Cache đọc được nhưng không dùng được ⇒ fail-closed | 2 ca cache + bài harness | **3 bài**, đúng y | **DIE** |
| `M-J8` | `_doc_counter` bỏ kiểm `date`/`bool` | Counter hỏng **không được fail-open** | 2 ca counter | **2 bài**, đúng y | **DIE** |

```text
M-J7  test_state_shape_sai_phai_fail_closed[cache-value-la-str] · [cache-verdict-khong-bool]
      test_cache_shape_sai_thi_tut_nac_chu_khong_vo_run
M-J8  test_state_shape_sai_phai_fail_closed[counter-date-sai-kieu] · [counter-count-la-bool]
```

Đây là hai mutant đầu tiên của ngày mà **dự đoán khớp thực tế chính xác** — khác `M-J1/J5/J6` (rộng
hơn dự đoán) và `M-J3` (hẹp hơn, sống một lượt). Lý do đọc được: bất biến này được phát hiện **từ một
ca hỏng cụ thể**, nên bản đồ lưới trong đầu người viết dựng **sau** khi đã thấy hình dạng thật — chứ
không phải suy trước rồi kiểm.

`167 passed, 1 skipped` sau vá (nền 162).

## §7 · Mời gieo vào `evalhub` — chỗ người viết BIẾT là chưa đo được

Không đưa bảng gợi ý (bảng gợi ý biến gieo chéo thành kiểm lại danh sách của người viết). Nêu đúng
chỗ tự biết là mỏng:

- **Lần cuối AIE-2 tự gieo:** hôm nay 12/08, 6 mutant `M-J1…M-J6`, cả 6 chết — nhưng `M-J3` phải gieo
  **hai lượt** mới chết ở nửa harness (§2), và §6 là một khiếm khuyết mà cả sáu mutant không chạm tới (đã vá, có `M-J7`/`M-J8` canh).
- **Chỗ chưa đo được ①** — *đồng thời*: `LLMJudge` khai tường minh chỉ đảm bảo cap cho **một writer tại
  một thời điểm** (`DEC-D18-05`). Chưa bài nào dựng hai tiến trình cùng ghi `cap_path`; assumption được
  khai ra chứ chưa được kiểm.
- **Chỗ chưa đo được ②** — *ngày đổi*: counter reset theo `date` UTC, nhưng chưa bài nào chạy qua ranh
  giới ngày; mọi bài đều trong cùng một ngày lịch.
- **Chỗ chưa đo được ③** — *định tuyến judge*: bài canh *"golden-30 không case nào đi qua judge"* chạy
  với **runner tốt**. Chưa bài nào đo với runner **tệ** + judge có mặt, tức chưa biết 22 case
  answer-branch sẽ gọi judge bao nhiêu lần khi agent trả lời sai — một câu hỏi về **quota**, không chỉ
  về đúng/sai.
