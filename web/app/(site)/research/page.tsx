import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  CircleHelp,
  Crosshair,
  GitBranch,
  Scale,
  Search,
  ShieldCheck,
  Sigma,
  Target,
} from "lucide-react";
import {
  contributions,
  gates,
  hypotheses,
  priorWork,
  priorWorkNote,
  theory,
  type ClaimStatus,
} from "@/lib/project-data";
import {
  Callout,
  Chip,
  FormulaBlock,
  PageHero,
  SectionHeading,
  SourceNote,
  StatusTag,
  type Tone,
} from "@/components/ui";

export const metadata: Metadata = {
  title: "Research design",
  description:
    "The research question, estimand, hypotheses H1–H7, theory, gates K1–K7 and G1–G5, and prior-work positioning for the energy-optimal retrieval-depth study.",
};

const symbols = [
  { symbol: "k", meaning: "Retrieval depth: the number of passages placed in the prompt." },
  { symbol: "J(k)", meaning: "Mean joules per query at depth k." },
  { symbol: "A(k)", meaning: "Accuracy at depth k, a proportion in [0, 1]." },
  { symbol: "E(k)", meaning: "Joules per correct answer, estimated as a ratio of sums." },
  { symbol: "A_min", meaning: "The pre-registered accuracy floor. Primary: A(32) − 0.05." },
  { symbol: "k*", meaning: "The feasible minimizer of E(k) under the gate." },
  { symbol: "N*", meaning: "Queries at which calibration energy equals the energy it saves." },
  { symbol: "capture", meaning: "The fraction of the oracle gap a learned policy recovers." },
];

function hypothesisTone(type: string): Tone {
  if (type === "Primary") return "signal";
  if (type.includes("adaptive") || type.includes("causal")) return "caution";
  if (type.includes("replication")) return "beam";
  return "data";
}

const gateStatus: Record<"pass" | "fail", ClaimStatus> = {
  pass: "supported",
  fail: "dead",
};

