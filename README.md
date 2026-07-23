# agentcore-studio-evalhub

> Eval harness, LLM-judge, scorecard, golden-set.

**Owner:** AIE-2 — Lưu Tiến Duy · **Loại:** uv workspace member (Python 3.14) · **Repo cha:** [agentcore-studio-kit](https://github.com/AI20K-VGR/agentcore-studio-kit)

## Repo này là gì
Submodule `packages/evalhub` của workspace `agentcore-studio-kit`. Owner: **AIE-2 — Lưu Tiến Duy**. Chứa eval harness, LLM-judge, scorecard, golden-set. (Tên `evalhub`, không phải `eval`, để tránh shadow builtin.)

## ⚠️ Không build/test độc lập được
`agentcore-studio-evalhub` phụ thuộc `agentcore-studio-contracts` + uv.lock + `docker/postgres-init` của repo cha, và cần **Postgres** cho test. Vì vậy:
- **Làm việc qua repo cha:** `git clone --recursive git@github.com:AI20K-VGR/agentcore-studio-kit.git`, rồi `cd packages/evalhub` để sửa / commit / push chính repo này.
- **Test đầy đủ:** đẩy PR → CI tự **dựng lại full workspace** rồi chạy `pytest packages/evalhub/tests` (Phương án B).

## CI
`.github/workflows/ci.yml` chỉ là **stub** gọi reusable workflow chung ở repo cha:
`AI20K-VGR/agentcore-studio-kit/.github/workflows/reusable-domain-ci.yml@main`.
Muốn đổi quy trình CI thì sửa ở repo cha (1 chỗ).

## Quy tắc
- Chỉ đụng file trong `packages/evalhub/**` (fence-lane của bạn) — không sửa surface domain khác.
- Đổi contract → sang repo `agentcore-studio-contracts` (mentor-approval).
- Không commit tài liệu mentor/rubric/answer-key (pre-commit `nda-denylist` chặn).

📖 Phân quyền + luồng thao tác đầy đủ: [GITFLOWS.md](https://github.com/AI20K-VGR/agentcore-studio-kit/blob/main/GITFLOWS.md)
