# B4 — D14 Golden-30 coverage acceptance

**Ngày:** 2026-08-06 · **Owner:** AIE-2 (matrix/consumer checks), DE (case value/label)
**Plan:** `day-14-aie2.md` §8
**Trạng thái:** **READY** — current KB main contains all 30 Golden30 rows; no case, label, or
expected value was invented or changed by AIE-2.

## Input → command → output

**Input:** current root pointer `a1c9bf8`; current KB pointer
`b57ba78ab936061cc487b76f1d6a47684f993a01`, the merge commit for kb#15; source file
`packages/kb/golden/callisto-handbook-30-draft.yaml`.

**Commands run:**

```text
current Golden30 count/corpus probe
current static citation-rank probe, top_k=50
.venv/bin/python -m pytest packages/kb/tests/test_golden_set.py packages/kb/tests/test_grid_inputs.py -q
```

**Output thực tế:**

```text
golden_set_ref=callisto-golden-30-v1
case_count=30
positive=22; refusal=8
case_ids=HB-01..HB-30
corpus=140 chunks / 42 docs
static expected-citation rank1=20/22; missing=0
HB-09 rank=4; HB-20 rank=3; all other answerable cases rank=1
106 passed in 0.30s
```

The static rank result is a fixed-set observation. It is not a held-out evaluation, a population
estimate, a PG measurement, or a threshold acceptance.

## 30 target rows

All rows below are present in the merged KB source. The query, expected value, citation, and label
remain DE-owned source data. `candidate, not held-out` is recorded because no held-out split was
provided; this does not turn the set into a quality estimate.

| slot | case | status | owner | ETA | provenance / current evidence |
|---|---|---|---|---|---|
| S-01 | HB-01 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-02 | HB-02 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-03 | HB-03 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-04 | HB-04 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-05 | HB-05 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-06 | HB-06 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-07 | HB-07 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-08 | HB-08 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-09 | HB-09 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 4 |
| S-10 | HB-10 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-11 | HB-11 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-12 | HB-12 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-13 | HB-13 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-14 | HB-14 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-15 | HB-15 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-16 | HB-16 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-17 | HB-17 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-18 | HB-18 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-19 | HB-19 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-20 | HB-20 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 3 |
| S-21 | HB-21 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-22 | HB-22 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; positive; candidate, not held-out; static rank 1 |
| S-23 | HB-23 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; refusal/T1; candidate, not held-out; citation ranking not applicable |
| S-24 | HB-24 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; refusal/T6; candidate, not held-out; citation ranking not applicable |
| S-25 | HB-25 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; refusal/T1; candidate, not held-out; citation ranking not applicable |
| S-26 | HB-26 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; refusal/T6; candidate, not held-out; citation ranking not applicable |
| S-27 | HB-27 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; refusal/T6; candidate, not held-out; citation ranking not applicable |
| S-28 | HB-28 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; refusal/T1; candidate, not held-out; citation ranking not applicable |
| S-29 | HB-29 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; refusal/T1; candidate, not held-out; citation ranking not applicable |
| S-30 | HB-30 | FILLED | DE / @DongAnh2704 | delivered; merged kb#15 2026-08-06 | KB Golden30 source; YAML header attributes authorship/annotation to DE; refusal/T6; candidate, not held-out; citation ranking not applicable |

**Count:** `30 FILLED + 0 MISSING = 30`.

## Interpretation / handoff

B4 is now a complete source-coverage acceptance for the current KB pointer. It removes the former
9-filled/21-missing dependency from the D14 handoff. It does not prove current PG retrieval quality,
refusal semantic correctness, held-out generalization, or a production threshold; those remain covered
by B2/B3 evidence and their blockers.
