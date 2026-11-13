import Image from "next/image";
import type { ReactElement } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Database,
  FlaskConical,
  Gauge,
  GitBranch,
  Layers,
  ListChecks,
  Search,
  ShieldCheck,
  Target,
  Timer,
  TrendingUp,
  XCircle,
  Zap,
} from "lucide-react";
import {
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
                Measuring joules per correct answer, and deciding whether calibrating the retrieval
                depth is worth its own energy.
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
/* 2 · Executive summary                                               */
/* ------------------------------------------------------------------ */

function ExecSummarySlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Executive summary"
      badgeTone="deep"
      title="The proposal in one slide."
      subtitle="A gated energy decision, a powered rerun, and a causal test of the energy split."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.4cqw]">
        <SlideCard title="Question" tone="deep" icon={<Target size="2.8cqh" />}>
          <p className="text-[2.6cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Which retrieval depth minimizes joules per correct answer under an accuracy floor?
          </p>
        </SlideCard>
        <SlideCard title="Gap" tone="amber" icon={<Search size="2.8cqh" />}>
          <p className="text-[2.6cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Existing work optimizes accuracy, latency, or tokens — not the gated energy decision.
          </p>
        </SlideCard>
        <SlideCard title="Method" tone="teal" icon={<FlaskConical size="2.8cqh" />}>
          <p className="text-[2.6cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            SQuAD (Stanford Question Answering Dataset) n=1,000 × 7 depths, GPU energy
            measurement, 5 percentage-point non-inferiority, 10,000 bootstrap, taxes, and a
            600/200/200 policy.
          </p>
        </SlideCard>
        <SlideCard title="Contribution" tone="deep" icon={<Zap size="2.8cqh" />}>
          <p className="text-[2.6cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Gated E(k), optimal-depth identity, static-depth bound, N*, causal tax test, and a
            learned policy.
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="amber">No confirmatory result is claimed yet. This is a proposal.</SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 3 · Introduction                                                    */
/* ------------------------------------------------------------------ */

