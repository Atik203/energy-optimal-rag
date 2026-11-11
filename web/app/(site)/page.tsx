import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  CircleCheck,
  CircleX,
  Cpu,
  Database,
  Flame,
  Gauge,
  GitBranch,
  Presentation,
  ScanLine,
  ShieldCheck,
} from "lucide-react";
import {
  claimBoundary,
  pilot,
  project,
  rerun,
} from "@/lib/project-data";
import {
  Callout,
  Chip,
  FormulaBlock,
  PilotChip,
  SectionHeading,
  SourceNote,
  StatBlock,
} from "@/components/ui";
import { ClaimLedger } from "@/components/claim-ledger";
import { DepthRuler, EnergyBars } from "@/components/charts";

const heroMetrics = [
  {
    label: "Energy span",
    value: pilot.energy.span.toFixed(2),
    unit: "×",
    note: `E(32) ${pilot.energy.e32} vs E(1) ${pilot.energy.e1} J per correct answer.`,
    tone: "signal" as const,
  },
  {
    label: "Context-side share",
    value: pilot.contextShare.at32.toFixed(1),
    unit: "%",
    note: `At k = 32; ${pilot.contextShare.at2}% at k = 2. Retrieval-only proxy ${pilot.retrievalShare.min}–${pilot.retrievalShare.max}%.`,
    tone: "data" as const,
  },
  {
    label: "2 pp selection",
    value: `P=${pilot.static2pp.pOptimal.toFixed(2)}`,
    note: `P(k* optimal) below the ${pilot.static2pp.threshold} gate. The static 2 pp claim is DEAD.`,
    tone: "dead" as const,
  },
  {
    label: `5 pp savings at k = ${pilot.fivePp.k}`,
    value: pilot.fivePp.savings.toFixed(1),
    unit: "%",
    note: "Pilot signal, not certified. The powered rerun decides.",
    tone: "caution" as const,
  },
];

const rerunCards = [
  {
    index: "01",
    value: String(rerun.replication.n),
    title: "Reader replication",
    detail: `${rerun.replication.reader} on SQuAD, same seven depths.`,
    icon: Cpu,
  },
  {
    index: "02",
    value: String(rerun.hotpot.n),
    title: "Distractor stress",
    detail: `HotpotQA distractor, k ∈ {${rerun.hotpot.depths.join(",")}}; no paragraph pooling.`,
    icon: Database,
  },
  {
    index: "03",
    value: String(rerun.boundary.n),
    title: "Boundary probe",
    detail: `k ∈ {${rerun.boundary.depths.join(",")}}, plus a 16k-token context check.`,
    icon: ScanLine,
  },
  {
    index: "04",
    value: String(rerun.taxes.n),
    title: "Energy taxes",
    detail: `Per condition. Fixed tax and per-passage tax, ${rerun.taxes.n} questions each.`,
    icon: Flame,
  },
  {
    index: "05",
    value: `${rerun.policy.train}/${rerun.policy.validation}/${rerun.policy.test}`,
    title: "Learned policy",
    detail: "Target counts; hashed assignment; test touched once.",
    icon: GitBranch,
  },
];

const nextLinks = [
  { href: "/research", label: "Research", note: "Question, hypotheses, theory, gates" },
  { href: "/method", label: "Method", note: "Pipeline, measurement, data, policy" },
  { href: "/results", label: "Results", note: "Pilot evidence and the dead claim" },
  { href: "/roadmap", label: "Roadmap", note: "P0–P6, budget, risks, decisions" },
];

