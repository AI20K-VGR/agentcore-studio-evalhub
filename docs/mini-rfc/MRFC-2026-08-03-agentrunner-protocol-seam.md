---
id: studio.mini-rfc.MRFC-2026-08-03-agentrunner-protocol-seam
type: mini-rfc
status: PRE-WRITTEN   # viết sẵn ở D11, KHÔNG nộp hôm nay — xem §2
contract: contracts (studio_contracts.protocols)
pen: contracts = shared (CODEOWNERS @TranBaDat2607 @hieubui2409)
proposer: AIE-2 — Lưu Tiến Duy (@dholmes0207)
opened: 2026-08-03
deadline_4of4: 2026-08-06 (D14)
---

# MRFC-2026-08-03 · Promote `AgentRunner` thành Protocol seam thứ 4 trong `studio_contracts`

> **Đây là bản ĐIỀN THẬT của [`TEMPLATE.md`](TEMPLATE.md), không phải ví dụ dựng.** Món này được
> chọn vì nó là **món duy nhất** trong danh sách hoãn của AIE-2 mà **sau freeze thật sự cần** con
> đường mini-RFC: nó thêm bề mặt vào `studio_contracts` (layer đáy, dùng chung 4 người).
>
> **Vì sao KHÔNG chọn "per-chunk `tenant_id` cho leak UUID"** — món mà kế hoạch D11 ban đầu định lấy
> làm bản điền đầu tiên: đo lại thì món đó **không cần mini-RFC**. Dữ liệu đã có từ D5 ở
> `outputs["chunks"]` (`interpreter.py:265-268`, `KbSearchResultItem.tenant_id: UUID`), 4 consumer
> đang đọc, `TraceEvent.outputs` **không đổi kiểu** ⇒ thiếu là **một dòng doc**, không phải một field.
> Tiền đề cũ (`scorecard-v0.md:335-337`) đã **rút**. Lấy một ca không-cần-mini-RFC làm ví dụ mini-RFC
> sẽ dạy sai chính cái template này muốn dạy — xem bảng *"KHÔNG dùng khi nào"* ở TEMPLATE §đầu.

## 0 · Metadata

| | |
|---|---|
| **Mini-RFC id** | `MRFC-2026-08-03-agentrunner-protocol-seam` |
| **Hợp đồng chạm** | `contracts` — `studio_contracts/protocols.py` |
| **Người giữ bút** | shared repo · CODEOWNERS `@TranBaDat2607 @hieubui2409` |
| **Người đề xuất** | @dholmes0207 (AIE-2) |
| **Loại thay đổi** | **thêm mới** (Protocol thứ 4) — không rename, không removal, không required-add |
| **Bump `SCHEMA_VERSION`?** | **Không.** Thêm một Protocol không đổi shape payload nào; `test_freeze_guard.py` không có ca nào bị chạm |
| **Ngày mở** | 2026-08-03 (viết sẵn) |
| **Hạn xin đủ 4/4** | 2026-08-06 (D14) — **nếu** quyết định nộp |

## 1 · Thay đổi cụ thể

```diff
--- a/src/studio_contracts/protocols.py
+++ b/src/studio_contracts/protocols.py
@@
+@runtime_checkable
+class AgentRunnerSeam(Protocol):
+    """Chạy một case qua recipe của `agent_id` rồi trả câu trả lời + trace của đúng run đó.
+
+    Seam này để bộ chấm (evalhub) gọi interpreter (engine) mà KHÔNG import nó —
+    `.importlinter` cấm `studio_evalhub` import `studio_engine`/`studio_kb`.
+    Bản thật tiêm từ `apps/studio` (composition root).
+    """
+
+    async def run_case(
+        self,
+        *,
+        agent_id: str,
+        query: str,
+        tenant_id: UUID,
+        section_roles: list[str],
+    ) -> object: ...   # kiểu trả về: xem §4 — đây đúng chỗ RFC này còn hở
```

## 2 · Vì sao cần — và vì sao KHÔNG nộp hôm nay

**Trạng thái: `PRE-WRITTEN`, cố ý không nộp ở D11.** Quyết định D11 (`DEC-Q4`,
`docs/scorecard-v0.md` §3 Q4) là **KHÔNG** đưa lên contracts hôm nay. Ba lý do:

- (a) `contracts` là layer đáy — thêm seam thứ 4/5 là **mở rộng bề mặt freeze đúng ngày đóng băng nó**;
- (b) `AgentRunner` (`packages/evalhub/src/studio_evalhub/agent_runner.py:76`) đang chạy tốt như
  **Protocol nội bộ quadrant**, và `lint-imports` vẫn `1 kept, 0 broken` ⇒ ràng buộc layering **không**
  đòi promote;
- (c) adapter `EngineAgentRunner` sống ở `apps/studio` — chỗ **duy nhất** chạm AIE-1, đã có và đã chạy.

**Vậy vì sao viết sẵn?** Vì **sau khi `scorecard` FROZEN, đây là món đầu tiên phải đi đường mini-RFC**,
và viết lúc còn rẻ thì lúc cần chỉ phải cập nhật số. Cái bị chặn nếu **không bao giờ** làm: `EvalHarness.run()`
thật sẽ phải tự chọn một kiểu nội bộ cho seam, và mỗi quadrant đọc trace qua một kiểu khác nhau.

