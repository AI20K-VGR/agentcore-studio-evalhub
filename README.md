# agentcore-studio-evalhub

> Eval harness, LLM-judge, scorecard, golden-set.

**Owner:** AIE-2 — Lưu Tiến Duy · **Loại:** uv workspace member (Python 3.14) · **Repo cha:** [agentcore-studio-kit](https://github.com/AI20K-VGR/agentcore-studio-kit)

## Repo này là gì
Submodule `packages/evalhub` của workspace `agentcore-studio-kit`. Owner: **AIE-2 — Lưu Tiến Duy**. Chứa eval harness, LLM-judge, scorecard, golden-set. (Tên `evalhub`, không phải `eval`, để tránh shadow builtin.)

## ⚠️ Không build/test độc lập được
`agentcore-studio-evalhub` phụ thuộc `agentcore-studio-contracts` + uv.lock + `docker/postgres-init` của repo cha, và cần **Postgres** cho test. Vì vậy:
- **Làm việc qua repo cha:** `git clone --recursive git@github.com:AI20K-VGR/agentcore-studio-kit.git`, rồi `cd packages/evalhub` để sửa / commit / push chính repo này.
- **Test đầy đủ:** đẩy PR → CI tự **dựng lại full workspace** rồi chạy `pytest packages/evalhub/tests` (Phương án B).

## 📊 Bảng điểm luồng thật nằm ở ĐÂU — đọc trước khi chạy CLI

Hai chỗ in bảng điểm, **hai con số khác nhau**, và chỗ dễ tìm hơn lại là chỗ ít nghĩa hơn:

| Chạy gì | Nguồn dữ liệu | Con số |
|---|---|---|
| `python -m studio_evalhub.cli` (repo này) | `StubAgentRunner` + `_demo_golden_set()` **in-code** — runner mô phỏng, trace mô phỏng | **5/5 PASS** |
| `uv run python apps/studio/scripts/e2e_smoke_eval.py` (**repo cha**) | luồng THẬT xuyên 4 quadrant: `create_recipe_d4` → `interpreter.run` → `StaticKbSearch` → `build_prompt` → adapter → `score_case` | **ĐẤU-NỐI 5/5 THÔNG · CHẤT-LƯỢNG TRÊN FIXTURE ĐỌC PROMPT 4/5** |

**Con số dùng để báo cáo là 4/5, không phải 5/5.** CLI ở repo này in 5/5 vì nó chấm trên câu trả lời mô phỏng — `cli.py` docstring đã ghi rõ *"runner + trace là mô phỏng"*, nhưng dòng đó dễ bị bỏ qua nên nhắc lại ở đây.

### Vì sao bảng điểm luồng thật KHÔNG THỂ nằm trong repo này

`.importlinter` xếp 4 quadrant (`kb` · `engine` · `workbench` · `evalhub`) là **sibling** — cấm import lẫn nhau. `studio_evalhub` do đó **không** import được `studio_engine`/`studio_kb`. Chỗ duy nhất hợp lệ để gom cả 4 là composition root `apps/studio`. Đây là ràng buộc kiến trúc, không phải lựa chọn xếp file — nên đừng đi tìm luồng thật trong `packages/evalhub/**`.

### Ba chỗ có bằng chứng, theo thứ tự nên đọc

| | Ở đâu | Chứng minh gì |
|---|---|---|
| 1 | `apps/studio/scripts/e2e_smoke_eval.py` | bảng điểm luồng thật + RED-CHECK 2 case cố-ý-sai + cột chẩn đoán KB-vs-LLM |
| 2 | `apps/studio/tests/test_spine_scored_from_postgres.py` | chấm điểm từ trace **đọc ra từ Postgres** (vế cuối DoD #30) |
| 3 | `packages/kb/tests/test_spine_live.py` (bút DE) | `engine → PgTraceWriter → obs.trace_events → PgTraceReader` |

Riêng trong repo này: `tests/test_determinism.py` khoá *"chạy lại ra cùng bảng điểm"*, `tests/test_smoke_runner.py` khoá luật chấm 2 nhánh, `tests/test_tenant_scope.py` khoá nhất-quán tenant mức trace (D8), `docs/scorecard-v0.md` là hợp đồng chấm.

### Nợ đã biết khiến hai con số lệch nhau

`_demo_golden_set()` là bản **chép in-code** của `packages/kb/golden/smoke-5.yaml` (bút DE) — nguồn sự thật thứ hai. Đóng bằng PR ở repo cha; theo dõi ở điểm gãy #8/#12.

**Không phải giới hạn của `run_smoke`.** Bộ **10 case** của DE (`callisto-smoke-10-v0`) đã đang được chấm qua chính harness này: `scripts/smoke_eval_d6.py` ở repo cha đọc thẳng `packages/kb/golden/smoke-10.yaml` rồi gọi `EvalHarness().run_smoke(...)` với cả 10 — con số **6/10** ra từ đó. `run_smoke` chỉ duyệt `golden_set.cases`, không có giả định 5 ở đâu. Thứ đứng ở 5 chỉ là hàm demo này.

Ba lý do chưa chuyển nó sang bộ 10 — không lý do nào là "chưa có thư viện":

1. **`_demo_golden_set` bị 2 file `apps/studio` import** (`scripts/e2e_smoke_eval.py`, `tests/test_spine_scored_from_postgres.py`). Là hàm private nhưng trên thực tế đã là API công khai — đổi nó là đổi hành vi 2 consumer một cách im lặng.
2. **Đọc YAML của DE = đọc file trong submodule SIBLING.** `.importlinter` chỉ soi *import*, không cấm đọc file, nhưng `studio_evalhub` khi dùng độc lập thì `packages/kb/golden/` không tồn tại. Script của DE làm được vì nó ở repo cha, nơi đường dẫn đó ổn định.
3. **`pyyaml` chưa được `pyproject.toml` nào khai** (kiểm 29/07). Nó CÓ trong `uv.lock` (6.0.3) và CÓ trong `.venv` — nhưng vào bằng đường **`uvicorn[standard]`**, extra đó kéo `httptools` + `python-dotenv` + `pyyaml`. Nghĩa là mọi `import yaml` trong workspace hôm nay đang **ăn ké extra của một web-server**; ai đổi `uvicorn[standard]` → `uvicorn` là loader YAML chết **im lặng**. Khai tường minh cần sửa `pyproject.toml` + `uv lock` ở **repo cha** (đang gộp vào PR bump con trỏ).

Và lối đúng **không** phải nạp YAML vào test của repo này: test unit nên hermetic, tự mang fixture. Cho nó đọc file của quadrant khác thì DE sửa một nhãn là test ở đây đỏ, mà lỗi lại không nằm ở code ở đây. Nhãn thì tái dùng nguyên văn của DE (xem `_paired_case` trong `tests/test_smoke_runner.py`), còn fixture thuộc về test.

## CI
`.github/workflows/ci.yml` chỉ là **stub** gọi reusable workflow chung ở repo cha:
`AI20K-VGR/agentcore-studio-kit/.github/workflows/reusable-domain-ci.yml@main`.
Muốn đổi quy trình CI thì sửa ở repo cha (1 chỗ).

## Quy tắc
- Chỉ đụng file trong `packages/evalhub/**` (fence-lane của bạn) — không sửa surface domain khác.
- Đổi contract → sang repo `agentcore-studio-contracts` (mentor-approval).
- Không commit tài liệu mentor/rubric/answer-key (pre-commit `nda-denylist` chặn).

📖 Phân quyền + luồng thao tác đầy đủ: [GITFLOWS.md](https://github.com/AI20K-VGR/agentcore-studio-kit/blob/main/GITFLOWS.md)
