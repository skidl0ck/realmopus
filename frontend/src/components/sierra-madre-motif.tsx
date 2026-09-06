/**
 * The Sierra Madre horizon - RealmOpus's one signature visual motif (see
 * docs/design.md section 5). Deliberately a long, layered, asymmetric
 * ridgeline rather than a symmetrical triangle-peak icon, so it reads as an
 * actual place rather than generic "mountain" clipart. Three layers create
 * depth: a faint far ridge, a mid ridge, and a slightly stronger near ridge.
 *
 * Usage: large + low-opacity behind a hero headline, or small + as a thin
 * footer divider - same component, different size/className.
 */
export function SierraMadreMotif({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 1200 220"
      preserveAspectRatio="none"
      className={className}
      aria-hidden="true"
    >
      {/* far ridge - faintest, sets the receding backdrop */}
      <path
        d="M0,140 L60,128 L130,134 L190,110 L260,120 L330,96 L410,112 L480,90 L560,104 L640,82 L720,98 L800,78 L880,94 L960,86 L1040,100 L1120,88 L1200,102 L1200,220 L0,220 Z"
        fill="var(--color-accent-600)"
        opacity="0.35"
      />
      {/* mid ridge */}
      <path
        d="M0,168 L70,150 L140,160 L210,132 L290,146 L360,118 L440,138 L510,108 L590,128 L670,100 L750,122 L830,96 L900,116 L980,104 L1060,124 L1130,108 L1200,120 L1200,220 L0,220 Z"
        fill="var(--color-accent-600)"
        opacity="0.6"
      />
      {/* near ridge - strongest, foreground */}
      <path
        d="M0,200 L90,178 L170,190 L240,156 L320,174 L400,140 L480,166 L550,128 L630,152 L710,116 L790,146 L870,112 L950,140 L1030,122 L1110,148 L1200,130 L1200,220 L0,220 Z"
        fill="var(--color-accent-600)"
        opacity="1"
      />
    </svg>
  );
}