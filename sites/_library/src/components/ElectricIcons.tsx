import type { ReactNode, SVGProps } from "react";

/**
 * Electrician icons lucide doesn't have, drawn on lucide's 24px grid with
 * the same round caps and joins so they sit in the same set. Irish kit:
 * the socket is the 3-pin Type G, not a two-pin or US outlet.
 */
type P = SVGProps<SVGSVGElement> & { strokeWidth?: number };

function Base({ children, strokeWidth = 1.6, ...rest }: P & { children: ReactNode }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" {...rest}>
      {children}
    </svg>
  );
}

/** Irish/UK 3-pin socket: vertical earth slot over two flat slots. */
export const SocketIcon = (p: P) => (
  <Base {...p}>
    <rect x="3.5" y="3.5" width="17" height="17" rx="2.5" />
    <path d="M12 7.5v3.5" />
    <path d="M7.5 15h2.5" />
    <path d="M14 15h2.5" />
  </Base>
);

/** Consumer unit: the enclosure, its label strip and a row of breakers. */
export const FuseBoardIcon = (p: P) => (
  <Base {...p}>
    <rect x="2.5" y="4" width="19" height="16" rx="1.5" />
    <path d="M2.5 8h19" />
    <rect x="5" y="10.5" width="2.4" height="6" rx="0.5" />
    <rect x="9" y="10.5" width="2.4" height="6" rx="0.5" />
    <rect x="13" y="10.5" width="2.4" height="6" rx="0.5" />
    <rect x="17" y="10.5" width="2.4" height="6" rx="0.5" />
    <path d="M6.2 12v1.4M10.2 12v1.4M14.2 12v1.4M18.2 12v1.4" />
  </Base>
);

/** Wall-mounted EV charger with its cable and plug. */
export const EvChargerIcon = (p: P) => (
  <Base {...p}>
    <rect x="3.5" y="2.5" width="10" height="13" rx="2" />
    <circle cx="8.5" cy="7.5" r="2" />
    <path d="M6.5 12h4" />
    <path d="M8.5 15.5v1.5a3.5 3.5 0 0 0 3.5 3.5h4" />
    <rect x="16" y="17.5" width="4.5" height="5" rx="1" />
  </Base>
);

/** Pendant light: flex, shade and the light falling from it. */
export const PendantIcon = (p: P) => (
  <Base {...p}>
    <path d="M12 2v5" />
    <path d="M9 7h6l3.5 7h-13z" />
    <path d="M10 14a2 2 0 0 0 4 0" />
    <path d="M12 18.5v2.5M7 17.2l-1.4 1.6M17 17.2l1.4 1.6" />
  </Base>
);

/** Smoke/heat alarm seen from below, with its indicator. */
export const SmokeAlarmIcon = (p: P) => (
  <Base {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <circle cx="12" cy="12" r="3.5" />
    <circle cx="16.8" cy="7.2" r="0.6" fill="currentColor" />
  </Base>
);

/** Light switch plate with its rocker. */
export const LightSwitchIcon = (p: P) => (
  <Base {...p}>
    <rect x="5" y="3" width="14" height="18" rx="2" />
    <rect x="9.5" y="7.5" width="5" height="9" rx="1" />
    <path d="M9.5 11h5" />
  </Base>
);

/** Multimeter: screen, dial and probe sockets. */
export const TesterIcon = (p: P) => (
  <Base {...p}>
    <rect x="6" y="2.5" width="12" height="19" rx="2" />
    <rect x="8.5" y="5" width="7" height="4" rx="0.5" />
    <circle cx="12" cy="14" r="2.5" />
    <path d="M12 14l1.6-1.6" />
    <circle cx="9.5" cy="19" r="0.5" fill="currentColor" />
    <circle cx="14.5" cy="19" r="0.5" fill="currentColor" />
  </Base>
);

/** Rewiring: three cables run into a back box. */
export const RewireIcon = (p: P) => (
  <Base {...p}>
    <rect x="14" y="7.5" width="7.5" height="9" rx="1" />
    <path d="M2 5.5c5.5 0 6 4.5 12 4.5" />
    <path d="M2 12h12" />
    <path d="M2 18.5c5.5 0 6-4.5 12-4.5" />
  </Base>
);
