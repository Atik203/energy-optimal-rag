import type { ReactNode } from "react";

export function MathLine({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex flex-wrap items-center gap-x-[0.18em] gap-y-1 align-middle ${className}`}
    >
      {children}
    </span>
  );
}

export function MathSub({ children }: { children: ReactNode }) {
  return <sub className="text-[0.62em] leading-none">{children}</sub>;
}

export function MathSup({ children }: { children: ReactNode }) {
  return <sup className="text-[0.62em] leading-none">{children}</sup>;
}

export function MathFrac({ num, den }: { num: ReactNode; den: ReactNode }) {
  return (
    <span className="mx-[0.12em] inline-flex min-w-[1.2em] flex-col items-center justify-center align-middle leading-none">
      <span className="px-[0.3em] pb-[0.14em]">{num}</span>
      <span className="h-px w-full bg-current" />
      <span className="px-[0.3em] pt-[0.14em]">{den}</span>
    </span>
  );
}
