# Data

This directory holds the **data policy and manifest**, not the data.

## Policy

- Raw SQuAD and HotpotQA text is **never committed**. `data/raw/`, `data/interim/`, and the
  contents of `data/processed/` are git-ignored.
- The tracked files here are `README.md`, `manifest.json`, and `splits/*.json`. The split files
  contain question IDs and hashes only, never question or context text.
- Do not add dataset archives, JSONL dumps, parquet files, or model weights.
- Do not add private queries, user logs, or scraped personal data.

## Layout

```
data/
├─ README.md          this policy
├─ manifest.json      dataset IDs, versions, licenses, checksums, counts
├─ splits/            tracked question-ID lists and hashes (no text)
├─ raw/               upstream downloads (git-ignored, created locally)
└─ processed/         questions, corpus, passages (git-ignored; .gitkeep kept)
```

## Datasets

| ID | Dataset | Split | License | Use |
|---|---|---|---|---|
| `squad` | SQuAD v1.1 | dev | CC BY-SA 4.0 | Primary controlled QA |
| `hotpot` | HotpotQA | distractor dev | CC BY-SA 4.0 | Multi-hop / distractor stress |

SQuAD v1.1 dev has 10,570 questions. The pilot's retrieval corpus contained 20,958 unique
contexts and 45,651 70-word passages; that count requires the **train and dev** files together
(dev alone has roughly 2,067 paragraphs). The pilot truncated contexts to 256 words and
chunked them into 70-word passages. The primary run samples 1,000 questions; the 1.5B
replication uses 500; the boundary probe uses 200.

HotpotQA distractor dev supplies 10 paragraphs per question (2 gold, 8 distractors). The run
uses 500 questions and a depth grid capped at 10.

## ID splits

`splits/squad_splits.json` is tracked. It contains the sampled question IDs and a SHA-256 per
split, never question text:

| Split | Size | Use |
|---|---:|---|
| `p0_golden` | 200 | P0 harness check; disjoint from P1 |
| `p1_primary` | 1,000 | P1 confirmatory sample |
| `replication` | 500 | Nested in P1; 1.5B replication and the Llama panel |
| `boundary` | 200 | Nested in P1 and disjoint from replication; 8k boundary probe |
| `context` | 200 | Same IDs as boundary; 4k/16k context-budget probe |
| `tax` | 150 | Nested in P1 and disjoint from replication/boundary |

The IDs are generated deterministically from seed `20261115`. P0 is disjoint from P1 so the
harness check does not consume the confirmatory sample.

## Preparation

1. Download from the official source; record the URL in `manifest.json`.
2. Record the SHA-256 of the downloaded file **before** processing.
3. Run the preparation script (P0/P2; stub in v0.1.0).
4. Record question count, corpus count, chunk size, seed, and checksums.
5. Set `status` to `prepared`, then `verified` after a second check.

Do not hand-edit `manifest.json` to claim a checksum that was not computed. `null` means
"not yet computed", never zero.

## Manifest schema

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | int | `1` |
| `generated_utc` | string/null | ISO 8601 |
| `project` | string | `energy-optimal-rag` |
| `policy` | string | redistribution rule |
| `datasets[]` | array | one object per dataset |
| `datasets[].id` | string | `squad`, `hotpot` |
| `datasets[].name` | string | human name |
| `datasets[].version` | string | upstream version |
| `datasets[].split` | string | split used |
| `datasets[].source_url` | string | official source |
| `datasets[].upstream_license` | string | license |
| `datasets[].n_questions_total` | int | upstream size |
| `datasets[].n_questions_used` | int | sampled size |
| `datasets[].corpus` | object | passage count, chunk size, construction |
| `datasets[].checksums` | object | SHA-256 of source and processed files |
| `datasets[].prepared_utc` | string/null | preparation time |
| `datasets[].status` | string | `not_prepared`, `prepared`, `verified` |
| `datasets[].notes` | string | limits and caveats |

## Licensing

Both datasets are CC BY-SA 4.0. Their licenses remain in force. See
[`../DATA_LICENSE.md`](../DATA_LICENSE.md) and [`../docs/DATA_CARD.md`](../docs/DATA_CARD.md).
