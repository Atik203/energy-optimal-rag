import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { pilot } from "@/lib/project-data";

const LOG_MAX = Math.log2(33);

function xPct(k: number) {
  return (Math.log2(k + 1) / LOG_MAX) * 100;
}

function pct(value: number, min: number, max: number) {
  return ((value - min) / (max - min)) * 100;
}

function yPct(value: number, min: number, max: number) {
  return 100 - ((value - min) / (max - min)) * 100;
}

const INST = {
  fg: "#eef3e5",
  muted: "#8aa294",
  line: "rgba(200, 240, 79, 0.14)",
  signal: "#c8f04f",
  data: "#5eead4",
  caution: "#fbbf24",
  dead: "#fb7185",
};

/* ------------------------------------------------------------------ */
/* Hero instrument bars                                                */
/* ------------------------------------------------------------------ */

export function EnergyBars() {
  const bars = [
    { k: 1, value: pilot.energy.e1, color: INST.signal },
    { k: 4, value: pilot.energy.e4, color: INST.caution },
    { k: 32, value: pilot.energy.e32, color: INST.data },
  ];
  const max = 160;

  return (
    <div aria-hidden="true">
      <div className="relative h-40 border-b border-l" style={{ borderColor: INST.line }}>
        {[0, 50, 100, 150].map((tick) => (
          <div
            key={tick}
            className="absolute inset-x-0 border-t"
            style={{ top: `${100 - (tick / max) * 100}%`, borderColor: INST.line }}
          />
        ))}
        <div className="absolute inset-0 flex items-end justify-around gap-3 px-3">
          {bars.map((bar) => (
            <div key={bar.k} className="flex h-full w-1/3 flex-col items-center justify-end">
              <span className="mb-1 font-mono text-[10px] tabular-nums" style={{ color: INST.fg }}>
                {bar.value.toFixed(1)}
              </span>
              <div
                className="w-full max-w-12"
                style={{
                  height: `${Math.max(2, (bar.value / max) * 82)}%`,
                  background: bar.color,
                  boxShadow: `0 0 18px ${bar.color}22`,
                }}
              />
            </div>
          ))}
        </div>
      </div>
      <div className="flex justify-around gap-3 px-3 pt-2">
        {bars.map((bar) => (
          <span key={bar.k} className="w-1/3 text-center font-mono text-[10px]" style={{ color: INST.muted }}>
            k = {bar.k}
          </span>
        ))}
      </div>
    </div>
  );
}

