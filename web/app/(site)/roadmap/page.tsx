import type { Metadata } from "next";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  Ban,
  FlaskConical,
  Gauge,
  HardDrive,
  Users,
  Zap,
} from "lucide-react";
import {
  budget,
  decisions,
  deliverables,
  gates,
  phases,
  risks,
} from "@/lib/project-data";
import {
  Callout,
  Chip,
  PageHero,
  SectionHeading,
  SourceNote,
  StatusTag,
} from "@/components/ui";

export const metadata: Metadata = {
  title: "Roadmap",
  description:
    "P0–P6, gates K1–K7 and G1–G5, the ≤$47 budget, deliverables, risks, stop rules, and decision-log highlights for the energy-optimal retrieval-depth study.",
};

const budgetColors = ["bg-muted", "bg-beam", "bg-signal", "bg-caution", "bg-data"];
const budgetValues = [0, 2, 25, 10, 10];

const stopRules = [
  ["K1", "Stops the depth story; report the null."],
  ["K2", "Extends the grid once; then reframe as “don't over-retrieve.”"],
  ["K3", "Raises power once; then drops static certification."],
  ["K4", "Reframes to generation, not depth."],
  ["K5", "Pivots to query-conditional policy; no population k*."],
  ["K6", "Kills the adaptive component if the held-out test fires."],
  ["K7", "Fixes measurement; do not interpret the curve."],
];

const outOfScope = [
  "A universal k* across tasks, readers, or hardware.",
  "Frontier or API readers (GPT, Claude, Gemini); no paid API calls.",
  "Full DPR/NQ corpus or dense-retriever training.",
  "Multi-GPU or datacenter GPU energy measurements. The optional H200 64k check is accuracy-only, with no energy claim.",
  "Carbon-optimal claims beyond constant-factor reporting and the split in Corollary 3.",
  "Prompt tuning, fine-tuning, or reranker training as a primary contribution.",
  "A production serving system or latency SLO study.",
];