export default function HomePage() {
  return (
    <div className="pb-2">
      {/* Hero */}
      <section aria-labelledby="hero-title" className="grid items-center gap-10 pt-8 sm:pt-12 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)] lg:gap-14">
        <div className="animate-rise">
          <div className="flex flex-wrap items-center gap-2">
            <Chip tone="caution" dot>
              Pilot evidence
            </Chip>
            <span className="eyebrow">Public scaffold v{project.version}</span>
          </div>

          <h1
            id="hero-title"
            className="display-title mt-6 text-[2.55rem] leading-[0.99] sm:text-6xl lg:text-[4.55rem]"
          >
            What does a<br />
            correct answer <em>cost?</em>
          </h1>

          <p className="mt-6 max-w-xl text-[1.02rem] leading-relaxed text-muted-foreground sm:text-lg">
            Retrieval depth in RAG, measured in joules per correct answer. The pilot found a
            steep energy–depth tradeoff — and killed its own 2 pp claim. The 5 pp signal is
            waiting for a powered rerun.
          </p>

          <div className="mt-5 flex flex-wrap gap-2">
            <Chip tone="caution" dot>
              Post-pilot MARGINAL
            </Chip>
            <Chip tone="dead" dot>
              No confirmatory results
            </Chip>
            <Chip tone="neutral">Prereg not frozen</Chip>
          </div>

          <div className="mt-7 flex flex-wrap items-center gap-3">
            <Link
              href="/results"
              className="inline-flex items-center gap-2 rounded-[3px] bg-signal px-4 py-2.5 text-sm font-semibold text-signal-foreground transition-transform hover:-translate-y-0.5"
            >
              Read the pilot evidence
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
            <Link
              href="/slide"
              className="inline-flex items-center gap-2 rounded-[3px] border border-line-strong px-4 py-2.5 text-sm font-semibold transition-colors hover:border-signal hover:text-signal"
            >
              <Presentation className="h-4 w-4" aria-hidden />
              The 15-slide deck
            </Link>
          </div>

          <p className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
            <span className="text-caution">Pilot</span>
            <span>{pilot.questions} SQuAD questions</span>
            <span aria-hidden>·</span>
            <span>{pilot.depths.length} depths</span>
            <span aria-hidden>·</span>
            <span>{pilot.generations.toLocaleString("en-US")} generations</span>
            <span aria-hidden>·</span>
            <span>{pilot.gpu}</span>
          </p>
        </div>

        {/* Instrument console */}
        <div className="animate-rise [animation-delay:120ms]">
          <div className="instrument p-4 sm:p-5">
            <div className="instrument-grid pointer-events-none absolute inset-0" aria-hidden="true" />
            <div className="relative">
              <div className="inst-rule flex flex-wrap items-center justify-between gap-2 border-b pb-3">
                <span className="inst-label">Joule observatory / pilot</span>
                <span className="inst-signal inline-flex items-center gap-2 font-mono text-[9px] uppercase tracking-[0.16em]">
                  <span className="h-1.5 w-1.5 animate-blink rounded-full bg-[#c8f04f]" aria-hidden />
                  Recording
                </span>
              </div>

              <div className="mt-4 flex items-end justify-between gap-3">
                <div>
                  <p className="inst-label">Energy per correct answer</p>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span className="inst-signal font-mono text-4xl font-medium tracking-[-0.05em] tnum sm:text-5xl">
                      {pilot.energy.span.toFixed(2)}×
                    </span>
                    <span className="inst-muted font-mono text-[10px]">E(32) / E(1)</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="inst-label">J / correct</p>
                  <p className="inst-muted mt-1 font-mono text-[10px]">{pilot.energy.e32} / {pilot.energy.e1}</p>
                </div>
              </div>

              <div className="mt-5">
                <EnergyBars />
              </div>

              <div className="mt-5">
                <DepthRuler />
              </div>

              <div className="inst-rule mt-5 grid grid-cols-2 gap-px overflow-hidden rounded-[2px] border bg-[rgba(200,240,79,0.12)] sm:grid-cols-4">
                {[
                  ["n", pilot.questions.toLocaleString("en-US")],
                  ["gens", pilot.generations.toLocaleString("en-US")],
                  ["passages", pilot.passages.toLocaleString("en-US")],
                  ["R²", pilot.fit.r2.toFixed(4)],
                ].map(([label, value]) => (
                  <div key={label} className="bg-[#0a1a12] p-2.5">
                    <p className="inst-label">{label}</p>
                    <p className="mt-1 font-mono text-sm tabular-nums text-[#eef3e5]">{value}</p>
                  </div>
                ))}
              </div>

              <p className="inst-muted mt-3 text-[10px] leading-relaxed">
                Pilot measurements only. Three documented E(k) points are shown; all seven depths
                were measured. Not confirmatory.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Metric strip */}
      <section aria-label="Pilot metrics" className="mt-12 sm:mt-16">
        <div className="grid grid-cols-2 gap-px overflow-hidden rounded-[4px] border border-line bg-line lg:grid-cols-4">
          {heroMetrics.map((metric) => (
            <div key={metric.label} className="bg-panel p-4 sm:p-5">
              <div className="flex items-center justify-between gap-2">
                <span className="eyebrow !text-[9px]">{metric.label}</span>
                <PilotChip />
              </div>
              <div className="mt-4">
                <StatBlock
                  value={metric.value}
                  unit={metric.unit}
                  label=""
                  note={metric.note}
                  tone={metric.tone}
                />
              </div>
            </div>
          ))}
        </div>
        <p className="mt-2 text-right font-mono text-[9px] uppercase tracking-[0.14em] text-muted-foreground">
          All four values are pilot evidence · not confirmatory
        </p>
      </section>

      {/* The question */}
      <section aria-labelledby="question-heading" className="mt-16 sm:mt-20">
        <SectionHeading
          index="01"
          eyebrow="The question"
          id="question-heading"
          title={
            <>
              Accuracy buys passages. Passages cost joules.{" "}
              <em>The decision is the exchange rate.</em>
            </>
          }
          description="The object is a gated ratio, a margin-indexed policy, and the energy cost of learning it. The pilot changed which of those objects survives."
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          <FormulaBlock
            label="Primary estimand"
            note="Total joules over total correct answers — not the mean of per-query ratios. Every E(k) is reported with A(k) and the gate."
          >
            <div className="text-[1.35rem] sm:text-[1.6rem]">
              E(k) = Σ J<sub>k</sub>(q) / Σ C<sub>k</sub>(q)
            </div>
          </FormulaBlock>

          <div className="panel flex flex-col p-5">
            <div className="flex items-center justify-between gap-3">
              <span className="eyebrow">Decision gate</span>
              <ShieldCheck className="h-4 w-4 text-data" aria-hidden />
            </div>
            <p className="mt-4 font-mono text-lg">A_min = A(32) − 0.05</p>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              Primary margin: 5 pp EM. The 2 pp margin is estimated with a confidence interval,
              never used for certification.
            </p>
          </div>

          <div className="panel flex flex-col p-5">
            <div className="flex items-center justify-between gap-3">
              <span className="eyebrow">Certification</span>
              <Gauge className="h-4 w-4 text-caution" aria-hidden />
            </div>
            <p className="mt-4 font-mono text-[0.92rem] leading-relaxed">
              N* = C_cert / [A(k*)(E(k₀) − E(k*))]
            </p>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              Finding the depth is itself an energy purchase. N* is reported descriptively, per
              dataset and reader.
            </p>
          </div>
        </div>

        <div className="mt-5 flex items-center justify-between gap-4 border-t border-line pt-4">
          <Callout tone="caution" className="max-w-2xl">
            The ratio can be gamed by failing cheaply. The accuracy gate is what makes{" "}
            <span className="font-mono text-foreground">E(k)</span> a decision object rather than
            a cost-per-answer trick.
          </Callout>
          <Link
            href="/research"
            className="hidden shrink-0 items-center gap-1.5 text-sm font-semibold text-muted-foreground transition-colors hover:text-foreground sm:inline-flex"
          >
            Research design
            <ArrowUpRight className="h-4 w-4" aria-hidden />
          </Link>
        </div>
      </section>

      {/* Survived / died */}
      <section aria-labelledby="ledger-heading" className="mt-16 sm:mt-20">
        <SectionHeading
          index="02"
          eyebrow="The pilot ledger"
          id="ledger-heading"
          title={
            <>
              Six measurements survived. <em>The headline did not.</em>
            </>
          }
          description="The pilot was precise about energy and underpowered about accuracy. That asymmetry is the result, not a footnote."
        />
        <div className="mt-8">
          <ClaimLedger />
        </div>
        <SourceNote>
          Source: README.md, ROADMAP.md §1.1, docs/proposal.md Appendix A, prereg/PREREGISTRATION.md §1.
          Pilot numbers are transcribed from the repository record; the pilot raw CSVs are not in
          this repository.
        </SourceNote>
      </section>

      {/* Powered rerun */}
      <section aria-labelledby="rerun-heading" className="mt-16 sm:mt-20">
        <SectionHeading
          index="03"
          eyebrow="The powered rerun"
          id="rerun-heading"
          title={
            <>
              The rerun is built around <em>the failure.</em>
            </>
          }
          description={`The pilot's minimum detectable effect was roughly ${pilot.mdeAt200} at n = ${pilot.questions}. The rerun is sized for a ${rerun.primary.marginPp} pp decision and treats ${rerun.primary.secondaryMarginPp} pp as estimation-only.`}
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="instrument p-5 sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="inst-label">Primary decision / P1</span>
              <span className="inst-caution font-mono text-[9px] uppercase tracking-[0.14em]">
                Planning target
              </span>
            </div>
            <p className="mt-4 font-mono text-3xl tracking-[-0.03em] text-[#eef3e5] sm:text-4xl">
              k = {rerun.primary.candidateK} <span className="inst-muted text-lg">vs</span> k = {rerun.primary.referenceK}
            </p>
            <p className="mt-2 text-sm font-semibold text-[#eef3e5]">
              {rerun.primary.marginPp} pp EM non-inferiority · one-sided α = 0.05
            </p>
            <p className="inst-muted mt-1 text-sm leading-relaxed">
              At least {rerun.primary.minSavingsPct}% energy savings required. The {rerun.primary.secondaryMarginPp} pp margin is reported with a CI and is
              never a certification target.
            </p>

            <div className="inst-rule mt-5 grid grid-cols-2 gap-px overflow-hidden rounded-[2px] border bg-[rgba(200,240,79,0.12)]">
              {[
                ["n", rerun.primary.n.toLocaleString("en-US")],
                ["depths", String(rerun.primary.depths.length)],
                ["MDE", rerun.power.mdeAt1000],
                ["95% half-width", rerun.power.halfWidthAt1000],
              ].map(([label, value]) => (
                <div key={label} className="bg-[#0a1a12] p-3">
                  <p className="inst-label">{label}</p>
                  <p className="mt-1 font-mono text-lg tabular-nums text-[#eef3e5]">{value}</p>
                </div>
              ))}
            </div>
            <p className="inst-muted mt-3 text-[10px] leading-relaxed">
              Power values are from the planning table, not results. Rerun reader: {rerun.primary.reader};
              dataset: {rerun.primary.dataset}.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {rerunCards.map((card) => {
              const Icon = card.icon;
              return (
                <div key={card.title} className="panel p-4">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-muted-foreground">{card.index}</span>
                    <Icon className="h-4 w-4 text-data" aria-hidden />
                  </div>
                  <p className="mt-3 font-mono text-xl font-medium tabular-nums">{card.value}</p>
                  <p className="mt-1 text-sm font-semibold">{card.title}</p>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{card.detail}</p>
                </div>
              );
            })}
            <div className="panel flex items-center justify-between gap-3 p-4 sm:col-span-2">
              <div>
                <p className="text-sm font-semibold">All gates are pre-registered.</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  G1–G5. A fired gate is a finding, not a tune-up.
                </p>
              </div>
              <Link
                href="/roadmap"
                className="inline-flex shrink-0 items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-signal"
              >
                Roadmap
                <ArrowRight className="h-3.5 w-3.5" aria-hidden />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Claim boundary */}
      <section aria-labelledby="boundary-heading" className="mt-16 sm:mt-20">
        <SectionHeading
          index="04"
          eyebrow="Claim boundary"
          id="boundary-heading"
          title={
            <>
              The boundary is part of <em>the result.</em>
            </>
          }
          description="A fired gate is reported, not tuned away. A negative result is a result. The site uses the same language as the repository record."
        />

        <div className="panel mt-8 overflow-hidden">
          <div className="grid md:grid-cols-2">
            <div className="border-b border-line p-5 sm:p-6 md:border-b-0 md:border-r">
              <p className="eyebrow !text-dead">Not claimed</p>
              <ul className="mt-4 space-y-3">
                {claimBoundary.notClaimed.map((item) => (
                  <li key={item} className="flex gap-3 text-sm leading-relaxed text-muted-foreground">
                    <CircleX className="mt-0.5 h-4 w-4 shrink-0 text-dead" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="p-5 sm:p-6">
              <p className="eyebrow !text-signal">What may be claimed now</p>
              <ul className="mt-4 space-y-3">
                {claimBoundary.mayClaim.map((item) => (
                  <li key={item} className="flex gap-3 text-sm leading-relaxed text-muted-foreground">
                    <CircleCheck className="mt-0.5 h-4 w-4 shrink-0 text-signal" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="border-t border-line bg-panel-soft p-5 sm:p-6">
            <div className="flex flex-wrap items-center gap-2">
              <span className="eyebrow">The defensible next claim</span>
              <Chip tone="caution">If the rerun supports it</Chip>
            </div>
            <blockquote className="display-title mt-3 max-w-4xl text-xl leading-[1.2] sm:text-2xl">
              “{claimBoundary.nextClaim}”
            </blockquote>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
              {claimBoundary.nextClaimNote}
            </p>
          </div>
        </div>
      </section>

      {/* Slides CTA */}
      <section aria-labelledby="deck-heading" className="mt-16 sm:mt-20">
        <div className="instrument p-6 sm:p-8 lg:p-10">
          <div className="instrument-grid pointer-events-none absolute inset-0" aria-hidden="true" />
          <div className="relative grid items-center gap-8 lg:grid-cols-[1.05fr_0.95fr]">
            <div>
              <p className="inst-label">Presentation / 15 slides</p>
              <h2
                id="deck-heading"
                className="display-title mt-4 text-3xl text-[#eef3e5] sm:text-4xl lg:text-5xl"
              >
                The whole argument, in <em className="text-[#c8f04f]">16:9.</em>
              </h2>
              <p className="mt-4 max-w-xl text-sm leading-relaxed text-[#8aa294]">
                A keyboard-driven deck for a supervisor meeting or a conference screen. Light
                slides, dark text, large type, and the pilot failure left visible.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/slide"
                  className="inline-flex items-center gap-2 rounded-[3px] bg-[#c8f04f] px-4 py-2.5 text-sm font-semibold text-[#0a1408] transition-transform hover:-translate-y-0.5"
                >
                  <Presentation className="h-4 w-4" aria-hidden />
                  Open the deck
                </Link>
                <Link
                  href="/results"
                  className="inline-flex items-center gap-2 rounded-[3px] border border-[rgba(200,240,79,0.28)] px-4 py-2.5 text-sm font-semibold text-[#eef3e5] transition-colors hover:border-[#c8f04f]"
                >
                  Read the evidence
                  <ArrowRight className="h-4 w-4" aria-hidden />
                </Link>
              </div>
              <p className="mt-4 font-mono text-[9px] uppercase tracking-[0.14em] text-[#8aa294]">
                ← → · space · home / end · F fullscreen
              </p>
            </div>

            <div className="relative mx-auto h-56 w-full max-w-md" aria-hidden="true">
              <div className="absolute inset-0 translate-x-3 translate-y-3 rotate-2 rounded-[2px] border border-[rgba(200,240,79,0.18)] bg-[#0a1a12]" />
              <div className="absolute inset-0 -translate-x-2 translate-y-1 -rotate-1 rounded-[2px] border border-[rgba(200,240,79,0.22)] bg-[#e9e4d5]" />
              <div className="absolute inset-0 flex flex-col justify-between rounded-[2px] border border-[rgba(0,0,0,0.1)] bg-[#f7f3e7] p-4 shadow-2xl">
                <div className="flex items-center justify-between font-mono text-[7px] uppercase tracking-[0.18em] text-[#3f5549]">
                  <span>Energy Observatory</span>
                  <span>04 / 15</span>
                </div>
                <div>
                  <div className="h-1 w-10 bg-[#1d5a3e]" />
                  <p className="mt-2 max-w-[16rem] font-serif text-lg leading-tight text-[#10231b]">
                    Energy per correct answer rises {pilot.energy.span.toFixed(2)}× from k = 1 to k = 32.
                  </p>
                </div>
                <div className="flex items-end justify-between">
                  <div className="flex items-end gap-1.5">
                    <div className="h-5 w-6 bg-[#1d5a3e]" />
                    <div className="h-6 w-6 bg-[#a16207]" />
                    <div className="h-16 w-6 bg-[#0f766e]" />
                  </div>
                  <span className="font-mono text-[8px] uppercase tracking-[0.14em] text-[#3f5549]">
                    Pilot
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Next */}
      <section aria-labelledby="next-heading" className="mt-14">
        <h2 id="next-heading" className="eyebrow">
          Continue reading
        </h2>
        <div className="mt-3 grid gap-px overflow-hidden rounded-[4px] border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
          {nextLinks.map((link, index) => (
            <Link
              key={link.href}
              href={link.href}
              className="group bg-panel p-4 transition-colors hover:bg-panel-soft"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] text-muted-foreground">0{index + 1}</span>
                <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-colors group-hover:text-signal" aria-hidden />
              </div>
              <p className="mt-3 text-sm font-semibold">{link.label}</p>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{link.note}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