export function DepthRuler() {
  const depths = pilot.depths;
  const highlight: Record<number, string> = {
    1: INST.signal,
    4: INST.caution,
    32: INST.data,
  };

  return (
    <div aria-hidden="true">
      <div className="mb-2 flex items-center justify-between">
        <span className="inst-label">Depth k</span>
        <span className="inst-label">7 measured</span>
      </div>
      <div className="relative">
        <div className="absolute inset-x-0 top-[3px] h-px" style={{ background: INST.line }} />
        <div className="relative flex justify-between">
          {depths.map((k) => (
            <div key={k} className="flex flex-col items-center gap-1.5">
              <span
                className="h-[7px] w-[7px] rounded-full"
                style={{
                  background: highlight[k] ?? INST.muted,
                  boxShadow: highlight[k] ? `0 0 8px ${highlight[k]}` : undefined,
                }}
              />
              <span className="font-mono text-[9px] tabular-nums" style={{ color: INST.muted }}>
                {k}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Shared chart frame                                                  */
/* ------------------------------------------------------------------ */

function ChartFrame({
  title,
  subtitle,
  tag,
  children,
  caption,
  className,
}: {
  title: string;
  subtitle: string;
  tag?: ReactNode;
  children: ReactNode;
  caption?: ReactNode;
  className?: string;
}) {
  return (
    <figure className={cn("panel p-4 sm:p-5", className)}>
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-line pb-3">
        <div>
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
            {subtitle}
          </p>
        </div>
        {tag}
      </div>
      <div className="pt-4">{children}</div>
      {caption && (
        <figcaption className="mt-3 border-t border-line pt-3 text-xs leading-relaxed text-muted-foreground">
          {caption}
        </figcaption>
      )}
    </figure>
  );
}

function XLabels({ ticks, className }: { ticks: number[]; className?: string }) {
  return (
    <div className={cn("relative ml-10 h-4", className)} aria-hidden="true">
      {ticks.map((tick, index) => {
        const first = index === 0;
        const last = index === ticks.length - 1;
        return (
          <span
            key={tick}
            className="absolute top-0 font-mono text-[9px] tabular-nums text-muted-foreground"
            style={{
              left: `${xPct(tick)}%`,
              transform: first ? "none" : last ? "translateX(-100%)" : "translateX(-50%)",
            }}
          >
            {tick}
          </span>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Energy fit — J(k) = 15.74 + 2.283k, R² = 0.9990                     */
/* ------------------------------------------------------------------ */

export function EnergyFitChart() {
  const maxJ = 95;
  const yTicks = [0, 30, 60, 90];
  const xTicks = [0, 1, 2, 4, 8, 16, 32];
  const points = [
    { k: 1, j: pilot.energyMeans.j1, side: "right" as const },
    { k: 4, j: pilot.energyMeans.j4, side: "right" as const },
    { k: 32, j: pilot.energyMeans.j32, side: "left" as const },
  ];

  const line = Array.from({ length: 65 }, (_, index) => {
    const k = index * 0.5;
    const j = pilot.fit.a + pilot.fit.b * k;
    return `${xPct(k)},${yPct(j, 0, maxJ)}`;
  }).join(" ");

  return (
    <ChartFrame
      title="Energy per query, fitted"
      subtitle="Pilot · SQuAD v1.1 dev · 200 questions"
      tag={<span className="font-mono text-[10px] text-caution">PILOT</span>}
      caption={
        <>
          The line is the reported affine fit <span className="font-mono">J(k) = 15.74 + 2.283k</span>{" "}
          J, R² = 0.9990. Dots are the documented mean energies at k = 1, 4, and 32. Other measured
          depths are not labelled because the source reports the fit, not every mean.
        </>
      }
    >
      <div className="grid grid-cols-[34px_1fr] gap-2">
        <div className="relative h-60" aria-hidden="true">
          {yTicks.map((tick) => (
            <span
              key={tick}
              className="absolute right-1 -translate-y-1/2 font-mono text-[9px] tabular-nums text-muted-foreground"
              style={{ top: `${yPct(tick, 0, maxJ)}%` }}
            >
              {tick}
            </span>
          ))}
        </div>
        <div className="relative h-60 border-b border-l border-line" role="img" aria-label="Pilot affine energy fit: energy per query rises from about 18 joules at depth 1 to about 90 joules at depth 32.">
          {yTicks.map((tick) => (
            <div
              key={tick}
              className="absolute inset-x-0 border-t border-line/70"
              style={{ top: `${yPct(tick, 0, maxJ)}%` }}
              aria-hidden="true"
            />
          ))}
          {xTicks.map((tick) => (
            <div
              key={tick}
              className="absolute bottom-0 top-0 border-l border-line/40"
              style={{ left: `${xPct(tick)}%` }}
              aria-hidden="true"
            />
          ))}
          <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            className="absolute inset-0 h-full w-full overflow-visible"
            aria-hidden="true"
          >
            <polyline
              points={line}
              fill="none"
              stroke="var(--chart-line)"
              strokeWidth="1.6"
              vectorEffect="non-scaling-stroke"
            />
          </svg>
          {points.map((point) => (
            <div
              key={point.k}
              className="absolute"
              style={{ left: `${xPct(point.k)}%`, top: `${yPct(point.j, 0, maxJ)}%` }}
            >
              <span
                className="absolute block h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background bg-signal"
                aria-hidden="true"
              />
              <span
                className="absolute top-0 whitespace-nowrap font-mono text-[10px] tabular-nums text-foreground"
                style={{
                  transform:
                    point.side === "left"
                      ? "translate(calc(-100% - 10px), -50%)"
                      : "translate(10px, -50%)",
                }}
              >
                {point.j.toFixed(2)} J
              </span>
            </div>
          ))}
        </div>
      </div>
      <XLabels ticks={xTicks} />
      <p className="mt-1 ml-10 font-mono text-[9px] uppercase tracking-[0.12em] text-muted-foreground">
        Depth k (log-spaced axis)
      </p>
    </ChartFrame>
  );
}

/* ------------------------------------------------------------------ */
/* Accuracy — documented points and the reported plateau band          */
/* ------------------------------------------------------------------ */

export function AccuracyChart() {
  const min = 0.35;
  const max = 0.6;
  const yTicks = [0.35, 0.4, 0.45, 0.5, 0.55, 0.6];
  const xTicks = [0, 1, 2, 4, 8, 16, 32];
  const points = [
    { k: 1, a: pilot.accuracy.a1, label: "0.395", side: "right" as const },
    { k: 4, a: pilot.accuracy.a4, label: "0.520", side: "right" as const },
    { k: 32, a: pilot.accuracy.a32, label: "0.570", side: "left" as const },
  ];

  const bandLeft = xPct(pilot.accuracy.plateauFrom);
  const bandRight = xPct(pilot.accuracy.plateauTo);
  const bandTop = yPct(pilot.accuracy.plateauHigh, min, max);
  const bandBottom = yPct(pilot.accuracy.plateauLow, min, max);

  return (
    <ChartFrame
      title="Accuracy at the documented points"
      subtitle="Pilot · normalized EM · strict scoring"
      tag={<span className="font-mono text-[10px] text-caution">PILOT</span>}
      caption={
        <>
          Markers are the reported points: A_EM = 0.395 at k = 1, 0.520 at k = 4, and 0.570 at
          k = 32. The shaded band is the reported plateau, 0.520–0.535 at k = 4–16.
          Intermediate values are not in the source, so no connecting line is drawn.
        </>
      }
    >
      <div className="grid grid-cols-[42px_1fr] gap-2">
        <div className="relative h-60" aria-hidden="true">
          {yTicks.map((tick) => (
            <span
              key={tick}
              className="absolute right-1 -translate-y-1/2 font-mono text-[9px] tabular-nums text-muted-foreground"
              style={{ top: `${yPct(tick, min, max)}%` }}
            >
              {tick.toFixed(2)}
            </span>
          ))}
        </div>
        <div className="relative h-60 border-b border-l border-line" role="img" aria-label="Pilot accuracy: 0.395 at depth 1, 0.520 at depth 4, a plateau of 0.520 to 0.535 from depth 4 to 16, and 0.570 at depth 32.">
          {yTicks.map((tick) => (
            <div
              key={tick}
              className="absolute inset-x-0 border-t border-line/70"
              style={{ top: `${yPct(tick, min, max)}%` }}
              aria-hidden="true"
            />
          ))}
          {xTicks.map((tick) => (
            <div
              key={tick}
              className="absolute bottom-0 top-0 border-l border-line/40"
              style={{ left: `${xPct(tick)}%` }}
              aria-hidden="true"
            />
          ))}
          <div
            className="absolute border-y border-dashed"
            style={{
              left: `${bandLeft}%`,
              width: `${bandRight - bandLeft}%`,
              top: `${bandTop}%`,
              height: `${bandBottom - bandTop}%`,
              background: "var(--chart-band)",
              borderColor: "var(--chart-line)",
            }}
            aria-hidden="true"
          />
          <span
            className="absolute -translate-x-1/2 whitespace-nowrap rounded-[2px] border border-line bg-background/90 px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground"
            style={{ left: `${(bandLeft + bandRight) / 2}%`, top: `calc(${bandTop}% - 20px)` }}
            aria-hidden="true"
          >
            plateau 0.520–0.535
          </span>
          {points.map((point) => (
            <div
              key={point.k}
              className="absolute"
              style={{ left: `${xPct(point.k)}%`, top: `${yPct(point.a, min, max)}%` }}
            >
              <span
                className="absolute block h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background bg-data"
                aria-hidden="true"
              />
              <span
                className="absolute top-0 whitespace-nowrap font-mono text-[10px] tabular-nums text-foreground"
                style={{
                  transform:
                    point.side === "left"
                      ? "translate(calc(-100% - 10px), -50%)"
                      : "translate(10px, -50%)",
                }}
              >
                {point.label}
              </span>
            </div>
          ))}
        </div>
      </div>
      <XLabels ticks={xTicks} />
      <p className="mt-1 ml-10 font-mono text-[9px] uppercase tracking-[0.12em] text-muted-foreground">
        Depth k (log-spaced axis)
      </p>
    </ChartFrame>
  );
}

/* ------------------------------------------------------------------ */
/* Context-side share                                                  */
/* ------------------------------------------------------------------ */

export function ContextShareChart() {
  const rows = [
    { k: 2, value: pilot.contextShare.at2 },
    { k: 32, value: pilot.contextShare.at32 },
  ];

  return (
    <div className="space-y-6">
      <div className="space-y-5" role="img" aria-label="Pilot context-side energy share rises from 36.3 percent at depth 2 to 85.1 percent at depth 32.">
        {rows.map((row) => (
          <div key={row.k}>
            <div className="flex items-baseline justify-between gap-3">
              <span className="font-mono text-xs text-muted-foreground">k = {row.k}</span>
              <span className="font-mono text-lg font-medium tabular-nums text-data">{row.value.toFixed(1)}%</span>
            </div>
            <div className="mt-2 h-3 w-full overflow-hidden rounded-[2px] border border-line bg-panel">
              <div
                className="h-full bg-data"
                style={{ width: `${row.value}%`, opacity: row.k === 2 ? 0.7 : 1 }}
              />
            </div>
            <div className="mt-1 flex justify-between font-mono text-[9px] text-muted-foreground" aria-hidden="true">
              <span>0</span>
              <span>50</span>
              <span>100%</span>
            </div>
          </div>
        ))}
      </div>
      <div className="border-t border-line pt-4">
        <div className="flex items-center justify-between gap-3">
          <span className="eyebrow">Retrieval-only proxy</span>
          <span className="font-mono text-xs text-muted-foreground">
            {pilot.retrievalShare.min}%–{pilot.retrievalShare.max}%
          </span>
        </div>
        <div className="relative mt-3 h-2 rounded-[2px] border border-line bg-panel" aria-hidden="true">
          <div
            className="absolute inset-y-0 bg-beam/60"
            style={{
              left: `${pilot.retrievalShare.min}%`,
              width: `${pilot.retrievalShare.max - pilot.retrievalShare.min}%`,
            }}
          />
        </div>
        <div className="mt-1 flex justify-between font-mono text-[9px] text-muted-foreground">
          <span>{pilot.retrievalShare.min}% at k = {pilot.retrievalShare.minAt}</span>
          <span>{pilot.retrievalShare.max}% at k = {pilot.retrievalShare.maxAt}</span>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
          The retrieval share is a CPU proxy: BM25 wall time × 20 W. It is an upper bound, not a
          measured share.
        </p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Identity gap dot plot                                               */
/* ------------------------------------------------------------------ */

export function IdentityPlot() {
  const min = -0.12;
  const max = 0.78;
  const row = (value: number) => pct(value, min, max);
  const zero = row(0);

  return (
    <div className="space-y-1" role="img" aria-label="Pilot identity gap: plus 0.044 with a 95 percent interval from minus 0.050 to plus 0.128 at depth 2, and plus 0.700 at depth 32.">
      {[
        { k: 2, gap: pilot.identity.at2.gap, ci: pilot.identity.at2.ci, tone: "bg-signal" },
        { k: 32, gap: pilot.identity.at32.gap, ci: null, tone: "bg-dead" },
      ].map((item) => (
        <div key={item.k} className="grid grid-cols-[88px_1fr] items-center gap-3 border-b border-line py-3 last:border-b-0">
          <div>
            <div className="font-mono text-xs text-muted-foreground">k = {item.k}</div>
            <div className="mt-1 font-mono text-sm font-medium tabular-nums">
              {item.gap > 0 ? "+" : ""}
              {item.gap.toFixed(3)}
            </div>
          </div>
          <div className="relative h-8">
            <div
              className="absolute inset-y-0 border-l border-dashed border-line-strong"
              style={{ left: `${zero}%` }}
              aria-hidden="true"
            />
            {item.ci && (
              <div
                className="absolute top-1/2 h-px -translate-y-1/2 bg-muted-foreground"
                style={{
                  left: `${row(item.ci[0])}%`,
                  width: `${row(item.ci[1]) - row(item.ci[0])}%`,
                }}
                aria-hidden="true"
              />
            )}
            {item.ci && (
              <>
                <span
                  className="absolute top-1/2 h-2.5 w-px -translate-y-1/2 bg-muted-foreground"
                  style={{ left: `${row(item.ci[0])}%` }}
                  aria-hidden="true"
                />
                <span
                  className="absolute top-1/2 h-2.5 w-px -translate-y-1/2 bg-muted-foreground"
                  style={{ left: `${row(item.ci[1])}%` }}
                  aria-hidden="true"
                />
              </>
            )}
            <span
              className={cn("absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background", item.tone)}
              style={{ left: `${row(item.gap)}%` }}
              aria-hidden="true"
            />
          </div>
        </div>
      ))}
      <div className="grid grid-cols-[88px_1fr] gap-3 pt-1">
        <span />
        <div className="relative h-4 font-mono text-[9px] text-muted-foreground" aria-hidden="true">
          <span className="absolute -translate-x-1/2" style={{ left: `${row(0)}%` }}>0</span>
          <span className="absolute -translate-x-1/2" style={{ left: `${row(0.2)}%` }}>0.2</span>
          <span className="absolute -translate-x-1/2" style={{ left: `${row(0.4)}%` }}>0.4</span>
          <span className="absolute -translate-x-1/2" style={{ left: `${row(0.6)}%` }}>0.6</span>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Recall bars                                                         */
/* ------------------------------------------------------------------ */

export function RecallBars() {
  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-4 font-mono text-[9px] uppercase tracking-[0.12em] text-muted-foreground">
        <span className="inline-flex items-center gap-2"><span className="h-2 w-3 bg-data" aria-hidden /> Gold context</span>
        <span className="inline-flex items-center gap-2"><span className="h-2 w-3 bg-beam" aria-hidden /> Gold answer in text</span>
      </div>
      <div className="space-y-3" role="img" aria-label="Pilot retrieval recall by depth. Gold context recall rises from 63 percent at depth 1 to 88 percent at depth 32. Gold answer string recall rises from 58 to 88.5 percent.">
        {pilot.recall.depths.map((k, index) => (
          <div key={k} className="grid grid-cols-[38px_1fr] items-center gap-3">
            <span className="font-mono text-[10px] text-muted-foreground">k={k}</span>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="h-2 flex-1 overflow-hidden rounded-[1px] bg-panel">
                  <div className="h-full bg-data" style={{ width: `${pilot.recall.goldContext[index]}%` }} />
                </div>
                <span className="w-10 text-right font-mono text-[9px] tabular-nums text-muted-foreground">
                  {pilot.recall.goldContext[index].toFixed(1)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 flex-1 overflow-hidden rounded-[1px] bg-panel">
                  <div className="h-2 bg-beam" style={{ width: `${pilot.recall.goldAnswer[index]}%` }} />
                </div>
                <span className="w-10 text-right font-mono text-[9px] tabular-nums text-muted-foreground">
                  {pilot.recall.goldAnswer[index].toFixed(1)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
      <p className="mt-3 font-mono text-[9px] uppercase tracking-[0.12em] text-caution">
        Pilot recall · percent
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Block calibration factors                                           */
/* ------------------------------------------------------------------ */

export function BlockFactorBars() {
  const max = 1.25;
  return (
    <div className="flex items-end gap-2" role="img" aria-label="Pilot block calibration factors range from 1.041 at depth 0 to 1.188 at depth 2, then decline to 1.073 at depth 32.">
      {pilot.blockFactors.map((item) => (
        <div key={item.k} className="flex flex-1 flex-col items-center justify-end gap-1">
          <span className="font-mono text-[9px] tabular-nums text-muted-foreground">{item.factor.toFixed(3)}</span>
          <div
            className="w-full max-w-7 bg-caution/70"
            style={{ height: `${(item.factor / max) * 64}px` }}
            aria-hidden="true"
          />
          <span className="font-mono text-[9px] text-muted-foreground">{item.k}</span>
        </div>
      ))}
    </div>
  );
}
