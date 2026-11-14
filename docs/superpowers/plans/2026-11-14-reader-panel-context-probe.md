# Reader Panel + Context Probe Implementation Plan

> **For agentic workers:** use `superpowers:executing-plans` for this plan. Steps use checkbox (`- [ ]`) syntax for tracking. Do not download model weights or run experiments as part of this plan.

**Goal:** Add a third exploratory reader (Llama 3.2 3B Instruct), a 16k context-budget probe, and the related configs/docs/slides without changing H1–H7, G5, the 5 pp primary decision, or the claim boundary.

**Architecture:** The third reader is config-only: use Ollama with a Q4 Llama model, not a new HF backend. The 16k probe uses Qwen3.5-4B because quantized Llama 3.2 lightweight models cap at 8k context. New run TOMLs are self-contained, following the existing `squad_qwen15b.toml` pattern. The existing boundary probe gets a context fix. All new arms are exploratory/diagnostic and are mirrored in the prereg draft, docs, web data, and the 12-slide deck.

**Tech Stack:** Python 3.12 stdlib config validation and pytest; TOML configs; Next.js 16 / React 19 / Tailwind 4; Markdown docs.

**Spec:** This plan and the approved design in the conversation. The source of truth for claims remains `README.md`, `ROADMAP.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/MEASUREMENT.md`, and `prereg/PREREGISTRATION.md`.

## Global constraints

- **H7 and G5 do not change.** H7 remains Qwen2.5-1.5B-Instruct or HotpotQA. Llama 3.2 3B does not satisfy H7 or G5.
- **Llama is exploratory.** No gate, no certification, no promotion after outcomes are seen. Report it reader-conditionally.
- **The 16k arm is diagnostic.** At 70 words/passage, `k ≤ 64` is roughly 6k tokens, not a 16k-token prompt. Call it a context-budget/truncation probe, not a 16k saturation test.
- **No H200 energy claim.** The H200 MIG slice reports `power.draw = N/A`; H200 is optional accuracy-only and not run in this plan.
- **Do not fabricate results.** No new scores, deltas, or completed-run claims. New arms are planned/exploratory.
- **Do not download models.** No `ollama pull`, no HF download, no weight files in git.
- **Fixed values:** Llama `llama3.2:3b`, `Q4_K_M`, `4096` context, 500 SQuAD IDs, 7 depths. Context probe: Qwen3.5-4B Q4, 200 boundary IDs, `k ∈ {32,48,64}`, `num_ctx=16384`, plus a `k=32 @ 4096` control; require 100% GPU residency. Budget addition: ~1.2–1.7 GPU-hours; total ~12.7–14.7 of 15–20.
- **Deck stays 12 slides.** No new slide.
- **No server identifiers** in the repo beyond the already-approved `uiu-h200` alias and hardware facts.

## File map

- Configs: `configs/grid/boundary_k3.toml` (edit), `configs/runs/squad_llama3b_p2.toml` (new), `configs/runs/squad_qwen4b_ctx16k_p2.toml` (new), `configs/runs/squad_qwen4b_ctx4k_p2.toml` (new).
- Validation: `src/rag_energy/config.py`, `tests/test_config.py`.
- Prereg: `prereg/PREREGISTRATION.md`, `prereg/analysis_plan.md`.
- Project docs: `README.md`, `ROADMAP.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/MEASUREMENT.md`, `docs/PROTOCOL.md`, `docs/DATA_CARD.md`, `docs/RISKS.md`, `docs/DECISIONS.md`, `docs/proposal.md`, `docs/presentation.md`, `AGENTS.md`.
- Web: `web/lib/project-data.ts`, `web/components/slides/slides.tsx`, `web/app/(site)/page.tsx`, `web/app/(site)/method/page.tsx`, `web/app/(site)/research/page.tsx`, `web/app/(site)/roadmap/page.tsx`, `web/app/(site)/about/page.tsx`, `web/README.md`.
- Verification: `python -m rag_energy.cli validate`, `pytest -q`, `pnpm typecheck`, `pnpm lint`, `pnpm build`, slide screenshots.

---

### Task 1: Configs for the reader panel and context probe

**Files:**
- Modify: `configs/grid/boundary_k3.toml`
- Create: `configs/runs/squad_llama3b_p2.toml`
- Create: `configs/runs/squad_qwen4b_ctx16k_p2.toml` (Qwen3.5-4B)
- Create: `configs/runs/squad_qwen4b_ctx4k_p2.toml` (Qwen3.5-4B control)

