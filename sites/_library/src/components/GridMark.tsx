import { cn } from "@/lib/cn";

/** A "+" registration mark for grid corners and rule crossings. Decorative. */
export function GridMark({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 12 12" className={cn("h-3 w-3", className)} fill="none" stroke="currentColor" strokeWidth="1.25">
      <path d="M6 0v12M0 6h12" />
    </svg>
  );
}
