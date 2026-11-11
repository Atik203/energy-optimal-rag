import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Database,
  ExternalLink,
  FileCheck2,
  FileText,
  Github,
  Globe,
  Lock,
  Presentation,
  Scale,
  ScrollText,
  ShieldCheck,
} from "lucide-react";
import { project } from "@/lib/project-data";
import {
  Callout,
  Chip,
  PageHero,
  SectionHeading,
  SourceNote,
} from "@/components/ui";

export const metadata: Metadata = {
  title: "About",
  description:
    "Project status, author, citation, licenses, data policy, evidence policy, and repository links for the energy-optimal retrieval-depth study.",
};

const statusRows = [
  ["Research status", "post-pilot MARGINAL"],
  ["Release", "public scaffold v0.1.0"],
  ["Last updated", project.updated],
  ["Confirmatory data", "none"],
  ["Preregistration", "DRAFT, not frozen · hash TBD"],
  ["Freeze tag", "prereg-freeze-v1 (pending)"],
  ["External registry", "none; a frozen git tag and SHA-256 will be the record"],
  ["Pilot raw data", "not in this repository; run CSVs are git-ignored"],
  ["Evidence map", "artifacts/claims_evidence.csv"],
  ["Run registry", "runs/registry.csv (tracked); raw runs are git-ignored"],
  ["Code license", "MIT"],
  ["Docs license", "CC BY 4.0"],
];

const repoLinks = [
  { href: `${project.repo}`, label: "Repository" },
  { href: `${project.repo}/blob/main/README.md`, label: "README" },
  { href: `${project.repo}/blob/main/ROADMAP.md`, label: "Roadmap" },
  { href: `${project.repo}/blob/main/docs/IMPLEMENTATION_PLAN.md`, label: "Implementation plan" },
  { href: `${project.repo}/blob/main/docs/MEASUREMENT.md`, label: "Measurement protocol" },
  { href: `${project.repo}/blob/main/docs/DATA_CARD.md`, label: "Data card" },
  { href: `${project.repo}/blob/main/docs/PILOT_EVIDENCE.md`, label: "Pilot evidence" },
  { href: `${project.repo}/blob/main/docs/RISKS.md`, label: "Risk register" },
  { href: `${project.repo}/blob/main/docs/DECISIONS.md`, label: "Decision log" },
  { href: `${project.repo}/blob/main/prereg/PREREGISTRATION.md`, label: "Preregistration" },
  { href: `${project.repo}/blob/main/artifacts/claims_evidence.csv`, label: "Claims evidence" },
  { href: `${project.repo}/blob/main/artifacts/ledger.csv`, label: "Energy ledger" },
  { href: `${project.repo}/issues`, label: "Issues" },
];

const siteMap = [
  { href: "/", label: "Home", note: "The question, the pilot metrics, the boundary" },
  { href: "/research", label: "Research", note: "Estimand, H1–H7, theory, gates, prior work" },
  { href: "/method", label: "Method", note: "Pipeline, measurement, data, scoring, policy, taxes" },
  { href: "/results", label: "Results", note: "Pilot evidence, dead claim, 5 pp signal, oracle" },
  { href: "/roadmap", label: "Roadmap", note: "P0–P6, budget, risks, decisions, stop rules" },
  { href: "/slide", label: "Slides", note: "15-slide keyboard-driven deck" },
];

const bibtex = `@software{rahaman_energy_optimal_rag_2026,
  author  = {Rahaman, Atikur},
  title   = {Energy-Optimal Retrieval Depth in Retrieval-Augmented Generation},
  year    = {2026},
  version = {0.1.0},
  license = {MIT},
  url     = {https://github.com/Atik203/energy-optimal-rag}
}`;

