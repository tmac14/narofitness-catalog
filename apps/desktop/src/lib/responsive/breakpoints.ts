/**
 * UX 3.0 canonical breakpoint ranges (Phase 0).
 * Aligned with tailwind.config.cjs semantic screens and CSS tokens.
 *
 * Boundaries are inclusive on both ends per band; bands are contiguous with no gaps.
 */

export const BREAKPOINT_PX = {
  mobileMin: 0,
  mobileMax: 639,
  tabletMin: 640,
  tabletMax: 1023,
  desktopMin: 1024,
  desktopMax: 1279,
  wideMin: 1280,
} as const;

export type Platform = "mobile" | "tablet" | "desktop" | "wide";

/** Tailwind semantic screen definitions — must stay aligned with tailwind.config.cjs */
export const TAILWIND_SEMANTIC_SCREENS = {
  /** max-width 639px — mobile band only (0–639px) */
  mobile: { max: `${BREAKPOINT_PX.mobileMax}px` },
  /** min 640px and max 1023px — tablet band only */
  tablet: { min: `${BREAKPOINT_PX.tabletMin}px`, max: `${BREAKPOINT_PX.tabletMax}px` },
  /** min 1024px and max 1279px — desktop band only */
  desktop: { min: `${BREAKPOINT_PX.desktopMin}px`, max: `${BREAKPOINT_PX.desktopMax}px` },
  /** min-width 1280px — wide band and above (1280px+) */
  wide: `${BREAKPOINT_PX.wideMin}px`,
} as const;

/** Maps legacy Tailwind min-width defaults to platform entry points (not closed ranges). */
export const LEGACY_TAILWIND_MIN_WIDTH_PX = {
  sm: BREAKPOINT_PX.tabletMin,
  md: 768,
  lg: BREAKPOINT_PX.desktopMin,
  xl: BREAKPOINT_PX.wideMin,
} as const;

export const PLATFORM_ORDER: readonly Platform[] = ["mobile", "tablet", "desktop", "wide"];
