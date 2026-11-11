"use client";

import { useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";

const THEME_KEY = "eor-theme";

function subscribe(onChange: () => void) {
  window.addEventListener("storage", onChange);
  return () => window.removeEventListener("storage", onChange);
}

function getSnapshot(): string {
  try {
    return localStorage.getItem(THEME_KEY) ?? "dark";
  } catch {
    return "dark";
  }
}

export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, getSnapshot, () => "dark");
  const dark = theme === "dark";

  const toggle = () => {
    const next = dark ? "light" : "dark";
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      // Storage is optional; the document class still changes for this visit.
    }
    document.documentElement.classList.toggle("dark", next === "dark");
    window.dispatchEvent(new Event("storage"));
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      aria-pressed={dark}
      title={dark ? "Switch to light theme" : "Switch to dark theme"}
      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[3px] border border-line bg-panel/60 text-muted-foreground transition-colors hover:border-line-strong hover:text-foreground"
    >
      {dark ? <Sun className="h-4 w-4" aria-hidden /> : <Moon className="h-4 w-4" aria-hidden />}
    </button>
  );
}