export default function RoadmapPage() {
  return (
    <div>
      <PageHero
        index="04"
        eyebrow="Roadmap"
        title={
          <>
            A 20-week plan that is <em>allowed to fail.</em>
          </>
        }
        lede="This is a working plan, not a promise of results. Gates are allowed to fire. A fired gate is a finding and must be reported, not tuned away."
        meta={[
          { label: "20 weeks", tone: "data" },
          { label: "3–4 people", tone: "neutral" },
          { label: "15–20 GPU-hours", tone: "signal" },
          { label: "≤ $47 cash", tone: "caution" },
        ]}
      />

      {/* 01 — Phases */}
      <section aria-labelledby="phases-heading" className="mt-4">
        <SectionHeading
          index="01"
          eyebrow="Phases"
          id="phases-heading"
          title={
            <>
              P0 to P6. <em>Human time is the binding constraint.</em>
            </>
          }
          description="Energy compute is local and cheap. The schedule is not. P5 and P6 are staffed for writing and release; the buffer is real, not a label for overtime."
        />

        <ol className="relative mt-8 space-y-4">
          <span className="absolute bottom-4 left-[18px] top-4 w-px bg-line" aria-hidden />
          {phases.map((phase) => (
            <li key={phase.id} className="relative pl-12 sm:pl-16">
              <span className="absolute left-0 top-0 z-10 flex h-9 w-9 items-center justify-center rounded-full border border-line-strong bg-background font-mono text-[10px] text-signal">
                {phase.id}
              </span>
              <div className="panel p-4 sm:p-5">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="text-base font-semibold">{phase.name}</h3>
                  <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                    {phase.weeks}
                  </span>
                </div>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{phase.goal}</p>
                <dl className="mt-4 grid gap-4 border-t border-line pt-3 sm:grid-cols-2">
                  <div>
                    <dt className="eyebrow">Key outputs</dt>
                    <dd className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{phase.outputs}</dd>
                  </div>
                  <div>
                    <dt className="eyebrow">Exit gate</dt>
                    <dd className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{phase.exit}</dd>
                  </div>
                </dl>
              </div>
            </li>
          ))}
        </ol>
        <SourceNote>
          Source: ROADMAP.md §2. P1 decides whether the paper has a static policy result; P6 is the
          buffer, not a second attempt at P1.
        </SourceNote>
      </section>

      {/* 02 — Gates */}
      <section aria-labelledby="gates-roadmap" className="mt-16">
        <SectionHeading
          index="02"
          eyebrow="Gates"
          id="gates-roadmap"
          title={
            <>
              Kill gates first. <em>Go gates only if the evidence is there.</em>
            </>
          }
          description="Gates are evaluated once per phase on the pre-specified analysis population. A gate may not be added, removed, or re-thresholded after the primary outcome is seen."
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="panel overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
              <span className="eyebrow">Kill / reframe · pilot adjudication</span>
              <Chip tone="caution" dot>
                Pilot
              </Chip>
            </div>
            {gates.kill.map((gate) => (
              <div
                key={gate.id}
                className="grid gap-2 border-t border-line px-4 py-3 first:border-t-0 sm:grid-cols-[58px_1fr_auto] sm:items-center"
              >
                <span className="font-mono text-xs font-medium text-signal">{gate.id}</span>
                <div>
                  <p className="text-sm leading-snug">{gate.criterion}</p>
                  <p className="mt-0.5 font-mono text-[9px] text-muted-foreground">{gate.pilot}</p>
                </div>
                <StatusTag status={gate.status === "pass" ? "supported" : "dead"} label={gate.status === "pass" ? "Pass" : "Fail"} />
              </div>
            ))}
          </div>

          <div className="panel p-4">
            <div className="flex items-center justify-between gap-2">
              <span className="eyebrow">Go gates · planned</span>
              <Chip tone="neutral" dot>
                Not yet evaluated
              </Chip>
            </div>
            <ul className="mt-3 divide-y divide-line">
              {gates.go.map((gate) => (
                <li key={gate.id} className="grid grid-cols-[48px_1fr] gap-3 py-3 first:pt-0 last:pb-0">
                  <span className="font-mono text-xs font-medium text-signal">{gate.id}</span>
                  <p className="text-xs leading-relaxed text-muted-foreground">{gate.criterion}</p>
                </li>
              ))}
            </ul>
            <p className="mt-4 border-t border-line pt-3 text-xs leading-relaxed text-muted-foreground">
              A paper may be written with G1, G3, and G5 but without G4. It may not claim
              adaptivity without G4.
            </p>
          </div>
        </div>

        <div className="mt-4">
          <Callout tone="dead" title="The pilot fired three gates" icon={<AlertTriangle className="h-4 w-4" />}>
            K2 failed at the grid boundary, K3 failed at P = 0.61 &lt; 0.8, and K5 failed with a span
            of 3. K1, K4, K6, and K7 passed. The static 2 pp claim is dead; the surviving object is
            the decision problem around the accuracy margin.
          </Callout>
        </div>
      </section>

      {/* 03 — Budget */}
      <section aria-labelledby="budget-heading" className="mt-16">
        <SectionHeading
          index="03"
          eyebrow="Budget"
          id="budget-heading"
          title={
            <>
              Local compute, one optional accuracy-only H200 check. <em>A hard $47 local cap.</em>
            </>
          }
          description="No rental, no paid API, no cloud inference. The H200 check is optional, accuracy-only, and outside the local cash cap."
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="panel overflow-hidden">
            <div className="hidden border-b border-line bg-panel-soft px-4 py-2.5 sm:grid sm:grid-cols-[1fr_90px_1.5fr] sm:gap-3">
              <span className="eyebrow">Item</span>
              <span className="eyebrow">Cost</span>
              <span className="eyebrow">Notes</span>
            </div>
            {budget.items.map((item) => (
              <div
                key={item.item}
                className={`grid gap-1 border-t border-line px-4 py-3 first:border-t-0 sm:grid-cols-[1fr_90px_1.5fr] sm:items-start sm:gap-3 ${
                  item.item === "Total" ? "bg-panel-soft" : ""
                }`}
              >
                <p className={`text-sm ${item.item === "Total" ? "font-semibold" : ""}`}>{item.item}</p>
                <p className={`font-mono text-sm tabular-nums ${item.item === "Total" ? "font-semibold text-signal" : ""}`}>
                  {item.cost}
                </p>
                <p className="text-xs leading-relaxed text-muted-foreground">{item.note}</p>
              </div>
            ))}
          </div>

          <div className="space-y-4">
            <div className="panel p-5">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-semibold">Where the cash goes</h3>
                <span className="font-mono text-xs text-signal">≤ $47</span>
              </div>
              <div className="mt-4 flex h-4 overflow-hidden rounded-[2px] border border-line">
                {budget.items
                  .filter((item) => item.item !== "Total")
                  .map((item, index) => (
                    <div
                      key={item.item}
                      className={budgetColors[index]}
                      style={{ width: `${(budgetValues[index] / 47) * 100}%` }}
                      title={`${item.item}: ${item.cost}`}
                    />
                  ))}
              </div>
              <ul className="mt-3 space-y-1.5">
                {budget.items
                  .filter((item) => item.item !== "Total")
                  .map((item, index) => (
                    <li key={item.item} className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
                      <span className="inline-flex items-center gap-2">
                        <span className={`h-2 w-2 ${budgetColors[index]}`} aria-hidden />
                        {item.item}
                      </span>
                      <span className="font-mono tabular-nums">{item.cost}</span>
                    </li>
                  ))}
              </ul>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { icon: Zap, label: "Compute", value: budget.computeHours },
                { icon: Users, label: "Team", value: budget.team },
                { icon: HardDrive, label: "Storage", value: "~5 GB local" },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.label} className="panel p-3">
                    <Icon className="h-4 w-4 text-data" aria-hidden />
                    <p className="mt-2 eyebrow">{item.label}</p>
                    <p className="mt-1 text-xs font-semibold leading-snug">{item.value}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
        <SourceNote>
          Source: ROADMAP.md §5. Electricity is indicative, not metered billing. Model weights stay
          in the existing Ollama store and are never copied into the repository.
        </SourceNote>
      </section>

      {/* 04 — Deliverables */}
      <section aria-labelledby="deliverables-heading" className="mt-16">
        <SectionHeading
          index="04"
          eyebrow="Deliverables"
          id="deliverables-heading"
          title={
            <>
              Ten artifacts, <em>one evidence chain.</em>
            </>
          }
          description="The deliverable is not just a paper. It is a harness, a ledger, a frozen intent, a data card, and a package that can be reproduced on a second machine."
        />

        <div className="mt-8 grid gap-px overflow-hidden rounded-[4px] border border-line bg-line sm:grid-cols-2">
          {deliverables.map((item, index) => (
            <div key={item} className="flex gap-3 bg-panel p-4">
              <span className="font-mono text-[10px] text-signal">{String(index + 1).padStart(2, "0")}</span>
              <p className="text-sm leading-relaxed text-muted-foreground">{item}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 05 — Risks */}
      <section aria-labelledby="risks-heading" className="mt-16">
        <SectionHeading
          index="05"
          eyebrow="Risks"
          id="risks-heading"
          title={
            <>
              The two thesis-changing risks <em>are pre-registered.</em>
            </>
          }
          description="Scoring dependence (R1) and a binding gate (R9) can change the thesis. Both have pre-registered mitigations. The full register is reviewed at every phase gate."
        />

        <div className="panel mt-8 overflow-hidden">
          <div className="hidden border-b border-line bg-panel-soft px-4 py-2.5 lg:grid lg:grid-cols-[54px_1.15fr_100px_1.55fr] lg:gap-3">
            <span className="eyebrow">ID</span>
            <span className="eyebrow">Risk</span>
            <span className="eyebrow">L / I</span>
            <span className="eyebrow">Mitigation</span>
          </div>
          {risks.map((risk) => (
            <div
              key={risk.id}
              className="grid gap-2 border-t border-line px-4 py-3 first:border-t-0 lg:grid-cols-[54px_1.15fr_100px_1.55fr] lg:items-start lg:gap-3"
            >
              <span className="font-mono text-xs font-medium text-signal">{risk.id}</span>
              <p className="text-sm font-medium leading-snug">{risk.risk}</p>
              <div className="flex gap-1.5">
                <Chip tone={risk.likelihood === "High" ? "dead" : risk.likelihood === "Medium" ? "caution" : "neutral"}>
                  L {risk.likelihood}
                </Chip>
                <Chip tone={risk.impact === "High" ? "dead" : risk.impact === "Medium" ? "caution" : "neutral"}>
                  I {risk.impact}
                </Chip>
              </div>
              <p className="text-xs leading-relaxed text-muted-foreground">{risk.mitigation}</p>
            </div>
          ))}
        </div>
        <SourceNote>
          Source: docs/RISKS.md. Likelihood and impact are Low / Medium / High. A risk that changes
          the claim boundary is escalated to the PI before the next analysis run.
        </SourceNote>
      </section>

      {/* 06 — Decisions */}
      <section aria-labelledby="decisions-heading" className="mt-16">
        <SectionHeading
          index="06"
          eyebrow="Decision log"
          id="decisions-heading"
          title={
            <>
              The decisions that <em>hold the boundary.</em>
            </>
          }
          description="Each entry is immutable. A reversal is a new entry, not an edit. The log is part of the reproducibility package, not a changelog for the site."
        />

        <div className="mt-8 grid gap-3 md:grid-cols-2">
          {decisions.map((decision) => (
            <article key={decision.id} className="panel p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-signal">{decision.id}</span>
                  <span className="font-mono text-[9px] text-muted-foreground">{decision.date}</span>
                </div>
                <Chip tone={decision.status.includes("pending") ? "caution" : "neutral"}>
                  {decision.status}
                </Chip>
              </div>
              <h3 className="mt-2 text-sm font-semibold leading-snug">{decision.title}</h3>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{decision.summary}</p>
            </article>
          ))}
        </div>
        <SourceNote>Source: docs/DECISIONS.md D-001–D-011.</SourceNote>
      </section>

      {/* 07 — Stop rules / out of scope */}
      <section aria-labelledby="stop-heading" className="mt-16">
        <SectionHeading
          index="07"
          eyebrow="Stop rules and scope"
          id="stop-heading"
          title={
            <>
              Decide in advance <em>what ends the story.</em>
            </>
          }
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <Gauge className="h-4 w-4 text-caution" aria-hidden />
              <h3 className="text-sm font-semibold">Gate actions</h3>
            </div>
            <ul className="mt-3 divide-y divide-line">
              {stopRules.map(([id, action]) => (
                <li key={id} className="grid grid-cols-[40px_1fr] gap-3 py-2.5 first:pt-0 last:pb-0">
                  <span className="font-mono text-[10px] text-signal">{id}</span>
                  <span className="text-xs leading-relaxed text-muted-foreground">{action}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <Ban className="h-4 w-4 text-dead" aria-hidden />
              <h3 className="text-sm font-semibold">Out of scope</h3>
            </div>
            <ul className="mt-3 space-y-2">
              {outOfScope.map((item) => (
                <li key={item} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-dead" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <FlaskConical className="h-4 w-4 text-caution" aria-hidden />
            <span>Failure is a reported result. The 2 pp claim is the proof.</span>
          </div>
          <div className="flex flex-wrap gap-4">
            <Link href="/method" className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-signal">
              Method <ArrowRight className="h-3.5 w-3.5" aria-hidden />
            </Link>
            <Link href="/research" className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-signal">
              Research <ArrowRight className="h-3.5 w-3.5" aria-hidden />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
