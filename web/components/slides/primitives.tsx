import type { ReactNode } from "react";
import { ArrowRight } from "lucide-react";

/* Projector-safe, light-deck palette. */
export const S = {
  paper: "#ffffff",
  alt: "#f3f4f6",
  ink: "#000000",
  inkSoft: "#111827",
  muted: "#374151",
  line: "#b8c0c8",
  deep: "#123a2a",
  lime: "#a8d43a",
  limeSoft: "#f1f7d9",
  teal: "#0f766e",
  tealSoft: "#e6f4f1",
  amber: "#9a4f00",
  amberSoft: "#fff3d6",
  rose: "#a3112f",
  roseSoft: "#ffe4e9",
  white: "#ffffff",
} as const;

export type SlideTone = "rose" | "amber" | "teal" | "deep" | "lime";

export function tone(t: SlideTone) {
  switch (t) {
    case "rose":
      return { main: S.rose, soft: S.roseSoft, on: S.white };
    case "amber":
      return { main: S.amber, soft: S.amberSoft, on: S.white };
    case "teal":
      return { main: S.teal, soft: S.tealSoft, on: S.white };
    case "lime":
      return { main: "#5d7a12", soft: S.limeSoft, on: S.white };
    case "deep":
    default:
      return { main: S.deep, soft: "#e4ebe0", on: S.white };
  }
}

