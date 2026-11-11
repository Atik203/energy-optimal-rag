# Energy Observatory — project website

A self-contained Next.js site for **Energy-Optimal Retrieval Depth in Retrieval-Augmented
Generation (G2)**: a measurement instrument for joules per correct answer.

**Research status: post-pilot MARGINAL.** This site contains **no confirmatory results**.
The preregistration is a draft until the P1 freeze. The pilot evidence is reported exactly as
measured, including the claim that failed.

## Claim boundary

- Every pilot number is labeled **pilot**.
- The static 2 pp claim is **DEAD**: `k* = 32` at the grid boundary, `P(k* optimal) = 0.61 < 0.8`.
- The 5 pp result at `k = 4` is a **pilot signal, not certified**.
- The 78.8% oracle gain is an **upper bound**, not a learned-policy result.
- No universal `k*`, no "2 pp optimal" depth, no "5 pp certified" result, no learned-policy
  gain, no carbon-optimal claim, and no generalization to frontier readers, dense retrievers, or
  full NQ.
- The site does not claim that any confirmatory experiment has been run.

All site facts and the numbers used on the site live in `lib/project-data.ts`, with source
documents named in comments. Fonts, copy, and data are local; the site makes no runtime API
calls, loads no remote images, and sets no analytics cookies.

## Run

```bash
pnpm dev
```

Open http://localhost:3000. The deck is at http://localhost:3000/slide (`?slide=N` deep-links
to a slide, 1-based). The deck is `robots: { index: false }`.

```bash
pnpm build
pnpm start
pnpm typecheck
pnpm lint
```

## Offline install

The packages and the pnpm store are already present on the development machine. Use the offline
command; do not run an online install.

```bash
pnpm install --offline --frozen-lockfile --ignore-scripts --store-dir "G:\.pnpm-store\v11"
```

Verified on this machine: 357 packages reused, 0 downloaded. The lockfile was copied unchanged
from the reference project so the store remains valid.

## Routes

| Route | Purpose |
|---|---|
| `/` | Hero, pilot metrics, question, survived/died ledger, rerun design, claim boundary, deck CTA |
| `/research` | Research question, estimand, H1–H7, theory, K/G gates, prior work |
| `/method` | Pipeline, energy decomposition, measurement controls, data, scoring, policy, taxes |
| `/results` | Pilot setup, energy fit, accuracy, context share, identity, full pilot table, 5 pp signal, oracle |
| `/roadmap` | P0–P6, gates, budget, deliverables, risks, decisions, stop rules |
| `/about` | Status, author, citation, licenses, data policy, evidence policy, links |
| `/slide` | 15-slide keyboard-driven 16:9 deck |

## Structure

- `app/(site)/` — public site routes with the shared header, footer, and skip link.
- `app/(present)/` — full-viewport presentation layout.
- `app/layout.tsx` — local fonts, metadata, theme bootstrap.
- `components/` — header, footer, theme toggle, charts, claim ledger, deck and slides.
- `lib/project-data.ts` — typed content and every number used on the site.
- `app/globals.css` — dark-first "energy observatory" tokens, light theme, grid/grain, deck styles.

## Fonts

Six OFL-licensed `.woff2` files are served locally from `app/fonts/` via `next/font/local`. No
font is requested from a third-party host at runtime.

- **Newsreader** — Copyright 2020 The Newsreader Project Authors
  (https://github.com/productiontype/Newsreader), SIL Open Font License 1.1.
- **Instrument Sans** — Copyright 2022 The Instrument Sans Project Authors
  (https://github.com/Instrument/instrument-sans), SIL Open Font License 1.1.
- **JetBrains Mono** — Copyright 2020 The JetBrains Mono Project Authors
  (https://github.com/JetBrains/JetBrainsMono), SIL Open Font License 1.1.

The font files were copied from the reference project's `app/fonts/` directory. Their OFL
licenses remain in force.

## Source documents

Content is transcribed from the repository record:

- `docs/PILOT_EVIDENCE.md`
- `README.md`
- `ROADMAP.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/MEASUREMENT.md`
- `docs/DATA_CARD.md`
- `docs/RISKS.md`
- `docs/DECISIONS.md`
- `docs/proposal.md`
- `prereg/PREREGISTRATION.md`

Pilot numbers are transcribed from `docs/PILOT_EVIDENCE.md` and the repository record; the pilot
raw CSVs are **not** in this repository. Where the record does not report a value, the site omits
it or marks it `TBD`. No confidence interval, p-value, run ID, or sample size has been invented.

## Licenses

- Site code: MIT, © 2026 Atikur Rahaman and contributors.
- Site text and figures: CC BY 4.0, following the documentation license.
- Upstream datasets: CC BY-SA 4.0; no raw SQuAD or HotpotQA text is redistributed.
- Fonts: SIL Open Font License 1.1.
