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
import { course, datasets, references, team } from "@/lib/project-data";

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
                Methodology · 2026
              </p>
              <h1
                className="mt-[1.4cqh] text-[5.8cqh] font-semibold leading-[1.02] tracking-[-0.03em]"
                style={{ fontFamily: "var(--font-serif)", color: S.ink }}
              >
                How the joules were{" "}
                <span style={{ fontStyle: "italic", color: S.teal, borderBottom: `0.2cqw solid ${S.lime}` }}>
                  measured
                </span>
              </h1>
              <p className="mt-[1.9cqh] text-[2.55cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
                Why the per-query windows were abandoned, what replaced them, and what the
                mechanism is.
              </p>
              <div className="mt-[2.0cqh] flex flex-wrap gap-[0.8cqw]">
                <SlideChip tone="deep">
                  {course.code} · Section {course.section}
                </SlideChip>
                <SlideChip tone="teal">3 frozen preregs</SlideChip>
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
/* 2 · The pipeline and the estimand                                   */
/* ------------------------------------------------------------------ */

function IntroProblemSlide({ index, total }: SlideProps) {
  const steps = ["Question", "BM25", "k passages", "Reader", "Answer"];
  return (
    <SlideFrame
      badge="Method in one picture"
      badgeTone="deep"
      title="RAG reads a few passages, then answers."
      subtitle="The number of passages is the retrieval depth, k. The decision quantity is energy per correct answer."
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
          <SlideCard title="Ratio of sums" tone="teal">
            <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              Total joules over total correct answers — never the mean of per-question ratios.
            </p>
          </SlideCard>
          <SlideCard title="Accuracy floor" tone="amber">
            <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              The 5 pp margin is the constraint; the saving is the objective.
            </p>
          </SlideCard>
          <SlideCard title="One GPU" tone="deep">
            <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              Every joule is GPU energy from NVML. No wall meter, no system claim.
            </p>
          </SlideCard>
        </div>
      </div>
      <SlideCallout tone="teal">
        5 pp = 5 percentage points. A depth-invariant calibration factor cancels in every ratio.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 3 · Block estimator                                                 */
/* ------------------------------------------------------------------ */

function BlockEstimatorSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Measurement Method"
      badgeTone="deep"
      title="One block, one depth, one integral."
      subtitle="Randomized block order, cooldown separation, idle from the cooldown tail — 35 blocks over 1,000 questions per depth."
      index={index}
      total={total}
    >
      <SlideKpiRow
        items={[
          { value: "1.2–7.0%", label: "block-to-block CV", sub: "all 7 depths, gate 20%", tone: "deep" },
          { value: "2.131", label: "J per passage", sub: "95% CI [2.043, 2.219]", tone: "teal" },
          { value: "65.25%", label: "saving k=4 vs k=32", sub: "95% CI [61.27, 69.11]", tone: "amber" },
        ]}
      />
      <div className="mt-[1.2cqh] grid min-h-0 flex-1 grid-cols-3 gap-[1.2cqw]">
        <SlideCard title="Randomize" tone="deep" icon={<Timer size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Depth × replicate order shuffled; 120 s cooldown before every block; 2 queries
            discarded to re-steady the device.
          </p>
        </SlideCard>
        <SlideCard title="Baseline honestly" tone="teal" icon={<Gauge size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Idle sampled from the tail of each block&apos;s own cooldown. A baseline read on a
            warm GPU understates energy by ~14%.
          </p>
        </SlideCard>
        <SlideCard title="Resume safely" tone="amber" icon={<ListChecks size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Every ledger row carries a protocol tag. A fixed method can never silently inherit
            rows measured with a broken one.
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="deep">
        Smoke-first on every GPU script; separate analysis directory per run so runs never overwrite each other.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 4 · Metrology audit                                                 */
/* ------------------------------------------------------------------ */

function AuditSlide({ index, total }: SlideProps) {
  const rows = [
    ["Window vs block at k=4", "−22%", "Depth-biased, not scalar-fixable", "Falsified"],
    ["Continuous replay / block", "0.847 median", "Drifts with heat (ρ = −0.855)", "Unstable"],
    ["Sessions (ICC)", "≈ 0", "Level ±3–6%, ratio ±0.92 pp", "Stable"],
  ];
  return (
    <SlideFrame
      badge="Metrology Audit"
      badgeTone="teal"
      title="The window lies; the block is stable."
      subtitle="Three instruments compared head-to-head. Only one is stationary."
      index={index}
      total={total}
    >
      <SlideTable
        head={["Comparison", "Value", "Reading", "Verdict"]}
        rows={rows}
        tone="amber"
        widths={["28%", "18%", "36%", "18%"]}
      />
      <div className="mt-[1.2cqh] grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="Kept on stability" tone="deep" icon={<Target size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            The block estimator is retained because its CV is 1.2–7.0%, not because a reference
            validates it — cross-estimator agreement at 3 pp is unattainable by construction.
          </p>
        </SlideCard>
        <SlideCard title="Absolute J is a range" tone="rose" icon={<AlertTriangle size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            The level carries a 3–6% between-occasion offset on identical questions. The ratio is
            reproducible; the level is not.
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="amber">
        G7 failed on replay agreement (7.08 pp vs 3 pp). The failure indicts the references, not just the estimate.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 5 · Dose-response                                                   */
/* ------------------------------------------------------------------ */

function DoseSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Causal Mechanism I"
      badgeTone="deep"
      title="Distractors help when gold comes first."
      subtitle="Gold held at rank 1, 0 to 31 distractors appended, 500 questions. H-overload predicted a fall."
      index={index}
      total={total}
    >
      <SlideKpiRow
        items={[
          { value: "0.382 → 0.528", label: "accuracy, dose 0 → 31", sub: "+14.6 pp", tone: "deep" },
          { value: "+3.06 pp", label: "per doubling", sub: "95% CI [1.43, 4.69]", tone: "teal" },
          { value: "Rejected", label: "H-overload", sub: "reader overload not observed", tone: "amber" },
        ]}
      />
      <div className="mt-[1.2cqh] grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="What this means" tone="teal" icon={<TrendingUp size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            With the gold present early, extra passages help. P1&apos;s precision collapse reads as
            gold displacement to lower ranks — not the reader choking on distractors.
          </p>
        </SlideCard>
        <SlideCard title="Scope" tone="amber" icon={<FlaskConical size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            On the 590 questions the reader already answers at 0.65 with gold alone, the same
            manipulation lowers accuracy by 3.73 pp. Overload is not uniform — it varies with
            the sample.
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="deep">
        Position conditions were halted by the preregistered stop rule (fresh gap 3.00 pp &lt; 10%).
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 6 · Dense swap + padding                                            */
/* ------------------------------------------------------------------ */

function DensePaddingSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Causal Mechanism II"
      badgeTone="teal"
      title="The knee does not travel; tokens cost."
      subtitle="Frozen MiniLM rankings over the same 45,651 passages, then length-matched padding."
      index={index}
      total={total}
    >
      <SlideKpiRow
        items={[
          { value: "−2.20 pp", label: "dense DiD", sub: "95% CI [−5.40, +1.00], null", tone: "deep" },
          { value: "75.93 J/q", label: "k=4 padded to k=32 length", sub: "87% of k=32 (87.22)", tone: "teal" },
          { value: "~25 mJ", label: "per prefill token", sub: "hardware-grounded", tone: "amber" },
        ]}
      />
      <div className="mt-[1.2cqh] grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="Retriever swap" tone="deep" icon={<GitBranch size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            MiniLM recall trails BM25 at both depths, yet both arms rise with depth. The knee is
            reader-side, not a rank artifact.
          </p>
        </SlideCard>
        <SlideCard title="Length, not passages" tone="teal" icon={<Zap size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Neutral tokens cost nearly as much as real passages (75.93 vs 87.22 J/q against 26.22
            at k=4). Energy follows prompt length.
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="teal">
        Two paths agree: padding proves it interventionally, the timing model observationally.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 7 · Token model                                                     */
/* ------------------------------------------------------------------ */

function TokenModelSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Token Model"
      badgeTone="deep"
      title="Energy follows prompt tokens."
      subtitle="7,000 P1 requests with the reader's own token counts: affine in tokens beats affine in depth."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-[1.1fr_0.9fr] gap-[1.4cqw]">
        <div className="flex flex-col justify-center gap-[1.2cqh]">
          <SlideFormula>
            <span className="inline-flex items-center gap-[0.18em]">
              <i>J</i>
              <span>{" = "}</span>
              <span>
                13.88 + 0.02549<i>T</i>
                <MathSub>pre</MathSub>
                {" + 1.135"}
                <i>T</i>
                <MathSub>dec</MathSub>
              </span>
            </span>
          </SlideFormula>
          <div
            className="grid grid-cols-2 gap-x-[1.2cqw] gap-y-[0.45cqh] text-[2.0cqh] font-semibold leading-snug"
            style={{ color: S.ink }}
          >
            <p>
              Token model <i>R</i>
              <MathSup>2</MathSup> = 0.9575
            </p>
            <p>
              Depth model <i>R</i>
              <MathSup>2</MathSup> = 0.8965
            </p>
            <p>Prefill grows 15× across the grid</p>
            <p>Decode stays flat (0.02–0.11 s)</p>
          </div>
        </div>
        <div className="grid min-h-0 grid-rows-2 gap-[1.0cqh]">
          <SlideCard title="Marginal cost" tone="teal">
            <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              About 25 mJ per prefill token; about 1.1 J per decode token. Prefill dominates the
              grid&apos;s energy.
            </p>
          </SlideCard>
          <SlideCard title="Why this matters" tone="amber">
            <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
              The H1 depth curve is really a token curve. Depth is just the cheapest way to count
              tokens — until distractors change what the tokens do.
            </p>
          </SlideCard>
        </div>
      </div>
      <SlideCallout tone="deep">
        J per prefill token falls 5× across depths — expected under a fixed 13.9 J overhead, not evidence against the model.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 8 · Preregistration discipline                                      */
/* ------------------------------------------------------------------ */

function PreregSlide({ index, total }: SlideProps) {
  const rows = [
    ["prereg-freeze-v1", "P1 confirmatory", "5 pp NI + 20% floor", "—"],
    ["prereg-measurement-v1", "Phase 7 blocks", "CV, slope, 3 pp replay", "A-003, A-004 (seen: yes)"],
    ["prereg-qc-v1", "Phase 8 mechanism", "Trend, DiD, ±2 pp TOST", "A-005 (seen: yes)"],
  ];
  return (
    <SlideFrame
      badge="Preregistration Discipline"
      badgeTone="amber"
      title="Frozen before outcome, amended in public."
      subtitle="Three frozen preregs. Amendments disclose outcome_data_seen. No gate re-thresholded after seeing data."
      index={index}
      total={total}
    >
      <SlideTable
        head={["Tag", "Scope", "Decides", "Amendments"]}
        rows={rows}
        tone="deep"
        widths={["24%", "24%", "28%", "24%"]}
      />
      <div className="mt-[1.2cqh] grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="The deviation rule" tone="deep" icon={<ListChecks size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Any change goes in amendments.md plus the decision log — with date, original text,
            reason, and whether outcome data had been seen.
          </p>
        </SlideCard>
        <SlideCard title="Failed gates stay failed" tone="rose" icon={<AlertTriangle size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            G1, G2, G7 never passed. They are reported as findings with measured reasons, never
            tuned away.
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="amber">
        A design change after seeing data is disclosed plainly — then the only credible posture is to publish whatever the rerun says.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 9 · Headline results                                                */
/* ------------------------------------------------------------------ */

function ResultsSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Headline Results"
      badgeTone="deep"
      title="A knee, not an optimum — and a precise negative."
      subtitle="Energy bottoms at k=1–2 while accuracy still climbs; k=4 loses 4.30 pp against k=32."
      index={index}
      total={total}
    >
      <SlideKpiRow
        items={[
          { value: "−4.30 pp", label: "k=4 vs k=32", sub: "lower bound −6.17 pp; 5 pp not supported", tone: "rose" },
          { value: ">60%", label: "saving, every estimator", sub: "65.25% block [61.27, 69.11]", tone: "teal" },
          { value: "0.459 → 0.490", label: "accuracy k=4 → k=32 (block)", sub: "monotone, reproduces P1", tone: "deep" },
        ]}
      />
      <div className="mt-[1.2cqh] grid min-h-0 flex-1 grid-cols-2 gap-[1.2cqw]">
        <SlideCard title="The knee" tone="teal" icon={<TrendingUp size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            E(k) is minimised at k=1–2, rises 14.5% to k=4, then steeply. Accuracy still climbs
            3.9 pp from k=2 to k=4, then 0.6 pp to k=8 for +30.5% energy. A property of this
            dataset, reader, and retriever — not a universal k*.
          </p>
        </SlideCard>
        <SlideCard title="Transportability" tone="amber" icon={<Layers size="2.8cqh" />}>
          <p className="text-[2.2cqh] font-semibold leading-snug" style={{ color: S.ink }}>
            Direction holds on HotpotQA (−10.80 pp), inconclusive on Qwen2.5-1.5B (+2.00 pp).
            BM25 policy captures −9.8% of the oracle gap: no adaptive claim.
          </p>
        </SlideCard>
      </div>
      <SlideCallout tone="deep">
        P1 used 1,000 SQuAD questions × 7 depths, Qwen3.5-4B (Q4), BM25, one RTX 3060 Laptop GPU.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 10 · Claim boundary                                                 */
/* ------------------------------------------------------------------ */

function BoundarySlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Claim Boundary"
      badgeTone="rose"
      title="What we claim — and what we don't."
      subtitle="The boundary is explicit so a failure reads as a finding, not a retraction."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.4cqw]">
        <SlideCard title="Claimed" tone="teal" icon={<Target size="2.8cqh" />}>
          <SlideBullets
            items={[
              "Block precision (CV 1.2–7.0%) and the affine slope 2.131 J/passage.",
              "Window bias direction: overstates short-depth energy by 22%.",
              "Saving above 60% on every estimator tested.",
              "Reader-side mechanism; ~25 mJ per prefill token.",
            ]}
            size="2.15cqh"
          />
        </SlideCard>
        <SlideCard title="Not claimed" tone="rose" icon={<AlertTriangle size="2.8cqh" />}>
          <SlideBullets
            items={[
              "No 5 pp guarantee; no point saving; no universal k*.",
              "No adaptive-policy gain; no 2 pp optimum.",
              "No absolute joule figure as a deployment guarantee.",
              "No system or wall energy — GPU integral only.",
            ]}
            size="2.15cqh"
          />
        </SlideCard>
      </div>
      <SlideCallout tone="rose">
        P0 stays FAIL (0.7944 not re-thresholded). The oracle figures are hindsight upper bounds.
      </SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 11 · Flow diagram                                                    */
/* ------------------------------------------------------------------ */

function FlowSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Study Workflow"
      badgeTone="deep"
      title="How the study runs."
      subtitle="Preregister, measure in blocks, audit the instrument, test the mechanism — each phase gated."
      index={index}
      total={total}
    >
      <div className="flex min-h-0 flex-1 items-center justify-center">
        <Image
          src="/flow-diagram-v4.png"
          alt="Study workflow: prepare SQuAD and HotpotQA, index with BM25, sweep seven SQuAD depths and six HotpotQA depths, measure NVML power with idle and block calibration, score normalized exact match, then analyze the paired non-inferiority test, bootstrap, E(k), N*, and policy. Measurement hardening adds block estimators, permutation replays, and session variance; Phase 8 adds distractor dose-response and a dense comparison."
          width={7512}
          height={3167}
          priority
          className="h-full w-full object-contain"
        />
      </div>
      <p className="mt-[0.4cqh] text-center text-[2.0cqh] font-semibold" style={{ color: S.inkSoft }}>
        BM25 = Best Matching 25 · NVML = NVIDIA Management Library · EM = exact match · DiD = difference-in-differences
      </p>
      <SlideCallout tone="teal">The run is the measurement; the checkpoints are the decision.</SlideCallout>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 12 · Datasets                                                       */
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
              "Retriever: BM25 (Best Matching 25) top-32; dense MiniLM arm in Phase 8.",
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
/* 13 · References                                                     */
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
  { id: "title", title: "How the joules were measured", Component: TitleSlide },
  { id: "estimand", title: "Energy per correct answer", Component: IntroProblemSlide },
  { id: "blocks", title: "One block, one depth, one integral", Component: BlockEstimatorSlide },
  { id: "audit", title: "The window lies; the block is stable", Component: AuditSlide },
  { id: "dose", title: "Distractors help when gold comes first", Component: DoseSlide },
  { id: "dense-padding", title: "The knee does not travel; tokens cost", Component: DensePaddingSlide },
  { id: "tokens", title: "Energy follows prompt tokens", Component: TokenModelSlide },
  { id: "prereg", title: "Frozen before outcome, amended in public", Component: PreregSlide },
  { id: "results", title: "A knee, not an optimum", Component: ResultsSlide },
  { id: "boundary", title: "What we claim and what we don't", Component: BoundarySlide },
  { id: "flow", title: "How the study runs", Component: FlowSlide },
  { id: "data", title: "Two datasets, one depth question", Component: DatasetSlide },
  { id: "references", title: "References", Component: ReferencesSlide },
];
