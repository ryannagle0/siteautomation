import { cn } from "@/lib/cn";

/**
 * Three cable cores laid side by side: brown live, blue neutral, green and
 * yellow earth. Decorative only; used once or twice a page as a rule.
 */
export function WireStripe({ className }: { className?: string }) {
  return (
    <div aria-hidden="true" className={cn("flex flex-col gap-[3px]", className)}>
      <span className="block h-[4px] rounded-full" style={{ background: "var(--wire-live)" }} />
      <span className="block h-[4px] rounded-full" style={{ background: "var(--wire-neutral)" }} />
      <span className="block h-[4px] rounded-full"
        style={{ background: "repeating-linear-gradient(-60deg, var(--wire-earth-a) 0 10px, var(--wire-earth-b) 10px 20px)" }} />
    </div>
  );
}