export default function ResearchPage() {
  return (
    <div>
      <PageHero
        index="01"
        eyebrow="Research design"
        title={
          <>
            A decision rule, <em>not a universal depth.</em>
          </>
        }
        lede="The object is a gated ratio, a margin-indexed policy, and the energy cost of learning it. The pilot changed which of those objects survives."
        meta={[
          { label: "Primary: 5 pp non-inferiority", tone: "signal" },
          { label: "n = 1,000", tone: "data" },
          { label: "2 pp estimation-only", tone: "caution" },
          { label: "Prereg: draft, not frozen", tone: "caution" },
        ]}
      />

      {/* 01 — Question */}
      <section aria-labelledby="question-heading" className="mt-4">
        <SectionHeading
          index="01"
          eyebrow="The question"
          id="question-heading"
          title={
            <>
              Which depth earns its joules <em>under a floor?</em>
            </>
          }
          description="The question is conditional by construction: a fixed reader, retriever, corpus, and hardware. The answer is a decision rule, not a property of RAG in general."
        />

        <div className="mt-8 grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="panel p-5 sm:p-6">
            <div className="flex items-center gap-2">
              <Crosshair className="h-4 w-4 text-signal" aria-hidden />
              <span className="eyebrow">Research question</span>
            </div>
            <blockquote className="display-title mt-4 text-xl leading-[1.3] sm:text-2xl">
              For a fixed reader, retriever, corpus, and hardware, which depth minimizes joules
              per correct answer subject to a pre-registered accuracy floor — and does a
              query-conditional policy beat the best static depth at matched accuracy?
            </blockquote>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              Second: is the energy cost of finding the depth smaller than what it saves? The
              calibration question is not an afterthought; it decides whether a small deployment
              should calibrate at all.
            </p>
          </div>

          <div className="panel">
            <div className="flex items-center justify-between border-b border-line px-4 py-3">
              <span className="eyebrow">Symbols</span>
              <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted-foreground">
                Units: J, J/correct, proportion
              </span>
            </div>
            <dl className="divide-y divide-line">
              {symbols.map((row) => (
                <div key={row.symbol} className="grid grid-cols-[64px_1fr] gap-3 px-4 py-2.5">
                  <dt className="font-mono text-xs text-signal">{row.symbol}</dt>
                  <dd className="text-xs leading-relaxed text-muted-foreground">{row.meaning}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      {/* 02 — Estimand and test */}
      <section aria-labelledby="estimand-heading" className="mt-16">
        <SectionHeading
          index="02"
          eyebrow="Estimand and primary test"
          id="estimand-heading"
          title={
            <>
              Total joules over total correct answers, <em>paired with the gate.</em>
            </>
          }
          description="The primary estimand is a ratio of expectations, not the mean of per-query ratios. The design has one confirmatory test; everything else is secondary or exploratory."
        />

        <div className="mt-8 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-4">
            <FormulaBlock
              label="Primary estimand"
              note="Estimated as sum(J_k) / sum(C_k) over the analysis population. Reported with A(k), the gate, and a 10,000-resample paired bootstrap interval."
            >
              <div className="text-[1.35rem] sm:text-[1.7rem]">
                E(k) = Σ J<sub>k</sub>(q) / Σ C<sub>k</sub>(q)
              </div>
            </FormulaBlock>

            <div className="panel p-5">
              <div className="flex items-center gap-2">
                <Sigma className="h-4 w-4 text-data" aria-hidden />
                <h3 className="text-sm font-semibold">Analysis population</h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                Descriptive statistics use every question with a valid row at that depth. A failed
                or empty generation is a wrong answer and is retained. A row is invalid only for a
                protocol violation: a missing nonce, a request failure, or a sampler error.
              </p>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                The primary paired test uses questions with valid rows at both k = 4 and k = 32.
                All invalid counts and the paired n are reported.
              </p>
              <p className="mt-3 font-mono text-[9px] uppercase tracking-[0.12em] text-caution">
                No outcome-based exclusions. No trimming.
              </p>
            </div>
          </div>

          <div className="panel p-5 sm:p-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="eyebrow">Primary decision</p>
                <h3 className="mt-2 font-mono text-2xl tracking-[-0.03em]">
                  k = 4 <span className="text-muted-foreground">vs</span> k = 32
                </h3>
              </div>
              <Chip tone="signal" dot>
                H2
              </Chip>
            </div>

            <dl className="mt-5 divide-y divide-line border-y border-line">
              {[
                ["Margin", "5 pp normalized EM"],
                ["Test", "One-sided paired non-inferiority, α = 0.05"],
                ["Gate", "A_min = A(32) − 0.05"],
                ["Energy", "≥ 20% savings, ratio of sums"],
                ["Uncertainty", "10,000 paired bootstrap resamples"],
                ["2 pp margin", "Estimation only; never a certification target"],
              ].map(([label, value]) => (
                <div key={label} className="grid grid-cols-[100px_1fr] gap-3 py-2.5">
                  <dt className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">
                    {label}
                  </dt>
                  <dd className="text-sm leading-snug">{value}</dd>
                </div>
              ))}
            </dl>

            <div className="mt-5 border-l-2 border-caution pl-4">
              <p className="text-sm font-semibold">Decision rule</p>
              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                H2 is supported iff the test rejects at α = 0.05 <strong>and</strong> point savings
                are at least 20%. If it rejects but savings are below 20%, the result is
                “non-inferior but not materially greener,” and the policy claim fails.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 03 — Hypotheses */}
      <section aria-labelledby="hypotheses-heading" className="mt-16">
        <SectionHeading
          index="03"
          eyebrow="Hypotheses"
          id="hypotheses-heading"
          title={
            <>
              Seven hypotheses. <em>One primary test.</em>
            </>
          }
          description="The 2 pp margin is not a hypothesis. It is an estimation target reported with a confidence interval and explicitly not used for certification."
        />

        <div className="panel mt-8 overflow-hidden">
          <div className="hidden border-b border-line bg-panel-soft px-4 py-2.5 md:grid md:grid-cols-[56px_1fr_170px] md:gap-4">
            <span className="eyebrow">ID</span>
            <span className="eyebrow">Hypothesis</span>
            <span className="eyebrow">Type</span>
          </div>
          {hypotheses.map((hypothesis) => (
            <div
              key={hypothesis.id}
              className="grid gap-2 border-t border-line px-4 py-4 first:border-t-0 md:grid-cols-[56px_1fr_170px] md:items-start md:gap-4"
            >
              <span className="font-mono text-sm font-medium text-signal">{hypothesis.id}</span>
              <p className="text-sm leading-relaxed">{hypothesis.statement}</p>
              <div className="md:justify-self-start">
                <Chip tone={hypothesisTone(hypothesis.type)}>{hypothesis.type}</Chip>
              </div>
            </div>
          ))}
        </div>
        <SourceNote>
          Source: prereg/PREREGISTRATION.md §2. The preregistration is a draft until
          prereg-freeze-v1; the hash is TBD until freeze.
        </SourceNote>
      </section>

      {/* 04 — Theory */}
      <section aria-labelledby="theory-heading" className="mt-16">
        <SectionHeading
          index="04"
          eyebrow="Theory"
          id="theory-heading"
          title={
            <>
              Small, falsifiable, <em>and local.</em>
            </>
          }
          description="Three results and one counterexample. The theory is not a universal law of RAG; it is a set of claims that can be wrong in specific, reportable ways."
        />

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {theory.assumptions.map((assumption) => (
            <div key={assumption.id} className="panel p-4">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] text-signal">{assumption.id}</span>
                <span className="eyebrow">Assumption</span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{assumption.text}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          {theory.theorems.map((theorem) => (
            <article key={theorem.id} className="panel flex flex-col p-5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                    {theorem.id}
                  </p>
                  <h3 className="mt-1 text-base font-semibold">{theorem.title}</h3>
                </div>
                <Scale className="h-4 w-4 shrink-0 text-data" aria-hidden />
              </div>
              <div className="surface-inset mt-4 overflow-x-auto p-3 font-mono text-[0.82rem] leading-relaxed">
                {theorem.formula}
              </div>
              <p className="mt-4 flex-1 text-sm leading-relaxed text-muted-foreground">{theorem.body}</p>
              <div className="mt-4 border-t border-line pt-3">
                <p className="flex items-center gap-2 font-mono text-[9px] uppercase tracking-[0.12em] text-muted-foreground">
                  Pilot check
                  {(theorem.id === "Theorem 1" || theorem.id === "Theorem 3") && (
                    <span className="text-caution">PILOT</span>
                  )}
                </p>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{theorem.pilot}</p>
              </div>
            </article>
          ))}
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-caution" aria-hidden />
              <h3 className="text-sm font-semibold">The distractor counterexample</h3>
            </div>
            <p className="mt-2 font-mono text-xs leading-relaxed text-muted-foreground">
              {theory.counterexample.setup}
            </p>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[320px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-line">
                    <th className="py-2 pr-3 text-left font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">k</th>
                    { [0, 1, 2, 4].map((k) => (
                      <th key={k} className="px-2 py-2 text-right font-mono text-[10px] text-muted-foreground">{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-line">
                    <td className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">A</td>
                    {[0.6, 0.9, 0.7, 1.0].map((value, index) => (
                      <td key={index} className="px-2 py-2 text-right font-mono tabular-nums">{value.toFixed(1)}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">E</td>
                    {[1.667, 1.133, 1.486, 1.08].map((value, index) => (
                      <td key={index} className={`px-2 py-2 text-right font-mono tabular-nums ${index === 3 ? "text-signal" : ""}`}>
                        {value.toFixed(3)}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
              {theory.counterexample.lesson}
            </p>
          </div>

          <div className="space-y-4">
            <Callout tone="caution" title="The coverage fit failed" icon={<CircleHelp className="h-4 w-4" />}>
              The coverage model fit poorly: A₀ = {theory.coverageFit.a0}, p ={" "}
              {theory.coverageFit.p}, R² = {theory.coverageFit.r2}. Global unimodality is rejected;
              the identity remains a local diagnostic.
            </Callout>
            <div className="panel p-5">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-dead" aria-hidden />
                <h3 className="text-sm font-semibold">What would falsify the theory</h3>
              </div>
              <ul className="mt-3 space-y-2">
                {theory.falsification.map((item) => (
                  <li key={item} className="flex gap-2 text-sm leading-relaxed text-muted-foreground">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-dead" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 05 — Gates */}
      <section aria-labelledby="gates-heading" className="mt-16">
        <SectionHeading
          index="05"
          eyebrow="Gates"
          id="gates-heading"
          title={
            <>
              A fired gate is <em>a finding.</em>
            </>
          }
          description="Gates are evaluated once per phase on the pre-specified analysis population. A change after the freeze is an amendment. The pilot adjudication is prior evidence, not a confirmatory result."
        />

        <div className="mt-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-semibold">Kill / reframe gates · pilot adjudication</h3>
            <Chip tone="caution" dot>
              Pilot
            </Chip>
          </div>
          <div className="panel mt-3 overflow-hidden">
            <div className="hidden border-b border-line bg-panel-soft px-4 py-2.5 lg:grid lg:grid-cols-[70px_1.05fr_0.75fr_1.3fr] lg:gap-4">
              <span className="eyebrow">Gate</span>
              <span className="eyebrow">Criterion</span>
              <span className="eyebrow">Pilot</span>
              <span className="eyebrow">If it fires</span>
            </div>
            {gates.kill.map((gate) => (
              <div
                key={gate.id}
                className="grid gap-2 border-t border-line px-4 py-4 first:border-t-0 lg:grid-cols-[70px_1.05fr_0.75fr_1.3fr] lg:items-start lg:gap-4"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-medium text-signal">{gate.id}</span>
                  <StatusTag status={gateStatus[gate.status]} label={gate.status === "pass" ? "Pass" : "Fail"} />
                </div>
                <div>
                  <p className="eyebrow lg:hidden">Criterion</p>
                  <p className="text-sm leading-snug">{gate.criterion}</p>
                </div>
                <div>
                  <p className="eyebrow lg:hidden">Pilot</p>
                  <p className="font-mono text-xs leading-snug text-muted-foreground">{gate.pilot}</p>
                </div>
                <div>
                  <p className="eyebrow lg:hidden">If it fires</p>
                  <p className="text-sm leading-relaxed text-muted-foreground">{gate.action}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-semibold">Go gates · planned for the rerun</h3>
            <Chip tone="neutral" dot>
              Not yet evaluated
            </Chip>
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {gates.go.map((gate) => (
              <div key={gate.id} className="panel flex flex-col p-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-medium text-signal">{gate.id}</span>
                  <ShieldCheck className="h-4 w-4 text-muted-foreground" aria-hidden />
                </div>
                <p className="mt-3 flex-1 text-sm leading-relaxed text-muted-foreground">
                  {gate.criterion}
                </p>
              </div>
            ))}
            <div className="panel flex items-center gap-3 p-4">
              <ArrowRight className="h-4 w-4 shrink-0 text-signal" aria-hidden />
              <p className="text-xs leading-relaxed text-muted-foreground">
                A paper may be written with G1, G3, and G5 but without G4; it may not claim
                adaptivity without G4.
              </p>
            </div>
          </div>
        </div>

        <SourceNote>
          Source: ROADMAP.md §4 and docs/IMPLEMENTATION_PLAN.md §12. K1–K7 pilot results are prior
          evidence; the rerun re-adjudicates each once.
        </SourceNote>
      </section>

      {/* 06 — Prior work */}
      <section aria-labelledby="prior-heading" className="mt-16">
        <SectionHeading
          index="06"
          eyebrow="Prior work"
          id="prior-heading"
          title={
            <>
              The metric is not new. <em>The decision is.</em>
            </>
          }
          description="We do not claim the metric, adaptive depth, or bandit machinery as new. The combination — gated E(k), identity, static-depth bound, N*, causal split test — is absent from the papers found."
        />

        <div className="panel mt-8 overflow-hidden">
          <div className="hidden border-b border-line bg-panel-soft px-4 py-2.5 lg:grid lg:grid-cols-[1.15fr_0.55fr_1.6fr] lg:gap-4">
            <span className="eyebrow">Work</span>
            <span className="eyebrow">Optimizes</span>
            <span className="eyebrow">Relation to this project</span>
          </div>
          {priorWork.map((work) => (
            <div
              key={work.work}
              className="grid gap-2 border-t border-line px-4 py-4 first:border-t-0 lg:grid-cols-[1.15fr_0.55fr_1.6fr] lg:items-start lg:gap-4"
            >
              <p className="text-sm font-semibold leading-snug">{work.work}</p>
              <div>
                <p className="eyebrow lg:hidden">Optimizes</p>
                <Chip tone="neutral">{work.optimize}</Chip>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">{work.relation}</p>
            </div>
          ))}
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {contributions.map((contribution) => (
            <div key={contribution.title} className="panel p-4">
              <div className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-signal" aria-hidden />
                <h3 className="text-sm font-semibold">{contribution.title}</h3>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{contribution.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-5 flex gap-3 border-l-2 border-caution pl-4">
          <Search className="mt-0.5 h-4 w-4 shrink-0 text-caution" aria-hidden />
          <p className="text-sm leading-relaxed text-muted-foreground">{priorWorkNote}</p>
        </div>
      </section>

      {/* Close */}
      <section aria-labelledby="close-heading" className="mt-16">
        <div className="instrument p-6 sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-2xl">
              <p className="inst-label">What the design protects</p>
              <h2 id="close-heading" className="display-title mt-3 text-2xl text-[#eef3e5] sm:text-3xl">
                The claim is indexed by a margin, a reader, a corpus, and one laptop GPU.
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-[#8aa294]">
                No universal k*. No 2 pp optimum. No 5 pp certification before the rerun. No
                learned-policy gain from the oracle. No carbon-optimal claim. The results page
                reports the pilot exactly as measured.
              </p>
            </div>
            <Link
              href="/results"
              className="inline-flex items-center gap-2 rounded-[3px] bg-[#c8f04f] px-4 py-2.5 text-sm font-semibold text-[#0a1408]"
            >
              See the pilot evidence
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
