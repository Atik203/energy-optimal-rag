import type { Metadata, Viewport } from "next";
import Script from "next/script";
import localFont from "next/font/local";
import "./globals.css";

const instrument = localFont({
  src: [
    { path: "./fonts/instrument-sans-latin.woff2", weight: "400 700", style: "normal" },
    { path: "./fonts/instrument-sans-latin-italic.woff2", weight: "400 700", style: "italic" },
  ],
  variable: "--font-instrument",
  display: "swap",
  preload: true,
});

const newsreader = localFont({
  src: [
    { path: "./fonts/newsreader-latin.woff2", weight: "200 800", style: "normal" },
    { path: "./fonts/newsreader-latin-italic.woff2", weight: "200 800", style: "italic" },
  ],
  variable: "--font-newsreader",
  display: "swap",
  preload: true,
});

const jetbrains = localFont({
  src: [
    { path: "./fonts/jetbrains-mono-latin.woff2", weight: "100 800", style: "normal" },
    { path: "./fonts/jetbrains-mono-latin-italic.woff2", weight: "100 800", style: "italic" },
  ],
  variable: "--font-jetbrains",
  display: "swap",
  preload: false,
});

export const metadata: Metadata = {
  title: {
    default: "Energy Observatory \u2014 Joules per Correct Answer",
    template: "%s \u2014 Energy Observatory",
  },
  description:
    "A measurement study of retrieval depth in retrieval-augmented generation: joules per correct answer, a margin-indexed decision rule, and the energy cost of finding it. Post-pilot MARGINAL; no confirmatory results.",
  applicationName: "Energy Observatory",
  authors: [{ name: "Atikur Rahaman" }],
  creator: "Atikur Rahaman",
  category: "research",
  keywords: [
    "retrieval-augmented generation",
    "retrieval depth",
    "energy efficiency",
    "joules per correct answer",
    "green AI",
    "measurement",
    "reproducibility",
  ],
  other: {
    "darkreader-lock": "true",
  },
  openGraph: {
    title: "Energy Observatory \u2014 Joules per Correct Answer",
    description:
      "Retrieval depth, measured in joules per correct answer. Pilot evidence, a dead 2 pp claim, and a powered rerun design. No confirmatory results.",
    siteName: "Energy Observatory",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#07110d" },
    { media: "(prefers-color-scheme: light)", color: "#f6f2e6" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${instrument.variable} ${newsreader.variable} ${jetbrains.variable} font-sans min-h-dvh flex flex-col bg-background text-foreground antialiased`}
      >
        <Script id="energy-observatory-theme" strategy="beforeInteractive">
          {`(function(){try{var t=localStorage.getItem("eor-theme");if(t==="light"){document.documentElement.classList.remove("dark")}else{document.documentElement.classList.add("dark")}}catch(e){document.documentElement.classList.add("dark")}})();`}
        </Script>
        {children}
      </body>
    </html>
  );
}