Điều kiện mở: **D14**, hoặc sớm hơn nếu D16 cần adapter thứ hai (vd đọc trace từ Postgres của DE thay
vì từ `RunResult` trong bộ nhớ) — hai adapter là lúc seam đáng có tên chung.

## 3 · Ai vỡ — đếm được

**0 consumer vỡ.** Đây là **thêm mới**: không tên nào bị đổi, không field nào bị bỏ.

| Consumer (file:line) | Repo | Vỡ thế nào | Ai sửa |
|---|---|---|---|
| `studio_evalhub/agent_runner.py:76` `AgentRunner` | evalhub | **Không vỡ.** Sẽ trùng nghĩa với seam mới ⇒ dọn dần, không bắt buộc cùng PR | AIE-2 |
| `apps/studio` adapter `EngineAgentRunner` | apps/studio | **Không vỡ.** Đã thoả shape (`runtime_checkable`) | AIE-2 + AIE-1 |
| `StubAgentRunner` (`agent_runner.py:100`) | evalhub | **Không vỡ** — cùng lý do | AIE-2 |

Lệnh đã chạy để có bảng trên:

```bash
grep -rn "AgentRunner\|run_case" packages apps scripts tests
grep -rn "class .*Protocol" packages/contracts/src/studio_contracts/protocols.py
uv run lint-imports          # 1 kept, 0 broken — layering hiện tại đã hợp lệ KHÔNG cần seam này
```

## 4 · Phương án đã cân nhắc và bỏ

| Phương án | Vì sao bỏ |
|---|---|
| **Giữ Protocol nội bộ quadrant (nguyên trạng)** | **Đây là phương án đang được chọn cho D11**, và nó là phương án mạnh nhất, không phải bù nhìn: 0 dòng code, 0 chữ ký, `lint-imports` đã xanh, `EvalHarness.run` D16 dựng được không cần promote. Chỉ bỏ khi có **adapter thứ hai** — lúc đó "kiểu nội bộ của evalhub" thành tên sai cho một thứ hai bên dùng |
| **Đưa `CaseRun`/`AgentAnswer` lên `contracts` luôn** | Nặng hơn nhiều: `CaseRun` chứa `list[TraceEvent]`, tức seam sẽ khoá cả **hình dạng gói kết quả**, không chỉ chữ ký gọi. Sau freeze mỗi lần đổi `CaseRun` là 4/4 chữ ký. Và `CaseRun` còn tiến hoá qua D16 (nguồn trace có thể là Postgres) |
| **Không dùng Protocol, để evalhub import engine trực tiếp** | Vi phạm `.importlinter` (contract `AgentCore Studio quadrant layering`), và làm evalhub phụ thuộc thứ tự deploy của engine |
| **Kiểu trả về `object` như diff §1** | Chỗ RFC này **còn hở, nói thẳng**: `-> object` làm seam mất tác dụng type-check. Muốn đúng thì phải promote `CaseRun` (dòng trên) hoặc dùng generic. **Chưa giải quyết** ⇒ thêm một lý do để chưa nộp |

## 5 · Proof consumer — CI KHÔNG chạy hộ

Chưa có nhánh cho RFC này (chưa nộp). Bảng dưới là **số baseline** đo ngày 2026-08-03, để lúc nộp chỉ
cần điền cột "Sau":

| Đo | Trước (`contracts@3d7004b`) | Sau |
|---|---|---|
| `pytest packages apps tests` | `331 passed, 8 skipped, 5 xfailed` (0 XPASS) | *(chưa đo)* |
| `mypy packages apps` | `Success — 0 lỗi / 110 file` | *(chưa đo)* |
| `lint-imports` | `1 kept, 0 broken` | *(chưa đo)* |
| `pytest packages/contracts` | `11 passed` | *(chưa đo)* |

Quy trình bắt buộc khi nộp (`reusable-domain-ci.yml:100` chỉ chạy `pytest <domain_path>/tests` ⇒ PR
contracts **không bao giờ** chạy test evalhub/apps):

```bash
git -C packages/contracts checkout <nhánh-RFC>
uv run pytest packages apps tests -q && uv run mypy packages apps && uv run lint-imports
git -C packages/contracts checkout 3d7004b2e55d500e3706b9eac412fc809eb4e839
git status --short    # PHẢI rỗng
```

## 6 · Chữ ký — 4/4

Chữ ký thật = Approve trên PR (ADR-D11-01 lớp 1). Bảng dưới là **dấu vết**:

| Vai | GitHub | PR đã Approve | Ngày | `<repo>@<sha>` |
|---|---|---|---|---|
| AIE-1 | @TranBaDat2607 | — | — | — |
| AIE-2 | @dholmes0207 | — | — | — |
| DE | @DongAnh2704 | — | — | — |
| SWE | @Dozyboy | — | — | — |

## 7 · Nếu không đủ 4/4 trước hạn

```
Trạng thái: PRE-WRITTEN, chưa nộp (quyết định DEC-Q4 ở D11 là chưa promote).
Chữ ký: 0/4 — đúng như dự kiến, vì chưa xin.
Mặc định đang áp: giữ Protocol nội bộ quadrant (`agent_runner.py:76`).
Điều kiện mở: D14, hoặc sớm hơn khi xuất hiện adapter thứ hai.
Chủ: AIE-2 + AIE-1.
```
