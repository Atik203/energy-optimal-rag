import { survivalClaims, type ClaimStatus } from "@/lib/project-data";
import { PilotChip, StatusTag } from "@/components/ui";
import { cn } from "@/lib/cn";

const groups: Array<{
  key: string;
  title: string;
  subtitle: string;
  tone: "signal" | "dead" | "caution";
  statuses: ClaimStatus[];
}> = [
  {
    key: "survived",
    title: "Survived",
    subtitle: "Measured, precise enough to keep",
    tone: "signal",
    statuses: ["supported"],
  },
  {
    key: "dead",
    title: "Did not survive",
    subtitle: "Reported, not resurrected",
    tone: "dead",
    statuses: ["dead"],
  },
  {
    key: "bounded",
    title: "Bounded or pending",
    subtitle: "A ceiling, a signal, or a rejected diagnostic",
    tone: "caution",
    statuses: ["rejected", "upper-bound", "signal"],
  },
];

const headerDot = {
  signal: "bg-signal",
  dead: "bg-dead",
  caution: "bg-caution",
};

export function ClaimLedger({ compact = false }: { compact?: boolean }) {
  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <span className="eyebrow">Pilot claim ledger</span>
        <PilotChip />
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {groups.map((group) => {
        const items = survivalClaims.filter((claim) => group.statuses.includes(claim.status));
        return (
          <section
            key={group.key}
            aria-labelledby={`claim-group-${group.key}`}
            className="panel flex flex-col"
          >
            <div className="flex items-start justify-between gap-3 border-b border-line px-4 py-3">
              <div>
                <h3 id={`claim-group-${group.key}`} className="flex items-center gap-2 text-sm font-semibold">
                  <span className={cn("h-1.5 w-1.5 rounded-full", headerDot[group.tone])} aria-hidden />
                  {group.title}
                </h3>
                <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.12em] text-muted-foreground">
                  {group.subtitle}
                </p>
              </div>
              <span className="font-mono text-[10px] tabular-nums text-muted-foreground">
                {String(items.length).padStart(2, "0")}
              </span>
            </div>
            <ul className="flex-1 divide-y divide-line">
              {items.map((claim) => (
                <li key={claim.claim} className={cn("px-4", compact ? "py-3" : "py-4")}>
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="max-w-[16rem] text-sm font-semibold leading-snug">{claim.claim}</p>
                    <StatusTag status={claim.status} />
                  </div>
                  <p className="mt-1.5 font-mono text-[10px] leading-relaxed text-muted-foreground">
                    {claim.evidence}
                  </p>
                </li>
              ))}
            </ul>
            {group.key === "dead" && (
              <div className="mt-auto border-t border-line bg-panel-soft px-4 py-3">
                <p className="text-xs leading-relaxed text-muted-foreground">
                  Power failure, not a flat-curve failure. The margin is estimation-only in the
                  rerun; the dead claim is not resurrected.
                </p>
              </div>
            )}
          </section>
        );
      })}
      </div>
    </div>
  );
}