**Interfaces:**
- Produces run IDs `squad_llama3b_p2`, `squad_qwen4b_ctx16k_p2`, `squad_qwen4b_ctx4k_p2`.
- The Llama run uses the same 500 SQuAD IDs as `squad_qwen15b_p2` (same seed, same n).
- The context probe reuses the 200 boundary IDs; the control is `k=32` at 4096.

- [ ] **Step 1: Fix the existing boundary context budget**

Edit `configs/grid/boundary_k3.toml` after `[retrieval]`:

```toml
[reader]
num_ctx = 8192
```

Add a note: `k=64` at 70-word passages needs ~6k tokens; 4096 would truncate. Keep `top_k=64`.

- [ ] **Step 2: Add the Llama exploratory run**

Create `configs/runs/squad_llama3b_p2.toml`:

```toml
# Exploratory third reader: Llama 3.2 3B Instruct Q4.
# Same 500 SQuAD IDs as squad_qwen15b_p2; not part of H7 or G5.
schema_version = 1
kind = "run"
run_id = "squad_llama3b_p2"
dataset = "squad"
dataset_version = "v1.1"
split = "dev"
n_questions = 500
k_grid = [0, 1, 2, 4, 8, 16, 32]
seed = 20261115
phase = "P2"

[reader]
backend = "ollama"
model = "llama3.2:3b"
quantization = "Q4_K_M"
num_ctx = 4096
num_predict = 24
temperature = 0.0
top_k = 1
seed = 42
think = false

[retrieval]
backend = "bm25"
top_k = 32
chunking = "word"
passage_words = 70
tokenizer = "lowercase_alnum"

[energy]
sampler = "nvml"
sample_interval_ms = 100
idle_baseline_s = 60
block_size = 20
warmup_queries = 20
nonce_hex_chars = 10
cpu_retrieval_proxy_watts = 20.0

[scoring]
primary = "normalized_em"
secondary = ["lenient_span", "token_f1_ge_0.5"]

[output]
dir = "runs"
raw_csv = "raw.csv"
blocks_json = "blocks.json"

[notes]
purpose = "Exploratory reader-family robustness; same 500 IDs as the 1.5B replication."
claim_status = "exploratory"
```

- [ ] **Step 3: Add the 16k context-budget probe**

Create `configs/runs/squad_qwen4b_ctx16k_p2.toml`:

- `run_id="squad_qwen4b_ctx16k_p2"`, `n_questions=200`, `k_grid=[32,48,64]`, `phase="P2"`.
- Reader: Ollama, `qwen3.5:4b`, `Q4`, `num_ctx=16384`, same decoding.
- Retrieval: `top_k=64`.
- Energy/scoring/output: same as the primary Qwen run.
- Hard gate: `ollama ps` must report 100% GPU and >300 MB VRAM headroom; CPU offload voids the arm.
- Notes: `purpose="Context-budget and truncation probe; not a 16k-token prompt."`, `claim_status="diagnostic"`.

- [ ] **Step 4: Add the 4k control**

Create `configs/runs/squad_qwen4b_ctx4k_p2.toml` with:

- `run_id="squad_qwen4b_ctx4k_p2"`, `n_questions=200`, `k_grid=[32]`, `phase="P2"`.
- Reader: Qwen3.5-4B, `num_ctx=4096`.
- Retrieval: `top_k=64`.
- Notes: `purpose="4k control for the context-budget probe."`, `claim_status="diagnostic"`.

- [ ] **Step 5: Run config validation**

Run: `python -m rag_energy.cli validate`
Expected: PASS; all TOML files parse. Do not run the experiments or download models.

- [ ] **Step 6: Commit**

```bash
git add configs/grid/boundary_k3.toml configs/runs/squad_llama3b_p2.toml configs/runs/squad_qwen4b_ctx16k_p2.toml configs/runs/squad_qwen4b_ctx4k_p2.toml
git commit -m "exp: add exploratory llama reader and context probe configs"
```

---

### Task 2: Config validation and tests

**Files:**
- Modify: `src/rag_energy/config.py`
- Modify: `tests/test_config.py`

**Interfaces:**
- `validate_config` now rejects unknown reader backends, empty model names, non-positive `num_ctx`, and `retrieval.top_k < max(k_grid)`.

- [ ] **Step 1: Write failing tests**

Add tests in `tests/test_config.py` using a temporary run config:

