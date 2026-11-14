# Risk Register

**Status:** living document · reviewed at every phase gate · v0.1.0 · 2026-11-09
**Scoring:** likelihood and impact are Low / Medium / High. The owner is a role, not a person.

| ID | Risk | Likelihood | Impact | Mitigation | Trigger | Owner |
|---|---|---|---|---|---|---|
| R1 | **Strict EM vs lenient scoring** decides the green verdict | High | High | Pre-register EM primary; report lenient span and F1 ≥ 0.5; require the qualitative conclusion to survive all three; report the dependence if it does not | Primary and secondary rules disagree on whether an interior `k` is non-inferior | Analysis lead |
| R2 | **Reader strength / SQuAD saturation** flattens the accuracy curve | Medium | High | 1.5B replication; exploratory Llama 3B panel; 16k context probe; HotpotQA; report reader-conditional results; no universal claim | `A(k)` is within 1 pp for `k ≥ 2`, or the 1.5B/Llama readers reverse the direction | PI |
| R3 | **Single corpus / single retriever** limits external validity | High | Medium | HotpotQA distractor; report recall@k; state the boundary in every claim | Reviewers ask for NQ or a dense retriever and the paper has neither | PI |
| R4 | **Thermal throttling** changes the energy curve over the run | High | Medium | Randomize `k` within question; log temperature and clock; block calibration at steady state; sensitivity analysis excluding the first 50 queries | Clock falls below 50% of starting clock and stays there | Measurement lead |
| R5 | **NVML coarse resolution** makes per-query joules look more precise than they are | High | Medium | 20-query block calibration; repeat CV; wall-meter cross-check; report the sensor caveat in every table | Repeat CV > 10%, or block factors outside [0.8, 1.4] | Measurement lead |
| R6 | **Ollama prefix cache** confounds depth with request order | Medium | High | Unique 10-hex nonce per request; verify prefill times; invalidate rows without a nonce | Prefill time drops at a fixed depth after a shorter prefix | Harness lead |
| R7 | **Energy noise** swamps the effect | Medium | High | Idle subtraction; blocks; repeats; bootstrap; pre-registered MDE; wall meter | CV > 20% or MDE > observed effect (K7) | Measurement lead |
| R8 | **Adaptive policy overfitting** on 600 training questions | High | High | Strict 600/200/200 split; simple model; no test tuning; report learning curve; compare to a trivial feature-free policy | Test capture is far below validation capture | Policy lead |
| R9 | **Gate binding defeats the tax test** | Medium | High | Run taxes at a mid-accuracy gate as well as the primary gate; pre-register both; report gated and unconstrained optima | `k*` does not move because the accuracy constraint is active at both taxes | Theory lead |
| R10 | **Data licensing** violation from redistributing text | Low | High | No raw text in repo or releases; release IDs, checksums, predictions, aggregates only; CC BY-SA notice | A tracked file or release asset contains raw SQuAD/HotpotQA text | PI |
| R11 | **Schedule slip** on a 20-week plan | Medium | Medium | P6 buffer; drop the optional H200 check first, then the 16k probe or Llama 3B panel, before dropping the boundary probe or 1.5B replication; never drop the primary; weekly gate review | A phase misses its exit gate by more than one week | PI |
| R12 | **Scope creep** into a universal-`k*` or carbon paper | Medium | Medium | Claim boundary in README/ROADMAP; out-of-scope list; amendment required for a new claim | A draft sentence says "optimal depth" without a dataset/reader qualifier | PI |
| R13 | **Model or dependency drift** breaks reproduction | Medium | Medium | Lock file generated on target; model digest recorded; config hash in registry; clean-room reproduction in P6 | Golden reproduction differs by more than 10% at any depth | Harness lead |
| R14 | **Secret leak** in a commit or run log | Low | High | `.gitignore`, secret scan before each push, private reporting, no tokens in configs | A scan hit or a report | Maintainer |
| R15 | **Reader/model shopping** creates a false replication | Medium | High | Pre-specify the exploratory panel; report all readers in one table; no post-outcome promotion; H7/G5 unchanged | A reader is added or dropped after seeing its direction | PI |
| R16 | **16k context OOM or CPU offload** invalidates the probe | Medium | High | Require `ollama ps` 100% GPU and >300 MB headroom; record `prompt_tokens`; reject rows over `num_ctx`; report the hardware limit | Any CPU offload or prompt truncation | Measurement lead |
| R17 | **Cross-hardware divergence** is mistaken for replication | Medium | High | Keep H200 accuracy-only; report hardware class; never pool H200 with RTX 3060 energy | An H200 accuracy difference is described as an energy result | PI |
| R18 | **Llama license/model-store growth** | Low | Medium | Use the official gated Llama 3.2 Community License; do not redistribute weights; record the digest; keep Q4 under the local/200 GB limits | A weight file is staged or the license is called OSI open source | PI |

## Review cadence

- Weekly during P0–P1.
- At every phase gate P0–P6.
- Any new High/High risk is discussed before the next run starts.
- A closed risk stays in the table with a closing date; it is not deleted.

## Escalation

A risk that changes the claim boundary (R1, R2, R9, R12) is escalated to the PI before the
next analysis run. A risk that changes the data or license posture (R10, R14) is escalated
immediately and blocks the release.
