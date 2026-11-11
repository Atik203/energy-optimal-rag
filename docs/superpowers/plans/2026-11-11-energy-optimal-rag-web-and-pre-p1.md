# Energy-Optimal RAG Website + Pre-P1 Hardening Plan

> **For agentic workers:** use subagent-driven execution. The frontend is one
> independent workstream under `web/`. The pre-P1 hardening work is split into
> four non-overlapping file sets: power, tests, configs, and docs/evidence.

**Goal:** Ship a public research website for `energy-optimal-rag` — a home page,
research/method/pilot/roadmap/about pages, and a keyboard-driven slides deck —
while fixing the highest-value pre-P1 inconsistencies found in the project audit.

**Architecture:** A self-contained Next.js 16 App Router app in `web/`, using
React 19, Tailwind 4, local OFL fonts, and pure SVG/CSS data visuals. The site
content lives in one typed `lib/project-data.ts` module so numbers are not
scattered across pages. The deck reuses the reference site's presenter mechanics
(keyboard navigation, deep links, fullscreen, 16:9) but has its own visual system
and content.

**Tech stack:** Next.js 16.4.6, React 19.3.1, Tailwind CSS 4.3.5,
TypeScript 5.9.3, `lucide-react` 0.475.0, `clsx`, `tailwind-merge`. All packages
are already present in the reference project's pnpm store.

**Reference:** `G:\PROJECT\tool-observation\web` (read-only). Do not modify it.

**Spec sources for content:** `README.md`, `ROADMAP.md`,
`docs/IMPLEMENTATION_PLAN.md`, `docs/MEASUREMENT.md`,
`prereg/PREREGISTRATION.md`, `docs/DATA_CARD.md`, `docs/RISKS.md`,
`docs/DECISIONS.md`, `docs/proposal.md`.

---

## Global constraints

- **Claim boundary is non-negotiable.** The site must say: post-pilot MARGINAL,
  public scaffold, no confirmatory results, prereg not frozen.
- Every pilot number is labeled **pilot**. The 2 pp static claim is **DEAD**.
  The 5 pp result is a **pilot signal, not certified**. The 78.8% oracle gain is
  an **upper bound**, not a learned-policy result.
- No universal `k*`; no "2 pp optimal"; no "5 pp certified"; no carbon-optimal
  claim; no generalization to frontier readers, dense retrievers, or full NQ.
- Do not invent numbers, confidence intervals, p-values, run IDs, or dataset
  sizes. Use only values present in the source docs. If a value is missing, omit
  it or mark it `TBD`.
- Do not commit raw SQuAD/HotpotQA text, model weights, run CSVs, or secrets.
- **No network install.** Use:
  `pnpm install --offline --frozen-lockfile --ignore-scripts --store-dir "G:\.pnpm-store\v11"`
  from `web/`. If it fails, stop and report; do not fall back to an online install.
- Keep the site self-contained: no runtime API calls, analytics, or external
  image/font requests.
- Accessibility: semantic landmarks, skip link, visible focus, keyboard deck
  controls, reduced-motion support, responsive layouts, alt/aria text for visuals.

---

## File ownership

| Workstream | Owns | Must not touch |
|---|---|---|
| Frontend | `web/**` | everything outside `web/` |
| Power fix | `src/rag_energy/stats/power.py`, `scripts/06_power.py`, `tests/test_power.py` | other files |
| Core tests | `tests/test_scoring.py`, `tests/test_stats_core.py`, `tests/test_energy.py`, `tests/test_data.py`, `tests/test_retrieval.py` | production code |
| Configs | `configs/grid/boundary_k3.toml`, `configs/runs/hotpot_qwen4b.toml`, `configs/runs/squad_qwen4b.toml`, `configs/runs/squad_qwen15b.toml`, `src/rag_energy/data/prep_hotpot.py`, `environment.yml`, `pyproject.toml`, `configs/analysis/prereg.toml`, `src/rag_energy/config.py`, `tests/test_config.py` | docs, README, prereg |
| Docs/evidence | `README.md`, `ROADMAP.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/PROTOCOL.md`, `docs/proposal.md`, `docs/DECISIONS.md`, `docs/PILOT_EVIDENCE.md`, `prereg/PREREGISTRATION.md`, `prereg/analysis_plan.md`, `artifacts/claims_evidence.csv`, `artifacts/ledger.csv`, `CHANGELOG.md` | code, configs |

