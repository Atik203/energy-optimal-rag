import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  CircleHelp,
  FlaskConical,
  ShieldAlert,
  ShieldX,
} from "lucide-react";
import { pilot, pilotTable, project, rerun } from "@/lib/project-data";
import {
  Callout,
  Chip,
  FormulaBlock,
  PageHero,
  PilotChip,
  SectionHeading,
  SourceNote,
  StatusTag,
} from "@/components/ui";
import {
  AccuracyChart,
  ContextShareChart,
  EnergyFitChart,
  IdentityPlot,
} from "@/components/charts";
import { ClaimLedger } from "@/components/claim-ledger";

export const metadata: Metadata = {
  title: "Pilot evidence",
  description:
    "The pilot evidence, exactly as measured: the energy curve, accuracy plateau, dead 2 pp claim, context-side share, identity diagnostic, repeatability, and the 5 pp signal. No confirmatory results.",
};

const setup = [
  { value: "200", label: "SQuAD questions", note: "v1.1 dev" },
  { value: "7", label: "depths", note: "0–32" },
  { value: "1,400", label: "generations", note: "200 × 7" },
  { value: "45,651", label: "passages", note: "BM25 top-32" },
  { value: "6 GB", label: "GPU memory", note: "RTX 3060 Laptop" },
  { value: "Q4", label: "quantization", note: "qwen3.5:4b" },
];

