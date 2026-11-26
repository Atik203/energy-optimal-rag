# Slides

Everything for the presentation lives here, in one place.

| File | What it is |
|---|---|
| `Energy_Methodology_Presentation.pptx` | The 13-slide deck (editable, animated) |
| `Energy_Methodology_Presentation.pdf` | The same deck as PDF, for backup or printing |
| `Presentation_Script_and_QA.pdf` | Speaker script (5 speakers, 1.5 min each) plus likely questions and answers |
| `Presentation_Script_and_QA.tex` | Source of the script, in case the wording needs editing |
| `GPU_Server_Guide.pdf` | Three-page guide for students: SSH access, `scp` transfer, Task Spooler, rules |
| `GPU_Server_Guide.tex` | Source of the guide |
| `figures/` | Every figure used in the deck, generated from registered analysis outputs |
| `reference/` | The example deck used as the style reference |

## The GPU server guide

Three pages, written for students who have never used a shared server: one line of context per
section, then the command block.

- All addresses and credentials in it are **placeholders** and are marked as such in a box on page
  1. `10.0.0.50` and `203.0.113.10` are documentation ranges, so they can never resolve to a real
  host. The real address and each person's login have to be handed over separately.
- Colour carries meaning: **amber** blocks run on the Windows laptop, **green** blocks run on the
  server.
- Section 3 sets up the short name, so students type `ssh uiu-gpu` instead of the full address.
  `scp` and VS Code Remote-SSH read the same `%USERPROFILE%\.ssh\config`.
- Section 7 documents Task Spooler, including the flags that are easy to get wrong: `ts` with no
  argument lists the queue, `ts -L` sets a **label**, `-k` kills one job, `-T` kills all running
  jobs, and `-K` stops the daemon.
- The closing box replaces a troubleshooting table: rules, a sign-off reminder, and one line
  pointing to UIU CITS for anything else.

Rebuild with:

```powershell
cd Slides
pdflatex -interaction=nonstopmode GPU_Server_Guide.tex
```

## The deck

13 slides: one title, ten main slides, one closing slide, one references slide.

| # | Slide | Main slide of | Figure on the slide |
|---|---|---|---|
| 1 | Energy cost of retrieval depth (title, team with IDs) | — intro, not counted | — |
| 2 | How we measure energy per correct answer | Member 1 | `eq_estimand.png` |
| 3 | The models, dataset and hardware we used | Member 1 | `fig_pipeline.png`, `fig_readers.png` |
| 4 | Why every question is tested at all seven depths | Member 2 | `fig_sweep.png` |
| 5 | How we measure GPU energy in batches | Member 2 | `fig_block_timeline.png` |
| 6 | Why single-question power readings were replaced | Member 3 | `fig_window_vs_block.png` |
| 7 | Why we report a ratio instead of absolute joules | Member 3 | `fig_drift.png` |
| 8 | How we decide whether a smaller depth is good enough | Member 4 | `eq_savings.png`, `fig_margin.png` |
| 9 | How the rules were fixed before results were seen | Member 4 | table |
| 10 | Three experiments that test the cause | Member 5 | `fig_rq.png`, `fig_dose.png` |
| 11 | Why energy follows text length, not passage count | Member 5 | `eq_token.png`, `fig_token.png` |
| 12 | Thank you | — closing | — |
| 13 | References | — | — |

Each member presents **two main slides**. Slide 1 is only the introduction and slide 12 is only the
close, so neither counts as a member's main slide.

## The models on slide 3

| Model | Role | Depth behaviour |
|---|---|---|
| Qwen3.5-4B, 4-bit | main reader | accuracy keeps rising to k = 32 |
| Llama-3.2-3B | weaker-reader check | peaks at k = 4, then falls |
| Qwen2.5-1.5B | replication | flat, no clear gain |

`fig_readers.png` plots all three curves from their registered `estimates.csv` files. The caption on
the slide states that the chart is accuracy only: the two replication readers did not pass energy
calibration, so their joules are not reported.

Deck rules that were checked, not assumed:

- No text smaller than **14 pt**, anywhere on any slide — including the type drawn **inside** each
  figure. Figures are generated at their exact on-slide size so nothing shrinks at placement.
- Every text pair meets **WCAG AA** (worst pair 6.6:1), so it survives a projector in daylight.
- Plain white background, no busy panels.
- Animations are grouped so a card arrives as a unit, not letter by letter.
- No presenter names on the slides; names and IDs appear only on the title slide.

## Regenerating the figures

```powershell
C:\ProgramData\anaconda3\python.exe scripts\70_figures_final.py
C:\ProgramData\anaconda3\python.exe scripts\71_pipeline_final.py
C:\ProgramData\anaconda3\python.exe scripts\72_fix_diagrams.py
C:\ProgramData\anaconda3\python.exe scripts\75_rq_figure_correct.py
C:\ProgramData\anaconda3\python.exe scripts\48b_render_deck_equations.py
```

All of them read only from `analysis/` and write to `Slides/figures/`. Every plotted value therefore
traces to a registered analysis output, not to a hand-typed number.

## Rebuilding the script PDF

```powershell
cd Slides
pdflatex -interaction=nonstopmode Presentation_Script_and_QA.tex
```

Seven pages, in the same colour language as the deck and the server guide: teal chips mark each
slide cue, teal panels hold what is said, amber strips hold the handover line, and the last page is
one card per speaker. Word counts and speaking time are checked with
`scripts\57_speech_timing.py`.

## Speaking plan

| Speaker | Slides | Main slides | Words | Time at 100 wpm |
|---|---|---|---:|---:|
| Member 1 | 1–3 | 2 | 150 | 1.50 min |
| Member 2 | 4–5 | 2 | 151 | 1.51 min |
| Member 3 | 6–7 | 2 | 153 | 1.53 min |
| Member 4 | 8–9 | 2 | 153 | 1.53 min |
| Member 5 | 10–12 | 2 | 149 | 1.49 min |
| **Total** | 13 slides | 10 | **756** | **7.56 min** |

That leaves about 26 seconds for thirteen slide changes, inside an eight-minute slot.