function IntroSlide({ index, total }: SlideProps) {
  const steps = ["Question", "BM25", "k passages", "Reader", "Answer"];
  return (
    <SlideFrame
      badge="Introduction"
      badgeTone="deep"
      title="RAG answers by choosing how much evidence to read."
      subtitle="Retrieval depth k is the number of passages placed before the reader."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-[1.15fr_0.85fr] gap-[1.8cqw]">
        <div className="flex flex-col justify-center gap-[2.0cqh]">
          <div className="flex flex-wrap items-center gap-[0.5cqw]">
            {steps.map((step, i) => (
              <div key={step} className="flex items-center gap-[0.5cqw]">
                <span
                  className="border-2 px-[0.9cqw] py-[0.7cqh] font-mono text-[2.1cqh] font-bold"
                  style={{ borderColor: S.deep, color: S.deep }}
                >
                  {step}
                </span>
                {i < steps.length - 1 && <ArrowRight size="2.3cqh" style={{ color: S.teal }} aria-hidden />}
              </div>
            ))}
          </div>
          <SlideDepthLadder />
          <SlideFormula>E(k) = Σ J_k / Σ C_k</SlideFormula>
          <div
            className="grid grid-cols-2 gap-x-[1.2cqw] gap-y-[0.55cqh] text-[2.1cqh] font-semibold leading-snug"
            style={{ color: S.ink }}
          >
            <p><b>k</b> = passages retrieved</p>
            <p><b>J_k</b> = joules at depth k</p>
            <p><b>C_k</b> = 1 correct, 0 wrong</p>
            <p><b>Σ</b> = sum over questions</p>
            <p><b>E(k)</b> = joules per correct answer</p>
            <p><b>BM25</b> = Best Matching 25</p>
          </div>
          <p className="text-[2.1cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
            The accuracy gate stops the ratio from rewarding cheap failure.
          </p>
        </div>
        <div className="grid min-h-0 grid-rows-3 gap-[1.1cqh]">
          <SlideCard title="More passages" tone="teal">
            <p className="text-[2.3cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              More evidence, higher accuracy — and more prefill energy.
            </p>
          </SlideCard>
          <SlideCard title="Fewer passages" tone="amber">
            <p className="text-[2.3cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              Cheaper, but the reader may miss the evidence.
            </p>
          </SlideCard>
          <SlideCard title="The decision" tone="deep">
            <p className="text-[2.3cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              Choose k under an accuracy floor to minimize joules per correct answer.
            </p>
          </SlideCard>
        </div>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 4 · Problem statement                                               */
/* ------------------------------------------------------------------ */

function ProblemSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Problem"
      badgeTone="rose"
      title="Depth is tuned for accuracy or latency — not joules per correct answer."
      subtitle="A cheap wrong answer can look efficient; an accurate answer can waste energy on passages that never help."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.6cqw]">
        <SlideCard title="What goes wrong" tone="rose" icon={<AlertTriangle size="2.8cqh" />}>
          <SlideBullets
            items={[
              "Accuracy-only tuning picks the highest depth.",
              "Energy-only tuning picks k = 0 and hides errors in the denominator.",
              "One static depth ignores query heterogeneity.",
              "Mean joules per query is not the deployment cost.",
            ]}
            size="2.4cqh"
          />
        </SlideCard>
        <SlideCard title="What we need" tone="teal" icon={<ShieldCheck size="2.8cqh" />}>
          <SlideBullets
            items={[
              "A gated ratio E(k) = ΣJ / ΣC.",
              "A paired 5 percentage-point (pp) non-inferiority decision.",
              "A causal test of the energy split.",
              "A query-conditional policy at matched accuracy.",
            ]}
            size="2.4cqh"
          />
        </SlideCard>
      </div>
      <SlideCallout tone="rose">The denominator is correct answers, not queries. A cheap failure is not a green result.</SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 5 · Motivation                                                      */
/* ------------------------------------------------------------------ */

function MotivationSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Motivation"
      badgeTone="teal"
      title="Retrieval energy is a deployment cost, not a benchmark detail."
      subtitle="Measured on 200 SQuAD questions: 32 passages cost 3.45× more per correct answer than one; accuracy was flat from k=4 to k=16."
      index={index}
      total={total}
    >
      <SlideKpiRow
        items={[
          {
            value: `${pilot.energy.span.toFixed(2)}×`,
            label: "energy per correct answer",
            sub: "E(32) vs E(1)",
            tone: "deep",
          },
          { value: `${pilot.contextShare.at32}%`, label: "context-side share", sub: "at k = 32", tone: "teal" },
          {
            value: `${pilot.fivePp.savings}%`,
            label: `savings at k = ${pilot.fivePp.k}`,
            sub: "5 pp signal",
            tone: "amber",
          },
        ]}
      />
      <div className="mt-[2.2cqh] grid min-h-0 flex-1 grid-cols-2 gap-[1.6cqw]">
        <SlideCard title="Why now" tone="teal" icon={<Zap size="2.8cqh" />}>
          <p className="text-[2.5cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Production RAG runs at scale. A 3× energy difference per correct answer is a real bill,
            not a rounding error.
          </p>
        </SlideCard>
        <SlideCard title="The green question" tone="amber" icon={<Gauge size="2.8cqh" />}>
          <p className="text-[2.5cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            How much accuracy are we willing to trade for how many joules — and is finding the
            trade-off worth its own energy?
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="amber">The 5 pp result is a signal, not a certificate.</SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 6 · Research gap                                                    */
/* ------------------------------------------------------------------ */

function GapSlide({ index, total }: SlideProps) {
  const rows = [
    ["Static top-k / accuracy-only", "Accuracy", "No", "No", "No"],
    ["Adaptive-k / token or latency", "Tokens or latency", "No", "No", "Partial policy"],
    ["Energy benchmarks", "Power / energy", "Partial", "No", "No"],
    ["This proposal", "Gated E(k)", "Yes", "Yes", "Yes"],
  ];
  return (
    <SlideFrame
      badge="Research gap"
      badgeTone="amber"
      title="Existing work optimizes accuracy, latency, or tokens. The gated energy decision is missing."
      subtitle="A qualitative benchmark matrix, not a performance leaderboard."
      index={index}
      total={total}
    >
      <div className="flex min-h-0 flex-1 flex-col justify-center gap-[1.6cqh]">
        <SlideTable
          head={["Approach", "Optimizes", "Gated E(k)?", "Causal test?", "Break-even + policy?"]}
          rows={rows}
          tone="amber"
          widths={["30%", "22%", "16%", "14%", "18%"]}
        />
        <p className="text-[2.4cqh] font-semibold leading-snug" style={{ color: S.ink }}>
          The missing object is a decision rule, not another benchmark.
        </p>
      </div>
      <SlideCallout tone="amber">
        Sources: Pan et al. 2025; Hwang 2026; Hashemi et al. 2025; RAGMark 2026;
        Tail-Aware Adaptive-k 2026; Taguchi et al. 2025; Token Arena 2026.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 7 · Objectives and hypotheses                                       */
/* ------------------------------------------------------------------ */

function ObjectivesSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Objectives"
      badgeTone="deep"
      title="Three questions, seven pre-registered hypotheses."
      subtitle="A decision problem, not a curve-fitting exercise."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-3 gap-[1.2cqw]">
        <SlideCard title="Question 1 · Static depth" tone="deep" icon={<Target size="2.8cqh" />}>
          <p className="text-[2.5cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Which depth minimizes E(k) under a 5 pp accuracy floor?
          </p>
          <p className="mt-[1.4cqh] font-mono text-[2.1cqh] font-bold" style={{ color: S.teal }}>
            Hypotheses H1–H4
          </p>
        </SlideCard>
        <SlideCard title="Question 2 · Adaptivity" tone="teal" icon={<GitBranch size="2.8cqh" />}>
          <p className="text-[2.5cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Does a query-conditional policy beat the best static depth at matched accuracy?
          </p>
          <p className="mt-[1.4cqh] font-mono text-[2.1cqh] font-bold" style={{ color: S.teal }}>
            Hypothesis H5
          </p>
        </SlideCard>
        <SlideCard title="Question 3 · Causality & cost" tone="amber" icon={<Timer size="2.8cqh" />}>
          <p className="text-[2.5cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Do energy taxes move k* in the predicted direction, and is calibration worth it?
          </p>
          <p className="mt-[1.4cqh] font-mono text-[2.1cqh] font-bold" style={{ color: S.amber }}>
            Hypotheses H6–H7 · N*
          </p>
          <p className="mt-[0.4cqh] text-[1.9cqh] font-semibold" style={{ color: S.inkSoft }}>
            N* = break-even queries.
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="teal">
        Primary decision: 5 percentage-point (pp) exact-match (EM) non-inferiority (NI) at k=4 vs
        k=32, with ≥20% savings. The 2 pp margin is estimation-only.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 8 · Scope and claim boundary                                        */
/* ------------------------------------------------------------------ */

function ScopeSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Scope"
      badgeTone="rose"
      title="The claim is deliberately narrow."
      subtitle="A proposal is also a decision about what not to claim."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.6cqw]">
        <SlideCard title="We will test" tone="teal" icon={<CheckCircle2 size="2.8cqh" />}>
          <SlideBullets
            items={[
              "5 pp non-inferiority at an interior k.",
              "At least 20% energy savings.",
              "Identity, context share, and replication.",
              "Policy capture and tax signs.",
            ]}
            size="2.4cqh"
          />
        </SlideCard>
        <SlideCard title="We will not claim" tone="rose" icon={<XCircle size="2.8cqh" />}>
          <SlideBullets
            items={[
              "A universal k*.",
              "A 2 pp optimum.",
              "5 pp certified before the rerun.",
              "A learned-policy gain from the oracle.",
              "Carbon optimality or frontier/dense/full Natural Questions (NQ) generalization.",
            ]}
            size="2.35cqh"
          />
        </SlideCard>
      </div>
      <SlideCallout tone="rose">
        The 2 pp static claim is dead. The 5 pp result is a preliminary signal, not a certificate.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 9 · Datasets                                                        */
/* ------------------------------------------------------------------ */

function DatasetSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Data"
      badgeTone="teal"
      title="Two corpora, one depth question."
      subtitle="SQuAD isolates depth; HotpotQA stresses multi-hop evidence and distractors."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.4cqw]">
        <SlideCard title="SQuAD v1.1 dev · primary" tone="teal" icon={<Database size="2.8cqh" />}>
          <SlideBullets
            items={[
              `Stanford Question Answering Dataset (SQuAD) v1.1 dev · ${datasets.squad.upstreamQuestions.toLocaleString("en-US")} questions.`,
              `Corpus: ${datasets.squad.corpus}.`,
              "Retriever: BM25 (Best Matching 25) Okapi, top-32.",
              `n=${datasets.squad.usedPrimary.toLocaleString("en-US")} primary · ${datasets.squad.usedReplication} replication · ${datasets.squad.usedBoundary} boundary.`,
              `Normalized EM (exact match); ${datasets.squad.license}.`,
            ]}
            size="2.25cqh"
          />
        </SlideCard>
        <SlideCard title="HotpotQA distractor · stress" tone="amber" icon={<Layers size="2.8cqh" />}>
          <SlideBullets
            items={[
              `HotpotQA (multi-hop question answering) distractor dev · ${datasets.hotpot.upstreamQuestions.toLocaleString("en-US")} questions; ${datasets.hotpot.used} used.`,
              `${datasets.hotpot.paragraphs} paragraphs per question: ${datasets.hotpot.goldParagraphs} gold + ${datasets.hotpot.distractors} distractors.`,
              `k ∈ {${datasets.hotpot.depths.join(",")}}; BM25 (Best Matching 25) Okapi, top-10.`,
              `No pooling across questions; ${datasets.hotpot.license}.`,
            ]}
            size="2.25cqh"
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
/* 10 · Conventional vs proposed                                       */
/* ------------------------------------------------------------------ */

function ContrastSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Method"
      badgeTone="deep"
      title="From static top-k to a gated energy decision."
      subtitle="The baseline is not wrong; it answers a different question."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.6cqw]">
        <SlideCard title="Conventional" tone="amber" icon={<Layers size="2.8cqh" />}>
          <SlideBullets
            items={[
              "Fixed top-k for every query.",
              "Accuracy-only or latency-only tuning.",
              "Mean energy or tokens, not per correct answer.",
              "No accuracy floor and no paired decision.",
            ]}
            size="2.4cqh"
          />
        </SlideCard>
        <SlideCard title="Proposed" tone="teal" icon={<Target size="2.8cqh" />}>
          <SlideBullets
            items={[
              "Gated E(k) = ΣJ / ΣC.",
              "Feasible set under the minimum accuracy A_min.",
              "Paired 5 pp non-inferiority.",
              "Identity, N*, causal taxes, and a learned policy.",
            ]}
            size="2.4cqh"
          />
        </SlideCard>
      </div>
      <SlideCallout tone="teal">The decision unit is joules per correct answer, not joules per query.</SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 11 · Method core                                                    */
