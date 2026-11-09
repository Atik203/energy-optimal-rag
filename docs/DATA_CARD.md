# Data Card

**Project:** Energy-Optimal Retrieval Depth in Retrieval-Augmented Generation (G2)
**Version:** 0.1.0 · 2026-11-09
**Policy:** no raw question or context text is stored in this repository. This card describes
provenance, sampling, and limits; it is not a redistribution of the data.

## 1. Datasets at a glance

| Field | SQuAD v1.1 dev | HotpotQA distractor dev |
|---|---|---|
| Role | Primary controlled QA | Multi-hop / distractor stress |
| Upstream | Stanford SQuAD | HotpotQA |
| Version | 1.1 | distractor setting |
| Split | dev | dev |
| Upstream license | CC BY-SA 4.0 | CC BY-SA 4.0 |
| Upstream size | 10,570 questions | 7,405 questions |
| Used here | 1,000 questions (primary); 500 (1.5B); 200 (boundary) | 500 questions |
| Corpus | 20,958 unique dev contexts → 45,651 70-word passages | 10 paragraphs per question (2 gold, 8 distractors) |
| Retriever | BM25 Okapi, top-32 | BM25 Okapi, top-10 |
| Answer type | Extractive span | Extractive span, multi-hop |
| Primary metric | Normalized EM | Normalized EM |
| Secondary metrics | Lenient span, token F1 ≥ 0.5 | Lenient span, token F1 ≥ 0.5 |

## 2. SQuAD v1.1 dev

**Source.** Stanford Question Answering Dataset, version 1.1, dev split. The canonical
distribution is the SQuAD explorer / the official `dev-v1.1.json`. Record the exact URL and
SHA-256 in `data/manifest.json` before preparation.

**Why this dataset.** SQuAD's closed corpus isolates the depth effect: every question's gold
evidence is in the same fixed context collection, so a change in `k` changes how much evidence
reaches the reader, not which corpus is searched. That isolation is a strength for the primary
mechanism test and a weakness for external validity.

**Composition.** The pilot sampled 200 questions stratified over the seven SQuAD wh-types
(28–30 each). The powered run samples 1,000 with the same stratification and seed `20261115`.
Question IDs are hashed into the manifest; the raw question text stays in `data/processed/`.

**Corpus construction.** All unique dev contexts (20,958 in the pilot) are truncated to 256
words and chunked into 70-word passages with no overlap, producing 45,651 passages. Mean
passage length was 53.4 words. Chunking is deterministic; the same text, size, and overlap
must produce the same passages.

**Retrieval ceiling.** In the pilot, the gold context appeared in the top-`k` for 63.0%
(`k=1`), 71.0% (2), 77.5% (4), 81.0% (8), 83.5% (16), and 88.0% (32). The gold answer string
appeared in the retrieved text for 58.0%, 67.5%, 75.5%, 80.5%, 84.0%, and 88.5%. About 12% of
questions have gold evidence outside the top-32 cap, which caps accuracy at 0.88 and adds a
final jump at `k=32` that a full-corpus retriever would not show. Report recall@k with every
accuracy curve.

**Label quality.** SQuAD answers are human-annotated spans. The primary correctness rule is
normalized EM, which is strict; lenient span and token F1 are reported because generative
readers produce short paraphrases that strict EM penalizes. The pilot's "Denver linebacker Von
Miller" versus "Von Miller" is the canonical example.

**Known biases.** Wikipedia-style factual questions; English only; answers are short spans;
the dev distribution is not a deployment distribution. The reader can exploit lexical overlap
between question and passage. Do not compare absolute accuracy to open-domain RAG papers.

## 3. HotpotQA distractor dev

**Source.** HotpotQA, distractor setting, dev split. The distractor setting supplies 10
paragraphs per question: 2 gold and 8 distractors. Record the exact URL and SHA-256 in the
manifest.

**Why this dataset.** It is the cheapest available stress test for two failure modes the
SQuAD condition cannot show: multi-hop evidence (the answer needs two paragraphs) and
distractor-induced non-monotonicity (more passages can lower accuracy). The Theorem 1
unimodality assumption is most likely to fail here, which is exactly what the distractor
counterexample predicts.

**Composition.** 500 dev questions, sampled with seed `20261115` and stratified by question
type and difficulty level where the metadata permits. The depth grid is `{0,1,2,4,8,10}`
because the setting caps the paragraph pool at 10.

**Corpus construction.** The corpus is per-question. Paragraphs are not pooled across
questions; pooling would change the task and inflate retrieval difficulty artificially. 70-word
chunking is applied within each paragraph only if a paragraph exceeds the reader's context
budget; the primary condition keeps whole paragraphs to preserve multi-hop evidence.

**Retrieval ceiling.** BM25 over 10 paragraphs is a weak retriever for multi-hop questions.
The condition is a stress test, not a leaderboard entry. Report recall@k and the
supporting-fact recall separately.

**Known biases.** The distractor set is constructed, not natural; the 8 distractors are
often topically related, which may overstate distraction relative to a real corpus. The
multi-hop annotation is human-generated and not error-free.

## 4. Processing and splits

- Normalization: lowercase, strip punctuation and articles, collapse whitespace.
- Chunking: whitespace tokens, 70 words, no overlap (SQuAD); whole paragraphs (HotpotQA).
- Seed: `20261115` for sampling and for the deterministic policy split.
- Policy split: 600 train / 200 validation / 200 test by SHA-256 of `seed:question_id`.
- No test-set tuning. The test split is evaluated once.
- Raw and processed text live in `data/raw/` and `data/processed/`, both git-ignored.

## 5. Privacy and PII

Both datasets are public research corpora of Wikipedia-derived text. They are not expected to
contain personal data, but they are not audited for PII here. Do not add private queries,
user logs, or scraped personal data to this repository. If a downstream use requires PII
screening, do it before preparation and document it.

## 6. Licensing and redistribution

Both datasets are CC BY-SA 4.0. Their licenses remain in force. This repository releases
dataset IDs, versions, checksums, sampling seeds, configs, prompts, predictions, and aggregate
statistics. It does **not** redistribute raw question or context text. See
[`../DATA_LICENSE.md`](../DATA_LICENSE.md).

## 7. Limits

- One closed corpus and one multi-hop distractor set; no open-domain NQ or fullwiki run.
- BM25 only in the primary condition; no dense retriever.
- English only.
- One 4B reader and one 1.5B replication reader; no frontier model.
- SQuAD is saturated for strong readers; the pilot's 4B reader is the binding constraint.
- The energy measurements are from one laptop GPU, not a datacenter.

## 8. Manifest fields

`data/manifest.json` records, per dataset: `id`, `name`, `version`, `split`, `source_url`,
`upstream_license`, `citation`, `n_questions_total`, `n_questions_used`, `corpus`, `checksums`
(questions and corpus SHA-256), `prepared_utc`, `preparation_seed`, `status`, and `notes`.
The file is a placeholder until preparation; `null` means "not yet computed", never "zero".

## 9. Maintenance

The data card is updated when a dataset version, sampling seed, chunk size, or license
changes. Any change after the prereg freeze is an amendment. Contact:
**atikurrahaman0305@gmail.com**.
