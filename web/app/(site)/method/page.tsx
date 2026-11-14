import type { Metadata } from "next";
import {
  Activity,
  ArrowRight,
  ClipboardCheck,
  Cpu,
  Database,
  FileCheck2,
  Gauge,
  GitBranch,
  ListChecks,
  PlugZap,
  RotateCcw,
  ScanLine,
  Scissors,
  ShieldCheck,
  Thermometer,
  Timer,
} from "lucide-react";
import {
  datasets,
  measurement,
  pilot,
  policy,
  scoring,
  taxes,
} from "@/lib/project-data";
import {
  Callout,
  Chip,
  FormulaBlock,
  PageHero,
  PilotChip,
  SectionHeading,
  SourceNote,
} from "@/components/ui";
import { BlockFactorBars, ContextShareChart, RecallBars } from "@/components/charts";

export const metadata: Metadata = {
  title: "Method",
  description:
    "The measurement pipeline: NVML energy integration, idle subtraction, 20-query block calibration, prefix-cache control, data preparation, scoring, policy, and the energy-tax design.",
};

const pipeline = [
  {
    id: "01",
    title: "Freeze",
    body: "Margins, gates, grids, reader, prompt, scoring, and code. Tag prereg-freeze-v1.",
  },
  {
    id: "02",
    title: "Prepare",
    body: "Official SQuAD/HotpotQA, SHA-256, seed 20261115. SQuAD 256-word contexts → 70-word chunks; no HotpotQA pooling; BM25 index.",
  },
  {
    id: "03",
    title: "Sweep",
    body: "Seven depths, randomized within question, fresh nonce, fixed prompt, greedy decoding, 24 new tokens.",
  },
  {
    id: "04",
    title: "Integrate",
    body: "NVML every 100 ms, idle subtraction, trapezoid over the call, 20-query block calibration, thermal log.",
  },
  {
    id: "05",
    title: "Score",
    body: "Normalized EM primary; lenient span and F1 ≥ 0.5 secondary. Empty or failed generation is wrong and retained.",
  },
  {
    id: "06",
    title: "Decide",
    body: "Ratio of sums, 5 pp non-inferiority, 10,000-resample bootstrap, affine fit, identity gap, held-out policy.",
  },
];

const controlIcons = [Activity, Gauge, ScanLine, Thermometer, RotateCcw, PlugZap];

function DataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[104px_1fr] gap-3 border-t border-line py-2.5 first:border-t-0">
      <dt className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">{label}</dt>
      <dd className="text-sm leading-snug">{value}</dd>
    </div>
  );
}