export default function ResultsPage() {
  return (
    <div>
      <PageHero
        index="03"
        eyebrow="Pilot evidence"
        title={
          <>
            The pilot, <em>exactly as measured.</em>
          </>
        }
        lede={`A ${pilot.questions}-question run on one laptop GPU. It produced a precise energy curve, a dead static claim, and one signal that still needs power. Nothing on this page is confirmatory.`}
        meta={[
          { label: `Pilot n = ${pilot.questions}`, tone: "caution" },
          { label: "No confirmatory results", tone: "dead" },
          { label: "2 pp claim DEAD", tone: "dead" },
          { label: "5 pp: signal, not certified", tone: "caution" },
        ]}
      />

      {/* Explicit banner */}
      <section
        aria-labelledby="no-confirmatory"
        className="mt-4 border border-dead/40 bg-dead/5 p-5 sm:p-6"
      >
        <div className="flex flex-col gap-4 sm:flex-row">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[3px] border border-dead/40 bg-dead/10 text-dead">
            <ShieldAlert className="h-5 w-5" aria-hidden />
          </span>
          <div>
            <p className="font-mono text-[10px] font-medium uppercase tracking-[0.18em] text-dead">
              No confirmatory results
            </p>
            <h2 id="no-confirmatory" className="display-title mt-2 text-2xl sm:text-3xl">
              This page reports pilot evidence only.
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
              The pilot raw CSVs are not in this repository. Values are transcribed from the
              repository record and are not independently reproducible from this public scaffold.
              No confirmatory run has been executed. The 2 pp static claim is dead; the 5 pp result
              is a pilot signal, not certified; the {pilot.oracle.gain}% oracle gain is an upper bound.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Chip tone="caution" dot>
                Pilot n = {pilot.questions}
              </Chip>
              <Chip tone="dead" dot>
                2 pp claim dead
              </Chip>
              <Chip tone="caution" dot>
                5 pp: signal, not certified
              </Chip>
              <Chip tone="caution" dot>
                {pilot.oracle.gain}%: upper bound
              </Chip>
            </div>
          </div>
        </div>
      </section>

      {/* Setup */}
      <section aria-label="Pilot setup" className="mt-6">
        <div className="panel overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
            <span className="eyebrow">Pilot setup</span>
            <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-caution">
              Two-hour run · prior evidence
            </span>
          </div>
          <div className="grid grid-cols-2 gap-px bg-line sm:grid-cols-3 lg:grid-cols-6">
            {setup.map((item) => (
              <div key={item.label} className="bg-panel p-4">
                <p className="font-mono text-xl font-medium tabular-nums text-signal">{item.value}</p>
                <p className="mt-1 text-xs font-semibold leading-snug">{item.label}</p>
                <p className="mt-0.5 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">
                  {item.note}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Energy */}
      <section aria-labelledby="energy-results" className="mt-16">
        <SectionHeading
          index="01"
          eyebrow="Energy"
          id="energy-results"
          title={
            <>
              The energy effect is <em>steep and precise.</em>
            </>
          }
          description={`E(32) is ${pilot.energy.span.toFixed(2)}× E(1) in joules per correct answer. The affine fit is excellent on this grid, which is a measurement result, not a law of RAG.`}
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <EnergyFitChart />

          <div className="panel p-5 sm:p-6">
            <div className="flex items-center justify-between gap-2">
              <span className="eyebrow">Energy per correct answer</span>
              <PilotChip />
            </div>
            <div className="mt-4">
              <span className="font-mono text-5xl font-medium tracking-[-0.05em] text-signal tnum">{pilot.energy.span.toFixed(2)}×</span>
              <p className="mt-2 text-sm font-semibold">E(32) / E(1)</p>
              <p className="mt-1 text-xs text-muted-foreground">{pilot.energy.e32} vs {pilot.energy.e1} J per correct answer</p>
            </div>

            <dl className="mt-5 divide-y divide-line border-y border-line">
              {[
                ["E(1)", `${pilot.energy.e1} J/correct`],
                ["E(4)", `${pilot.energy.e4} J/correct`],
                ["E(32)", `${pilot.energy.e32} J/correct`],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between gap-3 py-2.5">
                  <dt className="font-mono text-xs text-muted-foreground">{label}</dt>
                  <dd className="font-mono text-sm tabular-nums">{value}</dd>
                </div>
              ))}
            </dl>

            <div className="mt-5">
              <p className="eyebrow">Affine fit</p>
              <p className="mt-2 font-mono text-sm">{pilot.fit.formula} J</p>
              <p className="mt-1 font-mono text-xs text-data">R² = {pilot.fit.r2.toFixed(4)}</p>
            </div>

            <p className="mt-4 border-t border-line pt-3 text-xs leading-relaxed text-muted-foreground">
              The slope is {pilot.fit.b} J per passage; the intercept is {pilot.fit.a} J. The fit
              is affine on this depth grid and should not be extrapolated past it.
            </p>
          </div>
        </div>

        <div className="panel mt-4 overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
            <span className="eyebrow">Documented arithmetic at three depths</span>
            <Chip tone="caution" dot>
              Pilot
            </Chip>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[420px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-line bg-panel-soft">
                  <th className="px-4 py-2 text-left font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">Depth</th>
                  <th className="px-4 py-2 text-right font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">J(k)</th>
                  <th className="px-4 py-2 text-right font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">A(k)</th>
                  <th className="px-4 py-2 text-right font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">E(k)</th>
                </tr>
              </thead>
              <tbody>
                {[
                  [1, pilot.energyMeans.j1, pilot.accuracy.a1, pilot.energy.e1],
                  [4, pilot.energyMeans.j4, pilot.accuracy.a4, pilot.energy.e4],
                  [32, pilot.energyMeans.j32, pilot.accuracy.a32, pilot.energy.e32],
                ].map(([k, j, a, e]) => (
                  <tr key={String(k)} className="border-t border-line">
                    <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">k = {k}</td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums">{Number(j).toFixed(2)} J</td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums">{Number(a).toFixed(3)}</td>
                    <td className="px-4 py-2.5 text-right font-mono font-medium tabular-nums text-signal">{Number(e).toFixed(1)} J</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="border-t border-line px-4 py-3 text-xs leading-relaxed text-muted-foreground">
            These are the pilot’s documented worked-example values. They illustrate the arithmetic
            of E(k) = J(k) / A(k); they are not new estimates.
          </p>
        </div>
      </section>

      {/* Accuracy / dead claim */}
      <section aria-labelledby="accuracy-results" className="mt-16">
        <SectionHeading
          index="02"
          eyebrow="Accuracy and the dead claim"
          id="accuracy-results"
          title={
            <>
              Accuracy plateaus. <em>The 2 pp gate runs to the boundary.</em>
            </>
          }
          description="The accuracy side was underpowered at n = 200. The 2 pp margin could not be certified, so it is no longer a decision rule."
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <AccuracyChart />

          <div className="panel relative overflow-hidden p-5 sm:p-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="eyebrow">Static 2 pp claim</p>
                <h3 className="mt-2 text-base font-semibold">The original headline</h3>
              </div>
              <span className="stamp">Dead</span>
            </div>

            <div className="mt-5 space-y-4">
              <div>
                <p className="font-mono text-4xl font-medium tracking-[-0.04em] text-dead tnum">k* = 32</p>
                <p className="mt-1 text-xs text-muted-foreground">The grid boundary, not an interior optimum.</p>
              </div>
              <div className="border-t border-line pt-4">
                <p className="font-mono text-2xl font-medium tracking-[-0.03em] tnum">
                  P(k* optimal) = 0.61
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Below the 0.8 threshold. The selection is not stable enough to certify.
                </p>
              </div>
            </div>

            <div className="mt-5 border-l-2 border-dead pl-4">
              <p className="text-sm font-semibold">Power failure, not a flat-curve failure.</p>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                The MDE at n = 200 was roughly 4–5 pp. The paired accuracy interval for k = 16
                includes the 2 pp floor. The 2 pp margin is estimation-only in the rerun.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Context share */}
      <section aria-labelledby="share-results" className="mt-16">
        <SectionHeading
          index="03"
          eyebrow="Where the energy goes"
          id="share-results"
          title={
            <>
              The green lever is <em>prefill, not the fetch.</em>
            </>
          }
          description="The context-side share rises from 36.3% at k = 2 to 85.1% at k = 32. Retrieval alone is a small, proxy-estimated slice."
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="panel p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-semibold">Context-side share</h3>
              <PilotChip />
            </div>
            <div className="mt-5">
              <ContextShareChart />
            </div>
          </div>

          <div className="space-y-4">
            <FormulaBlock
              label="Share definitions"
              note="S(k) uses J_ret + J_pre. S_r(k) uses only J_ret and the CPU proxy. They are different quantities."
            >
              <div className="space-y-2 text-sm sm:text-base">
                <p>S(k) = (J_ret(k) + J_pre(k)) / J(k)</p>
                <p>S_r(k) = J_ret(k) / J(k)</p>
              </div>
            </FormulaBlock>

            <Callout tone="data" title="The retrieval share is an upper bound" icon={<CircleHelp className="h-4 w-4" />}>
              BM25 runs on the CPU and is not captured by NVML. It is estimated as wall time × 20 W
              single-thread active-above-idle: 0.149 s → 3.11 J/query in the pilot. At 10–15 W the
              term would be 1.6–2.3 J, lowering E by under 1.5%.
            </Callout>

            <div className="panel p-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="eyebrow">At k = 2</p>
                  <p className="mt-2 font-mono text-2xl text-signal">36.3%</p>
                  <p className="mt-1 text-xs text-muted-foreground">context-side</p>
                </div>
                <div>
                  <p className="eyebrow">At k = 32</p>
                  <p className="mt-2 font-mono text-2xl text-data">85.1%</p>
                  <p className="mt-1 text-xs text-muted-foreground">context-side</p>
                </div>
              </div>
              <p className="mt-4 border-t border-line pt-3 text-xs leading-relaxed text-muted-foreground">
                Passing more passages costs prefill and decode energy. The BM25 fetch is not the
                dominant term at high depth.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Identity / repeatability */}
      <section aria-labelledby="identity-results" className="mt-16">
        <SectionHeading
          index="04"
          eyebrow="Theory diagnostics"
          id="identity-results"
          title={
            <>
              The identity holds inside. <em>It fails at the boundary.</em>
            </>
          }
          description="The elasticity gap is a local diagnostic. At k = 2 the interval includes zero; at k = 32 the gap is large and flags over-retrieval."
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="panel p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-semibold">Identity gap, ε_J − ε_A</h3>
              <PilotChip />
            </div>
            <div className="mt-4">
              <IdentityPlot />
            </div>
            <p className="mt-3 border-t border-line pt-3 text-xs leading-relaxed text-muted-foreground">
              At k = 2, the gap is +0.044 with a 95% CI of [−0.050, +0.128]. At k = 32, the gap is
              +0.700. A point estimate without a CI is not given a fabricated interval here.
            </p>
          </div>

          <div className="space-y-4">
            <div className="panel p-5">
              <p className="eyebrow">What this supports</p>
              <ul className="mt-3 space-y-2 text-sm leading-relaxed text-muted-foreground">
                <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal" aria-hidden />The identity is a useful local diagnostic at an interior optimum.</li>
                <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal" aria-hidden />It correctly flags over-retrieval at high k.</li>
                <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-dead" aria-hidden />It does not certify high-k behaviour or a global optimum.</li>
              </ul>
            </div>

            <div className="panel p-5">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="eyebrow">Repeatability at k = 8</p>
                  <p className="mt-2 font-mono text-3xl font-medium tracking-[-0.04em] text-signal tnum">
                    {pilot.repeatCv.median.toFixed(2)}%
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">median CV · max {pilot.repeatCv.max}%</p>
                </div>
                <PilotChip />
              </div>
              <p className="mt-4 border-t border-line pt-3 text-xs leading-relaxed text-muted-foreground">
                Three blocks of 20 identical queries. The pilot’s noise floor is usable for the
                energy curve, which is why the energy effect is not in question.
              </p>
            </div>

            <Callout tone="caution" title="The coverage fit failed">
              A₀ = 0.324, p = 0.0218, R² = 0.332. Global unimodality is rejected; the identity
              remains a local diagnostic. This is why the rerun tests the identity at the selected
              interior depth rather than claiming a global law.
            </Callout>
          </div>
        </div>
      </section>

      {/* Full table */}
      <section aria-labelledby="table-heading" className="mt-16">
        <SectionHeading
          index="05"
          eyebrow="The ledger"
          id="table-heading"
          title={
            <>
              Every pilot value, <em>with its status.</em>
            </>
          }
          description="The table is the site's complete pilot claim set. A status is part of the value: supported, dead, rejected, pilot signal, or upper bound."
        />

        <div className="panel mt-8 overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
            <span className="eyebrow">Pilot evidence table</span>
            <PilotChip />
          </div>
          <div className="hidden border-b border-line bg-panel-soft px-4 py-2.5 md:grid md:grid-cols-[1.05fr_1.5fr_0.6fr_1.1fr] md:gap-3">
            <span className="eyebrow">Quantity</span>
            <span className="eyebrow">Value</span>
            <span className="eyebrow">Status</span>
            <span className="eyebrow">Note</span>
          </div>
          {pilotTable.map((row) => (
            <div
              key={row.quantity}
              className="grid gap-2 border-t border-line px-4 py-4 first:border-t-0 md:grid-cols-[1.05fr_1.5fr_0.6fr_1.1fr] md:items-start md:gap-3"
            >
              <p className="text-sm font-semibold leading-snug">{row.quantity}</p>
              <p className="font-mono text-xs leading-relaxed">{row.value}</p>
              <div className="md:justify-self-start">
                <StatusTag status={row.status} />
              </div>
              <p className="text-xs leading-relaxed text-muted-foreground">{row.note}</p>
            </div>
          ))}
        </div>
        <SourceNote>
          Source: README.md §Status, ROADMAP.md §1.1, docs/PILOT_EVIDENCE.md,
          docs/proposal.md Appendix A, prereg/PREREGISTRATION.md §1. Values are transcribed; run
          IDs are not invented.
        </SourceNote>
      </section>

      {/* Board */}
      <section aria-labelledby="board-heading" className="mt-16">
        <SectionHeading
          index="06"
          eyebrow="What survived / what died"
          id="board-heading"
          title={
            <>
              Keep the measurements. <em>Retire the headline.</em>
            </>
          }
          description="The pilot is not a failed project. It is a precise energy measurement and a failed accuracy certification. Both belong in the record."
        />
        <div className="mt-8">
          <ClaimLedger />
        </div>
      </section>

      {/* 5 pp */}
      <section aria-labelledby="five-heading" className="mt-16">
        <SectionHeading
          index="07"
          eyebrow="The 5 pp signal"
          id="five-heading"
          title={
            <>
              At 5 pp, the pilot picked k = 4. <em>That is a signal, not a certificate.</em>
            </>
          }
          description="The 5 pp margin is the primary decision in the rerun. The pilot estimate is promising, but n = 200 and the certification is not there."
        />

        <div className="instrument mt-8 p-5 sm:p-7">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="inst-label">Pilot / 5 pp margin</span>
                <span className="border border-[rgba(251,191,36,0.4)] bg-[rgba(251,191,36,0.1)] px-2 py-1 font-mono text-[9px] uppercase tracking-[0.14em] text-[#fbbf24]">
                  Pilot signal · not certified
                </span>
              </div>
              <div className="mt-5 grid grid-cols-2 gap-5 sm:grid-cols-4">
                {[
                  ["k", String(pilot.fivePp.k)],
                  ["Savings", `${pilot.fivePp.savings}%`],
                  ["N*", String(pilot.fivePp.nStar)],
                  ["P (reported)", pilot.fivePp.pReported.toFixed(3).replace(/^0/, "")],
                ].map(([label, value]) => (
                  <div key={label}>
                    <p className="inst-label">{label}</p>
                    <p className="mt-1 font-mono text-3xl font-medium tracking-[-0.04em] text-[#eef3e5] tabular-nums sm:text-4xl">
                      {value}
                    </p>
                  </div>
                ))}
              </div>
              <p className="inst-muted mt-5 max-w-xl text-sm leading-relaxed">
                The proposal reports P = {pilot.fivePp.pReported} for the 5 pp selection. No pilot
                non-inferiority test is reported. The rerun must report the NI test and the
                selection probability separately; they are not the same quantity, and neither is a
                certification.
              </p>
            </div>

            <div className="border-t border-[rgba(200,240,79,0.16)] pt-5 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
              <p className="inst-label">What N* means</p>
              <p className="mt-3 text-sm leading-relaxed text-[#eef3e5]">
                N* = 876 is a descriptive break-even: the number of deployment queries at which the
                k = 4 saving repays the pilot sweep energy. It is not a deployment guarantee.
              </p>
              <p className="inst-muted mt-3 text-xs leading-relaxed">
                The pilot sweep cost {pilot.sweepKj} kJ. N* = {pilot.nStar[1].n.toLocaleString("en-US")} for k = {pilot.nStar[1].k} and {pilot.nStar[2].n.toLocaleString("en-US")} for k = {pilot.nStar[2].k}. At {pilot.savingsAt.queries.toLocaleString("en-US")}
                queries, the k = {pilot.fivePp.k} saving is {pilot.savingsAt.kj} kJ and calibration is {pilot.savingsAt.calibrationShareOfSavingPct}% of that saving; at
                100,000, calibration is {pilot.calibrationShareAt100kPct}% of the saving.
              </p>
              <div className="mt-4 border border-[rgba(251,191,36,0.25)] bg-[rgba(251,191,36,0.06)] p-3">
                <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-[#fbbf24]">
                  Required before “certified”
                </p>
                <p className="mt-1 text-xs leading-relaxed text-[#c9d6c9]">
                  Prereg freeze · powered n = {rerun.primary.n.toLocaleString("en-US")} run · one-sided 5 pp NI test · ≥20% savings ·
                  G1/G2 adjudication. None has happened yet.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Oracle */}
      <section aria-labelledby="oracle-heading" className="mt-16">
        <SectionHeading
          index="08"
          eyebrow="The ceiling"
          id="oracle-heading"
          title={
            <>
              The oracle is a ceiling, <em>not a learned policy.</em>
            </>
          }
          description={`The ${pilot.oracle.gain}% figure chooses the cheapest correct depth per query with hindsight. No policy was trained. Reporting it as a policy gain would be fabricated.`}
        />

        <div className="panel mt-8 overflow-hidden">
          <div className="grid lg:grid-cols-[0.9fr_1.1fr]">
            <div className="border-b border-line p-5 sm:p-7 lg:border-b-0 lg:border-r">
              <div className="flex items-center justify-between gap-2">
                <span className="eyebrow">Adaptive oracle</span>
                <span className="stamp">Upper bound</span>
              </div>
              <p className="mt-6 font-mono text-6xl font-medium tracking-[-0.06em] text-caution tnum">
                {pilot.oracle.gain}%
              </p>
              <p className="mt-2 text-sm font-semibold">matched-accuracy gain</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Computed with hindsight from the pilot. No policy exists.
              </p>
            </div>
            <div className="p-5 sm:p-7">
              <p className="eyebrow">What would make it a result</p>
              <ul className="mt-3 space-y-2 text-sm leading-relaxed text-muted-foreground">
                <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal" aria-hidden />A policy trained on 600 questions and selected on 200 validation questions.</li>
                <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal" aria-hidden />One evaluation on 200 held-out questions at matched accuracy.</li>
                <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal" aria-hidden />Oracle gain ≥ 20% and capture ≥ 50% for G4.</li>
                <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-dead" aria-hidden />No test-set tuning. No report of the oracle as a learned gain.</li>
              </ul>
              <div className="mt-4 border-t border-line pt-3">
                <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                  Capture
                </p>
                <p className="mt-1 font-mono text-sm">
                  (E_static − E_policy) / (E_static − E_oracle)
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Provenance */}
      <section aria-labelledby="provenance-heading" className="mt-16">
        <SectionHeading
          index="09"
          eyebrow="Provenance"
          id="provenance-heading"
          title={
            <>
              What this page is, <em>and what it is not.</em>
            </>
          }
        />
        <div className="mt-8 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <FlaskConical className="h-4 w-4 text-caution" aria-hidden />
              <h3 className="text-sm font-semibold">Transcribed, not regenerated</h3>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              Every number on this page comes from README.md, ROADMAP.md,
              docs/IMPLEMENTATION_PLAN.md, docs/MEASUREMENT.md, docs/DATA_CARD.md,
              docs/proposal.md, or prereg/PREREGISTRATION.md. The pilot raw CSVs are not in this
              repository. The values are transcribed from the repository record, not independently
              reproduced here.
            </p>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              No confidence interval, p-value, run ID, or sample size has been added to make a
              figure look stronger. Where the record does not report a value, this page does not
              show one.
            </p>
          </div>

          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <ShieldX className="h-4 w-4 text-dead" aria-hidden />
              <h3 className="text-sm font-semibold">What is not here</h3>
            </div>
            <ul className="mt-3 space-y-2 text-sm leading-relaxed text-muted-foreground">
              <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-dead" aria-hidden />No confirmatory accuracy or energy results.</li>
              <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-dead" aria-hidden />No certified 5 pp result.</li>
              <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-dead" aria-hidden />No learned-policy gain.</li>
              <li className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-dead" aria-hidden />No universal optimum, carbon claim, or frontier/dense-retriever generalization.</li>
            </ul>
            <div className="mt-4 flex flex-wrap gap-2 border-t border-line pt-4">
              <Link href="/research" className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-signal">
                Research design <ArrowRight className="h-3.5 w-3.5" aria-hidden />
              </Link>
              <Link href="/roadmap" className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground hover:text-foreground">
                Roadmap <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
              </Link>
              <a
                href={`${project.repo}/blob/main/docs/PILOT_EVIDENCE.md`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground hover:text-foreground"
              >
                Pilot evidence table <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
              </a>
            </div>
          </div>
        </div>
        <SourceNote>
          Source documents are tracked in the repository. A result is not a result until it traces
          to runs/&lt;run_id&gt;/raw.csv and is mapped in artifacts/claims_evidence.csv.
        </SourceNote>
      </section>
    </div>
  );
}
