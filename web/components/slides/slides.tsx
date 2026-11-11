import type { ReactElement } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Cpu,
  Database,
  Gauge,
  GitBranch,
  Layers,
  PlugZap,
  ScanLine,
  Scale,
  ShieldCheck,
  Target,
  Thermometer,
  Timer,
  XCircle,
  Zap,
} from "lucide-react";
import {
  S,
  SlideBars,
  SlideBullets,
  SlideCallout,
  SlideCard,
  SlideChip,
  SlideFormula,
  SlideFrame,
  SlideKpiRow,
  SlideMark,
  SlideTable,
} from "@/components/slides/primitives";
import {
  claimBoundary,
  datasets,
  gates,
  measurement,
  pilot,
  rerun,
  theory,
} from "@/lib/project-data";

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
/* Small helpers                                                       */
/* ------------------------------------------------------------------ */

const LOG_MAX = Math.log2(33);
const xPos = (k: number) => (Math.log2(k + 1) / LOG_MAX) * 100;

function AccuracyPlot() {
  const min = 0.35;
  const max = 0.6;
  const yPos = (value: number) => 100 - ((value - min) / (max - min)) * 100;
  const points = [
    { k: 1, value: pilot.accuracy.a1, label: pilot.accuracy.a1.toFixed(3), side: "right" as const },
    { k: 4, value: pilot.accuracy.a4, label: pilot.accuracy.a4.toFixed(3), side: "right" as const },
    { k: 32, value: pilot.accuracy.a32, label: pilot.accuracy.a32.toFixed(3), side: "left" as const },
  ];
  const bandLeft = xPos(pilot.accuracy.plateauFrom);
  const bandRight = xPos(pilot.accuracy.plateauTo);
  const bandTop = yPos(pilot.accuracy.plateauHigh);
  const bandBottom = yPos(pilot.accuracy.plateauLow);

  return (
    <div
      role="img"
      aria-label="Pilot accuracy: 0.395 at depth 1, 0.520 at depth 4, a plateau of 0.520 to 0.535 from depth 4 to 16, and 0.570 at depth 32."
    >
      <div className="relative h-[34cqh] border-b border-l" style={{ borderColor: S.line }}>
        {[0.35, 0.4, 0.45, 0.5, 0.55, 0.6].map((tick) => (
          <div
            key={tick}
            className="absolute inset-x-0 border-t"
            style={{ top: `${yPos(tick)}%`, borderColor: S.line }}
          />
        ))}
        {[0, 1, 2, 4, 8, 16, 32].map((tick) => (
          <div
            key={tick}
            className="absolute bottom-0 top-0 border-l"
            style={{ left: `${xPos(tick)}%`, borderColor: S.line }}
          />
        ))}
        <div
          className="absolute border-y border-dashed"
          style={{
            left: `${bandLeft}%`,
            width: `${bandRight - bandLeft}%`,
            top: `${bandTop}%`,
            height: `${bandBottom - bandTop}%`,
            background: S.limeSoft,
            borderColor: S.teal,
          }}
        />
        <span
          className="absolute -translate-x-1/2 whitespace-nowrap px-[0.7cqw] py-[0.2cqh] font-mono text-[1.8cqh] font-bold"
          style={{ left: `${(bandLeft + bandRight) / 2}%`, top: `calc(${bandTop}% - 3.2cqh)`, color: S.teal, background: S.paper }}
        >
          plateau {pilot.accuracy.plateauLow.toFixed(3)}–{pilot.accuracy.plateauHigh.toFixed(3)}
        </span>
        {points.map((point) => (
          <div
            key={point.k}
            className="absolute"
            style={{ left: `${xPos(point.k)}%`, top: `${yPos(point.value)}%` }}
          >
            <span
              className="absolute block h-[1.6cqh] w-[1.6cqh] -translate-x-1/2 -translate-y-1/2 rounded-full border-2"
              style={{ background: S.teal, borderColor: S.paper }}
            />
            <span
              className="absolute top-0 whitespace-nowrap font-mono text-[1.9cqh] font-bold tnum"
              style={{
                color: S.ink,
                transform:
                  point.side === "left"
                    ? "translate(calc(-100% - 1.2cqh), -50%)"
                    : "translate(1.2cqh, -50%)",
              }}
            >
              {point.label}
            </span>
          </div>
        ))}
      </div>
      <div className="relative mt-[0.6cqh] h-[1.8cqh]" aria-hidden="true">
        {[0, 1, 2, 4, 8, 16, 32].map((tick) => (
          <span
            key={tick}
            className="absolute -translate-x-1/2 font-mono text-[1.8cqh]"
            style={{ left: `${xPos(tick)}%`, color: S.muted }}
          >
            {tick}
          </span>
        ))}
      </div>
    </div>
  );
}