export default function MethodPage() {
  return (
    <div>
      <PageHero
        index="02"
        eyebrow="Method"
        title={
          <>
            How a joule is <em>attributed.</em>
          </>
        }
        lede="GPU energy is the primary measurement. CPU retrieval is a time-to-joules proxy. The wall meter is a cross-check. Absolute joule claims are conditional on the calibration described here."
        meta={[
          { label: "NVML 100 ms cadence", tone: "data" },
          { label: "20-query blocks", tone: "signal" },
          { label: "10,000 bootstrap", tone: "neutral" },
          { label: "No raw text", tone: "caution" },
        ]}
      />

      {/* 01 — Pipeline */}
      <section aria-labelledby="pipeline-heading" className="mt-4">
        <SectionHeading
          index="01"
          eyebrow="Pipeline"
          id="pipeline-heading"
          title={
            <>
              Freeze first. <em>Then measure.</em>
            </>
          }
          description="The order is part of the method. A margin or gate chosen after the accuracy curve is not a pre-registered decision."
        />

        <div className="relative mt-8">
          <div className="absolute left-0 right-0 top-5 hidden h-px bg-line lg:block" aria-hidden />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {pipeline.map((step) => (
              <div key={step.id} className="relative flex flex-col">
                <div className="mb-3 flex items-center gap-3">
                  <span className="relative z-10 flex h-10 w-10 items-center justify-center rounded-full border border-line-strong bg-background font-mono text-[10px] text-signal">
                    {step.id}
                  </span>
                </div>
                <div className="panel flex-1 p-4">
                  <h3 className="text-sm font-semibold">{step.title}</h3>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{step.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <SourceNote>
          Source: docs/proposal.md §6 step table; docs/IMPLEMENTATION_PLAN.md §3–6. The pipeline is
          deterministic and reads only registered raw CSVs.
        </SourceNote>
      </section>

      {/* 02 — Energy decomposition */}
      <section aria-labelledby="energy-heading" className="mt-16">
        <SectionHeading
          index="02"
          eyebrow="Energy decomposition"
          id="energy-heading"
          title={
            <>
              Four terms. <em>One primary sensor.</em>
            </>
          }
          description="The GPU sensor captures prefill and decode directly, plus part of the fixed overhead. BM25 runs on the CPU and is not captured by NVML."
        />

        <div className="mt-8 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-4 min-w-0">
            <FormulaBlock
              label="Per query, per depth"
              note="The GPU sensor captures J_pre and J_dec; J_ret is a CPU proxy; J_fix is partly captured and partly amortized."
            >
              <div className="text-[1.15rem] sm:text-[1.35rem]">
                J<sub>k</sub>(q) = J<sub>ret,k</sub>(q) + J<sub>pre,k</sub>(q) + J
                <sub>dec,k</sub>(q) + J<sub>fix</sub>(q)
              </div>
            </FormulaBlock>

            <div className="grid gap-3 sm:grid-cols-2">
              {measurement.components.map((component) => (
                <div key={component.symbol} className="panel p-4">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-mono text-sm text-signal">{component.symbol}</span>
                    <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">
                      {component.label}
                    </span>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{component.body}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="panel p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-semibold">Where the energy goes</h3>
              <PilotChip />
            </div>
            <div className="mt-5">
              <ContextShareChart />
            </div>
            <p className="mt-4 border-t border-line pt-3 text-xs leading-relaxed text-muted-foreground">
              The context-side share is estimated from the per-passage GPU slope b = 2.283 J. The
              retrieval-only share uses the CPU proxy. They are never conflated.
            </p>
          </div>
        </div>

        <div className="mt-4 panel p-5">
          <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-data" aria-hidden />
                <h3 className="text-sm font-semibold">Primary sensor: NVML</h3>
              </div>
              <dl className="mt-3">
                <DataRow label="Library" value={measurement.sensor.library} />
                <DataRow label="Field" value={measurement.sensor.field} />
                <DataRow label="Cadence" value={measurement.sensor.cadence} />
                <DataRow label="Also" value={measurement.sensor.also} />
              </dl>
            </div>
            <Callout tone="caution" title="Resolution caveat">
              {measurement.sensor.caveat}
            </Callout>
          </div>
        </div>
      </section>

      {/* 03 — Controls */}
      <section aria-labelledby="controls-heading" className="mt-16">
        <SectionHeading
          index="03"
          eyebrow="Controls"
          id="controls-heading"
          title={
            <>
              Every correction is <em>recorded.</em>
            </>
          }
          description="The pilot's absolute energy is not a raw per-query integral. It is trapezoidal integration, idle-subtracted, block-calibrated, and checked against repeats and a wall meter."
        />

        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {measurement.controls.map((control, index) => {
            const Icon = controlIcons[index] ?? Activity;
            return (
              <div key={control.title} className="panel p-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <Icon className="h-4 w-4 text-data" aria-hidden />
                </div>
                <p className="mt-3 font-mono text-lg font-medium">{control.value}</p>
                <h3 className="mt-1 text-sm font-semibold">{control.title}</h3>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{control.detail}</p>
              </div>
            );
          })}
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="panel p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-semibold">Block calibration factors</h3>
              <PilotChip />
            </div>
            <div className="mt-4">
              <BlockFactorBars />
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
              The largest correction is at k = 2, where the per-query window is shortest relative to
              the power ramp. Both raw and calibrated values are stored.
            </p>
          </div>

          <div className="space-y-4 min-w-0">
            <div className="panel p-5">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-semibold">Integration</h3>
                <Timer className="h-4 w-4 text-caution" aria-hidden />
              </div>
              <pre className="mt-3 overflow-x-auto rounded-[2px] border border-line bg-panel-soft p-3 font-mono text-[11px] leading-relaxed text-foreground">
                {measurement.integration}
              </pre>
              <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                The idle baseline is subtracted per query and clipped at zero. Using the post-run
                baseline lowers every energy by about 4% almost uniformly and changes E ratios by
                under 1%.
              </p>
            </div>

            <div className="panel p-5">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-semibold">Block calibration</h3>
                <Gauge className="h-4 w-4 text-data" aria-hidden />
              </div>
              <pre className="mt-3 overflow-x-auto rounded-[2px] border border-line bg-panel-soft p-3 font-mono text-[11px] leading-relaxed text-foreground">
                {measurement.blockFormula}
              </pre>
              <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                Twenty back-to-back queries per depth are integrated as one window. The per-query
                integrals are scaled to the block total.
              </p>
            </div>
          </div>
        </div>

        <SourceNote>
          Source: docs/MEASUREMENT.md §2–8. Pilot values: idle 15.56 W, block factors 1.041–1.188,
          repeat CV 3.80% median / 9.24% max, CPU proxy 3.11 J/query.
        </SourceNote>
      </section>

      {/* 04 — Data */}
      <section aria-labelledby="data-heading" className="mt-16">
        <SectionHeading
          index="04"
          eyebrow="Data"
          id="data-heading"
          title={
            <>
              Two corpora. <em>One depth question.</em>
            </>
          }
          description="SQuAD isolates the depth effect inside a closed corpus. HotpotQA supplies multi-hop evidence and distractor-induced non-monotonicity. Neither is a deployment distribution."
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          <div className="panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="eyebrow">Primary</p>
                <h3 className="mt-1 text-lg font-semibold">{datasets.squad.name}</h3>
              </div>
              <Chip tone="signal" dot>
                {datasets.squad.role}
              </Chip>
            </div>
            <dl className="mt-4">
              <DataRow label="Upstream" value={`${datasets.squad.upstreamQuestions.toLocaleString("en-US")} questions · ${datasets.squad.upstreamContexts.toLocaleString("en-US")} contexts`} />
              <DataRow label="Used here" value={`${datasets.squad.usedPrimary.toLocaleString("en-US")} primary · 2 × ${datasets.squad.usedReplication} replication · ${datasets.squad.usedBoundary} boundary`} />
              <DataRow label="Corpus" value={datasets.squad.corpus} />
              <DataRow label="Retriever" value={datasets.squad.retriever} />
              <DataRow label="Primary metric" value={datasets.squad.primaryMetric} />
              <DataRow label="License" value={datasets.squad.license} />
            </dl>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{datasets.squad.note}</p>
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              Exploratory reader: Llama 3.2 3B. The 16k context-budget probe is a separate
              diagnostic on 200 boundary IDs; it is not a 16k-token prompt.
            </p>
          </div>

          <div className="panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="eyebrow">Stress</p>
                <h3 className="mt-1 text-lg font-semibold">{datasets.hotpot.name}</h3>
              </div>
              <Chip tone="caution" dot>
                {datasets.hotpot.role}
              </Chip>
            </div>
            <dl className="mt-4">
              <DataRow label="Upstream" value={`${datasets.hotpot.upstreamQuestions.toLocaleString("en-US")} questions`} />
              <DataRow label="Used here" value={`${datasets.hotpot.used} questions · ${datasets.hotpot.paragraphs} paragraphs each (${datasets.hotpot.goldParagraphs} gold, ${datasets.hotpot.distractors} distractors)`} />
              <DataRow label="Corpus" value={datasets.hotpot.corpus} />
              <DataRow label="Retriever" value={datasets.hotpot.retriever} />
              <DataRow label="Depths" value={datasets.hotpot.depths.join(", ")} />
              <DataRow label="License" value={datasets.hotpot.license} />
            </dl>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{datasets.hotpot.note}</p>
          </div>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="panel p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-semibold">Retrieval ceiling</h3>
              <PilotChip />
            </div>
            <div className="mt-4">
              <RecallBars />
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
              {datasets.squad.recallNote}
            </p>
          </div>

          <div className="space-y-4 min-w-0">
            <div className="panel p-5">
              <div className="flex items-center gap-2">
                <Scissors className="h-4 w-4 text-data" aria-hidden />
                <h3 className="text-sm font-semibold">Processing and splits</h3>
              </div>
              <ul className="mt-3 space-y-2">
                {datasets.processing.map((item) => (
                  <li key={item} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-data" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="panel p-5">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-caution" aria-hidden />
                <h3 className="text-sm font-semibold">Limits</h3>
              </div>
              <ul className="mt-3 space-y-2">
                {datasets.limits.map((item) => (
                  <li key={item} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-caution" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-4 flex gap-3 border-l-2 border-caution pl-4">
          <Database className="mt-0.5 h-4 w-4 shrink-0 text-caution" aria-hidden />
          <p className="text-sm leading-relaxed text-muted-foreground">
            Both datasets are CC BY-SA 4.0. Their licenses remain in force. The repository releases
            IDs, versions, checksums, seeds, configs, prompts, predictions, and aggregate
            statistics; it does not redistribute raw question or context text.
          </p>
        </div>

        <SourceNote>
          Source: docs/DATA_CARD.md. Recall values are pilot evidence from the 200-question run.
        </SourceNote>
      </section>

      {/* 05 — Scoring */}
      <section aria-labelledby="scoring-heading" className="mt-16">
        <SectionHeading
          index="05"
          eyebrow="Scoring"
          id="scoring-heading"
          title={
            <>
              Strict EM primary. <em>Survive the other rules.</em>
            </>
          }
          description="The conclusion must not depend on a single scoring rule. The rerun pre-registers EM and requires the qualitative conclusion to survive lenient span and F1 ≥ 0.5; if it does not, the dependence is reported."
        />

        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          {scoring.map((rule, index) => (
            <div key={rule.rule} className="panel p-5">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] text-muted-foreground">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <Chip tone={index === 0 ? "signal" : "neutral"}>{rule.id}</Chip>
              </div>
              <h3 className="mt-3 text-sm font-semibold">{rule.rule}</h3>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{rule.detail}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <Callout tone="caution" title="The pilot's scoring dependence" icon={<ClipboardCheck className="h-4 w-4" />}>
            Strict EM penalized answers such as “{pilot.scoringSensitivity.prediction}” for gold
            “{pilot.scoringSensitivity.gold}.” Lenient/F1 gave an interior k ={" "}
            {pilot.scoringSensitivity.interiorK} at {pilot.scoringSensitivity.savingsPct}% savings
            where EM gave the boundary. The conclusion “never 32” was robust; the location was
            not. This is why the rerun pre-registers scoring sensitivity.
          </Callout>
          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <ListChecks className="h-4 w-4 text-data" aria-hidden />
              <h3 className="text-sm font-semibold">Population rule</h3>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              Descriptive statistics use every question with a valid row at that depth. A failed or
              empty generation is a wrong answer and is retained. A row is invalid only for a
              missing nonce, a request failure, or a sampler error. The primary paired test uses
              questions with valid rows at both k = 4 and k = 32; invalid counts and paired n are
              reported.
            </p>
            <p className="mt-3 font-mono text-[9px] uppercase tracking-[0.12em] text-caution">
              Intent-to-evaluate · no outcome-based exclusions
            </p>
          </div>
        </div>
      </section>

      {/* 06 — Policy */}
      <section aria-labelledby="policy-heading" className="mt-16">
        <SectionHeading
          index="06"
          eyebrow="Policy"
          id="policy-heading"
          title={
            <>
              A static optimum is the wrong object <em>when queries differ.</em>
            </>
          }
          description="Theorem 2 says a static depth can be arbitrarily worse than a query-conditional policy at equal accuracy. The policy experiment is the adaptive contribution; 78.8% is only its ceiling."
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="panel p-5">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-sm font-semibold">Split</h3>
              <Chip tone="data" dot>
                Hashed by question ID
              </Chip>
            </div>
            <div className="mt-5 flex h-4 overflow-hidden rounded-[2px] border border-line">
              <div className="flex items-center justify-center bg-signal/80 font-mono text-[8px] text-signal-foreground" style={{ width: "60%" }}>
                600 train
              </div>
              <div className="flex items-center justify-center bg-data/70 font-mono text-[8px] text-[#07110d]" style={{ width: "20%" }}>
                200 val
              </div>
              <div className="flex items-center justify-center bg-caution/80 font-mono text-[8px] text-[#07110d]" style={{ width: "20%" }}>
                200 test
              </div>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{policy.split}</p>
            <div className="mt-4 border-t border-line pt-4">
              <p className="eyebrow">Features · pre-generation only</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {policy.features.map((feature) => (
                  <span key={feature} className="rounded-[2px] border border-line bg-panel-soft px-2 py-1 font-mono text-[9px] text-muted-foreground">
                    {feature}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-4 min-w-0">
            <div className="panel p-5">
              <div className="flex items-center gap-2">
                <GitBranch className="h-4 w-4 text-caution" aria-hidden />
                <h3 className="text-sm font-semibold">Model and evaluation</h3>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{policy.model}</p>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{policy.evaluation}</p>
            </div>
            <div className="panel p-5">
              <p className="eyebrow">Guardrails</p>
              <ul className="mt-3 space-y-2">
                {policy.guardrails.map((item) => (
                  <li key={item} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-data" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <Callout tone="dead" title="The 78.8% number is a ceiling">
              The oracle chooses the cheapest correct depth per query with hindsight. No policy was
              trained. G4 requires an oracle gain ≥ 20% and a learned policy capturing ≥ 50% of it
              at matched accuracy on held-out questions.
            </Callout>
          </div>
        </div>
      </section>

      {/* 07 — Taxes */}
      <section aria-labelledby="taxes-heading" className="mt-16">
        <SectionHeading
          index="07"
          eyebrow="Energy taxes"
          id="taxes-heading"
          title={
            <>
              Change the split. <em>Predict the sign.</em>
            </>
          }
          description="A fixed dummy GPU computation before generation raises a. A per-passage dummy computation raises b. Reader, prompt, passages, and answers stay unchanged. The predicted signs are falsifiable."
        />

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {[taxes.fixed, taxes.perPassage].map((tax) => (
            <div key={tax.label} className="panel p-5">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold">{tax.label}</h3>
                <Chip tone={tax.label === "Fixed tax" ? "signal" : "caution"} dot>
                  {tax.prediction}
                </Chip>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{tax.change}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="instrument p-5">
            <p className="inst-label">Predicted comparative statics</p>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="border border-[rgba(200,240,79,0.16)] p-3">
                <p className="font-mono text-xs text-[#8aa294]">Fixed tax Δa &gt; 0</p>
                <p className="inst-signal mt-2 font-mono text-lg">k* ↑</p>
                <p className="mt-1 text-[10px] leading-relaxed text-[#8aa294]">
                  The fixed cost is spread over more passages.
                </p>
              </div>
              <div className="border border-[rgba(200,79,79,0.2)] p-3">
                <p className="font-mono text-xs text-[#8aa294]">Per-passage tax Δb &gt; 0</p>
                <p className="inst-caution mt-2 font-mono text-lg">k* ↓</p>
                <p className="mt-1 text-[10px] leading-relaxed text-[#8aa294]">
                  Each additional passage costs more.
                </p>
              </div>
            </div>
            <p className="inst-muted mt-4 text-[10px] leading-relaxed">
              A wrong sign falsifies the affine/split model. The test is on the sign, not only
              significance.
            </p>
          </div>

          <div className="space-y-4 min-w-0">
            <div className="panel p-5">
              <div className="flex items-center gap-2">
                <PlugZap className="h-4 w-4 text-caution" aria-hidden />
                <h3 className="text-sm font-semibold">Design</h3>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{taxes.design}</p>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Configured at 20% of a = 15.74 J (3.148 J) and 20% of b = 2.283 J (0.457 J); the
                pre-registered range is 10–30%.
              </p>
            </div>
            <Callout tone="dead" title="Why the mid-accuracy gate exists">
              {taxes.falsification}
            </Callout>
          </div>
        </div>
      </section>

      {/* 08 — Reporting checklist */}
      <section aria-labelledby="checklist-heading" className="mt-16">
        <SectionHeading
          index="08"
          eyebrow="Reporting checklist"
          id="checklist-heading"
          title={
            <>
              A table missing these <em>is not reproducible.</em>
            </>
          }
          description="Every energy table states the conditions of its own measurement. The checklist is the minimum, not a nicety."
        />

        <div className="panel mt-8 p-5 sm:p-6">
          <div className="flex items-start gap-3">
            <FileCheck2 className="mt-0.5 h-5 w-5 shrink-0 text-signal" aria-hidden />
            <p className="text-sm leading-relaxed text-muted-foreground">{measurement.checklist}</p>
          </div>
          <div className="mt-5 flex flex-wrap gap-1.5 border-t border-line pt-5">
            {[
              "sensor",
              "cadence",
              "idle baseline + CV",
              "block factors",
              "repeat CV",
              "CPU proxy W",
              "wall-meter factor",
              "GPU model",
              "driver",
              "power mode",
              "model digest",
            ].map((item) => (
              <span key={item} className="rounded-[2px] border border-line bg-panel-soft px-2 py-1 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">
                {item}
              </span>
            ))}
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {[
            { label: "Pilot repeat CV", value: `${pilot.repeatCv.median.toFixed(2)}%`, note: "median at k = 8" },
            { label: "Pilot max CV", value: `${pilot.repeatCv.max}%`, note: "max across repeats" },
            { label: "CPU proxy", value: `${pilot.cpuProxy.joules} J`, note: `${pilot.cpuProxy.seconds} s × ${pilot.cpuProxy.watts} W` },
          ].map((stat) => (
            <div key={stat.label} className="panel flex items-center justify-between gap-3 p-4">
              <div>
                <p className="eyebrow">{stat.label}</p>
                <p className="mt-2 font-mono text-2xl font-medium tabular-nums text-signal">{stat.value}</p>
                <p className="mt-1 font-mono text-[9px] text-muted-foreground">{stat.note}</p>
              </div>
              <PilotChip />
            </div>
          ))}
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-line pt-4">
          <Cpu className="h-4 w-4 text-data" aria-hidden />
          <p className="text-xs text-muted-foreground">
            Reader: {pilot.reader} {pilot.quantization}, {pilot.readerContext}, greedy, 24 new
            tokens. Host: {pilot.gpu}, batch size 1, no concurrent jobs.
          </p>
          <span className="ml-auto inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-caution">
            Pilot <ArrowRight className="h-3.5 w-3.5" aria-hidden /> not confirmatory
          </span>
        </div>

        <SourceNote>
          Source: docs/MEASUREMENT.md §1–11; docs/IMPLEMENTATION_PLAN.md §3–9; prereg/PREREGISTRATION.md
          §3–4. Pilot values are transcribed, not recomputed here.
        </SourceNote>
      </section>
    </div>
  );
}
