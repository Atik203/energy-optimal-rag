"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Github, Menu, Presentation, X } from "lucide-react";
import { navItems, project } from "@/lib/project-data";
import { cn } from "@/lib/cn";
import { ObservatoryMark } from "@/components/observatory-mark";
import { ThemeToggle } from "@/components/theme-toggle";

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-background/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1240px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          aria-label="Energy Observatory home"
          className="group flex min-w-0 items-center gap-3"
        >
          <ObservatoryMark className="h-9 w-9" />
          <span className="flex min-w-0 flex-col leading-none">
            <span className="display-title truncate text-[1.15rem] tracking-[-0.02em]">
              Energy Observatory
            </span>
            <span className="mt-1 truncate font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">
              {project.shortName} / Retrieval depth
            </span>
          </span>
        </Link>

        <nav aria-label="Main" className="hidden items-center gap-4 lg:flex">
          {navItems.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative flex h-16 items-center gap-1.5 border-b-2 px-0.5 text-[0.86rem] font-medium transition-colors",
                  active
                    ? "border-signal text-foreground"
                    : "border-transparent text-muted-foreground hover:border-line-strong hover:text-foreground",
                )}
              >
                <span
                  className={cn(
                    "font-mono text-[9px] tracking-[0.1em]",
                    active ? "text-signal" : "text-muted-foreground/60",
                  )}
                >
                  {item.index}
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex shrink-0 items-center gap-2">
          <span className="hidden items-center gap-2 rounded-[2px] border border-caution/30 bg-caution/10 px-2.5 py-1.5 font-mono text-[9px] uppercase tracking-[0.14em] text-caution xl:inline-flex">
            <span className="h-1.5 w-1.5 animate-blink rounded-full bg-caution" aria-hidden />
            {project.status}
          </span>

          <Link
            href="/slide"
            className="hidden h-9 items-center gap-2 rounded-[3px] border border-line-strong px-3 font-mono text-[10px] uppercase tracking-[0.14em] text-foreground transition-colors hover:border-signal hover:text-signal sm:inline-flex"
          >
            <Presentation className="h-3.5 w-3.5" aria-hidden />
            Deck
          </Link>

          <a
            href={project.repo}
            target="_blank"
            rel="noreferrer"
            aria-label="Open the repository on GitHub"
            className="hidden h-9 w-9 items-center justify-center rounded-[3px] border border-line bg-panel/60 text-muted-foreground transition-colors hover:border-line-strong hover:text-foreground sm:flex"
          >
            <Github className="h-4 w-4" aria-hidden />
          </a>

          <ThemeToggle />

          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            aria-label={open ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={open}
            aria-controls="mobile-navigation"
            className="flex h-9 w-9 items-center justify-center rounded-[3px] border border-line bg-panel/60 text-muted-foreground transition-colors hover:text-foreground lg:hidden"
          >
            {open ? <X className="h-4.5 w-4.5" aria-hidden /> : <Menu className="h-4.5 w-4.5" aria-hidden />}
          </button>
        </div>
      </div>

      {open && (
        <nav
          id="mobile-navigation"
          aria-label="Main (mobile)"
          className="border-t border-line bg-background/95 px-4 pb-4 pt-2 backdrop-blur-xl lg:hidden"
        >
          <ul className="divide-y divide-line">
            {navItems.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    onClick={() => setOpen(false)}
                    className={cn(
                      "flex items-center gap-3 py-3 text-base font-medium",
                      active ? "text-signal" : "text-muted-foreground",
                    )}
                  >
                    <span className="font-mono text-[10px] tracking-[0.12em]">{item.index}</span>
                    {item.label}
                  </Link>
                </li>
              );
            })}
            <li>
              <Link href="/slide" onClick={() => setOpen(false)} className="flex items-center gap-3 py-3 text-base font-medium text-muted-foreground">
                <Presentation className="h-4 w-4" aria-hidden />
                Slides
              </Link>
            </li>
            <li>
              <a
                href={project.repo}
                target="_blank"
                rel="noreferrer"
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 py-3 text-base font-medium text-muted-foreground"
              >
                <Github className="h-4 w-4" aria-hidden />
                Repository
              </a>
            </li>
          </ul>
          <p className="mt-3 border-t border-line pt-3 font-mono text-[10px] uppercase tracking-[0.14em] text-caution">
            {project.status} · No confirmatory results
          </p>
        </nav>
      )}
    </header>
  );
}