export default function AboutPage() {
  return (
    <div>
      <PageHero
        index="05"
        eyebrow="About"
        title={
          <>
            A public scaffold, <em>with the failures left in.</em>
          </>
        }
        lede="This site describes a research project that has run a pilot, killed its own headline, and not yet collected confirmatory data. It is intentionally specific about what is not known."
        meta={[
          { label: "Post-pilot MARGINAL", tone: "caution" },
          { label: "v0.1.0", tone: "neutral" },
          { label: "Prereg not frozen", tone: "caution" },
          { label: "No confirmatory results", tone: "dead" },
        ]}
      />

      {/* 01 — Status */}
      <section aria-labelledby="status-heading" className="mt-4">
        <SectionHeading
          index="01"
          eyebrow="Status"
          id="status-heading"
          title={
            <>
              The state of the record, <em>without rounding up.</em>
            </>
          }
          description="The project is an initial public scaffold. The pilot is prior evidence, not part of the confirmatory sample."
        />

        <div className="panel mt-8 overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
            <span className="eyebrow">Project record</span>
            <Chip tone="caution" dot>
              Release v{project.version}
            </Chip>
          </div>
          <dl className="divide-y divide-line">
            {statusRows.map(([label, value]) => (
              <div key={label} className="grid gap-1 px-4 py-3 sm:grid-cols-[190px_1fr] sm:gap-4">
                <dt className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted-foreground">{label}</dt>
                <dd className="text-sm leading-snug">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="mt-4">
          <Callout tone="caution" title="What “post-pilot MARGINAL” means">
            The energy curve is precise and the 2 pp static claim is dead. The 5 pp policy is a
            pilot signal that needs a powered rerun. “MARGINAL” is the honest status, not a
            euphemism for a positive result.
          </Callout>
        </div>
      </section>

      {/* 02 — Author and citation */}
      <section aria-labelledby="author-heading" className="mt-16">
        <SectionHeading
          index="02"
          eyebrow="Author and citation"
          id="author-heading"
          title={
            <>
              Cite the scaffold. <em>Do not cite a result that does not exist.</em>
            </>
          }
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-signal" aria-hidden />
              <h3 className="text-sm font-semibold">Author</h3>
            </div>
            <p className="mt-3 text-lg font-semibold">{project.author}</p>
            <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
              Project team: PI and three collaborators (docs/proposal.md). The repository is the
              public record.
            </p>
            <div className="mt-4 border-t border-line pt-3">
              <p className="eyebrow">Contact</p>
              <a
                href={`${project.repo}/issues`}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-flex items-center gap-1.5 text-sm font-semibold text-signal"
              >
                Open an issue on GitHub
                <ExternalLink className="h-3.5 w-3.5" aria-hidden />
              </a>
            </div>
            <div className="mt-4 border-t border-line pt-3">
              <p className="eyebrow">Paper</p>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                The paper citation will be added when a manuscript is posted. No manuscript exists
                yet.
              </p>
            </div>
          </div>

          <div className="panel overflow-hidden">
            <div className="flex items-center justify-between gap-2 border-b border-line px-4 py-3">
              <span className="eyebrow">Suggested citation</span>
              <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted-foreground">
                From CITATION.cff
              </span>
            </div>
            <pre className="overflow-x-auto bg-panel-soft p-4 font-mono text-[11px] leading-relaxed text-foreground">
              {bibtex}
            </pre>
            <p className="border-t border-line px-4 py-3 text-xs leading-relaxed text-muted-foreground">
              The BibTeX key is a presentation convenience. The canonical metadata is CITATION.cff
              in the repository.
            </p>
          </div>
        </div>
      </section>

      {/* 03 — Policies */}
      <section aria-labelledby="policies-heading" className="mt-16">
        <SectionHeading
          index="03"
          eyebrow="Policies"
          id="policies-heading"
          title={
            <>
              Evidence first. <em>Then prose.</em>
            </>
          }
          description="These policies are not website copy. They are the operating rules the repository uses for results, data, and claims."
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <FileCheck2 className="h-4 w-4 text-signal" aria-hidden />
              <h3 className="text-sm font-semibold">Evidence policy</h3>
            </div>
            <ul className="mt-3 space-y-2">
              {[
                "Every number traces to runs/<run_id>/raw.csv or a registered analysis output.",
                "Pilot numbers are labeled pilot and transcribed from the repository record.",
                "Missing values are omitted or marked TBD. No invented CIs, p-values, run IDs, or sample sizes.",
                "The claims-evidence map is tracked at artifacts/claims_evidence.csv.",
                "A fired gate is reported, not tuned away. No post-hoc gate changes.",
              ].map((item) => (
                <li key={item} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-signal" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-data" aria-hidden />
              <h3 className="text-sm font-semibold">Data policy</h3>
            </div>
            <ul className="mt-3 space-y-2">
              {[
                "Raw SQuAD and HotpotQA text is never committed; data/processed/ is git-ignored.",
                "Tracked: data/manifest.json, data/README.md, runs/registry.csv, artifacts/ledger.csv, artifacts/claims_evidence.csv.",
                "Model weights are never committed. Names, quantization, and digests go in the manifest and registry.",
                "Both upstream datasets are CC BY-SA 4.0; their licenses remain in force.",
                "No private queries, user logs, or scraped personal data are added.",
              ].map((item) => (
                <li key={item} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-data" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-caution" aria-hidden />
              <h3 className="text-sm font-semibold">Claim policy</h3>
            </div>
            <ul className="mt-3 space-y-2">
              {[
                "No universal k*, 2 pp optimum, or 5 pp certification.",
                "No learned-policy gain from the oracle upper bound.",
                "No carbon-optimal claim beyond constant-factor reporting.",
                "No generalization to frontier readers, dense retrievers, or full NQ.",
                "A change to the claim requires a prereg amendment and a decision-log entry.",
              ].map((item) => (
                <li key={item} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-caution" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* 04 — Licenses */}
      <section aria-labelledby="licenses-heading" className="mt-16">
        <SectionHeading
          index="04"
          eyebrow="Licenses"
          id="licenses-heading"
          title={
            <>
              Three licenses, <em>three different objects.</em>
            </>
          }
          description="The code, the documentation, and the upstream datasets do not share a license. The distinction matters for redistribution."
        />

        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          {[
            {
              icon: Scale,
              label: "Code",
              value: "MIT",
              detail: "© 2026 Atikur Rahaman and contributors.",
              href: `${project.repo}/blob/main/LICENSE`,
            },
            {
              icon: ScrollText,
              label: "Docs and derived data",
              value: "CC BY 4.0",
              detail: "Site text and figures follow the documentation license.",
              href: `${project.repo}/blob/main/LICENSE-DOCS`,
            },
            {
              icon: Globe,
              label: "Upstream datasets",
              value: "CC BY-SA 4.0",
              detail: "SQuAD and HotpotQA remain under their own licenses. No raw text is redistributed.",
              href: `${project.repo}/blob/main/DATA_LICENSE.md`,
            },
          ].map((license) => {
            const Icon = license.icon;
            return (
              <div key={license.label} className="panel flex flex-col p-5">
                <div className="flex items-center justify-between gap-2">
                  <Icon className="h-4 w-4 text-data" aria-hidden />
                  <Chip tone="neutral">{license.label}</Chip>
                </div>
                <p className="mt-4 font-mono text-2xl font-medium text-signal">{license.value}</p>
                <p className="mt-2 flex-1 text-xs leading-relaxed text-muted-foreground">{license.detail}</p>
                <a
                  href={license.href}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-[0.12em] text-muted-foreground hover:text-foreground"
                >
                  Read license <ExternalLink className="h-3 w-3" aria-hidden />
                </a>
              </div>
            );
          })}
        </div>

        <div className="mt-4 flex gap-3 border-l-2 border-caution pl-4">
          <Lock className="mt-0.5 h-4 w-4 shrink-0 text-caution" aria-hidden />
          <p className="text-sm leading-relaxed text-muted-foreground">
            Site fonts are OFL-licensed and served locally: Newsreader, Instrument Sans, and
            JetBrains Mono. No font is requested from a third-party host at runtime.
          </p>
        </div>
      </section>

      {/* 05 — Links and site map */}
      <section aria-labelledby="links-heading" className="mt-16">
        <SectionHeading
          index="05"
          eyebrow="Links and site map"
          id="links-heading"
          title={
            <>
              The public record <em>and the local map.</em>
            </>
          }
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="panel p-5">
            <div className="flex items-center gap-2">
              <Github className="h-4 w-4 text-signal" aria-hidden />
              <h3 className="text-sm font-semibold">Repository</h3>
            </div>
            <ul className="mt-3 grid grid-cols-1 gap-x-4 gap-y-1.5 sm:grid-cols-2">
              {repoLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {link.label}
                    <ExternalLink className="h-2.5 w-2.5" aria-hidden />
                  </a>
                </li>
              ))}
            </ul>
            <p className="mt-4 border-t border-line pt-3 font-mono text-[9px] uppercase tracking-[0.1em] text-muted-foreground">
              Repository: Atik203/energy-optimal-rag
            </p>
          </div>

          <div className="panel overflow-hidden">
            <div className="border-b border-line px-4 py-3">
              <span className="eyebrow">Site map</span>
            </div>
            <ul className="divide-y divide-line">
              {siteMap.map((route) => (
                <li key={route.href}>
                  <Link
                    href={route.href}
                    className="group flex items-start justify-between gap-3 px-4 py-3 transition-colors hover:bg-panel-soft"
                  >
                    <div>
                      <p className="text-sm font-semibold">{route.label}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">{route.note}</p>
                    </div>
                    <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground group-hover:text-signal" aria-hidden />
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* 06 — Site behavior */}
      <section aria-labelledby="site-heading" className="mt-16">
        <div className="instrument p-6 sm:p-8">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div>
              <p className="inst-label">Site behavior</p>
              <h2 id="site-heading" className="display-title mt-3 text-2xl text-[#eef3e5] sm:text-3xl">
                Static, self-contained, no telemetry.
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-[#8aa294]">
                This site is a static Next.js build. It sets no analytics cookies, makes no remote
                font or image requests, and runs no runtime fetch calls. The only client-side
                storage is the theme preference in localStorage.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { icon: Lock, label: "No analytics" },
                { icon: Globe, label: "No remote assets" },
                { icon: FileText, label: "No raw data" },
                { icon: Presentation, label: "Keyboard deck" },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.label} className="border border-[rgba(200,240,79,0.16)] p-3">
                    <Icon className="h-4 w-4 text-[#c8f04f]" aria-hidden />
                    <p className="mt-2 font-mono text-[9px] uppercase tracking-[0.12em] text-[#8aa294]">
                      {item.label}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <SourceNote>
          Source: README.md, CITATION.cff, docs/DATA_CARD.md, prereg/PREREGISTRATION.md,
          docs/DECISIONS.md, ROADMAP.md. Last updated {project.updated}.
        </SourceNote>
      </section>
    </div>
  );
}