---

## Task 1 — Frontend scaffold and design system

**Files:** `web/package.json`, `web/pnpm-lock.yaml`, `web/pnpm-workspace.yaml`,
`web/.npmrc`, `web/next.config.ts`, `web/tsconfig.json`,
`web/postcss.config.mjs`, `web/eslint.config.mjs`, `web/.gitignore`,
`web/app/layout.tsx`, `web/app/globals.css`, `web/app/icon.svg`,
`web/app/fonts/*`, `web/lib/cn.ts`, `web/lib/project-data.ts`,
`web/components/site-header.tsx`, `web/components/site-footer.tsx`,
`web/components/theme-toggle.tsx`, `web/components/section-heading.tsx`.

- [ ] Copy the reference `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`,
      `.npmrc`, `next.config.ts`, `tsconfig.json`, `postcss.config.mjs`, and
      `eslint.config.mjs` into `web/`. Rename the package to
      `energy-optimal-rag-web`; keep dependency versions identical so the
      lockfile stays valid. Add `typecheck: "tsc --noEmit"`.
- [ ] Copy the six OFL `.woff2` files from the reference `app/fonts/` into
      `web/app/fonts/`; keep the font attribution in `web/README.md`.
- [ ] Install offline with the command above. Verify `node_modules` exists.
- [ ] Build the design tokens in `app/globals.css`: dark-first "energy
      observatory" palette (deep green-black, phosphor lime, teal, amber, rose),
      light theme, glass panels, grid/oscilloscope utilities, display serif,
      mono numerals, reduced-motion rules.
- [ ] Add the root layout with local fonts, metadata, theme bootstrap script,
      skip link, and `suppressHydrationWarning`.
- [ ] Add a typed `lib/project-data.ts` with all site content and source
      comments. No number may appear in a page without a source note.
- [ ] Add the header (sticky, active nav, GitHub link, theme toggle, mobile
      menu), footer, and shared section-heading/metric components.

**Acceptance:** `pnpm typecheck` passes; the shell renders in both themes.

---

## Task 2 — Site pages

**Files:** `web/app/(site)/layout.tsx`, `web/app/(site)/page.tsx`,
`web/app/(site)/research/page.tsx`, `web/app/(site)/method/page.tsx`,
`web/app/(site)/results/page.tsx`, `web/app/(site)/roadmap/page.tsx`,
`web/app/(site)/about/page.tsx`, plus page-local components.

- [ ] **Home `/`** — hero with `E(k)=ΣJ/ΣC`; pilot metric strip
      (`3.45×`, `85.1%`, `P=.61 → DEAD`, `69.3% pilot signal`); the question;
      survived/died board; powered rerun design cards; claim-boundary callout;
      slides CTA.
- [ ] **Research `/research`** — estimand; H1–H7 table; primary 5 pp test and
      2 pp estimation-only note; theory cards (identity, static-depth price,
      `N*`); K1–K7 and G1–G5 gates; prior-work positioning.
- [ ] **Method `/method`** — pipeline strip; `J_k = J_ret + J_pre + J_dec +
      J_fix`; NVML 100 ms caveat, idle, 20-query blocks, nonce/prefix-cache
      control, thermal log, repeat CV, wall meter, CPU proxy; SQuAD and
      HotpotQA data cards; scoring rules; policy split; energy-tax design.
- [ ] **Pilot `/results`** — pilot setup; full pilot table with every value
      labeled pilot; SVG energy-fit chart (`J=15.74+2.283k`); context-share
      bars; documented accuracy points; identity gaps; "what survived / what
      died" board; explicit "no confirmatory results" banner.