export function SlideMark({ size = "7cqh" }: { size?: string }) {
  return (
    <svg viewBox="0 0 48 48" style={{ width: size, height: size }} aria-hidden="true">
      <rect width="48" height="48" rx="9" fill={S.deep} />
      <circle cx="24" cy="24" r="17" fill="none" stroke={S.lime} strokeOpacity="0.3" strokeWidth="1" />
      <path d="M16 34V14" stroke={S.lime} strokeWidth="1.8" strokeLinecap="round" />
      <path
        d="M16 19h6.5M16 23.7h9.5M16 28.4h12.5M16 33h15"
        stroke={S.lime}
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeOpacity="0.75"
      />
      <circle cx="16" cy="14" r="2.2" fill={S.lime} />
      <path d="M34 16v-3M34 16h-3" stroke={S.teal} strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

export function SlideFrame({
  badge,
  badgeTone,
  title,
  subtitle,
  index,
  total,
  pilot = false,
  children,
}: {
  badge: string;
  badgeTone: SlideTone;
  title: ReactNode;
  subtitle?: ReactNode;
  index: number;
  total: number;
  pilot?: boolean;
  children: ReactNode;
}) {
  const badgeColors = tone(badgeTone);

  return (
    <div
      className="relative flex h-full w-full flex-col overflow-hidden"
      style={{ background: S.paper, color: S.ink }}
    >
      <div className="absolute inset-y-0 left-0 w-[0.45cqw]" style={{ background: S.lime }} />
      <div className="slide-grid pointer-events-none absolute inset-0 opacity-25" />

      <div className="relative flex h-full min-h-0 flex-col px-[4.2cqw] pb-[1.9cqh] pt-[3.1cqh]">
        <div className="flex items-start justify-between gap-[2cqw]">
          <div className="flex flex-wrap items-center gap-[0.9cqw]">
            <span
              className="px-[1.2cqw] py-[0.5cqh] font-mono text-[1.95cqh] font-bold uppercase tracking-[0.14em]"
              style={{ background: badgeColors.soft, color: badgeColors.main }}
            >
              {badge}
            </span>
            {pilot && (
              <span
                className="border px-[0.9cqw] py-[0.4cqh] font-mono text-[1.7cqh] font-bold uppercase tracking-[0.12em]"
                style={{ borderColor: S.amber, color: S.amber }}
              >
                Pilot
              </span>
            )}
          </div>
          <span
            className="pt-[0.5cqh] font-mono text-[1.7cqh] font-semibold uppercase tracking-[0.16em]"
            style={{ color: S.muted }}
          >
            Energy Observatory / G2
          </span>
        </div>

        <div className="mt-[2.1cqh] max-w-[86cqw]">
          <h1
            className="text-[5.2cqh] font-semibold leading-[1.02] tracking-[-0.02em]"
            style={{ fontFamily: "var(--font-serif)", color: S.ink }}
          >
            {title}
          </h1>
          {subtitle && (
            <div
              className="mt-[1.05cqh] max-w-[78cqw] text-[2.45cqh] font-semibold leading-snug"
              style={{ color: S.inkSoft }}
            >
              {subtitle}
            </div>
          )}
        </div>

        <div className="relative mt-[1.9cqh] flex min-h-0 flex-1 flex-col">{children}</div>

        <div
          className="mt-[1.5cqh] flex items-center justify-between gap-[2cqw] border-t pt-[0.9cqh] font-mono text-[1.6cqh] font-semibold uppercase tracking-[0.1em]"
          style={{ borderColor: S.line, color: S.muted }}
        >
          <span>Energy-Optimal Retrieval Depth</span>
          <span style={{ color: pilot ? S.amber : S.muted }}>
            {pilot ? "Pilot evidence · not confirmatory" : "No confirmatory results"}
          </span>
          <span className="tnum">
            {String(index + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
          </span>
        </div>
      </div>
    </div>
  );
}

export function SlideCard({
  title,
  tone: cardTone,
  icon,
  children,
  fill,
  className = "",
}: {
  title: string;
  tone: SlideTone;
  icon?: ReactNode;
  children: ReactNode;
  fill?: string;
  className?: string;
}) {
  const c = tone(cardTone);
  return (
    <div
      className={`flex min-h-0 flex-col border-2 px-[1.6cqw] py-[1.35cqh] ${className}`}
      style={{ borderColor: c.main, background: fill ?? c.soft }}
    >
      <div className="flex items-center gap-[0.8cqw]">
        {icon && (
          <span
            className="flex flex-shrink-0 items-center justify-center"
            style={{ width: "3.3cqh", height: "3.3cqh", background: c.main, color: c.on }}
          >
            {icon}
          </span>
        )}
        <span
          className="font-mono text-[2.2cqh] font-bold uppercase tracking-[0.08em]"
          style={{ color: c.main }}
        >
          {title}
        </span>
      </div>
      <div className="mt-[1.1cqh] min-h-0 flex-1">{children}</div>
    </div>
  );
}

export function SlideKpi({
  value,
  label,
  sub,
  tone: kpiTone = "deep",
}: {
  value: string;
  label: string;
  sub?: string;
  tone?: SlideTone;
}) {
  const c = tone(kpiTone);
  return (
    <div className="min-w-0 text-center">
      <p
        className="font-mono text-[6.8cqh] font-bold leading-none tracking-[-0.05em] tnum"
        style={{ color: c.main }}
      >
        {value}
      </p>
      <p className="mt-[0.75cqh] text-[2.2cqh] font-bold leading-snug" style={{ color: S.ink }}>
        {label}
      </p>
      {sub && (
        <p className="mt-[0.35cqh] text-[1.9cqh] font-semibold leading-snug" style={{ color: S.muted }}>
          {sub}
        </p>
      )}
    </div>
  );
}

export function SlideKpiRow({
  items,
  cols,
}: {
  items: Array<{ value: string; label: string; sub?: string; tone?: SlideTone }>;
  cols?: number;
}) {
  return (
    <div
      className="grid gap-[1.2cqw] border px-[1.8cqw] py-[1.5cqh]"
      style={{
        background: S.alt,
        borderColor: S.line,
        gridTemplateColumns: `repeat(${cols ?? items.length}, minmax(0, 1fr))`,
      }}
    >
      {items.map((item) => (
        <SlideKpi key={item.label} {...item} />
      ))}
    </div>
  );
}

export function SlideBullets({
  items,
  tone: bulletTone = "deep",
  size = "2.45cqh",
}: {
  items: ReactNode[];
  tone?: SlideTone;
  size?: string;
}) {
  const c = tone(bulletTone);
  return (
    <ul className="flex h-full flex-col justify-center gap-[0.95cqh]">
      {items.map((item, index) => (
        <li key={index} className="flex items-start gap-[0.9cqw]">
          <span
            className="mt-[0.9cqh] flex-shrink-0"
            style={{ width: "1.05cqh", height: "1.05cqh", background: c.main }}
            aria-hidden="true"
          />
          <span className="font-semibold leading-snug" style={{ color: S.ink, fontSize: size }}>
            {item}
          </span>
        </li>
      ))}
    </ul>
  );
}

export function SlideChip({ children, tone: chipTone = "deep" }: { children: ReactNode; tone?: SlideTone }) {
  const c = tone(chipTone);
  return (
    <span
      className="inline-block px-[1.1cqw] py-[0.55cqh] font-mono text-[1.9cqh] font-bold uppercase tracking-[0.08em]"
      style={{ background: c.soft, color: c.main }}
    >
      {children}
    </span>
  );
}

export function SlideFormula({
  children,
  tone: formulaTone = "deep",
}: {
  children: ReactNode;
  tone?: SlideTone;
}) {
  const c = tone(formulaTone);
  return (
    <div
      className="px-[1.5cqw] py-[1.1cqh]"
      style={{ borderLeft: `0.4cqw solid ${c.main}`, background: c.soft }}
    >
      <div className="font-mono text-[2.55cqh] font-semibold leading-relaxed" style={{ color: S.ink }}>
        {children}
      </div>
    </div>
  );
}

export function SlideCallout({
  children,
  tone: calloutTone = "deep",
}: {
  children: ReactNode;
  tone?: SlideTone;
}) {
  const c = tone(calloutTone);
  return (
    <div
      className="flex items-center gap-[1.2cqw] px-[1.6cqw] py-[1.1cqh] text-[2.3cqh] font-bold leading-snug"
      style={{ background: c.soft, color: S.ink, borderLeft: `0.4cqw solid ${c.main}` }}
    >
      <ArrowRight size="2.4cqh" style={{ color: c.main, flexShrink: 0 }} aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

export function SlideTable({
  head,
  rows,
  tone: tableTone = "deep",
  widths,
  compact = false,
  highlightRow,
}: {
  head: string[];
  rows: ReactNode[][];
  tone?: SlideTone;
  widths?: string[];
  compact?: boolean;
  highlightRow?: number;
}) {
  const c = tone(tableTone);
  return (
    <div className="min-h-0 overflow-hidden border-2" style={{ borderColor: c.main }}>
      <table className="w-full border-collapse" style={{ tableLayout: "fixed" }}>
        <thead>
          <tr style={{ background: c.soft }}>
            {head.map((cell, index) => (
              <th
                key={cell}
                className={`px-[1.1cqw] text-left font-mono font-bold uppercase tracking-[0.06em] ${
                  compact ? "py-[0.75cqh] text-[2.0cqh]" : "py-[0.9cqh] text-[2.15cqh]"
                }`}
                style={{ color: c.main, width: widths?.[index] }}
              >
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              style={{
                background: rowIndex === highlightRow ? c.soft : rowIndex % 2 ? S.alt : S.paper,
                borderTop: `1px solid ${S.line}`,
              }}
            >
              {row.map((cell, cellIndex) => (
                <td
                  key={cellIndex}
                  className={`px-[1.1cqw] align-top font-semibold leading-snug ${
                    compact ? "py-[0.85cqh] text-[2.15cqh]" : "py-[0.95cqh] text-[2.3cqh]"
                  } ${cellIndex === 0 ? "text-left" : "text-left"}`}
                  style={{ color: S.ink }}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SlideBars({
  items,
  max,
  height = "26cqh",
}: {
  items: Array<{ label: string; value: number; display: string; tone: SlideTone }>;
  max: number;
  height?: string;
}) {
  return (
    <div>
      <div className="relative border-b border-l" style={{ height, borderColor: S.line }}>
        <div className="absolute inset-0 flex items-end justify-around gap-[2cqw] px-[1.5cqw]">
          {items.map((item) => {
            const c = tone(item.tone);
            return (
              <div key={item.label} className="flex h-full w-1/3 flex-col items-center justify-end">
                <span className="mb-[0.4cqh] font-mono text-[1.9cqh] font-bold tnum" style={{ color: S.ink }}>
                  {item.display}
                </span>
                <div
                  style={{
                    width: "58%",
                    height: `${Math.max(2, (item.value / max) * 82)}%`,
                    background: c.main,
                  }}
                />
              </div>
            );
          })}
        </div>
      </div>
      <div className="flex justify-around gap-[2cqw] px-[1.5cqw] pt-[0.6cqh]">
        {items.map((item) => (
          <span key={item.label} className="w-1/3 text-center font-mono text-[1.9cqh] font-semibold" style={{ color: S.muted }}>
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export function SlideDepthLadder({ values = [0, 1, 2, 4, 8, 16, 32] }: { values?: number[] }) {
  return (
    <div className="relative">
      <div className="absolute inset-x-0 top-[0.5cqh] h-px" style={{ background: S.line }} />
      <div className="relative flex justify-between">
        {values.map((k) => {
          const highlight = k === 1 || k === 4 || k === 32;
          const color = k === 4 ? S.amber : k === 32 ? S.teal : k === 1 ? S.deep : S.line;
          return (
            <div key={k} className="flex flex-col items-center gap-[0.5cqh]">
              <span
                style={{
                  width: highlight ? "1.6cqh" : "1.1cqh",
                  height: highlight ? "1.6cqh" : "1.1cqh",
                  background: color,
                  borderRadius: "999px",
                }}
              />
              <span className="font-mono text-[1.65cqh] font-semibold tnum" style={{ color: S.muted }}>
                {k}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