/* ------------------------------------------------------------------ */

function MethodSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Method"
      badgeTone="deep"
      title="Four pieces, each falsifiable."
      subtitle="None of them assumes a universal k*. pp = percentage points."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="Gated estimand" tone="deep" icon={<Gauge size="2.8cqh" />}>
          <SlideFormula>E(k) = Σ J_k / Σ C_k</SlideFormula>
          <p className="mt-[1.0cqh] text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            k = passages · J_k = joules · C_k = correctness.
          </p>
          <p className="mt-[0.7cqh] text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            A(k) = accuracy; feasible set: A(k) ≥ A(32) − 5 pp.
          </p>
        </SlideCard>
        <SlideCard title="Optimal-depth identity" tone="teal" icon={<GitBranch size="2.8cqh" />}>
          <SlideFormula>k J′(k) / J(k) = k A′(k) / A(k)</SlideFormula>
          <p className="mt-[1.0cqh] text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            J′ and A′ are derivatives; the elasticities are equal at an interior optimum.
          </p>
          <p className="mt-[0.7cqh] text-[2.2cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
            It is a local diagnostic and flags over-retrieval.
          </p>
        </SlideCard>
        <SlideCard title="Certification threshold" tone="amber" icon={<Timer size="2.8cqh" />}>
          <SlideFormula>N* = C_cert / [A(k*)(E(k₀) − E(k*))]</SlideFormula>
          <p className="mt-[1.0cqh] text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            C_cert = sweep energy · k₀ = default depth · k* = selected depth.
          </p>
          <p className="mt-[0.7cqh] text-[2.2cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
            N* = break-even queries; finding the depth is an energy purchase.
          </p>
        </SlideCard>
        <SlideCard title="Causal energy tax" tone="rose" icon={<FlaskConical size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            a = fixed cost · b = per-passage cost · k* = selected depth.
          </p>
          <p className="mt-[0.8cqh] text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Fixed tax raises k*; per-passage tax lowers k*. A wrong sign falsifies the affine/split
            model.
          </p>
        </SlideCard>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 12 · Flow diagram                                                   */
/* ------------------------------------------------------------------ */

function FlowSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Flow"
      badgeTone="deep"
      title="One pipeline from data to decision."
      subtitle="The same sweep produces the curve, the identity test, the certification cost, and the policy data."
      index={index}
      total={total}
    >
      <div className="flex min-h-0 flex-1 items-center justify-center">
        <Image
          src="/flow-diagram.png"
          alt="Experiment pipeline: prepare data, build a BM25 index, sweep seven depths, measure energy with NVML and blocks, score with exact match and bootstrap, and analyze E(k), N*, and policy. Decision flow: freeze the preregistration, P0 golden reproduction, P1 powered run, gates G1-G5 and K1-K7, then P2, P3, and P4."
          width={7512}
          height={3167}
          priority
          className="h-full w-full object-contain"
        />
      </div>
      <p className="mt-[0.4cqh] text-center text-[2.0cqh] font-semibold" style={{ color: S.inkSoft }}>
        BM25 = Best Matching 25 · NVML = NVIDIA Management Library · EM = exact match
      </p>
      <SlideCallout tone="teal">The sweep is the measurement; the gates are the decision.</SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 13 · Experimental setup                                             */
/* ------------------------------------------------------------------ */

function SetupSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Setup"
      badgeTone="amber"
      title="A powered, controlled, local experiment."
      subtitle="Everything is pre-registered before the confirmatory accuracy data are seen."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-3 gap-[1.2cqw]">
        <SlideCard title="Conditions" tone="deep" icon={<Layers size="2.8cqh" />}>
          <SlideBullets
            items={[
              `SQuAD: ${rerun.primary.n.toLocaleString("en-US")} × 7 depths`,
              `Qwen2.5-1.5B replication: ${rerun.replication.n} × 7`,
              `HotpotQA: ${rerun.hotpot.n} × 6`,
              `Boundary ${rerun.boundary.n} × 3 · taxes ${rerun.taxes.n} × 2`,
            ]}
            size="2.25cqh"
          />
        </SlideCard>
        <SlideCard title="Measurement" tone="teal" icon={<Gauge size="2.8cqh" />}>
          <SlideBullets
            items={[
              "NVIDIA Management Library (NVML): 100 ms; idle 60 s.",
              "20-query blocks; 10-hex nonce.",
              "Thermal log; coefficient of variation (CV); wall meter.",
              "10,000 paired bootstrap resamples.",
            ]}
            size="2.25cqh"
          />
        </SlideCard>
        <SlideCard title="Decision" tone="rose" icon={<ShieldCheck size="2.8cqh" />}>
          <SlideBullets
            items={[
              "5 percentage-point (pp) non-inferiority (NI) at k=4 vs k=32.",
              "≥20% energy savings.",
              "One-sided significance level α = 0.05.",
              "2 pp estimation-only; go/kill gates.",
            ]}
            size="2.25cqh"
          />
        </SlideCard>
      </div>
      <SlideCallout tone="amber">
        15–20 GPU (graphics processing unit) hours · RTX 3060 6 GB · batch 1 · AC power · screen off.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 14 · Analysis plan and gates                                        */
/* ------------------------------------------------------------------ */

function AnalysisSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Analysis"
      badgeTone="rose"
      title="The gates decide what the result means."
      subtitle="A fired gate is a finding, not a failure to hide."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.4cqw]">
        <SlideCard title="Primary decision" tone="rose" icon={<Target size="2.8cqh" />}>
          <p className="text-[2.45cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            5 percentage-point (pp) exact-match (EM) non-inferiority (NI) at k=4 vs k=32.
          </p>
          <div className="mt-[1.0cqh]">
            <SlideFormula>A(4) − A(32) &gt; −5 pp · savings ≥ 20%</SlideFormula>
          </div>
          <p className="mt-[0.9cqh] text-[2.3cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            P(k*) = bootstrap probability that the selected depth is optimal.
          </p>
          <p className="mt-[0.9cqh] text-[2.3cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            One-sided significance level α = .05 · 10,000 paired bootstrap resamples.
          </p>
          <p className="mt-[0.9cqh] text-[2.4cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Paired n, discordant counts, and invalid counts are reported.
          </p>
          <p className="mt-[0.9cqh] text-[2.4cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
            The 2 pp margin is estimation-only.
          </p>
        </SlideCard>
        <SlideCard title="Gate families" tone="deep" icon={<ListChecks size="2.8cqh" />}>
          <div className="grid grid-cols-2 gap-[1.2cqw]">
            <div>
              <p className="font-mono text-[2.05cqh] font-bold uppercase tracking-[0.1em]" style={{ color: S.teal }}>
                Go gates · G1–G5
              </p>
              <ul className="mt-[0.6cqh] space-y-[0.55cqh] text-[2.15cqh] font-semibold leading-snug" style={{ color: S.ink }}>
                <li>G1 · 5 pp non-inferiority + ≥20%</li>
                <li>G2 · upper bound ≤5 pp</li>
                <li>G3 · context share [0.10, 0.70]</li>
                <li>G4 · oracle ≥20%, capture ≥50%</li>
                <li>G5 · replication</li>
              </ul>
            </div>
            <div>
              <p className="font-mono text-[2.05cqh] font-bold uppercase tracking-[0.1em]" style={{ color: S.rose }}>
                Kill gates · K1–K7
              </p>
              <ul className="mt-[0.6cqh] space-y-[0.55cqh] text-[2.15cqh] font-semibold leading-snug" style={{ color: S.ink }}>
                <li>K1 · energy effect &lt;10%</li>
                <li>K2 · k* at boundary</li>
                <li>K3 · P(k*) &lt; 0.8</li>
                <li>K4 · context share &lt;5%</li>
                <li>K5 · k* span &gt;1</li>
                <li>K6 · oracle gain &lt;15%</li>
                <li>K7 · repeat CV &gt;20%</li>
              </ul>
            </div>
          </div>
        </SlideCard>
      </div>
      <SlideCallout tone="rose">
        No gate is added, removed, or re-thresholded after the primary outcome.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 15 · Preliminary results                                            */
