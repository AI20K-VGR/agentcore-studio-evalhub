# B3 — D14 retrieval measurement evidence review

**Ngày:** 2026-08-06 · **Owner:** AIE-2, với measurement report từ AIE-1  
**Plan:** `day-14-aie2.md` §7  
**Trạng thái:** **READY** — current PG measurement đã chạy xong trên Docker Postgres/pgvector thật
và được ghi rõ theo source/config. Kết quả chỉ estimable cho fixed candidate set/config này; chưa phải
population estimate, held-out result hoặc threshold acceptance.

## Input → command → output

**Input / provenance:**

- Root pointer: `a1c9bf8`.
- KB: `b57ba78ab936061cc487b76f1d6a47684f993a01`.
- Engine: `f50cab937d902459f380142193873b95e17d5c04`.
- Evalhub: `a60855d43f4c5923d0a5e696d51be330dcaa8508`.
- Corpus: `packages/kb/docs/callisto` — 42 documents, 140 chunks ingest thật.
- Golden set: `callisto-golden-30-v1` — 22 answerable, 8 refusal.

**Measurement command supplied by AIE-1:**

```bash
git -C packages/kb checkout --detach b57ba78
git -C packages/engine checkout --detach f50cab9
git -C packages/evalhub checkout --detach a60855d
docker compose -f docker-compose.test.yml up -d
uv run --python 3.14 python pg_retrieval_measurement.py
```

The measurement used real Docker Postgres/pgvector and called `PgKbSearch` directly. No CI link
exists; the script was ad hoc and untracked, and the raw JSON was kept in the AIE-1 scratchpad. AIE-1
reported that the submodules were restored and the container was stopped after the run. This is a
reproducibility limitation, not a fabricated artifact.

**Config thực tế:**

| item | value | limitation |
|---|---|---|
| search path | `PgKbSearch.search()` directly | engine/evalhub SHAs are provenance only; `EngineAgentRunner` and `EvalHarness.run()` were not in this measurement path |
| embedding | `BagOfWordsEmbedding` / `studio_kb.embeddings.derive_vector` | current shipped embedding at KB `b57ba78`; module warns it is not semantic-quality evidence |
| dimension | `EMBEDDING_DIM=8` | fixed by current schema |
| top_k | `10` | explicitly chosen for this measurement; not a frozen D16 default |
| database | Docker Postgres/pgvector, real DSNs | no mock/test double; local run, no CI artifact |
| held-out | none | all 30 cases are candidate/draft; no held-out claim |

## Per-case PG result

Rank means the expected citation position in the `PgKbSearch` top-10 result. `missing` means the
expected citation was not present in top-10.

| case_id | expected citation | PG rank | status |
|---|---|---:|---|
| HB-01 | `ankor-remote-001#c1` | 8 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-02 | `borea-remote-001#c1` | 7 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-03 | `ankor-training-001#c1` | 2 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-04 | `borea-training-001#c1` | 1 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-05 | `ankor-oncall-001#c2` | 1 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-06 | `borea-oncall-001#c2` | 5 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-07 | `ankor-procurement-001#c2` | 2 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-08 | `ankor-salary-001#c1` | 5 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-09 | `borea-salary-001#c1` | 8 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-10 | `ankor-benefits-001#c1` | missing | `RETRIEVAL_EVIDENCE` — not found in top-10 |
| HB-11 | `ankor-holidays-001#c1` | missing | `RETRIEVAL_EVIDENCE` — not found in top-10 |
| HB-12 | `borea-holidays-001#c1` | 4 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-13 | `ankor-reimbursement-001#c1` | 7 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-14 | `ankor-incident-001#c1` | 8 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-15 | `ankor-leave-001#c1` | 1 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-16 | `borea-leave-001#c1` | 3 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-17 | `ankor-expense-001#c2` | 1 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-18 | `ankor-performance-001#c1` | 10 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-19 | `borea-procurement-001#c2` | 1 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-20 | `ankor-invoicing-001#c3` | 6 | `RETRIEVAL_EVIDENCE` — fixed candidate |
| HB-21 | `ankor-recruitment-001#c3` | missing | `RETRIEVAL_EVIDENCE` — not found in top-10 |
| HB-22 | `borea-benefits-001#c1` | missing | `RETRIEVAL_EVIDENCE` — not found in top-10 |

## Refusal / fence evidence

Refusal cases do not enter the citation denominator. AIE-1 measured the tenant/section fence directly
on returned `KbSearchResultItem` fields using real Postgres RLS; all eight were `PASS — 0 leak`.

| case_id | axis | requested scope | expected scope | result |
|---|---|---|---|---|
| HB-23 | T1 | ankor/hr | borea/hr | `FENCE_EVIDENCE` — 0 leak |
| HB-24 | T6 | ankor/engineering | ankor/hr | `FENCE_EVIDENCE` — 0 leak |
| HB-25 | T1 | ankor/engineering | borea/engineering | `FENCE_EVIDENCE` — 0 leak |
| HB-26 | T6 | ankor/public | ankor/hr | `FENCE_EVIDENCE` — 0 leak |
| HB-27 | T6 | ankor/public | ankor/finance | `FENCE_EVIDENCE` — 0 leak |
| HB-28 | T1 reverse | borea/finance | ankor/finance | `FENCE_EVIDENCE` — 0 leak |
| HB-29 | T1 reverse | borea/public | ankor/public | `FENCE_EVIDENCE` — 0 leak |
| HB-30 | T6 | borea/public | borea/hr | `FENCE_EVIDENCE` — 0 leak |

`0 leak` means no returned chunk had a DB `tenant_id` different from the requesting tenant or a
`section_role` outside the requesting roles. It does not by itself prove the semantic correctness of
the refusal answer.

## Metrics

For the 22 answerable candidate cases:

```text
recall@1  = 5/22  = 22.7%
recall@3  = 8/22  = 36.4%
recall@5  = 11/22 = 50.0%
recall@10 = 18/22 = 81.8%
missing   = 4     = HB-10, HB-11, HB-21, HB-22
MRR       = 0.36  (missing counts as 0)
found-only mean / median rank = 4.44 / 4.5
fence     = 8/8   = 100%, with no citation denominator
```

These are fixed-set observations under `PgKbSearch`, `BagOfWordsEmbedding`, `EMBEDDING_DIM=8`, and
`top_k=10`. They are not lower bounds, population estimates, or threshold recommendations.

## Comparison and estimability

The earlier current static probe reported `20/22` rank 1 under `StaticKbSearch` with a different
probe/top-k configuration. The current PG result is `5/22` rank 1 under the named PG/BOW/top-10
configuration. This is a configuration/backend finding; it must not be collapsed into one score or
called a regression without a controlled same-config comparison.

The historical A2-bis PG result remains separately labeled: its source SHAs were kit `5c6f6d8`, KB
`51df3a4`, engine `87c18e8`, evalhub `96e3110`; it reported 2/7 rank 1 at `top_k=5`. It is not reused
as the current result.

| claim | status |
|---|---|
| current fixed-set PG ranking under named config | **ESTIMABLE** |
| refusal fence observations under named scope | **ESTIMABLE as fence evidence** |
| semantic refusal correctness / no-leak answer quality | **NOT_ESTIMABLE** from this measurement alone |
| population quality / generalization | **NOT_ESTIMABLE** — no held-out split |
| D16 threshold | **NOT_DECIDED** — top_k was chosen for measurement, not frozen as a gate |

## Blocker status

No B3 input blocker remains. D16 still needs to decide whether to create a held-out set and how to set
any threshold; those are downstream decisions and must not be inferred from `recall@10=81.8%` or
`MRR=0.36`.
