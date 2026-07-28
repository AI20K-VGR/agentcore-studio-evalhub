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

Riêng trong repo này: `tests/test_determinism.py` khoá *"chạy lại ra cùng bảng điểm"*, `tests/test_smoke_runner.py` khoá luật chấm 2 nhánh, `docs/scorecard-v0.md` là hợp đồng chấm.

### Nợ đã biết khiến hai con số lệch nhau

`_demo_golden_set()` là bản **chép in-code** của `packages/kb/golden/smoke-5.yaml` (bút DE) — nguồn sự thật thứ hai. Đọc YAML thật cần khai `pyyaml`, mà `uv.lock` nằm ở repo cha nên `uv lock --check` đỏ nếu khai ở đây. Đóng bằng PR ở repo cha; theo dõi ở điểm gãy #8/#12.

## CI
`.github/workflows/ci.yml` chỉ là **stub** gọi reusable workflow chung ở repo cha:
`AI20K-VGR/agentcore-studio-kit/.github/workflows/reusable-domain-ci.yml@main`.
Muốn đổi quy trình CI thì sửa ở repo cha (1 chỗ).

## Quy tắc
- Chỉ đụng file trong `packages/evalhub/**` (fence-lane của bạn) — không sửa surface domain khác.
- Đổi contract → sang repo `agentcore-studio-contracts` (mentor-approval).
- Không commit tài liệu mentor/rubric/answer-key (pre-commit `nda-denylist` chặn).

📖 Phân quyền + luồng thao tác đầy đủ: [GITFLOWS.md](https://github.com/AI20K-VGR/agentcore-studio-kit/blob/main/GITFLOWS.md)
