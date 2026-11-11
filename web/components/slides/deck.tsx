"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Home,
  Maximize2,
  Minimize2,
  Presentation,
} from "lucide-react";
import { SLIDES } from "@/components/slides/slides";

function clamp(value: number, max: number) {
  return Math.min(max, Math.max(0, value));
}

/**
 * Projector-safe 16:9 deck.
 *
 * Keyboard: ← → PageUp/PageDown Space Home End, F fullscreen (Esc exits).
 * Deep link: /slide?slide=7. The URL is updated with replaceState, not a
 * router navigation, so slide changes stay instant and do not create history.
 */
export function SlideDeck({ initialSlide = 1 }: { initialSlide?: number }) {
  const total = SLIDES.length;
  const [index, setIndex] = useState(() => clamp(initialSlide - 1, total - 1));
  const [isFs, setIsFs] = useState(false);
  const indexRef = useRef(index);
  const containerRef = useRef<HTMLDivElement>(null);
  const touchX = useRef<number | null>(null);

  const goTo = useCallback(
    (next: number) => {
      const clamped = clamp(next, total - 1);
      if (clamped === indexRef.current) return;
      indexRef.current = clamped;
      setIndex(clamped);
      const url = new URL(window.location.href);
      url.searchParams.set("slide", String(clamped + 1));
      window.history.replaceState(null, "", url);
    },
    [total],
  );

  const toggleFullscreen = useCallback(() => {
    const element = containerRef.current;
    if (!element) return;
    if (!document.fullscreenElement) {
      element.requestFullscreen?.().catch(() => {});
    } else {
      document.exitFullscreen?.().catch(() => {});
    }
  }, []);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if ((event.key === " " || event.key === "Enter") && target?.closest("button, a")) {
        return;
      }

      switch (event.key) {
        case "ArrowRight":
        case "PageDown":
        case " ":
          event.preventDefault();
          goTo(indexRef.current + 1);
          break;
        case "ArrowLeft":
        case "PageUp":
          event.preventDefault();
          goTo(indexRef.current - 1);
          break;
        case "Home":
          event.preventDefault();
          goTo(0);
          break;
        case "End":
          event.preventDefault();
          goTo(total - 1);
          break;
        case "f":
        case "F":
          event.preventDefault();
          toggleFullscreen();
          break;
        default:
          break;
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goTo, toggleFullscreen, total]);

  useEffect(() => {
    const onFullscreenChange = () => setIsFs(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, []);

  const Current = SLIDES[index].Component;
  const progress = ((index + 1) / total) * 100;

  return (
    <div ref={containerRef} className="fixed inset-0 z-[100] flex flex-col bg-[#07100c]">
      <div
        className="relative flex min-h-0 flex-1 items-center justify-center overflow-hidden p-2 sm:p-4"
        onTouchStart={(event) => {
          touchX.current = event.touches[0]?.clientX ?? null;
        }}
        onTouchEnd={(event) => {
          if (touchX.current === null) return;
          const end = event.changedTouches[0]?.clientX ?? touchX.current;
          const delta = end - touchX.current;
          touchX.current = null;
          if (Math.abs(delta) > 40) {
            goTo(indexRef.current + (delta < 0 ? 1 : -1));
          }
        }}
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 z-10 h-[2px] bg-white/10">
          <div className="h-full bg-[#c8f04f]" style={{ width: `${progress}%` }} />
        </div>

        <div
          className="relative overflow-hidden border border-[#c8f04f]/25 shadow-[0_24px_80px_rgba(0,0,0,0.55)]"
          style={{
            width: "min(calc(100vw - 2rem), calc((100dvh - 6rem) * 1.7778))",
            maxWidth: "100%",
            maxHeight: "100%",
            aspectRatio: "16 / 9",
            containerType: "size",
          }}
          role="region"
          aria-roledescription="slide"
          aria-label={`Slide ${index + 1} of ${total}: ${SLIDES[index].title}`}
        >
          <div key={index} className="h-full w-full animate-fade">
            <Current index={index} total={total} />
          </div>
        </div>

        <p className="sr-only" aria-live="polite">
          Slide {index + 1} of {total}: {SLIDES[index].title}
        </p>
      </div>

      <div className="flex h-14 shrink-0 items-center gap-2 border-t border-white/10 bg-[#07100c] px-2 text-white/70 sm:px-4">
        <Link
          href="/"
          aria-label="Back to the site"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[2px] border border-white/10 transition-colors hover:border-[#c8f04f]/50 hover:text-white"
        >
          <Home className="h-4 w-4" aria-hidden />
        </Link>

        <div className="hidden items-center gap-2 sm:flex">
          <Presentation className="h-4 w-4 text-[#c8f04f]" aria-hidden />
          <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-white/45">
            Energy Observatory / Deck
          </span>
        </div>

        <div className="flex items-center">
          <button
            type="button"
            onClick={() => goTo(indexRef.current - 1)}
            disabled={index === 0}
            aria-label="Previous slide"
            className="flex h-8 w-8 items-center justify-center rounded-[2px] text-white/70 transition-colors hover:bg-white/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden />
          </button>
          <button
            type="button"
            onClick={() => goTo(indexRef.current + 1)}
            disabled={index === total - 1}
            aria-label="Next slide"
            className="flex h-8 w-8 items-center justify-center rounded-[2px] text-white/70 transition-colors hover:bg-white/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
          >
            <ChevronRight className="h-4 w-4" aria-hidden />
          </button>
        </div>

        <div className="flex min-w-0 flex-1 items-center gap-3">
          <div className="relative h-1 flex-1 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-[#c8f04f] transition-[width] duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="shrink-0 font-mono text-[10px] tabular-nums text-white/65">
            {String(index + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
          </span>
        </div>

        <span className="hidden font-mono text-[9px] uppercase tracking-[0.14em] text-white/35 md:inline">
          ← → · space · F
        </span>

        <button
          type="button"
          onClick={toggleFullscreen}
          aria-label={isFs ? "Exit fullscreen" : "Enter fullscreen"}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[2px] border border-white/10 transition-colors hover:border-[#c8f04f]/50 hover:text-white"
        >
          {isFs ? <Minimize2 className="h-4 w-4" aria-hidden /> : <Maximize2 className="h-4 w-4" aria-hidden />}
        </button>
      </div>
    </div>
  );
}