/* ------------------------------------------------------------------ */

function PreliminarySlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Preliminary results"
      badgeTone="teal"
      title="The preliminary study changed the claim."
      subtitle="A precise energy measurement and a failed accuracy certification. Both belong in the record."
      index={index}
      total={total}
      pilot
    >
      <SlideKpiRow
        cols={3}
        items={[
          {
            value: `${pilot.energy.span.toFixed(2)}×`,
            label: "energy at k=32 vs k=1",
            sub: `${pilot.energy.e32.toFixed(1)} vs ${pilot.energy.e1.toFixed(1)} J/correct`,
            tone: "deep",
          },
          {
            value: `${pilot.contextShare.at32}%`,
            label: "context-side share",
            sub: `at k=32; retrieval ${pilot.retrievalShare.min}–${pilot.retrievalShare.max}%`,
            tone: "teal",
          },
          {
            value: `${pilot.repeatCv.median.toFixed(2)}%`,
            label: "median coefficient of variation (CV)",
            sub: `max ${pilot.repeatCv.max.toFixed(2)}%; k=${pilot.repeatCv.k}`,
            tone: "amber",
          },
          {
            value: pilot.accuracy.a32.toFixed(3),
            label: "exact-match accuracy (A_EM) at k=32",
            sub: `${pilot.accuracy.a1.toFixed(3)} at k=1; plateau ${pilot.accuracy.plateauLow.toFixed(3)}–${pilot.accuracy.plateauHigh.toFixed(3)}`,
            tone: "deep",
          },
          {
            value: `P = ${pilot.static2pp.pOptimal.toFixed(2).replace(/^0/, "")}`,
            label: "2 pp selection",
            sub: "DEAD at the boundary",
            tone: "rose",
          },
          {
            value: `${pilot.fivePp.savings}%`,
            label: `5 pp savings at k=${pilot.fivePp.k}`,
            sub: `N* = ${pilot.fivePp.nStar}; signal, not certified`,
            tone: "amber",
          },
        ]}
      />
      <div className="mt-[1.3cqh] border-l-[0.4cqw] px-[1.4cqw] py-[0.8cqh]" style={{ borderColor: S.rose, background: S.roseSoft }}>
        <p className="text-[2.25cqh] font-bold leading-snug" style={{ color: S.ink }}>
          pp = percentage points. The 2 pp static claim is DEAD. The 5 pp result is a preliminary signal, not a certificate.
        </p>
      </div>
      <div className="mt-[1.2cqh] grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="What survived" tone="teal">
          <SlideBullets
            items={[
              "Steep energy–depth tradeoff: 3.45×.",
              "Affine fit R² (goodness of fit) = 0.9990; context share 36.3% → 85.1%.",
              "Optimal-depth identity holds at k=2; repeat CV median 3.80%.",
            ]}
            size="2.2cqh"
          />
        </SlideCard>
        <SlideCard title="What died / is bounded" tone="rose">
          <SlideBullets
            items={[
              "2 pp static optimum: DEAD (P = .61).",
              "5 pp at k=4: signal, not certified.",
              `Oracle ${pilot.oracle.gain}%: upper bound only.`,
            ]}
            size="2.2cqh"
          />
        </SlideCard>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 16 · Expected results and decision rules                            */
