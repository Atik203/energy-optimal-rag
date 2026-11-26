# Slides

Everything for the presentation lives here, in one place.

| File | What it is |
|---|---|
| `Energy_Methodology_Presentation.pptx` | The 13-slide deck (editable, animated) |
| `Energy_Methodology_Presentation.pdf` | The same deck as PDF, for backup or printing |
| `Presentation_Script_and_QA.pdf` | Speaker script (5 speakers, 1.5 min each) plus likely questions and answers |
| `Presentation_Script_and_QA.tex` | Source of the script, in case the wording needs editing |
| `figures/` | Every figure used in the deck, generated from registered analysis outputs |
| `reference/` | The example deck used as the style reference |

## The deck

13 slides: 12 content slides and one references slide. Method-first structure, one claim per
slide, plain-language headers.

| # | Slide | Figure |
|---|---|---|
| 1 | Energy cost of retrieval depth (title) | — |
| 2 | How we measure energy per correct answer | `eq_estimand.png` |
| 3 | The models, dataset and hardware we used | `fig_pipeline.png` |
| 4 | Why every question is tested at all seven depths | `fig_sweep.png` |
| 5 | How we measure GPU energy in batches | `fig_block_timeline.png` |
| 6 | Why single-question power readings were replaced | `fig_window_vs_block.png` |
| 7 | Why we report a ratio instead of absolute joules | `fig_drift.png` |
| 8 | How we decide whether a smaller depth is good enough | `eq_savings.png`, `fig_margin.png` |
| 9 | How the rules were fixed before results were seen | table |
| 10 | Three experiments that test the cause | `fig_rq.png`, `fig_dose.png` |
| 11 | Why energy follows text length, not passage count | `eq_token.png`, `fig_token.png` |
| 12 | What the method found, and what it cannot claim | `fig_savings_forest.png` |
| 13 | References | — |

Deck rules that were checked, not assumed:

- No text smaller than **14 pt**, anywhere on any slide.
- Every text pair meets **WCAG AA** (worst pair 6.6:1), so it survives a projector in daylight.
- Windows and panels are avoided; the background is plain white.
- Animations are grouped so a card arrives as a unit, not letter by letter.
- No presenter names on the slides.

## Regenerating the figures

```powershell
C:\ProgramData\anaconda3\python.exe scripts\48_make_deck_figures.py
C:\ProgramData\anaconda3\python.exe scripts\48b_render_deck_equations.py
```

Both read only from `analysis/` and write to `Slides/figures/`. Every plotted value therefore
traces to a registered analysis output, not to a hand-typed number.

## Rebuilding the script PDF

```powershell
cd Slides
pdflatex -interaction=nonstopmode Presentation_Script_and_QA.tex
```

Word counts and speaking time are checked with `scripts\57_speech_timing.py`.

## Speaking plan

| Speaker | Slides | Words | Time at 100 wpm |
|---|---|---:|---:|
| Member 1 | 1–3 | 147 | 1.47 min |
| Member 2 | 4–5 | 151 | 1.51 min |
| Member 3 | 6–7 | 143 | 1.43 min |
| Member 4 | 8–10 | 150 | 1.50 min |
| Member 5 | 11–13 | 152 | 1.52 min |
| **Total** | 13 slides | **743** | **7.43 min** |

That leaves about 34 seconds for thirteen slide changes, inside an eight-minute slot.
