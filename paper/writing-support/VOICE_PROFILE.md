# VOICE_PROFILE.md

- **Confidence:** low. No reliable author-written sample is available.
- **Samples used (author-written only):** none.
- **Samples excluded and why:**
  - `README.md`, `ROADMAP.md`, `docs/*`, `prereg/*`: project documents maintained for and with
    AI agents under `AGENTS.md`; authorship is mixed across sessions and cannot be attributed
    to the author's unassisted writing.
  - `CITATION.cff` abstract: a project description of unknown drafting history.
  - `G:\HaluRISC\Journal_Paper\halurisc.tex`: a different paper by the same first author. Its
    prose is not verified as unassisted, and its subject matter and review history differ, so
    it is not a calibration sample for this paper.
- **Authorship rung:** **C** — the agent drafts from the project evidence in
  `PROJECT_BRIEF.md`; the author verifies every factual claim and revises the prose into their
  own words.

Because no sample exists, the working voice is plain, neutral academic English. The table below
records the default conventions the draft follows until real samples replace them.

| Feature | Observed in the author's writing | Working default (rung C) |
|---|---|---|
| Person and voice | No reliable sample | First person plural for author actions; passive only when the actor is irrelevant |
| Tense habits | No reliable sample | Past for procedures and observations; present for definitions, equations, and table references |
| Sentence rhythm | No reliable sample | Mixed length driven by content; no variation for its own sake |
| Paragraph shape | No reliable sample | Claim first, then evidence, then qualification; one job per paragraph |
| Connectors | No reliable sample | Only connectors that name a real relation ("because", "therefore", "in contrast") |
| Hedging | No reliable sample | Hedge only where the evidence is indirect; keep claim strength fixed by the gates |
| Tables, figures, numbers | No reliable sample | Introduce the object, state what it shows, then interpret; units in every column header |
| Preferred terms | No reliable sample | Use the terminology lock in `PROJECT_BRIEF.md` §8 |
| Formality and punctuation | No reliable sample | Formal but plain; Oxford comma off; no exclamation marks; no rhetorical questions |
| Recurring issues to fix | No reliable sample | Watch article use, subject–verb agreement, and run-on sentences in author revisions |

**Keep:** any clear author phrasing supplied later; do not flatten it into house style.
**Never copy:** errors or habits that cause ambiguity.
**Learned from the author's edits to agent output:** none recorded yet.

## How to recalibrate

Supply 500–1,000 words the author wrote without assistance (a report section, a literature
summary, a methods draft). Record the file path and word count above, fill the table from that
sample, and raise confidence to medium. Do not infer voice from the repository documents.

## Disclosure

Rung C means the agent produces draft prose from project evidence. The institution's AI-use
policy is not stated in the repository, so confirm it before submission. If disclosure is
required, record the tool, the sections drafted, and the date, and state that the author
reviewed and revised the text. The author must verify every number against
`artifacts/claims_evidence.csv` and every citation against the primary source; the agent does
not invent citations, and `refs.bib` does not yet exist.