/* ------------------------------------------------------------------ */

function ExpectedSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Expected results"
      badgeTone="deep"
      title="What the rerun must show — and what would falsify it."
      subtitle="We pre-commit to the decision, not to a positive result. H1–H7 are the pre-registered hypotheses."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="Hypothesis 1 · affine energy" tone="deep" icon={<TrendingUp size="2.8cqh" />}>
          <p className="text-[2.45cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Supported if R² (goodness of fit) ≥ 0.95 and lack-of-fit is not rejected at 5%.
          </p>
          <p className="mt-[1.0cqh] text-[2.25cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
            Falsified if R² &lt; 0.95 or the lack-of-fit check rejects.
          </p>
        </SlideCard>
        <SlideCard title="Hypothesis 2 · primary decision" tone="rose" icon={<Target size="2.8cqh" />}>
          <p className="text-[2.45cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Supported if the 5 percentage-point (pp) lower bound &gt; −5 pp and savings ≥ 20%.
          </p>
          <p className="mt-[1.0cqh] text-[2.25cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
            Falsified if the lower bound ≤ −5 pp or savings &lt; 20%.
          </p>
        </SlideCard>
        <SlideCard title="Hypotheses 3–4 · identity + split" tone="teal" icon={<GitBranch size="2.8cqh" />}>
          <p className="text-[2.45cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Optimal-depth identity confidence interval (CI) includes 0; context share in [0.10, 0.70]
            and rising.
          </p>
          <p className="mt-[1.0cqh] text-[2.25cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
            Falsified if the CI excludes 0 or the share leaves the band.
          </p>
        </SlideCard>
        <SlideCard title="Hypotheses 5–6 · policy + taxes" tone="amber" icon={<FlaskConical size="2.8cqh" />}>
          <p className="text-[2.45cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Hindsight oracle ≥ 20%, capture ≥ 50%; fixed tax ↑ k*, per-passage ↓ k*.
          </p>
          <p className="mt-[1.0cqh] text-[2.25cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
            Falsified if capture &lt; 50% or a tax sign is wrong.
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="deep">
        Hypothesis H7: the primary-decision direction replicates on Qwen2.5-1.5B or HotpotQA. A
        null or fired gate is a reportable result.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 17 · Applications, timeline, conclusion                             */
