import type { Metadata } from "next";
import { SlideDeck } from "@/components/slides/deck";

export const metadata: Metadata = {
  title: "Project Proposal",
  description:
    "EEE 4261: Green Computing, Section C — Energy-Optimal Retrieval Depth in Retrieval-Augmented Generation.",
  robots: {
    index: false,
    follow: false,
  },
};

type SlidePageProps = {
  searchParams: Promise<{ slide?: string | string[] }>;
};

export default async function SlidePage({ searchParams }: SlidePageProps) {
  const params = await searchParams;
  const raw = Array.isArray(params.slide) ? params.slide[0] : params.slide;
  const parsed = Number.parseInt(raw ?? "1", 10);
  const initialSlide = Number.isFinite(parsed) ? parsed : 1;

  return <SlideDeck initialSlide={initialSlide} />;
}