1. `test_run_rejects_unknown_reader_backend` — backend `"vllm"` → error.
2. `test_run_rejects_empty_reader_model` — model `""` → error.
3. `test_run_rejects_nonpositive_num_ctx` — `num_ctx=0` → error.
4. `test_run_rejects_top_k_below_max_depth` — `k_grid=[32,48,64]`, `top_k=32` → error.
5. `test_run_accepts_llama_panel_shape` — `top_k=32`, `k_grid` max 32, `num_ctx=4096` → no errors.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -q`
Expected: the new tests fail because the checks do not exist.

- [ ] **Step 3: Implement validation**

In `validate_config`, for `category in {"run","grid"}`:

- If `reader` is a dict:
  - `backend` must be `"ollama"` or `"hf"` when present.
  - `model` must be a non-empty string when present.
  - `num_ctx` must be a positive integer when present.
- If `retrieval` is a dict with `top_k` and `k_grid` exists:
  - `top_k` must be a positive integer.
  - `top_k >= max(k_grid)`; otherwise report the exact values.

Do not reject missing optional keys in grid overrides.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_config.py -q`
Expected: PASS.

- [ ] **Step 5: Run the full smoke suite**

Run: `pytest -q`
Expected: PASS without numpy/pandas/torch/GPU.

- [ ] **Step 6: Commit**

```bash
git add src/rag_energy/config.py tests/test_config.py
git commit -m "fix: validate reader and retrieval configuration"
```

---

### Task 3: Prereg, analysis plan, and decision records

**Files:**
- Modify: `prereg/PREREGISTRATION.md`
- Modify: `prereg/analysis_plan.md`
- Modify: `docs/DECISIONS.md`
- Modify: `docs/RISKS.md`
- Modify: `docs/MEASUREMENT.md`
- Modify: `docs/DATA_CARD.md`
- Modify: `docs/PROTOCOL.md`

**Interfaces:**
- H7/G5 remain unchanged.
- New exploratory labels are consistent across all documents.

- [ ] **Step 1: Add the exploratory arms to the prereg**

In `prereg/PREREGISTRATION.md` after H7:

- Add an **Exploratory arms (not hypotheses)** subsection.
- Reader panel: Llama 3.2 3B Instruct, SQuAD, same 500 IDs, 7 depths, 4k, Q4, direction-only, no gate.
- Context-budget probe: Qwen3.5-4B Q4, 200 boundary IDs, `k=32/48/64`, `num_ctx=16384`, `k=32@4096` control; diagnostic, not a new `k*`; 100% GPU residency required.
- H200 64k: optional accuracy-only; no energy; not pooled; not run.
- State explicitly: H7 remains 1.5B or HotpotQA; G5 unchanged; the third reader does not satisfy H7/G5.

- [ ] **Step 2: Add the analysis rules**

In `prereg/analysis_plan.md`, add `## 16. Exploratory reader and context-budget analyses` with:

- Saturation rule: if `A(32) ≥ 0.90` or `max |A(k) − A(32)| ≤ 1 pp` for `k ≥ 4`, label the accuracy arm uninformative and report only the energy slope.
- Truncation rule: invalidate a row if `prompt_tokens + num_predict > num_ctx`.
- Recall rule: report `recall@k` and gold-answer-in-context at every depth.
- Context control: compare `k=32 @ 16384` with `k=32 @ 4096`; report the delta as a context-budget effect, not a new `k*`.
- Cross-hardware rule: report H200 accuracy separately; never pool with 3060 energy.
- No reader selection: report all readers in one table; no promotion after outcomes.

- [ ] **Step 3: Add decision entries**

In `docs/DECISIONS.md`, add:

- `D-012 — Third reader is exploratory`: Llama 3.2 3B, Ollama Q4, 500 paired IDs; H7/G5 unchanged; no gate.
- `D-013 — Boundary context fix and context-budget probe`: boundary grid `num_ctx=8192`; 16k probe is diagnostic; H200 accuracy-only, no energy.

- [ ] **Step 4: Update risks**

In `docs/RISKS.md`, update R2/R11 and add:

- R15 model shopping / multiple readers.
- R16 16k OOM or CPU offload.
- R17 cross-hardware accuracy divergence.
- R18 Llama license/model-store growth.

- [ ] **Step 5: Update measurement, data card, protocol**

- `docs/MEASUREMENT.md`: add a no-energy-on-MIG clause and a context-budget/truncation note.
- `docs/DATA_CARD.md`: add Llama 3.2 3B, Q4, 4k, Llama 3.2 Community License; state weights are not redistributed; update limits and SQuAD counts.
- `docs/PROTOCOL.md`: add the exploratory reader and context rows; add preflight checks for `num_ctx`, prompt tokens, CPU offload, and H200 power `N/A`.

