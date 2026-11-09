# Data

This directory holds the **data policy and manifest**, not the data.

## Policy

- Raw SQuAD and HotpotQA text is **never committed**. `data/raw/`, `data/interim/`, and the
  contents of `data/processed/` are git-ignored.
- The only tracked files here are `README.md` and `manifest.json`.
- Do not add dataset archives, JSONL dumps, parquet files, or model weights.
- Do not add private queries, user logs, or scraped personal data.

## Layout

```
data/
├─ README.md          this policy
├─ manifest.json      dataset IDs, versions, licenses, checksums, counts
├─ raw/               upstream downloads (git-ignored, created locally)
└─ processed/         questions, corpus, passages (git-ignored; .gitkeep kept)
```

## Datasets

| ID | Dataset | Split | License | Use |
|---|---|---|---|---|
| `squad` | SQuAD v1.1 | dev | CC BY-SA 4.0 | Primary controlled QA |
| `hotpot` | HotpotQA | distractor dev | CC BY-SA 4.0 | Multi-hop / distractor stress |

SQuAD v1.1 dev has 10,570 questions and 20,958 unique contexts. The pilot truncated contexts
to 256 words and chunked them into 70-word passages (45,651 passages). The primary run samples
1,000 questions; the 1.5B replication uses 500; the boundary probe uses 200.

HotpotQA distractor dev supplies 10 paragraphs per question (2 gold, 8 distractors). The run
uses 500 questions and a depth grid capped at 10.

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
