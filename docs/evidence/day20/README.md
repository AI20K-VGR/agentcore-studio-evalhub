# D20 evidence — GATE-2 · khối SHA nền của ngày

> Plan: [`docs/plans/day-20-aie2.md`](../../plans/day-20-aie2.md) · Issue `kit#128` (con, AIE-2)
> dưới `kit#129` (cha, GATE-2 cả nhóm).

**Vì sao file này đứng đầu bộ evidence:** T3/T4/T5 chạy **giữa** ngày, mà `evalhub` còn đổi tiếp sau
đó (T6 · T8a · lint/format · vá review) trước khi merge ⇒ SHA lúc chạy số **khác** SHA lúc bàn giao.
Khối dưới đây là **nền**, không phải câu trả lời: mỗi bảng số trong bộ evidence này ghi SHA của
**chính lúc chạy**, không dùng lại khối nền. Neo `file:line` neo được **nội dung**; nó không neo
được **phiên bản**.

---

## Khối SHA nền — sau T0a, trước T2/T3/T4

```console
$ git rev-parse HEAD                          # kit
e1d8d62b7bc78fe502033a4e79ef5e401fd1fd06

$ git submodule status
 db9ec90b8dea1e17eebc2ff26bf77179157d4eef apps/studio (remotes/origin/HEAD)
 44fe582a5bb9554c1f42f7d03854cf285dac3b19 apps/web (remotes/origin/HEAD)
 8c4f119ee30bf6c1de354ab2e40dcb401bc29322 docs/reports (heads/main)
 c64a212e41aeae7521ded0edcd00e981d18c59c8 docs/requirements (remotes/origin/HEAD)
 b642af1e711e0c46639e7aaf69de730f71380bec packages/contracts (heads/main)
+bfa19cc8712e153d0e38e3e94e72623422b3c88a packages/engine (remotes/origin/HEAD)
+24066c6db2fb61a039ca0ead9b2521c94e6714d0 packages/evalhub (heads/main)
 01941998cef0375aec3b8a2115db61849c22be56 packages/kb (remotes/origin/HEAD)
 04ca988853cb2d23fe37137a047a3568c4519e7b packages/workbench (remotes/origin/HEAD)

$ git status --porcelain                      # kit
 M docs/reports
 M packages/engine
 M packages/evalhub
```

### Đọc khối trên — ba dòng `+` không giống nhau, đừng gộp

| Con trỏ | kit ghi | Working tree | Nghĩa |
|---|---|---|---|
| `apps/studio` | `db9ec90` | `db9ec90` | ✅ khớp — bump ở `e1d8d62` (T0a). Điều kiện của T3 |
| `packages/workbench` | `04ca988` | `04ca988` | ✅ khớp — bump ở `e1d8d62` (T0a). Điều kiện của T4 (`publish()` chỉ tồn tại từ `04ca988`) |
| `packages/engine` | `62773ba` | `bfa19cc` | ⚠️ lệch **có chủ đích** — bump đã nằm trong kit PR#151 (`d74afed`), chưa merge. Commit lại ở đây là bump chồng |
| `packages/evalhub` | `afe35a5` | `24066c6` | ⚠️ như trên — bump nằm ở PR#151 (`23a455e`), chưa merge |
| `docs/reports` | `8c4f119` | `8c4f119` (dirty) | Daily-note D19 chưa commit trong repo con. Bump ở T8b |

**Hai dòng ⚠️ không phải bẩn ngẫu nhiên.** `engine` và `evalhub` đã được bump trên nhánh
`chore/d19-bump-engine` (kit PR#151, đã push, còn OPEN). Working tree mang sẵn hai checkout đó;
commit lại chúng ở nhánh D20 sẽ tạo hai gitlink commit trùng nội dung trên hai nhánh khác nhau.
Nên `e1d8d62` **chỉ** chứa `apps/studio` + `workbench`.

---

## Trạng thái nợ D19 khi D20 bắt đầu — đo lại, khác plan

Plan `§1` viết `evalhub#22` `state=OPEN reviews=[] mergeStateStatus=BLOCKED`. Đo lại đầu D20:

```console
$ gh pr view 22 -R AI20K-VGR/agentcore-studio-evalhub --json state,mergedAt,mergeCommit
state       = MERGED
mergedAt    = 2026-08-13T04:58:16Z
mergeCommit = 24066c6db2fb61a039ca0ead9b2521c94e6714d0     # merge-commit, đúng quy ước repo
review      = APPROVED (DongAnh2704, trên tip 05c81f4)
```

⇒ **T0a bước 1 và bước 2 đã xong trước khi D20 bắt đầu.** Không có việc để làm; ghi lại để
plan-vs-actual có neo, và để không ai đọc `§1` rồi tưởng còn nợ.

Còn OPEN, và **chưa** đóng ở thời điểm khối nền này:

| Món | Trạng thái | Xử ở |
|---|---|---|
| `kit#123` (issue D19) | OPEN | T0a bước 4 |
| kit PR#151 (bump engine + evalhub) | OPEN, đã push | Ngoài quyền merge của phiên này |
| kit PR#152 (`ruff format --check` vào make lint + CI) | OPEN, 0 review | Ngoài quyền merge của phiên này |
