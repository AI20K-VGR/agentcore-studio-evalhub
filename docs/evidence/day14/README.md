# D14 evidence B1–B7 — bản publish

**Publish ngày D15 (07/08/2026) như một phần của T1 (vá link chết).**

Bộ B1–B7 này được viết trong phiên D14 (06/08) và ban đầu chỉ nằm ở `.local-reviews/day14/` của
parent kit. `.local-reviews/` được liệt trong `.git/info/exclude` — tức là một exclude **cấp máy**,
vô hình với mọi clone khác, kể cả clone của đồng đội. Daily note D14 trỏ vào đó bằng đường dẫn
tương đối `../../../.local-reviews/day14/B7-evidence.md`, nên với người đọc thứ hai nó là một link
chết dù file có thật.

`kit#74`: *"Closing an issue whose artifact I cannot find in a fresh clone counts against you, not
for you."* ⇒ artifact được chuyển vào repo có track.

## Đã đổi gì so với bản local

**Nội dung phân tích giữ nguyên**, chỉ sửa đường dẫn cho resolve được từ fresh clone:

| Link gốc (local) | Bản publish |
|---|---|
| `../../../packages/evalhub/docs/mini-rfc/…` | `../../mini-rfc/…` — cùng repo, đường dẫn tương đối trong evalhub |
| `../../../packages/contracts/…` | URL tuyệt đối tới `AI20K-VGR/agentcore-studio-contracts` — repo khác, không reach được bằng đường dẫn tương đối |
| `../../../packages/engine/…` | URL tuyệt đối tới `AI20K-VGR/agentcore-studio-engine` — như trên |
| `../day13/A*.md` (5 link) | **Bỏ link, giữ tên file + lý do.** Bộ A-series D13 chưa publish; để link là tái tạo đúng lỗi đang vá |

## Đọc theo thứ tự nào

Bắt đầu ở [B7](B7-evidence.md) — nó là index và có mục FACT/FINDING/BLOCKER/OWNER. B1–B6 là chi tiết
từng mảng.

| ID | Nội dung |
|---|---|
| [B1](B1-workspace.md) | snapshot SHA/source, baseline test |
| [B2](B2-trace-carrier.md) | trace carrier mapping + DB round-trip |
| [B3](B3-retrieval-evidence.md) | đo retrieval trên Postgres thật, có ghi giới hạn |
| [B4](B4-coverage-acceptance.md) | ma trận coverage golden-30 |
| [B5](B5-judge-optional-adr.md) | ADR judge optional — `NO_BUMP` |
| [B6](B6-q4-seam-decision.md) | quyết định seam Q4 — `OPEN_MINI_RFC` |
| [B7](B7-evidence.md) | tổng hợp + handoff D16/D18 |
