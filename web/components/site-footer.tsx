import Link from "next/link";
import { navItems, project } from "@/lib/project-data";
import { ObservatoryMark } from "@/components/observatory-mark";

const EVIDENCE_LINKS = [
  { href: `${project.repo}#readme`, label: "README" },
  { href: `${project.repo}/blob/main/ROADMAP.md`, label: "Roadmap" },
  { href: `${project.repo}/blob/main/docs/PILOT_EVIDENCE.md`, label: "Pilot evidence" },
  { href: `${project.repo}/blob/main/prereg/PREREGISTRATION.md`, label: "Preregistration" },
  { href: `${project.repo}/blob/main/artifacts/claims_evidence.csv`, label: "Claims evidence" },
];

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-line">
      <div className="mx-auto w-full max-w-[1240px] px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid gap-9 md:grid-cols-2 lg:grid-cols-[1.35fr_0.8fr_0.85fr_1.1fr]">
          <div>
            <div className="flex items-center gap-3">
              <ObservatoryMark className="h-9 w-9" />
              <div>
                <p className="display-title text-lg leading-none">{project.siteName}</p>
                <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">
                  {project.shortName} / Joules per correct answer
                </p>
              </div>
            </div>
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted-foreground">
              A measurement instrument for retrieval depth in RAG. Pilot evidence is
              reported exactly as measured, including the claim that failed.
            </p>
            <p className="mt-4 inline-flex items-center gap-2 rounded-[2px] border border-caution/30 bg-caution/10 px-2.5 py-1.5 font-mono text-[9px] uppercase tracking-[0.14em] text-caution">
              <span className="h-1.5 w-1.5 rounded-full bg-caution" aria-hidden />
              {project.status} · No confirmatory results
            </p>
          </div>

          <div>
            <p className="eyebrow">Explore</p>
            <ul className="mt-3 space-y-2">
              {navItems.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
              <li>
                <Link href="/slide" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                  Slides
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <p className="eyebrow">Evidence</p>
            <ul className="mt-3 space-y-2">
              {EVIDENCE_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="eyebrow">Fine print</p>
            <ul className="mt-3 space-y-2 text-sm leading-relaxed text-muted-foreground">
              <li>Code: {project.licenseCode}.</li>
              <li>Docs and derived data: {project.licenseDocs}.</li>
              <li>Upstream datasets: {project.licenseData}; no raw text is redistributed.</li>
              <li>No analytics, cookies, remote fonts, or runtime fetches.</li>
            </ul>
          </div>
        </div>

        <div className="mt-9 flex flex-col gap-2 border-t border-line pt-5 font-mono text-[10px] leading-relaxed tracking-[0.04em] text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <span>© 2026 {project.author} · Site v{project.version}</span>
          <span>Updated {project.updated} · Static, self-contained site</span>
        </div>
      </div>
    </footer>
  );
}