- [ ] **Roadmap `/roadmap`** — P0–P6 timeline; gates; budget (`≤$47`);
      deliverables; top risks; decision-log highlights.
- [ ] **About `/about`** — status, author, citation, licenses, data policy,
      evidence policy, repository/docs links, site map.
- [ ] Every page: breadcrumb/eyebrow, `SectionHeading`, responsive grids,
      accessible headings, no claim-boundary drift.

**Acceptance:** all routes render; no horizontal overflow at 360 px; every pilot
number is visibly labeled pilot or upper bound.

---

## Task 3 — Slides page

**Files:** `web/app/(present)/layout.tsx`, `web/app/(present)/slide/page.tsx`,
`web/components/slides/deck.tsx`, `web/components/slides/primitives.tsx`,
`web/components/slides/slides.tsx`.

- [ ] 15-slide deck: title; the decision; pilot setup; energy curve; accuracy
      and the dead 2 pp claim; what survives; the 5 pp signal; powered rerun;
      measurement; data; theory; gates; policy + taxes; claim boundary; thank
      you.
- [ ] Keyboard: ←/→, PageUp/PageDown, Space, Home/End, F fullscreen.
      Deep link `?slide=N`; progress bar; slide counter; 16:9 projector-safe
      light deck with dark text and lime/teal/amber accents.
- [ ] No slide may claim a confirmatory result. The 5 pp slide says "pilot
      signal, not certified" and reports `P=.537` with a caveat.
- [ ] `robots: { index: false }` on the slides route.

**Acceptance:** deck navigates by keyboard, deep links work, fullscreen works,
and the deck fits a 16:9 viewport without clipping.

---

## Task 4 — Frontend verification

- [ ] `pnpm typecheck`
- [ ] `pnpm lint`
- [ ] `pnpm build`
- [ ] `pnpm start` + `curl` each route for HTTP 200.
- [ ] Optionally run `pnpm dev` and capture a screenshot of `/`, `/results`, and
      `/slide?slide=4` with the browser tool.

---

## Task 5 — Power fix

**Files:** `src/rag_energy/stats/power.py`, `scripts/06_power.py`,
`tests/test_power.py`.

- [ ] Change the planning discordant rate to `0.08` in the `06_power.py` default
      and in the `power.py` docstring. Remove the stale `0.145`/`1.2 pp` claim.
- [ ] Add tests that pin the documented table:
      `MDE(200) ≈ 4.97 pp`, `MDE(1000) ≈ 2.22 pp`,
      `power(1000, 0) > .99`, `power(1000, .03) ≈ .72`.
- [ ] Verify `python scripts/06_power.py` prints
      `Assumed discordant rate = 0.080`.

---

## Task 6 — Core unit tests

**Files:** `tests/test_scoring.py`, `tests/test_stats_core.py`,
`tests/test_energy.py`, `tests/test_data.py`, `tests/test_retrieval.py`.

- [ ] Stdlib-only tests, no numpy/pandas/torch/GPU.
- [ ] Cover: scoring normalization/EM/lenient/F1; ratio estimand and delta
      variance; affine fit; elasticity/identity gap; Holm; trapezoid/idle/blocks/
      meter/nonce; chunking/splits/manifest; BM25 features/proxy energy.
- [ ] Run `pytest -q` and confirm the new tests pass.

---

## Task 7 — Config and environment fixes

**Files:** `configs/grid/boundary_k3.toml`,
`configs/runs/hotpot_qwen4b.toml`, `configs/runs/squad_qwen4b.toml`,
`configs/runs/squad_qwen15b.toml`, `src/rag_energy/data/prep_hotpot.py`,
`environment.yml`, `pyproject.toml`, `configs/analysis/prereg.toml`,
`src/rag_energy/config.py`, `tests/test_config.py`.

