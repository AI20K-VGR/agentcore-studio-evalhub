# B1 — D14 workspace / source snapshot

**Ngày:** 2026-08-06 · **Owner:** AIE-2 · **Plan:** `day-14-aie2.md` §5  
**Trạng thái:** **READY** — snapshot và baseline đã chạy; có finding về SHA/branch drift so với D13.

## Input → command → output

**Input:** workspace hiện tại tại `/home/dholmes/VFS_Intern/agentcore-studio-kit`; không dùng bản copy
không có SHA.

**Command:**

```bash
git status --short --branch
git rev-parse HEAD
git submodule status
git -C packages/evalhub status --short --branch
git -C packages/evalhub rev-parse HEAD
git -C packages/evalhub rev-parse origin/main
git -C packages/kb rev-parse HEAD
git -C packages/engine rev-parse HEAD
UV_CACHE_DIR=/tmp/agentcore-evalhub-uv-cache uv run pytest packages/evalhub/tests -q
UV_CACHE_DIR=/tmp/agentcore-evalhub-uv-cache uv run ruff check packages/evalhub
UV_CACHE_DIR=/tmp/agentcore-evalhub-uv-cache uv run lint-imports
```

**Output thực tế:**

```text
## day13/pointer-aie2...origin/day13/pointer-aie2 [ahead 8]
f1cc23b (final parent pointer for D14 daily note; includes KB bump)
 0352176797fa6d3cd14d298117db790b65115c21 apps/studio (heads/main)
 265fdd32051c5d438fb32437fb19784d7be7774c apps/web (remotes/origin/HEAD)
 05e9243a0cd8950621f48c4bc2ae1fd629e2c797 docs/reports (heads/main)
 c64a212e41aeae7521ded0edcd00e981d18c59c8 docs/requirements (remotes/origin/HEAD)
 79edfb796f753b9af8b48a5027a4d9e01ea5ff94 packages/contracts (remotes/origin/HEAD)
 f50cab937d902459f380142193873b95e17d5c04 packages/engine (heads/main)
 a60855d43f4c5923d0a5e696d51be330dcaa8508 packages/evalhub (heads/main)
 b57ba78ab936061cc487b76f1d6a47684f993a01 packages/kb (remotes/origin/HEAD)
 e8a9899e1e672f9906c990e21735704748023133 packages/workbench (remotes/origin/HEAD)
## main...origin/main
a60855d43f4c5923d0a5e696d51be330dcaa8508
a60855d43f4c5923d0a5e696d51be330dcaa8508
b57ba78ab936061cc487b76f1d6a47684f993a01
f50cab937d902459f380142193873b95e17d5c04
.....x...........s..................x................                    [100%]
50 passed, 1 skipped, 2 xfailed in 0.53s
All checks passed!

Contracts: 1 kept, 0 broken.
```

The first rerun with the default uv cache was blocked by the read-only environment cache at
`/home/dholmes/.cache/uv`. The same commands were then rerun with
`UV_CACHE_DIR=/tmp/agentcore-evalhub-uv-cache`; the output above is from that successful rerun.

## Source-of-truth snapshot

| Thành phần | SHA / trạng thái hiện tại |
|---|---|
| root | `f1cc23b`; clean; `day13/pointer-aie2` is 8 commits ahead of `origin/day13/pointer-aie2`; includes the local KB pointer bump and D14 daily-note pointer |
| evalhub | `a60855d43f4c5923d0a5e696d51be330dcaa8508`; clean; `origin/main` cùng SHA |
| KB | `b57ba78ab936061cc487b76f1d6a47684f993a01` (merge of kb#15) |
| engine | `f50cab937d902459f380142193873b95e17d5c04` |
| workbench | `e8a9899e1e672f9906c990e21735704748023133`; pointer mới từ kit `origin/main` |
| test baseline | `50 passed, 1 skipped, 2 xfailed, 0 XPASS` |
| ruff | `All checks passed!` |
| import-linter | `Contracts: 1 kept, 0 broken` |

## FINDING — không trộn với snapshot D13

D13 A1 ghi root `5c6f6d8`, evalhub local `96e3110`, KB `51df3a4`, engine `87c18e8`. D14 đang đọc một
pointer snapshot khác: root `f1cc23b`, evalhub `a60855d`, KB `b57ba78`, engine `f50cab9`, workbench
`e8a9899`. Test baseline vẫn cùng shape/count (`50/1/2xf/0 XPASS`), nhưng branch và SHA không được gọi
 là D13 SHA. Pointer refresh thay đổi workbench và sau đó KB; các SHA trực tiếp của evalhub/engine cho B2
không đổi.

Diff tree KB từ SHA measurement D13 `51df3a4` tới SHA hiện tại now includes the merged D14 Golden30/grid
inputs and their guards. AIE-1 has now supplied a current PG measurement at KB `b57ba78`; B3 keeps it
separate from the historical A2-bis result and records that the direct `PgKbSearch` run did not execute
engine/evalhub. The measurement was taken before the docs-only parent commits; component
SHAs used by B2/B3 are unchanged. Web pointer vẫn `265fdd3`; `studio-web#2` đã approved/clean nhưng
chưa merged.

## Interpretation

Workspace đủ sạch để tiếp tục B2–B7. Không có source-code, label, contract hoặc scorer nào bị sửa ở
T1. Baseline xanh không phải bằng chứng trace/measurement/Golden-30 đã sẵn sàng.