function Status({ pass }: { pass: boolean }) {
  return (
    <span
      className="font-mono text-[2.2cqh] font-bold uppercase tracking-[0.08em]"
      style={{ color: pass ? S.teal : S.rose }}
    >
      {pass ? "Pass" : "Fail"}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* 1 · Title                                                           */
/* ------------------------------------------------------------------ */

function TitleSlide({ index, total }: SlideProps) {
  return (
    <div className="relative flex h-full w-full overflow-hidden" style={{ background: S.paper, color: S.ink }}>
      <div className="absolute inset-y-0 left-0 w-[0.5cqw]" style={{ background: S.lime }} />
      <div className="slide-grid pointer-events-none absolute inset-0 opacity-60" />

      <div className="relative grid h-full grid-cols-[1.12fr_0.88fr] gap-[4.5cqw] px-[5.6cqw] py-[4.6cqh]">
        <div className="flex min-h-0 flex-col">
          <div className="flex items-center gap-[1.4cqw]">
            <SlideMark size="7.2cqh" />
            <div>
              <p className="font-mono text-[2.1cqh] font-bold uppercase tracking-[0.18em]" style={{ color: S.deep }}>
                Energy Observatory
              </p>
              <p className="mt-[0.3cqh] font-mono text-[1.9cqh] uppercase tracking-[0.14em]" style={{ color: S.muted }}>
                G2 / Retrieval depth
              </p>
            </div>
          </div>

          <div className="mt-auto">
            <p className="font-mono text-[2.05cqh] font-bold uppercase tracking-[0.14em]" style={{ color: S.teal }}>
              Public scaffold v0.1.0 · Post-pilot MARGINAL
            </p>
            <h1
              className="mt-[1.6cqh] max-w-[58cqw] text-[7.8cqh] font-semibold leading-[0.97] tracking-[-0.03em]"
              style={{ fontFamily: "var(--font-serif)", color: S.ink }}
            >
              What does a correct answer{" "}
              <span style={{ fontStyle: "italic", color: S.teal, borderBottom: `0.22cqw solid ${S.lime}` }}>
                cost?
              </span>
            </h1>
            <p className="mt-[2.2cqh] max-w-[52cqw] text-[2.85cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
              Retrieval depth in retrieval-augmented generation, measured in joules per correct
              answer.
            </p>
            <div className="mt-[2.2cqh] flex flex-wrap gap-[0.8cqw]">
              <SlideChip tone="amber">Pilot n = {pilot.questions}</SlideChip>
              <SlideChip tone="rose">No confirmatory results</SlideChip>
              <SlideChip tone="deep">Prereg not frozen</SlideChip>
            </div>
          </div>

          <div
            className="mt-[3cqh] flex items-center justify-between border-t pt-[1.1cqh] font-mono text-[1.9cqh] uppercase tracking-[0.1em]"
            style={{ borderColor: S.line, color: S.muted }}
          >
            <span>Energy-Optimal Retrieval Depth</span>
            <span className="tnum">{String(index + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}</span>
          </div>
        </div>

        <div className="flex min-h-0 items-center">
          <div className="w-full border-2 p-[2.4cqw]" style={{ borderColor: S.deep, background: S.deep }}>
            <div className="flex items-center justify-between">
              <p className="font-mono text-[1.95cqh] font-bold uppercase tracking-[0.16em]" style={{ color: S.lime }}>
                Pilot readout
              </p>
              <span className="h-[1.3cqh] w-[1.3cqh] rounded-full" style={{ background: S.lime }} />
            </div>
            <div className="mt-[3.2cqh] flex h-[25cqh] items-end justify-around gap-[2cqw]">
              {[
                { k: 1, value: pilot.energy.e1, color: S.lime },
                { k: 4, value: pilot.energy.e4, color: S.amber },
                { k: 32, value: pilot.energy.e32, color: S.teal },
              ].map((bar) => (
                <div key={bar.k} className="flex h-full w-1/3 flex-col items-center justify-end">
                  <span className="mb-[0.5cqh] font-mono text-[1.95cqh] font-bold tnum" style={{ color: S.white }}>
                    {bar.value.toFixed(1)}
                  </span>
                  <div
                    style={{
                      width: "62%",
                      height: `${Math.max(2, (bar.value / 160) * 82)}%`,
                      background: bar.color,
                    }}
                  />
                  <span className="mt-[0.6cqh] font-mono text-[1.85cqh]" style={{ color: "#b8c7b8" }}>
                    k = {bar.k}
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-[2.4cqh] font-mono text-[5.2cqh] font-semibold leading-none tracking-[-0.05em]" style={{ color: S.lime }}>
              {pilot.energy.span.toFixed(2)}×
            </p>
            <p className="mt-[0.7cqh] text-[2.15cqh] font-semibold" style={{ color: "#c9d6c9" }}>
              E(32) / E(1) · joules per correct answer
            </p>
            <div className="mt-[2.2cqh] flex justify-between border-t pt-[1.1cqh] font-mono text-[1.8cqh] uppercase tracking-[0.08em]" style={{ borderColor: "rgba(200,240,79,0.2)", color: "#a9baa9" }}>
              <span>{pilot.generations.toLocaleString("en-US")} generations</span>
              <span>R² {pilot.fit.r2.toFixed(4)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* 2 · The decision                                                    */
/* ------------------------------------------------------------------ */

function DecisionSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="The decision"
      badgeTone="rose"
      pilot
      title="The pilot killed its own headline."
      subtitle="The original target was a static 2 pp optimum. The data selected the grid boundary. The surviving object is a decision problem around the accuracy margin."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-3 gap-[1.5cqw]">
        <SlideCard title="2 pp · static" tone="rose" icon={<XCircle size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <p className="font-mono text-[6.8cqh] font-bold leading-none" style={{ color: S.rose }}>
              DEAD
            </p>
            <p className="mt-[1.6cqh] text-[2.6cqh] font-bold">k* = {pilot.static2pp.kStar}, the grid boundary</p>
            <p className="mt-[0.8cqh] font-mono text-[2.15cqh] leading-relaxed" style={{ color: S.inkSoft }}>
              P(k* optimal) = {pilot.static2pp.pOptimal.toFixed(2)}, below the {pilot.static2pp.threshold} gate.
            </p>
            <p className="mt-[1.1cqh] border-t pt-[0.8cqh] text-[1.95cqh] leading-snug" style={{ color: S.muted, borderColor: S.line }}>
              MDE at n = {pilot.questions}: roughly {pilot.mdeAt200}. A power failure, not a flat curve.
            </p>
          </div>
        </SlideCard>

        <SlideCard title="5 pp · policy" tone="amber" icon={<Target size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <p className="font-mono text-[5.8cqh] font-semibold leading-none" style={{ color: S.amber }}>
              k = {pilot.fivePp.k}
            </p>
            <p className="mt-[1.2cqh] font-mono text-[2.9cqh] font-bold">{pilot.fivePp.savings}% savings</p>
            <p className="mt-[0.8cqh] text-[2.35cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
              Pilot signal, not certified.
            </p>
            <p className="mt-[1.1cqh] border-t pt-[0.8cqh] font-mono text-[1.95cqh] leading-snug" style={{ color: S.muted, borderColor: S.line }}>
              N* = {pilot.fivePp.nStar} · P reported = {pilot.fivePp.pReported}
            </p>
          </div>
        </SlideCard>

        <SlideCard title="Oracle · ceiling" tone="teal" icon={<BarChart3 size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <p className="font-mono text-[5.8cqh] font-semibold leading-none" style={{ color: S.teal }}>
              {pilot.oracle.gain}%
            </p>
            <p className="mt-[1.2cqh] text-[2.5cqh] font-bold leading-snug">
              Matched-accuracy gain, with hindsight.
            </p>
            <p className="mt-[0.8cqh] text-[2.25cqh] font-semibold" style={{ color: S.inkSoft }}>
              Upper bound only. No learned policy exists.
            </p>
            <p className="mt-[1.1cqh] border-t pt-[0.8cqh] text-[1.95cqh] leading-snug" style={{ color: S.muted, borderColor: S.line }}>
              G4 requires a policy to capture ≥50% of a ≥20% oracle gap.
            </p>
          </div>
        </SlideCard>
      </div>

      <div className="mt-[1.5cqh]">
        <SlideCallout tone="deep">
          The question is now margin-indexed: how much accuracy will you trade for how many joules?
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 3 · Pilot setup                                                     */
/* ------------------------------------------------------------------ */

function PilotSetupSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Pilot setup"
      badgeTone="amber"
      pilot
      title="200 questions. Seven depths. One laptop."
      subtitle="SQuAD v1.1 dev · qwen3.5:4b Q4 · BM25 top-32 over 45,651 passages."
      index={index}
      total={total}
    >
      <SlideKpiRow
        items={[
          { value: String(pilot.questions), label: "SQuAD questions", sub: "v1.1 dev", tone: "deep" },
          { value: String(pilot.depths.length), label: "depths", sub: pilot.depths.join(","), tone: "deep" },
          { value: pilot.generations.toLocaleString("en-US"), label: "generations", sub: `${pilot.questions} × ${pilot.depths.length}`, tone: "deep" },
          { value: "6 GB", label: "GPU memory", sub: pilot.gpu, tone: "deep" },
        ]}
      />

      <div className="mt-[2cqh] grid min-h-0 flex-1 grid-cols-3 gap-[1.6cqw]">
        <SlideCard title="Data" tone="teal" icon={<Database size="2.2cqh" />}>
          <SlideBullets
            tone="teal"
            items={[
              "SQuAD v1.1 dev.",
              `${pilot.contexts.toLocaleString("en-US")} contexts → ${pilot.passages.toLocaleString("en-US")} ${pilot.chunkWords}-word passages.`,
              `${pilot.retriever}. No dense retriever.`,
            ]}
          />
        </SlideCard>
        <SlideCard title="Reader" tone="deep" icon={<Cpu size="2.2cqh" />}>
          <SlideBullets
            tone="deep"
            items={[
              `${pilot.reader}, ${pilot.quantization}, ${pilot.readerContext}.`,
              "Greedy decoding, 24 new tokens.",
              "One model; no frontier reader.",
            ]}
          />
        </SlideCard>
        <SlideCard title="Rig" tone="amber" icon={<Gauge size="2.2cqh" />}>
          <SlideBullets
            tone="amber"
            items={[
              `${pilot.gpu}.`,
              "Batch size 1, no concurrent jobs.",
              "AC power, screen off, thermal log on.",
            ]}
          />
        </SlideCard>
      </div>

      <div className="mt-[1.5cqh]">
        <SlideCallout tone="amber">
          Pilot only. The confirmatory sample is separate, and no confirmatory run has been executed.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 4 · Energy curve                                                    */
/* ------------------------------------------------------------------ */

function EnergyCurveSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Pilot evidence"
      badgeTone="teal"
      pilot
      title="Energy per correct answer rises 3.45×."
      subtitle={`E(32) = ${pilot.energy.e32} vs E(1) = ${pilot.energy.e1} J/correct. The affine fit is ${pilot.fit.formula} J, R² = ${pilot.fit.r2.toFixed(4)}.`}
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-[1.1fr_0.9fr] gap-[2cqw]">
        <SlideCard title="Joules per correct answer" tone="teal" icon={<BarChart3 size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <SlideBars
              items={[
                { label: "k = 1", value: pilot.energy.e1, display: pilot.energy.e1.toFixed(1), tone: "deep" },
                { label: "k = 4", value: pilot.energy.e4, display: pilot.energy.e4.toFixed(1), tone: "amber" },
                { label: "k = 32", value: pilot.energy.e32, display: pilot.energy.e32.toFixed(1), tone: "teal" },
              ]}
              max={160}
              height="34cqh"
            />
            <p className="mt-[1.4cqh] text-center font-mono text-[2.0cqh]" style={{ color: S.muted }}>
              Three documented E(k) points; all seven depths were measured.
            </p>
          </div>
        </SlideCard>

        <div className="flex min-h-0 flex-col gap-[1.4cqh]">
          <SlideFormula tone="deep">{pilot.fit.formula} J</SlideFormula>
          <div className="grid flex-1 grid-cols-2 gap-[1.2cqh]">
            {[
              ["a", `${pilot.fit.a} J`, "fixed cost"],
              ["b", `${pilot.fit.b} J`, "per passage"],
              ["R²", pilot.fit.r2.toFixed(4), "affine fit"],
              ["span", `${pilot.energy.span.toFixed(2)}×`, "E(32) / E(1)"],
            ].map(([label, value, note]) => (
              <div key={label} className="flex flex-col justify-center border px-[1.2cqw] py-[1cqh]" style={{ borderColor: S.line, background: S.alt }}>
                <p className="font-mono text-[1.9cqh] uppercase tracking-[0.1em]" style={{ color: S.muted }}>{label}</p>
                <p className="mt-[0.4cqh] font-mono text-[3.0cqh] font-bold tnum" style={{ color: S.ink }}>{value}</p>
                <p className="mt-[0.2cqh] text-[1.95cqh]" style={{ color: S.inkSoft }}>{note}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-[1.5cqh]">
        <SlideCallout tone="teal">
          Steep and precise under pilot conditions. This is not a universal law or an identified optimum.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 5 · Accuracy and the dead 2 pp claim                                */
/* ------------------------------------------------------------------ */

function AccuracyDeadSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="The dead claim"
      badgeTone="rose"
      pilot
      title="Accuracy plateaus. The 2 pp gate runs to the boundary."
      subtitle={`A_EM ${pilot.accuracy.a1.toFixed(3)} → ${pilot.accuracy.a32.toFixed(3)}; flat ${pilot.accuracy.plateauLow.toFixed(3)}–${pilot.accuracy.plateauHigh.toFixed(3)} at k = ${pilot.accuracy.plateauFrom}–${pilot.accuracy.plateauTo}. The accuracy side was underpowered at n = ${pilot.questions}.`}
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-[1.1fr_0.9fr] gap-[2cqw]">
        <SlideCard title="A_EM, documented points" tone="deep" icon={<BarChart3 size="2.2cqh" />} fill={S.paper}>
          <div className="flex h-full flex-col justify-center">
            <AccuracyPlot />
            <p className="mt-[1.2cqh] text-center font-mono text-[1.9cqh]" style={{ color: S.muted }}>
              No connecting line: intermediate accuracy values are not reported in the source.
            </p>
          </div>
        </SlideCard>

        <SlideCard title="Static 2 pp claim" tone="rose" icon={<XCircle size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <p className="font-mono text-[6.2cqh] font-bold leading-none" style={{ color: S.rose }}>
              DEAD
            </p>
            <p className="mt-[1.4cqh] font-mono text-[2.8cqh] font-bold">k* = {pilot.static2pp.kStar} · P = {pilot.static2pp.pOptimal.toFixed(2)}</p>
            <p className="mt-[0.6cqh] text-[2.3cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
              Below the {pilot.static2pp.threshold} selection gate. A power failure, not a flat-curve failure.
            </p>
            <div className="mt-[1.2cqh] border-t pt-[0.9cqh]" style={{ borderColor: S.line }}>
              <p className="font-mono text-[2.0cqh]" style={{ color: S.inkSoft }}>
                MDE at n = {pilot.questions}: roughly {pilot.mdeAt200}.
              </p>
              <p className="mt-[0.3cqh] font-mono text-[2.0cqh]" style={{ color: S.inkSoft }}>
                The k = 16 interval includes the 2 pp floor.
              </p>
            </div>
          </div>
        </SlideCard>
      </div>

      <div className="mt-[1.5cqh]">
        <SlideCallout tone="rose">
          2 pp is estimation-only in the rerun. It is not a certification target, and the dead claim is not resurrected.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 6 · What survives                                                   */
/* ------------------------------------------------------------------ */

function SurvivesSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="What survives"
      badgeTone="teal"
      pilot
      title="Six measurements survive. One claim does not."
      subtitle="The pilot is a precise energy measurement and a failed accuracy certification. Both belong in the record."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.6cqw]">
        <SlideCard title="Survived" tone="teal" icon={<CheckCircle2 size="2.2cqh" />}>
          <SlideBullets
            tone="teal"
            items={[
              <><strong>{pilot.energy.span.toFixed(2)}×</strong> energy span, E(32) vs E(1).</>,
              <><strong>R² = {pilot.fit.r2.toFixed(4)}</strong> affine energy fit.</>,
              <><strong>{pilot.accuracy.plateauLow.toFixed(3)}–{pilot.accuracy.plateauHigh.toFixed(3)}</strong> accuracy plateau at k = {pilot.accuracy.plateauFrom}–{pilot.accuracy.plateauTo}.</>,
              <><strong>{pilot.contextShare.at2}% → {pilot.contextShare.at32}%</strong> context-side share.</>,
              <><strong>+{pilot.identity.at2.gap.toFixed(3)}</strong> identity gap at k = 2; CI includes zero.</>,
              <><strong>{pilot.repeatCv.median.toFixed(2)}%</strong> median repeat CV at k = {pilot.repeatCv.k}.</>,
            ]}
          />
        </SlideCard>

        <SlideCard title="Did not / bounded" tone="rose" icon={<AlertTriangle size="2.2cqh" />}>
          <SlideBullets
            tone="rose"
            items={[
              <><strong>2 pp static optimum: DEAD.</strong> k* = {pilot.static2pp.kStar} boundary, P = {pilot.static2pp.pOptimal.toFixed(2)}.</>,
              <><strong>Identity at k = 32: rejected.</strong> Gap +{pilot.identity.at32.gap.toFixed(3)} flags over-retrieval.</>,
              <><strong>5 pp at k = {pilot.fivePp.k}: pilot signal.</strong> {pilot.fivePp.savings}% savings, not certified.</>,
              <><strong>Oracle: upper bound.</strong> {pilot.oracle.gain}% with hindsight, no learned policy.</>,
            ]}
          />
        </SlideCard>
      </div>

      <div className="mt-[1.5cqh]">
        <SlideCallout tone="deep">
          The surviving object is the decision problem around the accuracy margin, not a universal depth.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 7 · The 5 pp signal                                                 */
/* ------------------------------------------------------------------ */

function FivePpSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="The 5 pp signal"
      badgeTone="amber"
      pilot
      title="At 5 pp, the pilot chose k = 4."
      subtitle="Pilot signal, not certified. The powered rerun decides whether the policy claim survives."
      index={index}
      total={total}
    >
      <SlideKpiRow
        items={[
          { value: `k = ${pilot.fivePp.k}`, label: "selected depth", sub: "interior candidate", tone: "amber" },
          { value: `${pilot.fivePp.savings}%`, label: "energy savings", sub: "vs k = 32", tone: "amber" },
          { value: String(pilot.fivePp.nStar), label: "N*", sub: "descriptive break-even", tone: "deep" },
          { value: pilot.fivePp.pReported.toFixed(3).replace(/^0/, ""), label: "P reported", sub: "proposal value", tone: "deep" },
        ]}
      />

      <div className="mt-[2cqh] grid min-h-0 flex-1 grid-cols-2 gap-[1.6cqw]">
        <SlideCard title="What N* means" tone="deep" icon={<Timer size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <SlideFormula tone="deep">N* = C_cert / [A(k*)(E(k₀) − E(k*))]</SlideFormula>
            <p className="mt-[1.2cqh] text-[2.35cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
              The pilot sweep cost {pilot.sweepKj} kJ. N* = {pilot.fivePp.nStar} at k = {pilot.fivePp.k} is the query count at which the saving
              repays the sweep. It is not a deployment guarantee.
            </p>
            <p className="mt-[0.8cqh] font-mono text-[2.0cqh]" style={{ color: S.muted }}>
              {pilot.savingsAt.queries.toLocaleString("en-US")} queries: {pilot.savingsAt.kj} kJ saved; calibration is {pilot.savingsAt.calibrationShareOfSavingPct}% of the saving. At 100,000: {pilot.calibrationShareAt100kPct}%.
            </p>
          </div>
        </SlideCard>

        <SlideCard title="Why it is not certified" tone="rose" icon={<XCircle size="2.2cqh" />}>
          <SlideBullets
            tone="rose"
            items={[
              `Pilot n = ${pilot.questions}; the rerun is n = ${rerun.primary.n.toLocaleString("en-US")}.`,
              `P = ${pilot.fivePp.pReported} is the proposal's 5 pp selection value; no pilot NI test is reported.`,
              "The rerun must report the NI test and selection probability separately.",
              "No “certified” language before the freeze and the powered rerun.",
            ]}
          />
        </SlideCard>
      </div>

      <div className="mt-[1.5cqh]">
        <SlideCallout tone="amber">
          The pilot picked a candidate. It did not certify one.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 8 · Powered rerun                                                   */
/* ------------------------------------------------------------------ */

function RerunSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="The rerun"
      badgeTone="deep"
      title="Sized around the failure."
      subtitle={`The pilot's MDE was roughly ${pilot.mdeAt200} at n = ${pilot.questions}. The rerun is powered for a 5 pp decision.`}
      index={index}
      total={total}
    >
      <SlideKpiRow
        items={[
          { value: `${rerun.primary.n.toLocaleString("en-US")} × ${rerun.primary.depths.length}`, label: "SQuAD primary", sub: "n × depths", tone: "deep" },
          { value: String(rerun.replication.n), label: "1.5B replication", sub: rerun.replication.reader, tone: "teal" },
          { value: String(rerun.hotpot.n), label: "HotpotQA", sub: "distractor, k ≤ 10", tone: "amber" },
          { value: String(rerun.boundary.n), label: "boundary probe", sub: "k = 32, 48, 64", tone: "rose" },
        ]}
      />

      <div className="mt-[2cqh] grid min-h-0 flex-1 grid-cols-[1.05fr_0.95fr] gap-[1.8cqw]">
        <div className="flex flex-col justify-between border-2 p-[1.8cqw]" style={{ borderColor: S.deep, background: S.deep, color: S.white }}>
          <div>
            <p className="font-mono text-[1.95cqh] uppercase tracking-[0.14em]" style={{ color: S.lime }}>
              Primary decision / P1
            </p>
            <p className="mt-[1.4cqh] font-mono text-[3.9cqh] font-semibold tracking-[-0.03em]">
              k = {rerun.primary.candidateK} <span style={{ color: "#9fb09f" }}>vs</span> k = {rerun.primary.referenceK}
            </p>
            <p className="mt-[0.8cqh] text-[2.5cqh] font-bold">5 pp EM non-inferiority · one-sided α = .05</p>
            <p className="mt-[0.4cqh] text-[2.25cqh]" style={{ color: "#c9d6c9" }}>
              ≥ {rerun.primary.minSavingsPct}% savings required. {rerun.primary.secondaryMarginPp} pp is estimation-only.
            </p>
          </div>
          <div className="mt-[1.4cqh] grid grid-cols-3 gap-[1cqw] border-t pt-[1.1cqh]" style={{ borderColor: "rgba(200,240,79,0.2)" }}>
            {[
              ["MDE", rerun.power.mdeAt1000],
              ["SE", rerun.power.seAt1000],
              ["95% half-width", rerun.power.halfWidthAt1000],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="font-mono text-[1.75cqh] uppercase tracking-[0.08em]" style={{ color: "#a9baa9" }}>{label}</p>
                <p className="mt-[0.2cqh] font-mono text-[2.4cqh] font-bold" style={{ color: S.white }}>{value}</p>
              </div>
            ))}
          </div>
          <p className="mt-[1.2cqh] font-mono text-[1.8cqh] leading-relaxed" style={{ color: "#a9baa9" }}>
            Planning values, not results. Pilot-derived MDE at n = {pilot.questions}: {pilot.mdeAt200}.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-[1.2cqw]">
          {[
            { icon: Database, title: "Distractor", body: "10 paragraphs per question; no pooling." },
            { icon: ScanLine, title: "Boundary", body: "16k-token context check; diagnostic, not powered." },
            { icon: PlugZap, title: "Taxes", body: "150 questions per condition; fixed and per-passage." },
            { icon: GitBranch, title: "Policy", body: "600 / 200 / 200; test touched once." },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.title} className="border-2 p-[1.2cqw]" style={{ borderColor: S.line, background: S.alt }}>
                <Icon size="2.4cqh" style={{ color: S.teal }} aria-hidden="true" />
                <p className="mt-[0.8cqh] text-[2.4cqh] font-bold">{item.title}</p>
                <p className="mt-[0.4cqh] text-[2.05cqh] leading-snug" style={{ color: S.inkSoft }}>{item.body}</p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-[1.5cqh]">
        <SlideCallout tone="deep">
          No confirmatory result exists yet. This is the design, with the gates to be frozen before the data.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 9 · Measurement                                                     */
/* ------------------------------------------------------------------ */

function MeasurementSlide({ index, total }: SlideProps) {
  const blockMin = Math.min(...pilot.blockFactors.map((item) => item.factor)).toFixed(3);
  const blockMax = Math.max(...pilot.blockFactors.map((item) => item.factor)).toFixed(3);

  return (
    <SlideFrame
      badge="Measurement"
      badgeTone="amber"
      pilot
      title="A joule is attributed, not guessed."
      subtitle="GPU energy is the primary measurement. CPU retrieval is a time-to-joules proxy. The wall meter is a cross-check."
      index={index}
      total={total}
    >
      <SlideFormula tone="deep">
        J_k(q) = J_ret + J_pre + J_dec + J_fix
      </SlideFormula>

      <div className="mt-[1.4cqh] grid grid-cols-4 gap-[1.2cqw]">
        {[
          ["J_ret", "BM25 + fetch", "CPU proxy · 20 W"],
          ["J_pre", "Prefill", "NVML · dominant at high k"],
          ["J_dec", "Decode", "NVML"],
          ["J_fix", "Fixed", "Partly amortized"],
        ].map(([symbol, label, note]) => (
          <div key={symbol} className="border px-[1cqw] py-[0.9cqh]" style={{ borderColor: S.line, background: S.paper }}>
            <p className="font-mono text-[2.4cqh] font-bold" style={{ color: S.teal }}>{symbol}</p>
            <p className="mt-[0.3cqh] text-[2.15cqh] font-bold">{label}</p>
            <p className="mt-[0.2cqh] text-[1.9cqh]" style={{ color: S.muted }}>{note}</p>
          </div>
        ))}
      </div>

      <div className="mt-[1.4cqh] grid min-h-0 flex-1 grid-cols-3 gap-[1.2cqw]">
        {[
          { icon: Activity, value: measurement.sensor.cadence, title: "NVML cadence", note: "Coarse driver update, about 1 Hz. Not 100 ms of independent information." },
          { icon: Zap, value: `${pilot.idle.preW} W`, title: "Idle baseline", note: `60 s pre-run, CV ${pilot.idle.preCv}%. Post-run ${pilot.idle.postW} W changes E ratios by under 1%.` },
          { icon: Gauge, value: "20 queries", title: "Block calibration", note: `Pilot factors ${blockMin}–${blockMax}; largest correction at k = 2.` },
          { icon: ShieldCheck, value: "10-hex", title: "Nonce control", note: `Prefix reuse cut prefill from ${pilot.nonce.prefillWithMs} ms to ${pilot.nonce.prefillWithoutMs} ms. Every request gets a fresh nonce.` },
          { icon: Thermometer, value: `${pilot.thermal.tempStartC} → ${pilot.thermal.tempEndC} °C`, title: "Thermal log", note: `Clock ${pilot.thermal.clockStartMhz} → ${pilot.thermal.clockEndMhz} MHz; power ${pilot.thermal.powerStartW} → ${pilot.thermal.powerEndW} W. Energy stayed stable.` },
          { icon: Timer, value: `${pilot.repeatCv.median.toFixed(2)}%`, title: "Repeat CV", note: `Median at k = ${pilot.repeatCv.k}; max ${pilot.repeatCv.max}%. Three blocks of 20 identical queries.` },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.title} className="flex flex-col border p-[1.2cqw]" style={{ borderColor: S.line, background: S.alt }}>
              <Icon size="2.2cqh" style={{ color: S.amber }} aria-hidden="true" />
              <p className="mt-[0.7cqh] font-mono text-[2.8cqh] font-bold tnum" style={{ color: S.ink }}>{item.value}</p>
              <p className="mt-[0.2cqh] text-[2.1cqh] font-bold">{item.title}</p>
              <p className="mt-[0.3cqh] text-[1.9cqh] leading-snug" style={{ color: S.inkSoft }}>{item.note}</p>
            </div>
          );
        })}
      </div>

      <div className="mt-[1.4cqh]">
        <SlideCallout tone="amber">
          Absolute joules are conditional on block calibration and the repeat CV. Per-query energy is a paired observation.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 10 · Data                                                           */
/* ------------------------------------------------------------------ */

function DataSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Data"
      badgeTone="teal"
      title="Two corpora, one depth question."
      subtitle="SQuAD isolates the depth effect inside a closed corpus. HotpotQA stresses multi-hop evidence and distractor-induced non-monotonicity."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.6cqw]">
        <SlideCard title="SQuAD v1.1 dev · primary" tone="teal" icon={<Database size="2.2cqh" />}>
          <SlideTable
            head={["Field", "Value"]}
            rows={[
              ["Upstream", `${datasets.squad.upstreamQuestions.toLocaleString("en-US")} questions · ${datasets.squad.upstreamContexts.toLocaleString("en-US")} contexts`],
              ["Corpus", `${pilot.passages.toLocaleString("en-US")} ${pilot.chunkWords}-word passages`],
              ["Used", `${datasets.squad.usedPrimary.toLocaleString("en-US")} primary · ${datasets.squad.usedReplication} replication · ${datasets.squad.usedBoundary} boundary`],
              ["Retriever", datasets.squad.retriever],
              ["Metric", datasets.squad.primaryMetric],
            ]}
            tone="teal"
            widths={["26%", "74%"]}
            compact
          />
          <p className="mt-[1.1cqh] text-[1.95cqh] leading-snug" style={{ color: S.inkSoft }}>
            Closed corpus: every question searches the same fixed collection. That isolates depth
            and limits external validity.
          </p>
        </SlideCard>

        <SlideCard title="HotpotQA · distractor" tone="amber" icon={<Layers size="2.2cqh" />}>
          <SlideTable
            head={["Field", "Value"]}
            rows={[
              ["Upstream", `${datasets.hotpot.upstreamQuestions.toLocaleString("en-US")} questions`],
              ["Used", `${datasets.hotpot.used} questions`],
              ["Corpus", `${datasets.hotpot.paragraphs} paragraphs: ${datasets.hotpot.goldParagraphs} gold + ${datasets.hotpot.distractors} distractors`],
              ["Depths", `${datasets.hotpot.depths.join(",")}; ${datasets.hotpot.retriever}`],
              ["Constraint", "No pooling across questions"],
            ]}
            tone="amber"
            widths={["26%", "74%"]}
            compact
          />
          <p className="mt-[1.1cqh] text-[1.95cqh] leading-snug" style={{ color: S.inkSoft }}>
            Per-question corpus; pooling paragraphs across questions would change the task.
          </p>
        </SlideCard>
      </div>

      <div className="mt-[1.6cqh] grid grid-cols-3 gap-[1.2cqw]">
        <div className="border-l-[0.35cqw] px-[1.2cqw] py-[0.9cqh]" style={{ borderColor: S.teal, background: S.tealSoft }}>
          <p className="font-mono text-[2.6cqh] font-bold" style={{ color: S.teal }}>
            {pilot.recall.goldContext[pilot.recall.goldContext.length - 1].toFixed(1)}%
          </p>
          <p className="mt-[0.2cqh] text-[1.95cqh] font-semibold">Pilot gold-context recall at k = 32</p>
          <p className="mt-[0.2cqh] font-mono text-[1.75cqh]" style={{ color: S.muted }}>Pilot recall</p>
        </div>
        <div className="border-l-[0.35cqw] px-[1.2cqw] py-[0.9cqh]" style={{ borderColor: S.amber, background: S.amberSoft }}>
          <p className="font-mono text-[2.6cqh] font-bold" style={{ color: S.amber }}>~{datasets.squad.goldOutsideCapPct}%</p>
          <p className="mt-[0.2cqh] text-[1.95cqh] font-semibold">Gold evidence outside the top-32 cap</p>
          <p className="mt-[0.2cqh] font-mono text-[1.75cqh]" style={{ color: S.muted }}>Pilot recall ceiling</p>
        </div>
        <div className="border-l-[0.35cqw] px-[1.2cqw] py-[0.9cqh]" style={{ borderColor: S.rose, background: S.roseSoft }}>
          <p className="font-mono text-[2.6cqh] font-bold" style={{ color: S.rose }}>CC BY-SA 4.0</p>
          <p className="mt-[0.2cqh] text-[1.95cqh] font-semibold">No raw question or context text is redistributed</p>
          <p className="mt-[0.2cqh] font-mono text-[1.75cqh]" style={{ color: S.muted }}>Both datasets</p>
        </div>
      </div>

      <div className="mt-[1.4cqh]">
        <SlideCallout tone="deep">
          One closed corpus, one distractor set, BM25 only, English only. External validity is bounded by design.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 11 · Theory                                                         */
/* ------------------------------------------------------------------ */

function TheorySlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Theory"
      badgeTone="deep"
      pilot
      title="Small theory, falsifiable."
      subtitle="Three results and one counterexample. The identity is local, not a global law of retrieval."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-3 grid-rows-[1fr_auto] gap-[1.5cqw]">
        <SlideCard title="Identity" tone="teal" icon={<Scale size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <SlideFormula tone="teal">{theory.theorems[0].formula}</SlideFormula>
            <p className="mt-[1.1cqh] text-[2.2cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
              At an interior optimum, energy and accuracy elasticities are equal. A local, scale-free
              diagnostic.
            </p>
            <p className="mt-[1cqh] font-mono text-[2.0cqh] font-bold" style={{ color: S.teal }}>
              k = 2: +{pilot.identity.at2.gap.toFixed(3)} · CI [{pilot.identity.at2.ci[0].toFixed(3)}, +{pilot.identity.at2.ci[1].toFixed(3)}]
            </p>
            <p className="mt-[0.3cqh] font-mono text-[2.0cqh]" style={{ color: S.rose }}>
              k = 32: +{pilot.identity.at32.gap.toFixed(3)} → over-retrieval
            </p>
          </div>
        </SlideCard>

        <SlideCard title="Price of static depth" tone="amber" icon={<BarChart3 size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <SlideFormula tone="amber">{theory.theorems[1].formula}</SlideFormula>
            <p className="mt-[1.1cqh] text-[2.2cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
              For any static depth there is a query mixture on which it is arbitrarily worse at equal
              accuracy. An impossibility result, not a policy claim.
            </p>
          </div>
        </SlideCard>

        <SlideCard title="Certification" tone="deep" icon={<Timer size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <SlideFormula tone="deep">{theory.theorems[2].formula}</SlideFormula>
            <p className="mt-[1.1cqh] text-[2.2cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
              Finding the depth is itself an energy purchase. The pilot sweep cost {pilot.sweepKj} kJ; N* = {pilot.fivePp.nStar}
              at k = {pilot.fivePp.k}.
            </p>
          </div>
        </SlideCard>

        <div className="col-span-3">
          <SlideCard title="Distractor counterexample" tone="rose" icon={<AlertTriangle size="2.2cqh" />}>
            <div className="grid grid-cols-[1.25fr_1fr_1.1fr] items-center gap-[1.4cqw]">
              <p className="font-mono text-[2.0cqh] leading-snug" style={{ color: S.inkSoft }}>
                {theory.counterexample.setup}
              </p>
              <p className="font-mono text-[2.0cqh] leading-snug" style={{ color: S.ink }}>
                {theory.counterexample.energies}
              </p>
              <p className="text-[2.0cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
                A local minimum at k = 1 and a lower global minimum at k = 4. A greedy policy misses 4.
              </p>
            </div>
          </SlideCard>
        </div>
      </div>

      <div className="mt-[1.5cqh]">
        <SlideCallout tone="rose">
          Coverage fit: A₀ = {theory.coverageFit.a0}, p = {theory.coverageFit.p}, R² = {theory.coverageFit.r2}. Global unimodality is rejected.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 12 · Gates                                                          */
/* ------------------------------------------------------------------ */

function GatesSlide({ index, total }: SlideProps) {
  const killRows = gates.kill.map((gate) => [
    <span key="id" className="font-mono font-bold" style={{ color: S.deep }}>{gate.id}</span>,
    gate.criterion,
    <Status key="status" pass={gate.status === "pass"} />,
  ]);

  return (
    <SlideFrame
      badge="Gates"
      badgeTone="rose"
      pilot
      title="Gates are allowed to fire."
      subtitle="Pilot adjudication: four pass, three fail. The rerun re-adjudicates each once, on the pre-specified population."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-[1.2fr_0.8fr] items-center gap-[1.6cqw]">
        <div className="min-h-0">
          <SlideTable
            head={["Gate", "Criterion", "Pilot"]}
            rows={killRows}
            tone="rose"
            widths={["9%", "72%", "19%"]}
            compact
          />
          <p className="mt-[0.8cqh] font-mono text-[1.9cqh]" style={{ color: S.muted }}>
            K1–K4 and K6 firing is a kill/reframe. K5 and K7 are fixable before they are kills.
          </p>
        </div>

        <SlideCard title="Go gates · planned" tone="deep" icon={<ShieldCheck size="2.2cqh" />}>
          <SlideBullets
            tone="deep"
            size="1.8cqh"
            items={[
              <><strong>G1</strong> 5 pp NI at interior k, ≥ 20% savings.</>,
              <><strong>G2</strong> upper CI loss ≤ 5 pp, P(k*) ≥ 0.8.</>,
              <><strong>G3</strong> context share in [0.10, 0.70], varies with k.</>,
              <><strong>G4</strong> oracle ≥ 20%, policy captures ≥ 50%.</>,
              <><strong>G5</strong> replication on 1.5B or HotpotQA.</>,
            ]}
          />
        </SlideCard>
      </div>

      <div className="mt-[1.4cqh]">
        <SlideCallout tone="rose">
          A fired gate is reported, not tuned away. No gate is added, removed, or re-thresholded after the primary outcome.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 13 · Policy and taxes                                               */
/* ------------------------------------------------------------------ */

function PolicyTaxesSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Policy and causality"
      badgeTone="amber"
      title="Adaptivity is the ceiling. Taxes are the test."
      subtitle="The policy is a held-out experiment. The oracle is only its upper bound. The tax signs are a causal falsification test."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.6cqw]">
        <SlideCard title="Learned policy" tone="teal" icon={<GitBranch size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <p className="font-mono text-[3.9cqh] font-bold tracking-[-0.03em]" style={{ color: S.teal }}>
              {rerun.policy.train} / {rerun.policy.validation} / {rerun.policy.test}
            </p>
            <p className="mt-[0.4cqh] font-mono text-[1.95cqh]" style={{ color: S.muted }}>
              target counts · hashed question ID · realized counts reported
            </p>
            <div className="mt-[1.3cqh]">
              <SlideBullets
                tone="teal"
                size="1.75cqh"
                items={[
                  "Pre-generation features only: BM25 scores, gaps, entropy, question type, length.",
                  "Matched-accuracy evaluation against the best static k.",
                  "G4: oracle ≥ 20%; policy captures ≥ 50% on 200 held-out questions.",
                ]}
              />
            </div>
          </div>
        </SlideCard>

        <SlideCard title="Energy taxes" tone="amber" icon={<PlugZap size="2.2cqh" />}>
          <div className="flex h-full flex-col justify-center">
            <div className="grid grid-cols-2 gap-[1.1cqw]">
              <div className="flex flex-col justify-center border p-[1.2cqw]" style={{ borderColor: S.line, background: S.paper }}>
                <p className="font-mono text-[1.95cqh] uppercase tracking-[0.08em]" style={{ color: S.muted }}>Fixed Δa +20%</p>
                <p className="mt-[0.5cqh] font-mono text-[3.7cqh] font-bold" style={{ color: S.teal }}>k* ↑</p>
                <p className="mt-[0.4cqh] text-[1.95cqh] leading-snug" style={{ color: S.inkSoft }}>
                  {rerun.taxes.fixedJ} J before generation.
                </p>
              </div>
              <div className="flex flex-col justify-center border p-[1.2cqw]" style={{ borderColor: S.line, background: S.paper }}>
                <p className="font-mono text-[1.95cqh] uppercase tracking-[0.08em]" style={{ color: S.muted }}>Per-passage Δb +20%</p>
                <p className="mt-[0.5cqh] font-mono text-[3.7cqh] font-bold" style={{ color: S.rose }}>k* ↓</p>
                <p className="mt-[0.4cqh] text-[1.95cqh] leading-snug" style={{ color: S.inkSoft }}>
                  {rerun.taxes.perPassageJ} J per passage.
                </p>
              </div>
            </div>
            <p className="mt-[1.2cqh] font-mono text-[1.9cqh]" style={{ color: S.muted }}>
              {rerun.taxes.n} questions per condition · mid-accuracy gate · report gated and unconstrained optima.
            </p>
          </div>
        </SlideCard>
      </div>

      <div className="mt-[1.4cqh]">
        <SlideCallout tone="amber">
          {pilot.oracle.gain}% (pilot) is an oracle upper bound. No learned policy exists. A wrong tax sign falsifies the model.
        </SlideCallout>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 14 · Claim boundary                                                 */
/* ------------------------------------------------------------------ */

function BoundarySlide({ index, total }: SlideProps) {
  return (
    <SlideFrame
      badge="Claim boundary"
      badgeTone="rose"
      pilot
      title="What this project will not claim."
      subtitle="The boundary is part of the result. A fired gate is reported, not tuned away."
      index={index}
      total={total}
    >
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[1.6cqw]">
        <SlideCard title="Not claimed" tone="rose" icon={<XCircle size="2.2cqh" />}>
          <SlideBullets
            tone="rose"
            items={claimBoundary.notClaimed.slice(0, 6)}
          />
        </SlideCard>
        <SlideCard title="May be claimed now" tone="teal" icon={<CheckCircle2 size="2.2cqh" />}>
          <SlideBullets
            tone="teal"
            items={[
              "The energy-depth tradeoff is real and steep under pilot conditions.",
              "The affine model and context-side share are measurable in the pilot.",
              "The identity is a local diagnostic and flags over-retrieval.",
              "At 5 pp, k = 4 is non-inferior in the pilot and saves energy — pilot evidence, not certified.",
              "Query-conditional depth is promising; 78.8% is an oracle ceiling.",
            ]}
          />
        </SlideCard>
      </div>

      <div className="mt-[1.5cqh] border-l-[0.4cqw] px-[1.6cqw] py-[1.2cqh]" style={{ borderColor: S.lime, background: S.limeSoft }}>
        <p className="font-mono text-[1.9cqh] font-bold uppercase tracking-[0.12em]" style={{ color: S.deep }}>
          The defensible next claim — if the rerun supports it
        </p>
        <p className="mt-[0.6cqh] text-[2.6cqh] font-semibold leading-snug" style={{ color: S.ink, fontFamily: "var(--font-serif)" }}>
          “At a 5 pp EM non-inferiority margin, k = {pilot.fivePp.k} retains accuracy while saving roughly {pilot.fivePp.savings}% of
          GPU energy per correct answer relative to k = 32.”
        </p>
      </div>
    </SlideFrame>
  );
}

/* ------------------------------------------------------------------ */
/* 15 · Thank you                                                      */
/* ------------------------------------------------------------------ */

function ThanksSlide({ index, total }: SlideProps) {
  return (
    <div className="relative flex h-full w-full overflow-hidden" style={{ background: S.paper, color: S.ink }}>
      <div className="absolute inset-y-0 left-0 w-[0.5cqw]" style={{ background: S.lime }} />
      <div className="slide-grid pointer-events-none absolute inset-0 opacity-60" />

      <div className="relative grid h-full grid-cols-[1.12fr_0.88fr] gap-[4.5cqw] px-[5.6cqw] py-[4.6cqh]">
        <div className="flex min-h-0 flex-col">
          <div className="flex items-center gap-[1.4cqw]">
            <SlideMark size="7.2cqh" />
            <div>
              <p className="font-mono text-[2.1cqh] font-bold uppercase tracking-[0.18em]" style={{ color: S.deep }}>
                Energy Observatory
              </p>
              <p className="mt-[0.3cqh] font-mono text-[1.9cqh] uppercase tracking-[0.14em]" style={{ color: S.muted }}>
                G2 / Retrieval depth
              </p>
            </div>
          </div>

          <div className="mt-auto">
            <h1
              className="text-[8.8cqh] font-semibold leading-none tracking-[-0.035em]"
              style={{ fontFamily: "var(--font-serif)", color: S.ink }}
            >
              Thank you.
            </h1>
            <p className="mt-[2cqh] max-w-[50cqw] text-[2.9cqh] font-semibold leading-snug" style={{ color: S.inkSoft }}>
              The failure is in the record. The next claim is conditional on the powered rerun.
            </p>
            <div className="mt-[2.2cqh] flex flex-wrap gap-[0.8cqw]">
              <SlideChip tone="amber">Pilot n = {pilot.questions}</SlideChip>
              <SlideChip tone="rose">No confirmatory results</SlideChip>
              <SlideChip tone="deep">Prereg not frozen</SlideChip>
            </div>
            <div className="mt-[2.4cqh] flex flex-wrap gap-x-[2cqw] gap-y-[0.6cqh] font-mono text-[1.95cqh] font-bold uppercase tracking-[0.1em]" style={{ color: S.teal }}>
              <span>Repository: Atik203/energy-optimal-rag</span>
              <span>Site: /research · /results</span>
            </div>
          </div>

          <div
            className="mt-[3cqh] flex items-center justify-between border-t pt-[1.1cqh] font-mono text-[1.9cqh] uppercase tracking-[0.1em]"
            style={{ borderColor: S.line, color: S.muted }}
          >
            <span>Energy-Optimal Retrieval Depth</span>
            <span className="tnum">{String(index + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}</span>
          </div>
        </div>

        <div className="flex min-h-0 items-center">
          <div className="w-full border-2 p-[2.4cqw]" style={{ borderColor: S.deep, background: S.deep }}>
            <p className="font-mono text-[1.9cqh] font-bold uppercase tracking-[0.16em]" style={{ color: S.lime }}>
              The record
            </p>
            <div className="mt-[2.4cqh] space-y-[1.4cqh]">
              {[
                ["2 pp", "DEAD", "#fecaca"],
                ["5 pp", "PILOT SIGNAL", "#fde68a"],
                [`${pilot.oracle.gain}%`, "UPPER BOUND", "#99f6e4"],
              ].map(([label, status, color]) => (
                <div key={label} className="flex items-center justify-between border-b pb-[1.1cqh]" style={{ borderColor: "rgba(200,240,79,0.16)" }}>
                  <span className="font-mono text-[2.8cqh] font-bold" style={{ color: S.white }}>{label}</span>
                  <span className="font-mono text-[2.05cqh] font-bold uppercase tracking-[0.1em]" style={{ color }}>{status}</span>
                </div>
              ))}
            </div>
            <p className="mt-[2.2cqh] text-[2.1cqh] leading-snug" style={{ color: "#c9d6c9" }}>
              A fired gate is a finding. A dead claim stays in the results.
            </p>
            <div className="mt-[2.2cqh] flex items-center gap-[0.8cqw] border-t pt-[1.2cqh]" style={{ borderColor: "rgba(200,240,79,0.16)" }}>
              <Target size="2.1cqh" style={{ color: S.lime }} aria-hidden="true" />
              <span className="font-mono text-[1.85cqh] uppercase tracking-[0.1em]" style={{ color: "#a9baa9" }}>
                Joules per correct answer
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */

export const SLIDES: SlideDef[] = [
  { id: "title", title: "What does a correct answer cost?", Component: TitleSlide },
  { id: "decision", title: "The pilot killed its own headline", Component: DecisionSlide },
  { id: "pilot-setup", title: "200 questions, seven depths, one laptop", Component: PilotSetupSlide },
  { id: "energy", title: "Energy per correct answer rises 3.45 times", Component: EnergyCurveSlide },
  { id: "accuracy", title: "Accuracy plateaus and the 2 pp gate runs to the boundary", Component: AccuracyDeadSlide },
  { id: "survives", title: "Six measurements survive, one claim does not", Component: SurvivesSlide },
  { id: "five-pp", title: "At 5 pp the pilot chose k equals 4, a signal not a certificate", Component: FivePpSlide },
  { id: "rerun", title: "The powered rerun is sized around the failure", Component: RerunSlide },
  { id: "measurement", title: "A joule is attributed, not guessed", Component: MeasurementSlide },
  { id: "data", title: "Two corpora, one depth question", Component: DataSlide },
  { id: "theory", title: "Small theory, falsifiable", Component: TheorySlide },
  { id: "gates", title: "Gates are allowed to fire", Component: GatesSlide },
  { id: "policy-taxes", title: "Adaptivity is the ceiling, taxes are the test", Component: PolicyTaxesSlide },
  { id: "boundary", title: "What this project will not claim", Component: BoundarySlide },
  { id: "thanks", title: "Thank you", Component: ThanksSlide },
];