/* ------------------------------------------------------------------ */

function ImpactSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Impact & plan"
      badgeTone="deep"
      title="A green-RAG decision rule — and a plan to test it."
      subtitle="Applications, risks, and the ask."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="Applications" tone="teal" icon={<Zap size="2.8cqh" />}>
          <SlideBullets
            items={[
              "Green RAG serving and capacity planning.",
              "Edge and consumer-GPU deployment.",
              "Energy-aware retrieval benchmarks.",
              "Accuracy-margin policy for operators.",
              "Open harness and reproducibility package.",
            ]}
            size="2.3cqh"
          />
        </SlideCard>
        <SlideCard title="Risks & resources" tone="rose" icon={<AlertTriangle size="2.8cqh" />}>
          <p className="text-[2.25cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Top risks: scoring dependence, reader strength, single corpus/retriever, thermal
            throttling, NVML resolution, prefix cache, policy overfitting, gate binding.
          </p>
          <p className="mt-[1.0cqh] text-[2.25cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Mitigation: pre-register scoring, replicate on 1.5B/HotpotQA, log thermal, use a nonce.
          </p>
          <p className="mt-[1.0cqh] text-[2.3cqh] font-bold" style={{ color: S.ink }}>
            15–20 GPU-hours · ≤ $47 · local RTX 3060 only.
          </p>
        </SlideCard>
        <div
          className="col-span-2 flex min-h-0 items-center justify-between gap-[2cqw] border-2 p-[1.8cqw]"
          style={{ borderColor: S.deep, background: S.deep }}
        >
          <div className="max-w-[72%]">
            <p className="font-mono text-[2.0cqh] font-bold uppercase tracking-[0.14em]" style={{ color: S.lime }}>
              The ask
            </p>
            <p className="mt-[0.9cqh] text-[2.4cqh] font-semibold leading-snug" style={{ color: S.white }}>
              Test whether an interior depth retains accuracy while saving roughly 69% of energy per
              correct answer — and whether finding that depth is worth its energy.
            </p>
          </div>
          <p className="text-right font-mono text-[2.4cqh] font-bold uppercase leading-snug tracking-[0.12em]" style={{ color: S.lime }}>
            Thank you
            <br />
            Questions
          </p>
        </div>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 18 · References                                                     */
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
            start={8}
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
  { id: "summary", title: "The proposal in one slide", Component: ExecSummarySlide },
  { id: "introduction", title: "RAG answers by choosing how much evidence to read", Component: IntroSlide },
  { id: "problem", title: "Depth is tuned for accuracy or latency, not joules per correct answer", Component: ProblemSlide },
  { id: "motivation", title: "Retrieval energy is a deployment cost", Component: MotivationSlide },
  { id: "gap", title: "Existing work optimizes accuracy, latency, or tokens", Component: GapSlide },
  { id: "objectives", title: "Three questions, seven pre-registered hypotheses", Component: ObjectivesSlide },
  { id: "scope", title: "The claim is deliberately narrow", Component: ScopeSlide },
  { id: "data", title: "Two corpora, one depth question", Component: DatasetSlide },
  { id: "contrast", title: "From static top-k to a gated energy decision", Component: ContrastSlide },
  { id: "method", title: "Four pieces, each falsifiable", Component: MethodSlide },
  { id: "flow", title: "One pipeline from data to decision", Component: FlowSlide },
  { id: "setup", title: "A powered, controlled, local experiment", Component: SetupSlide },
  { id: "analysis", title: "The gates decide what the result means", Component: AnalysisSlide },
  { id: "preliminary", title: "The preliminary study changed the claim", Component: PreliminarySlide },
  { id: "expected", title: "What the rerun must show, and what would falsify it", Component: ExpectedSlide },
  { id: "impact", title: "A green-RAG decision rule and a plan to test it", Component: ImpactSlide },
  { id: "references", title: "References", Component: ReferencesSlide },
];
