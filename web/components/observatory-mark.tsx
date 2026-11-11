import { cn } from "@/lib/cn";

/**
 * Observatory mark: a depth ladder inside a measurement ring.
 * Uses the theme signal colour, so it is lime on dark and deep green on paper.
 */
export function ObservatoryMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      aria-hidden="true"
      className={cn("shrink-0", className)}
      fill="none"
    >
      <rect x="0.75" y="0.75" width="46.5" height="46.5" rx="10" fill="var(--panel)" stroke="var(--line)" />
      <circle cx="24" cy="24" r="16.5" stroke="var(--signal)" strokeOpacity="0.28" strokeWidth="1" />
      <path d="M16 34V14" stroke="var(--signal)" strokeWidth="1.8" strokeLinecap="round" />
      <path
        d="M16 19h6.5M16 23.7h9.5M16 28.4h12.5M16 33h15"
        stroke="var(--signal)"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeOpacity="0.72"
      />
      <circle cx="16" cy="14" r="2.2" fill="var(--signal)" />
      <path d="M34 16v-3M34 16h-3" stroke="var(--data)" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}