- [ ] Boundary probe: add `retrieval.top_k = 64`; the base run is top-32.
- [ ] HotpotQA: make whole-paragraph retrieval explicit
      (`chunking = "whole_paragraph"`; `passage_words = 0` or omit), and update
      the `prep_hotpot` contract to match. SQuAD stays `chunking = "word"`.
- [ ] HF replication: add an optional `hf` extra (`torch`, `transformers`) and
      document that the base environment does not install it.
- [ ] Analysis config: add `n_questions = 1000` and validate the policy split
      sum against it instead of a hard-coded 1000.
- [ ] Add `tests/test_config.py` for the split-sum validation.
- [ ] Run `python -m rag_energy.cli validate`.

---

## Task 8 — Docs, prereg, and evidence alignment

**Files:** `README.md`, `ROADMAP.md`, `docs/IMPLEMENTATION_PLAN.md`,
`docs/PROTOCOL.md`, `docs/proposal.md`, `docs/DECISIONS.md`,
`docs/PILOT_EVIDENCE.md`, `prereg/PREREGISTRATION.md`,
`prereg/analysis_plan.md`, `artifacts/claims_evidence.csv`,
`artifacts/ledger.csv`, `CHANGELOG.md`.

- [ ] **Population/failure rule.** Adopt one rule everywhere:
      descriptive statistics use every question with a valid row at that depth;
      a failed or empty generation is a wrong answer and is retained; a row is
      invalid only for a protocol violation (missing nonce, request failure,
      sampler error); the primary paired test uses questions with valid rows at
      both `k=4` and `k=32`; report all invalid counts and paired n.
      Update README, implementation plan, protocol, prereg, analysis plan, and
      proposal.
- [ ] **5 pp wording.** Replace "Pilot PASS" with "pilot signal, not certified";
      add `P=.537` and say the NI test and selection probability must be
      reported separately in the rerun. Do not imply G2 passed.
- [ ] **Split wording.** State that the 600/200/200 split is a target; hashed
      assignment can produce slightly different realized counts, which are
      reported. No test-set tuning.
- [ ] **Pilot evidence.** Create `docs/PILOT_EVIDENCE.md` with a table of every
      pilot claim, value, source, status, and the explicit statement that the
      pilot raw CSVs are not in this repository and the numbers are transcribed,
      not independently reproducible here.
- [ ] Populate `artifacts/claims_evidence.csv` with pilot rows
      (`run_id=pilot`, `artifact_path=docs/PILOT_EVIDENCE.md`, statuses
      `pilot`/`dead`/`upper_bound`). Add a ledger row for the new evidence file
      with a computed SHA-256 and byte count.
- [ ] Add D-009 (population/failure rule), D-010 (5 pp wording), and D-011
      (pilot provenance) to `docs/DECISIONS.md`.
- [ ] Add a short "Website" section to README pointing at `web/` and
      `web/README.md`.
- [ ] Update `CHANGELOG.md` under Unreleased.

---

## Task 9 — Integration verification

- [ ] `pytest -q` — all tests pass.
- [ ] `python -m rag_energy.cli validate` — all configs valid.
- [ ] `ruff check .` and `ruff format --check .` — clean.
- [ ] `pnpm typecheck`, `pnpm lint`, `pnpm build` in `web/` — clean.
- [ ] `git status` — confirm no raw data, model weights, secrets, or run CSVs.
- [ ] Review the claim boundary one final time against the rendered site.

---

## Review focus

1. **Claim drift on the site** — a headline or slide that says "optimal depth",
   "certified", or "learned policy gain" without the qualifier.
2. **Pilot numbers without provenance** — any number in `web/` not present in
   `lib/project-data.ts` with a source comment.
3. **Population inconsistency** — the same failure rule must appear in README,
   implementation plan, protocol, prereg, and analysis plan.
4. **Offline install** — a subagent accidentally running `pnpm install` without
   `--offline --store-dir`.
5. **Build-time network** — `next/font/google`, remote images, or runtime fetch.
