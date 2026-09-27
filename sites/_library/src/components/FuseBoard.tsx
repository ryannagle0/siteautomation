import { cn } from "@/lib/cn";

/**
 * A consumer unit drawn as a line illustration: main switch, RCD and a row
 * of breakers on the DIN rail, a circuit chart underneath and the three
 * cable cores feeding in from above (they run off the top of the section).
 * On load the breakers flip on one by one, main switch first; with reduced
 * motion it's simply on. Every colour is a token; ink comes from
 * currentColor so it works on light and dark presets.
 */
const MCBS = 6;

function Toggle({ x, w, i, accent = false }: { x: number; w: number; i: number; accent?: boolean }) {
  const slotW = accent ? 40 : 18;
  const knobW = accent ? 32 : 12;
  const cx = x + w / 2;
  return (
    <g>
      <rect x={cx - slotW / 2} y={148} width={slotW} height={46} rx={4} fill="var(--surface-2)" stroke="currentColor" strokeWidth={1.5} />
      <rect className="fb-toggle" style={{ animationDelay: `${i === 0 ? 150 : 260 + i * 110}ms` }}
        x={cx - knobW / 2} y={152} width={knobW} height={22} rx={3}
        fill={accent ? "var(--accent)" : "currentColor"} stroke="currentColor" strokeWidth={accent ? 1.5 : 0} />
    </g>
  );
}

function Device({ x, w, i, accent, rcd }: { x: number; w: number; i: number; accent?: boolean; rcd?: boolean }) {
  return (
    <g>
      <rect x={x} y={98} width={w} height={146} rx={5} fill="var(--surface)" stroke="currentColor" strokeWidth={2} />
      <path d={`M${x} 122h${w}`} stroke="currentColor" strokeWidth={1.2} opacity={0.5} />
      <Toggle x={x} w={w} i={i} accent={accent} />
      {/* The rating printed under the handle. */}
      <path d={`M${x + w / 2 - 7} 214h14`} stroke="currentColor" strokeWidth={2} opacity={0.55} />
      {rcd && <circle cx={x + w - 14} cy={110} r={4.5} fill="var(--surface-2)" stroke="currentColor" strokeWidth={1.5} />}
      {accent && <circle className="fb-led" cx={x + 14} cy={110} r={4} fill="var(--accent)" />}
    </g>
  );
}

export function FuseBoard({ className, title }: { className?: string; title?: string }) {
  const mcbX = (i: number) => 204 + i * 36;
  const cables = [
    { x: 146, stroke: "var(--wire-live)" },
    { x: 168, stroke: "var(--wire-neutral)" },
    { x: 190, stroke: "url(#fb-earth)" },
  ];
  return (
    <svg viewBox="0 0 480 380" className={cn("fuse-board overflow-visible", className)}
      role={title ? "img" : undefined} aria-label={title} aria-hidden={title ? undefined : true}>
      <defs>
        <pattern id="fb-earth" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
          <rect width="8" height="16" fill="var(--wire-earth-a)" />
          <rect x="8" width="8" height="16" fill="var(--wire-earth-b)" />
        </pattern>
      </defs>

      {/* Supply cables, dropping in from above the section. */}
      {cables.map((c, i) => (
        <path key={i} d={`M${c.x + (i - 1) * 26} -900 V-60 C${c.x + (i - 1) * 26} -20 ${c.x} -20 ${c.x} 20 V34`}
          fill="none" stroke={c.stroke} strokeWidth={8} strokeLinecap="round" />
      ))}
      {cables.map((c, i) => (
        <rect key={i} x={c.x - 9} y={22} width={18} height={12} rx={2} fill="var(--surface-2)" stroke="currentColor" strokeWidth={1.5} />
      ))}

      {/* Enclosure, screws and the cover's window. */}
      <rect x={20} y={32} width={440} height={330} rx={16} fill="var(--surface)" stroke="currentColor" strokeWidth={2.5} />
      {[[42, 54], [438, 54], [42, 340], [438, 340]].map(([cx, cy], i) => (
        <g key={i}>
          <circle cx={cx} cy={cy} r={5} fill="var(--surface-2)" stroke="currentColor" strokeWidth={1.5} />
          <path d={`M${cx - 3} ${cy}h6`} stroke="currentColor" strokeWidth={1.5} />
        </g>
      ))}
      <rect x={52} y={74} width={376} height={228} rx={8} fill="var(--bg)" stroke="currentColor" strokeWidth={1.5} />

      {/* DIN rail, visible between the devices. */}
      <rect x={52} y={164} width={376} height={12} fill="var(--surface-2)" stroke="currentColor" strokeWidth={1.2} />

      <Device x={64} w={64} i={0} accent />
      <Device x={134} w={64} i={1} rcd />
      {Array.from({ length: MCBS }, (_, i) => <Device key={i} x={mcbX(i)} w={32} i={i + 2} />)}

      {/* Circuit chart: a ruled strip with pencilled labels. */}
      <rect x={64} y={256} width={352} height={30} rx={3} fill="var(--surface)" stroke="currentColor" strokeWidth={1.5} />
      {[134, 204, ...Array.from({ length: MCBS - 1 }, (_, i) => mcbX(i + 1) - 2)].map((x, i) => (
        <path key={i} d={`M${x} 256v30`} stroke="currentColor" strokeWidth={1} opacity={0.5} />
      ))}
      {[76, 146, ...Array.from({ length: MCBS }, (_, i) => mcbX(i) + 6)].map((x, i) => (
        <path key={i} d={`M${x} 273c3-4 6 3 9-1s5 2 ${i < 2 ? 18 : 6}-1`} fill="none" stroke="currentColor" strokeWidth={1.4} opacity={0.6} />
      ))}

      {/* The standard electrical-hazard sign on the cover. */}
      <path d="M52 348 L70 316 L88 348 Z" fill="var(--wire-earth-b)" stroke="var(--hazard-ink)" strokeWidth={2} strokeLinejoin="round" />
      <path d="M72 324 L65 336 H71 L67 344 L76 331 H70 Z" fill="var(--hazard-ink)" />
    </svg>
  );
}
