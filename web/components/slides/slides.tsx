import Image from "next/image";
import type { ReactElement } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Database,
  FlaskConical,
  Gauge,
  GitBranch,
  Layers,
  ListChecks,
  Target,
  Timer,
  TrendingUp,
  Zap,
} from "lucide-react";
import {
  Frac,
  MathSub,
  MathSup,
  S,
  SlideBullets,
  SlideCallout,
  SlideCard,
  SlideChip,
  SlideDepthLadder,
  SlideFormula,
  SlideFrame,
  SlideKpiRow,
  SlideMark,
  SlideTable,
} from "@/components/slides/primitives";
import { course, datasets, pilot, references, rerun, team } from "@/lib/project-data";

export interface SlideProps {
  index: number;
  total: number;
}

export interface SlideDef {
  id: string;
  title: string;
  Component: (props: SlideProps) => ReactElement;
}

function EnergyFormula() {
  return (
    <span className="inline-flex items-center gap-[0.12em]">
      <span>
        <i>E</i>(<i>k</i>){" = "}
      </span>
      <Frac
        num={
          <>
            <span className="text-[1.12em]">Σ</span> <i>J</i>
            <MathSub>k</MathSub>
          </>
        }
        den={
          <>
            <span className="text-[1.12em]">Σ</span> <i>C</i>
            <MathSub>k</MathSub>
          </>
        }
      />
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* 1 · Title                                                           */
/* ------------------------------------------------------------------ */

function TitleSlide({ index }: SlideProps) {
  return (
    <div className="relative flex h-full w-full overflow-hidden" style={{ background: S.paper, color: S.ink }}>
      <div className="absolute inset-y-0 left-0 w-[0.5cqw]" style={{ background: S.lime }} />
      <div className="slide-grid pointer-events-none absolute inset-0 opacity-30" />

      <div className="relative grid h-full grid-cols-[1.08fr_0.92fr] gap-[4.2cqw] px-[5.4cqw] py-[4.2cqh]">
        <div className="flex min-h-0 flex-col">
          <div className="flex items-center gap-[1.4cqw]">
            <SlideMark size="7.2cqh" />
            <div>
              <p className="font-mono text-[2.1cqh] font-bold uppercase tracking-[0.16em]" style={{ color: S.deep }}>
                {course.code} · {course.name}
              </p>
              <p className="mt-[0.3cqh] font-mono text-[1.9cqh] font-semibold uppercase tracking-[0.14em]" style={{ color: S.inkSoft }}>
                Section {course.section}
              </p>
            </div>
          </div>

          <div className="flex min-h-0 flex-1 items-center">
            <div className="w-full">
              <p className="font-mono text-[2.1cqh] font-bold uppercase tracking-[0.14em]" style={{ color: S.teal }}>
                Project Proposal · 2026
              </p>
              <h1
                className="mt-[1.4cqh] text-[5.8cqh] font-semibold leading-[1.02] tracking-[-0.03em]"
                style={{ fontFamily: "var(--font-serif)", color: S.ink }}
              >
                Energy-Optimal Retrieval Depth in{" "}
                <span style={{ fontStyle: "italic", color: S.teal, borderBottom: `0.2cqw solid ${S.lime}` }}>
                  Retrieval-Augmented Generation
                </span>
              </h1>
              <p className="mt-[1.9cqh] text-[2.55cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
                Measuring the energy cost of each correct answer, and finding the depth that keeps
                that cost low.
              </p>
              <div className="mt-[2.0cqh] flex flex-wrap gap-[0.8cqw]">
                <SlideChip tone="deep">
                  {course.code} · Section {course.section}
                </SlideChip>
              </div>
            </div>
          </div>

          <div
            className="mt-[2.6cqh] flex justify-end border-t pt-[1.0cqh] font-mono text-[2.1cqh] font-bold"
            style={{ borderColor: S.line, color: S.inkSoft }}
          >
            <span className="tnum">{index + 1}</span>
          </div>
        </div>

        <div className="flex min-h-0 items-center">
          <div className="w-full border-2 p-[2.2cqw]" style={{ borderColor: S.deep, background: S.deep }}>
            <p className="font-mono text-[2.1cqh] font-bold uppercase tracking-[0.16em]" style={{ color: S.lime }}>
              Team
            </p>
            <div className="mt-[2.0cqh] space-y-[1.0cqh]">
              {team.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center justify-between gap-[1cqw] border-b pb-[0.9cqh]"
                  style={{ borderColor: "rgba(200,240,79,0.16)" }}
                >
                  <div>
                    <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.white }}>
                      {member.name}
                    </p>
                    <p className="mt-[0.2cqh] font-mono text-[1.8cqh] font-semibold" style={{ color: "#c9d6c9" }}>
                      {member.id}
                    </p>
                  </div>
                  {member.section === "E" && (
                    <span
                      className="border px-[0.7cqw] py-[0.35cqh] font-mono text-[1.55cqh] font-bold uppercase tracking-[0.08em]"
                      style={{ borderColor: S.lime, color: S.lime }}
                    >
                      Section E
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* 2 · Introduction + problem                                          */
/* ------------------------------------------------------------------ */

function IntroProblemSlide({ index, total }: SlideProps) {
  const steps = ["Question", "BM25", "k passages", "Reader", "Answer"];
  return (
    <SlideFrame
      badge="Introduction & Problem Statement"
      badgeTone="deep"
      title="RAG reads a few passages, then answers."
      subtitle="The number of passages is the retrieval depth, k. More passages can help accuracy, but they cost more energy."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-[1.15fr_0.85fr] gap-[1.8cqw]">
        <div className="flex flex-col justify-center gap-[1.5cqh]">
          <div className="flex flex-wrap items-center gap-[0.5cqw]">
            {steps.map((step, i) => (
              <div key={step} className="flex items-center gap-[0.5cqw]">
                <span
                  className="border-2 px-[0.9cqw] py-[0.65cqh] font-mono text-[2.0cqh] font-bold"
                  style={{ borderColor: S.deep, color: S.deep }}
                >
                  {step}
                </span>
                {i < steps.length - 1 && <ArrowRight size="2.2cqh" style={{ color: S.teal }} aria-hidden />}
              </div>
            ))}
          </div>
          <SlideDepthLadder />
          <SlideFormula>
            <EnergyFormula />
          </SlideFormula>
          <div
            className="grid grid-cols-2 gap-x-[1.2cqw] gap-y-[0.45cqh] text-[2.0cqh] font-semibold leading-snug"
            style={{ color: S.ink }}
          >
            <p><i>k</i> = passages retrieved</p>
            <p><i>J</i><MathSub>k</MathSub> = energy for one question at depth <i>k</i></p>
            <p><i>C</i><MathSub>k</MathSub> = 1 if correct, 0 if wrong</p>
            <p><i>E</i>(<i>k</i>) = energy per correct answer</p>
            <p><span className="text-[1.12em]">Σ</span> = sum over questions</p>
            <p><b>BM25</b> = Best Matching 25</p>
          </div>
        </div>
        <div className="grid min-h-0 grid-rows-3 gap-[1.0cqh]">
          <SlideCard title="More passages" tone="teal">
            <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              More evidence, higher accuracy, more energy.
            </p>
          </SlideCard>
          <SlideCard title="Fewer passages" tone="amber">
            <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              Lower energy, but the answer may be wrong.
            </p>
          </SlideCard>
          <SlideCard title="The problem" tone="deep">
            <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              Tuning only for accuracy or only for energy gives the wrong depth.
            </p>
          </SlideCard>
        </div>
      </div>
      <SlideCallout tone="teal">
        We choose k under an accuracy floor. 5 accuracy points = 5 percentage points (pp). The goal is
        the lowest energy per correct answer.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 3 · Motivation + research gap                                       */
/* ------------------------------------------------------------------ */

function MotivationGapSlide({ index, total }: SlideProps) {
  const rows = [
    ["Static top-k / accuracy-only", "Accuracy", "No", "No", "No"],
    ["Adaptive retrieval", "Query-aware context or cost", "No", "No fixed margin", "Partial policy"],
    ["Energy benchmarks", "Power / energy", "Partial", "No", "No"],
    ["This proposal", "Energy per correct", "Yes", "Yes", "Yes"],
  ];

  return (
    <SlideFrame
      badge="Motivation & Literature Review"
      badgeTone="teal"
      title="Prior work covers parts; the depth decision remains."
      subtitle="In our early study, 32 passages cost 3.45 times more per correct answer than 1 passage. Accuracy was flat from 4 to 16 passages."
      index={index}
      total={total}
    >
      <SlideKpiRow
        items={[
          {
            value: `${pilot.energy.span.toFixed(2)}×`,
            label: "energy per correct answer",
            sub: "k=32 vs k=1",
            tone: "deep",
          },
          {
            value: `${pilot.contextShare.at32}%`,
            label: "energy for retrieval + passage input",
            sub: "at k=32",
            tone: "teal",
          },
          {
            value: `${pilot.fivePp.savings}%`,
            label: "saved at k=4 vs k=32",
            sub: "5-point margin, early result",
            tone: "amber",
          },
        ]}
      />
      <div className="mt-[1.4cqh] flex min-h-0 flex-1 flex-col justify-center gap-[1.0cqh]">
        <SlideTable
          head={["Approach", "Improves", "Energy per correct?", "Accuracy floor?", "Break-even + policy?"]}
          rows={rows}
          tone="amber"
          widths={["30%", "22%", "16%", "14%", "18%"]}
          compact
        />
      </div>
      <SlideCallout tone="amber">
        Literature: Lewis 2020; Jeong 2024; Hwang 2026; Hashemi 2025; Pan 2025; Song 2026; Taguchi
        2025; RAGMark and Token Arena 2026. The reviewed work does not combine an accuracy-gated
        depth decision with break-even, causal tests, and a matched-accuracy policy.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 4 · Objectives + scope                                              */
/* ------------------------------------------------------------------ */

function ObjectivesScopeSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Objectives & Scope"
      badgeTone="deep"
      title="Three questions, seven tests."
      subtitle="H1–H7 are the seven hypotheses. A hypothesis is a test statement with a clear pass/fail rule. The margin is 5 percentage points (pp)."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-3 gap-[1.2cqw]">
        <SlideCard title="Question 1 · Static depth" tone="deep" icon={<Target size="2.8cqh" />}>
          <p className="text-[2.35cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Which depth gives the lowest energy per correct answer while staying within 5 accuracy
            points of k=32?
          </p>
          <p className="mt-[1.0cqh] font-mono text-[2.0cqh] font-bold" style={{ color: S.teal }}>
            Tests H1–H4 · H7 replication
          </p>
        </SlideCard>
        <SlideCard title="Question 2 · Adaptivity" tone="teal" icon={<GitBranch size="2.8cqh" />}>
          <p className="text-[2.35cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Can a policy choose a different depth for each question and still match the best static
            depth?
          </p>
          <p className="mt-[1.0cqh] font-mono text-[2.0cqh] font-bold" style={{ color: S.teal }}>
            Test H5
          </p>
        </SlideCard>
        <SlideCard title="Question 3 · Cause and cost" tone="amber" icon={<Timer size="2.8cqh" />}>
          <p className="text-[2.35cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Do energy costs move the best depth as predicted, and does the measurement sweep repay
            its energy?
          </p>
          <p className="mt-[1.0cqh] font-mono text-[2.0cqh] font-bold" style={{ color: S.amber }}>
            Tests H6 · N* = break-even questions
          </p>
        </SlideCard>
      </div>
      <div
        className="mt-[1.0cqh] grid grid-cols-2 gap-[1.4cqw] border-2 p-[1.0cqw]"
        style={{ borderColor: S.line, background: S.alt }}
      >
        <div>
          <p className="font-mono text-[1.95cqh] font-bold uppercase tracking-[0.1em]" style={{ color: S.teal }}>
            We will test
          </p>
          <p className="mt-[0.4cqh] text-[2.05cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            The 5-point rule, at least 20% energy savings, the energy–accuracy link, the passage-energy
            share, the policy, and the energy-cost signs.
          </p>
        </div>
        <div>
          <p className="font-mono text-[1.95cqh] font-bold uppercase tracking-[0.1em]" style={{ color: S.rose }}>
            We will not claim
          </p>
          <p className="mt-[0.4cqh] text-[2.05cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            One best depth for every case, a 2-point optimum, a final 5-point result before the rerun,
            or a learned-policy gain yet.
          </p>
        </div>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 5 · Datasets                                                        */
/* ------------------------------------------------------------------ */

function DatasetSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Dataset"
      badgeTone="teal"
      title="Two datasets, one depth question."
      subtitle="SQuAD uses one fixed collection. HotpotQA adds multi-hop questions and wrong paragraphs."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.4cqw]">
        <SlideCard title="SQuAD · primary" tone="teal" icon={<Database size="2.8cqh" />}>
          <SlideBullets
            items={[
              `Stanford Question Answering Dataset (SQuAD) v1.1 dev · ${datasets.squad.upstreamQuestions.toLocaleString("en-US")} questions.`,
              `Corpus: ${datasets.squad.corpus}.`,
              "Retriever: BM25 (Best Matching 25) top-32.",
              `Runs: ${datasets.squad.usedPrimary.toLocaleString("en-US")} primary · 2 × ${datasets.squad.usedReplication} replication · ${datasets.squad.usedBoundary} boundary.`,
              `Metric: exact match · License: ${datasets.squad.license}.`,
            ]}
            size="2.2cqh"
          />
        </SlideCard>
        <SlideCard title="HotpotQA · multi-hop stress" tone="amber" icon={<Layers size="2.8cqh" />}>
          <SlideBullets
            items={[
              `HotpotQA (multi-hop question answering) · ${datasets.hotpot.upstreamQuestions.toLocaleString("en-US")} questions; ${datasets.hotpot.used} used.`,
              `${datasets.hotpot.paragraphs} paragraphs per question: 2 right + ${datasets.hotpot.distractors} wrong.`,
              `k ∈ {${datasets.hotpot.depths.join(",")}}; BM25 (Best Matching 25) top-10.`,
              `No mixing across questions · License: ${datasets.hotpot.license}.`,
            ]}
            size="2.2cqh"
          />
        </SlideCard>
      </div>
      <SlideCallout tone="deep">
        Sources: SQuAD — Rajpurkar et al. 2016 · HotpotQA — Yang et al. 2018 · BM25 — Robertson &amp;
        Zaragoza 2009.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 6 · Proposed method                                                 */
/* ------------------------------------------------------------------ */

function MethodSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Proposed Method"
      badgeTone="deep"
      title="Four ideas we will test."
      subtitle="Baseline: one fixed number of passages for every question, tuned only for accuracy or speed. Our proposal: choose depth by energy per correct answer, under an accuracy floor."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="Energy per correct answer" tone="deep" icon={<Gauge size="2.8cqh" />}>
          <SlideFormula>
            <EnergyFormula />
          </SlideFormula>
          <p className="mt-[0.9cqh] text-[2.15cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Read as: total energy ÷ total correct answers.
          </p>
          <p className="mt-[0.45cqh] text-[2.1cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            <i>k</i> = passages; <i>J</i> = energy; <i>C</i> = 1 if correct, 0 if wrong.
          </p>
        </SlideCard>
        <SlideCard title="Energy–accuracy link" tone="teal" icon={<GitBranch size="2.8cqh" />}>
          <SlideFormula>
            <span className="inline-flex items-center gap-[0.18em]">
              <Frac
                num={
                  <>
                    <i>k</i> <i>J</i>′(<i>k</i>)
                  </>
                }
                den={
                  <>
                    <i>J</i>(<i>k</i>)
                  </>
                }
              />
              <span>{" = "}</span>
              <Frac
                num={
                  <>
                    <i>k</i> <i>A</i>′(<i>k</i>)
                  </>
                }
                den={
                  <>
                    <i>A</i>(<i>k</i>)
                  </>
                }
              />
            </span>
          </SlideFormula>
          <p className="mt-[0.9cqh] text-[2.15cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            At an interior optimum, energy and accuracy change by the same percentage. <i>J</i>(<i>k</i>)
            is energy per query; <i>A</i>(<i>k</i>) is accuracy. Primes show their rates of change.
          </p>
        </SlideCard>
        <SlideCard title="Break-even measurement" tone="amber" icon={<Timer size="2.8cqh" />}>
          <SlideFormula>
            <span className="inline-flex items-center gap-[0.12em]">
              <span>
                <i>N</i>
                <MathSup>*</MathSup>
                {" = "}
              </span>
              <Frac
                num={
                  <>
                    <i>C</i>
                    <MathSub>cert</MathSub>
                  </>
                }
                den={
                  <>
                    <i>A</i>(<i>k</i>
                    <MathSup>*</MathSup>)(<i>E</i>(<i>k</i>
                    <MathSub>0</MathSub>) − <i>E</i>(<i>k</i>
                    <MathSup>*</MathSup>))
                  </>
                }
              />
            </span>
          </SlideFormula>
          <p className="mt-[0.9cqh] text-[2.15cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            <i>N</i>
            <MathSup>*</MathSup> = questions needed before the sweep saves more energy than it costs.
          </p>
          <p className="mt-[0.45cqh] text-[2.1cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            <i>C</i>
            <MathSub>cert</MathSub> = sweep energy; <i>k</i>
            <MathSub>0</MathSub> = default depth; <i>k</i>
            <MathSup>*</MathSup> = best depth.
          </p>
        </SlideCard>
        <SlideCard title="Energy-cost test" tone="rose" icon={<FlaskConical size="2.8cqh" />}>
          <p className="text-[2.15cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Add a fixed cost (a) or a cost per passage (b). A fixed cost should push the best depth up;
            a per-passage cost should push it down. A wrong sign means the model is wrong.
          </p>
        </SlideCard>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 7 · Flow diagram                                                    */
/* ------------------------------------------------------------------ */

function FlowSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Methodology Flow"
      badgeTone="deep"
      title="How the experiment runs."
      subtitle="The same run gives us the energy curve, the energy–accuracy link, the break-even cost, and the policy data."
      index={index}
      total={total}
    >
      <div className="flex min-h-0 flex-1 items-center justify-center">
        <Image
          src="/flow-diagram-v4.png"
          alt="Study workflow: prepare SQuAD and HotpotQA, index with BM25, sweep seven SQuAD depths and six HotpotQA depths, measure NVML power with idle and block calibration, score normalized exact match, then analyze the paired non-inferiority test, bootstrap, E(k), N*, and policy. The decision flow starts with the 200-question P0 check, freezes the plan before P1, runs 1,000 questions across seven depths, reviews gates, then continues to replication, taxes, policy, and theory."
          width={7512}
          height={3167}
          priority
          className="h-full w-full object-contain"
        />
      </div>
      <p className="mt-[0.4cqh] text-center text-[2.0cqh] font-semibold" style={{ color: S.inkSoft }}>
        BM25 = Best Matching 25 · NVML = NVIDIA Management Library · EM = exact match
      </p>
      <SlideCallout tone="teal">The run is the measurement; the checkpoints are the decision.</SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 8 · Experimental setup                                              */
/* ------------------------------------------------------------------ */

function SetupSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Experimental Setup"
      badgeTone="amber"
      title="What we will run."
      subtitle="All settings are fixed before we look at the new accuracy data."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-3 gap-[1.2cqw]">
        <SlideCard title="Runs" tone="deep" icon={<Layers size="2.8cqh" />}>
          <SlideBullets
            items={[
              `SQuAD primary (4B): ${rerun.primary.n.toLocaleString("en-US")} × 7 depths`,
              `Replication: ${rerun.replication.n} × 7 each — Qwen2.5-1.5B, Llama 3.2 3B`,
              `HotpotQA: ${rerun.hotpot.n} × 6 depths`,
              `Boundary: ${rerun.boundary.n} × 3 · 16k probe: ${rerun.contextProbe.n} × 3`,
              `Taxes: ${rerun.taxes.n} × 2 · policy: 600/200/200`,
            ]}
            size="2.0cqh"
          />
        </SlideCard>
        <SlideCard title="Measurement" tone="teal" icon={<Gauge size="2.8cqh" />}>
          <SlideBullets
            items={[
              "NVML samples every 100 ms; on this laptop, power readings update about once a second.",
              "60 s idle baseline; 20-question blocks.",
              "A unique code in each request helps prevent cache reuse.",
              "Log temperature and clock; wall meter checks a 30-query subset.",
              "We repeat a block to check noise.",
            ]}
            size="2.15cqh"
          />
        </SlideCard>
        <SlideCard title="Decision" tone="rose" icon={<Target size="2.8cqh" />}>
          <SlideBullets
            items={[
              "Main rule: k=4 must be no more than 5 accuracy points below k=32 (non-inferiority, NI).",
              "At least 20% energy savings.",
              "5% one-sided false-positive limit; 10,000 resamples for uncertainty.",
              "The 2-point rule is only an estimate.",
            ]}
            size="2.2cqh"
          />
        </SlideCard>
      </div>
      <SlideCallout tone="amber">
        15–20 local GPU hours · RTX 3060 6 GB · optional H200 64k: accuracy-only, no energy claim.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 9 · Checkpoints and gates                                           */
/* ------------------------------------------------------------------ */

function AnalysisSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Analysis & Gates"
      badgeTone="rose"
      title="When do we continue, and when do we stop?"
      subtitle="G means go: continue if the checkpoint passes. K means stop: report and reframe if it fails. H means hypothesis: a test statement."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.4cqw]">
        <SlideCard title="Main decision" tone="rose" icon={<Target size="2.8cqh" />}>
          <p className="text-[2.35cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            k=4 must be no more than 5 accuracy points below k=32 (non-inferiority, NI).
          </p>
          <div className="mt-[0.9cqh]">
            <SlideFormula tone="rose">
              <span className="text-[2.3cqh]">
                <i>A</i>(4) − <i>A</i>(32) &gt; −5 pp · savings ≥ 20%
              </span>
            </SlideFormula>
          </div>
          <p className="mt-[0.8cqh] text-[2.25cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            5% one-sided false-positive limit; 10,000 resamples.
          </p>
          <p className="mt-[0.8cqh] text-[2.25cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            <i>P</i>(<i>k</i>
            <MathSup>*</MathSup>) = share of bootstrap samples where this depth is best under the gate.
          </p>
          <p className="mt-[0.8cqh] text-[2.25cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
            The 2-point rule is only an estimate.
          </p>
        </SlideCard>
        <SlideCard title="Checkpoints" tone="deep" icon={<ListChecks size="2.8cqh" />}>
          <div className="grid grid-cols-2 gap-[1.1cqw]">
            <div>
              <p className="font-mono text-[1.95cqh] font-bold uppercase tracking-[0.1em]" style={{ color: S.teal }}>
                Go · G1–G5
              </p>
              <ul className="mt-[0.5cqh] space-y-[0.5cqh] text-[2.0cqh] font-semibold leading-snug" style={{ color: S.ink }}>
                <li>G1 · 5 pp NI at an interior depth; ≥20% savings</li>
                <li>
                  G2 · accuracy-loss upper bound ≤5 pp; <i>P</i>(<i>k</i>
                  <MathSup>*</MathSup>) ≥ 0.8
                </li>
                <li>G3 · context share 10–70% at k*; varies with k</li>
                <li>G4 · oracle ≥20%; policy captures ≥50% at matched accuracy</li>
                <li>G5 · replication</li>
              </ul>
            </div>
            <div>
              <p className="font-mono text-[1.95cqh] font-bold uppercase tracking-[0.1em]" style={{ color: S.rose }}>
                Stop · K1–K7
              </p>
              <ul className="mt-[0.5cqh] space-y-[0.5cqh] text-[2.0cqh] font-semibold leading-snug" style={{ color: S.ink }}>
                <li>K1 · energy effect &lt;10%</li>
                <li>K2 · best depth at boundary</li>
                <li>
                  K3 · <i>P</i>(<i>k</i>
                  <MathSup>*</MathSup>) &lt; 0.8
                </li>
                <li>K4 · context share &lt;5% and flat</li>
                <li>K5 · k* spans &gt;1 tested depth across samples/datasets</li>
                <li>K6 · best-possible gain &lt;15%</li>
                <li>K7 · repeat variation &gt;20% or effect below detection limit</li>
              </ul>
            </div>
          </div>
        </SlideCard>
      </div>
      <SlideCallout tone="rose">
        If a checkpoint fails, we report it and change the claim.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 10 · Expected results                                               */
/* ------------------------------------------------------------------ */

function ExpectedSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Expected Results"
      badgeTone="deep"
      title="What we expect — and what would prove us wrong."
      subtitle="H1–H7 are the seven hypotheses. Each has a clear pass/fail rule. A null result is still a result."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="H1 · energy follows a straight line" tone="deep" icon={<TrendingUp size="2.8cqh" />}>
          <p className="text-[2.3cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Pass if the slope is positive, <i>R</i>
            <MathSup>2</MathSup> (fit quality) ≥ 0.95, and the lack-of-fit test is not rejected at 5%.
            Fail if not.
          </p>
        </SlideCard>
        <SlideCard title="H2 · main decision" tone="rose" icon={<Target size="2.8cqh" />}>
          <p className="text-[2.3cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Pass if the paired one-sided test supports a loss ≤5 pp at the 5% level and savings are
            ≥20%. Fail if not.
          </p>
        </SlideCard>
        <SlideCard title="H3–H4 · energy link and passage share" tone="teal" icon={<GitBranch size="2.8cqh" />}>
          <p className="text-[2.3cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Pass if the 95% interval for the identity gap includes 0; context share at k* is 10–70%
            and rises with k. Fail if not.
          </p>
        </SlideCard>
        <SlideCard title="H5–H6 · policy and energy costs" tone="amber" icon={<FlaskConical size="2.8cqh" />}>
          <p className="text-[2.3cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Pass if the best-possible (oracle) gain is ≥20%, the policy captures ≥50% at matched
            accuracy, a fixed cost raises <i>k</i>
            <MathSup>*</MathSup>, and a per-passage cost lowers <i>k</i>
            <MathSup>*</MathSup>. Fail if not.
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="deep">
        H7 · replication: H2&apos;s direction on Qwen2.5-1.5B or HotpotQA. Exploratory: Llama 3.2
        3B. A null result is still a result.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 11 · Applications, risks, conclusion                                */
/* ------------------------------------------------------------------ */

function ImpactSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Applications, Risks & Conclusion"
      badgeTone="deep"
      title="Why it matters — and what we propose."
      subtitle="Applications, risks, and the three-part proposal."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="Applications" tone="teal" icon={<Zap size="2.8cqh" />}>
          <SlideBullets
            items={[
              "Green RAG serving and capacity planning.",
              "Smaller GPUs and edge devices.",
              "Energy-aware retrieval benchmarks.",
              "Accuracy-margin policy for operators.",
              "Open harness and reusable code.",
            ]}
            size="2.2cqh"
          />
        </SlideCard>
        <SlideCard title="Risks and resources" tone="rose" icon={<AlertTriangle size="2.8cqh" />}>
          <SlideBullets
            items={[
              "Scoring rule: exact match vs lenient.",
              "Reader strength, context limits, one dataset.",
              "GPU heat and power-sensor limits.",
              "Cached prompts and policy overfitting.",
              "Budget: 15–20 GPU hours; ≤ $47.",
            ]}
            size="2.2cqh"
          />
        </SlideCard>
        <div
          className="col-span-2 flex min-h-0 flex-col justify-center border-2 p-[1.5cqw]"
          style={{ borderColor: S.deep, background: S.deep }}
        >
          <p className="font-mono text-[1.95cqh] font-bold uppercase tracking-[0.14em]" style={{ color: S.lime }}>
            What we propose
          </p>
          <div className="mt-[0.7cqh] grid grid-cols-3 gap-[1.2cqw]">
            <p className="text-[2.1cqh] font-semibold leading-snug" style={{ color: S.white }}>
              A clear rule: choose depth by energy per correct answer, under an accuracy floor.
            </p>
            <p className="text-[2.1cqh] font-semibold leading-snug" style={{ color: S.white }}>
              A causal test: add energy costs and check whether the best depth moves as predicted.
            </p>
            <p className="text-[2.1cqh] font-semibold leading-snug" style={{ color: S.white }}>
              A policy: choose a different depth for each question and compare at matched accuracy.
            </p>
          </div>
          <div className="mt-[1.0cqh] flex flex-wrap items-center justify-between gap-[1cqw]">
            <p className="text-[2.0cqh] font-semibold" style={{ color: "#d7e5d7" }}>
              We ask to run the 1,000-question study and report the result, positive or null.
            </p>
            <p className="font-mono text-[2.2cqh] font-bold uppercase tracking-[0.12em]" style={{ color: S.lime }}>
              Thank you · Questions
            </p>
          </div>
        </div>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 12 · References                                                     */
/* ------------------------------------------------------------------ */

function ReferencesSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="References"
      badgeTone="amber"
      title="References"
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-[1.2fr_0.8fr] gap-[1.4cqw]">
        <SlideCard title="Prior work" tone="teal">
          <ol
            className="list-decimal space-y-[0.75cqh] pl-[1.7cqw] text-[2.0cqh] font-semibold leading-snug"
            style={{ color: S.ink }}
          >
            {references.priorWork.map((ref) => (
              <li key={ref.id}>{ref.text}</li>
            ))}
          </ol>
        </SlideCard>
        <SlideCard title="Data &amp; tools" tone="amber">
          <ol
            start={10}
            className="list-decimal space-y-[1.1cqh] pl-[1.7cqw] text-[2.0cqh] font-semibold leading-snug"
            style={{ color: S.ink }}
          >
            {references.dataTools.map((ref) => (
              <li key={ref.id}>{ref.text}</li>
            ))}
          </ol>
        </SlideCard>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */

export const SLIDES: SlideDef[] = [
  { id: "title", title: "Energy-Optimal Retrieval Depth in Retrieval-Augmented Generation", Component: TitleSlide },
  { id: "introduction", title: "RAG reads a few passages, then answers", Component: IntroProblemSlide },
  { id: "motivation-gap", title: "Energy per correct answer changes a lot with depth", Component: MotivationGapSlide },
  { id: "objectives-scope", title: "Three questions, seven tests", Component: ObjectivesScopeSlide },
  { id: "data", title: "Two datasets, one depth question", Component: DatasetSlide },
  { id: "method", title: "Four ideas we will test", Component: MethodSlide },
  { id: "flow", title: "How the experiment runs", Component: FlowSlide },
  { id: "setup", title: "What we will run", Component: SetupSlide },
  { id: "analysis", title: "When do we continue, and when do we stop", Component: AnalysisSlide },
  { id: "expected", title: "What we expect, and what would prove us wrong", Component: ExpectedSlide },
  { id: "impact", title: "Why it matters, and what we propose", Component: ImpactSlide },
  { id: "references", title: "References", Component: ReferencesSlide },
];
