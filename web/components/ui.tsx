import type { ReactNode } from "react";
import { FileText } from "lucide-react";
import { cn } from "@/lib/cn";
import type { ClaimStatus } from "@/lib/project-data";

export type Tone = "signal" | "data" | "beam" | "caution" | "dead" | "neutral";

const chipTones: Record<Tone, string> = {
  signal: "border-signal/30 bg-signal/10 text-signal",
  data: "border-data/30 bg-data/10 text-data",
  beam: "border-beam/30 bg-beam/10 text-beam",
  caution: "border-caution/35 bg-caution/10 text-caution",
  dead: "border-dead/35 bg-dead/10 text-dead",
  neutral: "border-line bg-panel/60 text-muted-foreground",
};

const dotTones: Record<Tone, string> = {
  signal: "bg-signal",
  data: "bg-data",
  beam: "bg-beam",
  caution: "bg-caution",
  dead: "bg-dead",
  neutral: "bg-muted-foreground",
};

export function Chip({
  children,
  tone = "neutral",
  dot = false,
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-[2px] border px-2 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.13em]",
        chipTones[tone],
        className,
      )}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full", dotTones[tone])} aria-hidden />}
      {children}
    </span>
  );
}

export function PilotChip({ label = "Pilot" }: { label?: string }) {
  return (
    <Chip tone="caution" dot>
      {label}
    </Chip>
  );
}

const statusMeta: Record<ClaimStatus, { label: string; tone: Tone }> = {
  supported: { label: "Supported", tone: "signal" },
  dead: { label: "Dead", tone: "dead" },
  rejected: { label: "Rejected", tone: "dead" },
  "upper-bound": { label: "Upper bound", tone: "caution" },
  signal: { label: "Pilot signal", tone: "caution" },
  pending: { label: "Pending", tone: "neutral" },
};

export function StatusTag({ status, label }: { status: ClaimStatus; label?: string }) {
  const meta = statusMeta[status];
  return (
    <Chip tone={meta.tone} dot>
      {label ?? meta.label}
    </Chip>
  );
}

export function PageHero({
  index,
  eyebrow,
  title,
  lede,
  meta,
  children,
}: {
  index: string;
  eyebrow: string;
  title: ReactNode;
  lede: ReactNode;
  meta?: Array<{ label: string; tone?: Tone }>;
  children?: ReactNode;
}) {
  return (
    <header className="relative pb-10 pt-8 sm:pt-12">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-mono text-[10px] tracking-[0.18em] text-signal">{index}</span>
        <span className="eyebrow">{eyebrow}</span>
        <span className="h-px flex-1 bg-line" aria-hidden />
        <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-muted-foreground">
          Status / Post-pilot MARGINAL
        </span>
      </div>
      <h1 className="display-title mt-6 max-w-4xl text-[2.55rem] leading-[1.01] sm:text-5xl lg:text-[3.65rem]">
        {title}
      </h1>
      <p className="mt-5 max-w-2xl text-[1.05rem] leading-relaxed text-muted-foreground">{lede}</p>
      {meta && meta.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2">
          {meta.map((item) => (
            <Chip key={item.label} tone={item.tone ?? "neutral"} dot={item.tone !== undefined}>
              {item.label}
            </Chip>
          ))}
        </div>
      )}
      {children}
    </header>
  );
}

export function SectionHeading({
  index,
  eyebrow,
  title,
  description,
  id,
  className,
}: {
  index: string;
  eyebrow: string;
  title: ReactNode;
  description?: ReactNode;
  id?: string;
  className?: string;
}) {
  return (
    <div className={cn("border-t border-line pt-7", className)}>
      <div className="grid gap-4 md:grid-cols-[180px_1fr] lg:grid-cols-[220px_1fr]">
        <div className="flex items-start gap-3 md:flex-col md:gap-2">
          <span className="font-mono text-[11px] text-signal">{index}</span>
          <span className="eyebrow">{eyebrow}</span>
          <span className="hidden h-px w-10 bg-line-strong md:mt-3 md:block" aria-hidden />
        </div>
        <div>
          <h2 id={id} className="display-title text-3xl leading-[1.06] sm:text-4xl lg:text-[2.75rem]">
            {title}
          </h2>
          {description && (
            <p className="mt-4 max-w-2xl text-[0.98rem] leading-relaxed text-muted-foreground">
              {description}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export function PanelHeader({
  label,
  aside,
  className,
}: {
  label: ReactNode;
  aside?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3", className)}>
      <span className="eyebrow">{label}</span>
      {aside}
    </div>
  );
}

export function FormulaBlock({
  label = "Definition",
  children,
  note,
  className,
}: {
  label?: string;
  children: ReactNode;
  note?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("instrument p-5", className)}>
      <div className="flex items-center justify-between gap-3">
        <span className="inst-label">{label}</span>
        <span className="inst-label">Readout</span>
      </div>
      <div className="mt-3 overflow-x-auto pb-1 font-mono text-[0.95rem] leading-relaxed text-[#eef3e5] sm:text-lg">
        {children}
      </div>
      {note && <p className="mt-2 text-xs leading-relaxed text-[#8aa294]">{note}</p>}
    </div>
  );
}

export function StatBlock({
  value,
  unit,
  label,
  note,
  tone = "signal",
}: {
  value: string;
  unit?: string;
  label: string;
  note?: ReactNode;
  tone?: Tone;
}) {
  const toneClass: Record<Tone, string> = {
    signal: "text-signal",
    data: "text-data",
    beam: "text-beam",
    caution: "text-caution",
    dead: "text-dead",
    neutral: "text-foreground",
  };

  return (
    <div>
      <div className="flex items-baseline gap-1">
        <span className={cn("font-mono text-3xl font-medium leading-none tracking-[-0.04em] tnum sm:text-4xl", toneClass[tone])}>
          {value}
        </span>
        {unit && <span className="font-mono text-base text-muted-foreground">{unit}</span>}
      </div>
      {label && <p className="mt-2 text-sm font-semibold leading-snug">{label}</p>}
      {note && <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{note}</p>}
    </div>
  );
}

const calloutTones = {
  signal: "border-signal",
  data: "border-data",
  caution: "border-caution",
  dead: "border-dead",
} as const;

export function Callout({
  tone = "caution",
  title,
  icon,
  children,
  className,
}: {
  tone?: keyof typeof calloutTones;
  title?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("border-l-2 py-0.5 pl-4", calloutTones[tone], className)}>
      {title && (
        <p className="flex items-center gap-2 text-sm font-semibold">
          {icon}
          {title}
        </p>
      )}
      <div className={cn("text-sm leading-relaxed text-muted-foreground", title && "mt-1")}>{children}</div>
    </div>
  );
}

export function SourceNote({ children }: { children: ReactNode }) {
  return (
    <p className="mt-4 flex items-start gap-2 font-mono text-[10px] leading-relaxed text-muted-foreground">
      <FileText className="mt-0.5 h-3 w-3 shrink-0" aria-hidden />
      <span>{children}</span>
    </p>
  );
}