- [ ] **Step 6: Commit**

```bash
git add prereg/PREREGISTRATION.md prereg/analysis_plan.md docs/DECISIONS.md docs/RISKS.md docs/MEASUREMENT.md docs/DATA_CARD.md docs/PROTOCOL.md
git commit -m "docs: record exploratory reader and context probe"
```

---

### Task 4: README, roadmap, implementation plan, proposal, AGENTS

**Files:**
- Modify: `README.md`
- Modify: `ROADMAP.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`
- Modify: `docs/proposal.md`
- Modify: `AGENTS.md`

**Interfaces:**
- The public claim boundary stays unchanged; new arms are labeled exploratory/diagnostic.
- No H200 energy claim; no universal `k*`.

- [ ] **Step 1: README**

- Add a third-reader row: Llama 3.2 3B, SQuAD 500, 7 depths, 4k, Q4, exploratory.
- Add a context-budget row: 200 boundary IDs, `k=32/48/64`, 16k budget + 4k control, diagnostic.
- Change the boundary row from “16k-token context check” to “8k context budget for k=64; separate 16k context-budget probe.”
- Add H200 optional accuracy-only row, status “not run; no energy claim.”
- Add one claim-boundary sentence: third reader and context probe are exploratory; H7/G5 unchanged; H200 no energy.
- Update budget note: +1.2–1.7 local GPU-hours; total ~12.7–14.7 of 15–20.

- [ ] **Step 2: ROADMAP**

- P2 outputs: add Llama 3B 500, context probe 200, optional H200 accuracy-only.
- P2 goal/detail: two replication readers, not a “second reader”; boundary 8k, context probe 16k budget.
- R2/R11 mitigation; out-of-scope: no H200 energy claim; budget note.
- G5/H7 unchanged.

- [ ] **Step 3: IMPLEMENTATION_PLAN**

- §3 environment: add Llama 3B Q4 via Ollama; H200 accuracy-only.
- §5: add the reader panel and context probe; preserve 1,000/500/500/200 counts.
- §7/§10/§12/§14: add context, identity, G5, and risk notes.
- §6: H7 unchanged.

- [ ] **Step 4: proposal**

- §8 readers: add Llama 3B exploratory.
- §9 measurement: context-budget caveat.
- §10/§12: exploratory analysis; no H7/G5 change.
- §13 budget/fallback.
- §19 data/tools: add Llama 3.2 3B model card and license.
- §18 glossary: add “context budget.”

- [ ] **Step 5: AGENTS**

- Add Llama 3.2 3B Q4 as exploratory third reader; 16k context probe diagnostic; H200 accuracy-only.
- Do not add host/user/password. Keep the existing server rules.

- [ ] **Step 6: Commit**

```bash
git add README.md ROADMAP.md docs/IMPLEMENTATION_PLAN.md docs/proposal.md AGENTS.md
git commit -m "docs: add exploratory reader panel and context probe"
```

---

### Task 5: Web data, pages, slides, and Bangla script

**Files:**
- Modify: `web/lib/project-data.ts`
- Modify: `web/components/slides/slides.tsx`
- Modify: `web/app/(site)/page.tsx`
- Modify: `web/app/(site)/method/page.tsx`
- Modify: `web/app/(site)/research/page.tsx`
- Modify: `web/app/(site)/roadmap/page.tsx`
- Modify: `web/app/(site)/about/page.tsx`
- Modify: `web/README.md`
- Modify: `docs/presentation.md`

**Interfaces:**
- Data fields `rerun.readerPanel`, `rerun.contextProbe`, `rerun.optionalH200` feed the slides and pages.
- H7 and G5 strings remain unchanged.

- [ ] **Step 1: Extend `project-data.ts`**

Add to `rerun`:

- `readerPanel`: n 500, reader Llama 3.2 3B, quantization Q4_K_M, context 4096, depths 7, status exploratory, same 500 IDs.
- `contextProbe`: n 200, reader Qwen3.5-4B, context 16384, control 4096, depths 32/48/64, hardware RTX 3060, status diagnostic, 100% GPU residency required.
- `optionalH200`: H200 MIG 1g.18gb, 18 GB, 64k, accuracy-only, energyClaim false, status optional/not run.

Update `boundary.contextCheck` to “8k context budget for k=64”; keep the 16k probe separate. Update `datasets.limits`, P2 outputs, R2, R11, budget note, `project.updated=2026-11-14`, and `claimBoundary.notClaimed` with the H200 no-energy sentence. Do not change H7/G5.

- [ ] **Step 2: Update the deck**

- Slide 5: `Runs: 1,000 primary · 2 × 500 replication · 200 boundary`.
- Slide 8 Runs card: merge to 5 bullets:
  - `SQuAD primary (4B): 1,000 × 7 depths`
  - `Replication: 500 × 7 each — Qwen2.5-1.5B, Llama 3.2 3B`
  - `HotpotQA: 500 × 6`
  - `Boundary: 200 × 3 + 16k context check`
  - `Taxes: 150 × 2 · policy: 600/200/200`
- Slide 8 callout: `15–20 local GPU hours · RTX 3060 6 GB · optional H200 64k: accuracy-only, no energy`.
- Slide 9 G5 remains unchanged.
- Slide 10 H7: keep H7 1.5B/HotpotQA; add `Exploratory: Llama 3.2 3B; no gate.`
- Slide 11: `Reader strength, context limits, and one dataset.`
- Keep slides 1–7, 9, 12 structurally unchanged.

- [ ] **Step 3: Update pages**

- Home: reader card `2 × 500`, detail includes Qwen2.5-1.5B + Llama 3.2 3B; boundary card uses context probe; fix 15-slide labels to 12.
- Method: `500 per replication reader`; add context probe note.
- Research: `one laptop GPU, plus an optional accuracy-only H200 check with no energy claim`.
- Roadmap: budget title/description; out-of-scope only H200 **energy**; P2 data comes from project-data.
- About: 12-slide label; claim policy includes H200 no-energy sentence.
- `web/README.md`: claim boundary update.

- [ ] **Step 4: Update `docs/presentation.md`**

- Slide 8 speech: mention Llama 3.2 3B exploratory and 16k context-budget probe.
- Slide 10 speech: H7 stays 1.5B/HotpotQA; Llama is exploratory.
- Add Q&A:
  1. Why Llama 3.2 3B?
  2. Does Llama satisfy H7?
  3. What is the 16k probe?
  4. Can we use H200?
  5. Why not many models?
- Add a short model note (Llama 3.2 3B, Q4, 4096; Llama 3.2 Community License). Do not add a new numbered reference.

- [ ] **Step 5: Build and inspect**

Run:

```bash
pnpm typecheck
pnpm lint
pnpm build
```

Take screenshots of slides 5, 8, 9, 10, 11 at 1280×720. Check slide 8 for clipping; reduce bullet size from 2.1cqh to 1.95cqh only if needed.

- [ ] **Step 6: Commit**

```bash
git add web/lib/project-data.ts web/components/slides/slides.tsx web/app/(site)/page.tsx web/app/(site)/method/page.tsx web/app/(site)/research/page.tsx web/app/(site)/roadmap/page.tsx web/app/(site)/about/page.tsx web/README.md docs/presentation.md
git commit -m "feat: add exploratory reader panel and context probe to deck"
```

---

### Task 6: Final verification and deployment

- [ ] Run `python -m rag_energy.cli validate`
- [ ] Run `pytest -q`
- [ ] Run `pnpm typecheck`
- [ ] Run `pnpm lint`
- [ ] Run `pnpm build`
- [ ] Run `git diff --check`
- [ ] Confirm no model weights, raw data, credentials, or server identifiers are staged.
- [ ] Commit any remaining changes.
- [ ] Push `main`.
- [ ] Verify Vercel production deployment is `READY`.
- [ ] Verify the live slides at `/slide?slide=8` and `/slide?slide=10`.

## Review Focus

- **Slide 8 overflow:** five run bullets plus a longer callout can clip. Screenshot and reduce font only if needed.
- **H7/G5 drift:** ensure no page or slide silently adds Llama to H7/G5. Search for `H7`, `G5`, `Qwen2.5-1.5B`, `replication`.
- **Context wording:** never call the `k≤64` arm a “16k-token prompt.” Use “16k context budget / truncation probe.”
- **H200 energy:** no page, table, or script may show H200 joules or `E(k)`.
- **Config validity:** `boundary_k3` must have `num_ctx=8192`; every run must have `top_k >= max(k_grid)`.
- **No fabricated results:** new arms are `planned`, `exploratory`, or `diagnostic` until a registered raw CSV exists.
