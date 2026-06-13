import { BREAKPOINT_PX, PLATFORM_ORDER, type Platform } from "./breakpoints";

/** Classify a viewport width (px) into exactly one UX 3.0 platform band. */
export function classifyPlatformWidth(widthPx: number): Platform {
  if (!Number.isFinite(widthPx) || widthPx < BREAKPOINT_PX.mobileMin) {
    return "mobile";
  }
  if (widthPx <= BREAKPOINT_PX.mobileMax) return "mobile";
  if (widthPx <= BREAKPOINT_PX.tabletMax) return "tablet";
  if (widthPx <= BREAKPOINT_PX.desktopMax) return "desktop";
  return "wide";
}

/** True when width falls inside the closed mobile band [0, 639]. */
export function isMobileWidth(widthPx: number): boolean {
  return classifyPlatformWidth(widthPx) === "mobile";
}

/** True when width falls inside the closed tablet band [640, 1023]. */
export function isTabletWidth(widthPx: number): boolean {
  return classifyPlatformWidth(widthPx) === "tablet";
}

/** True when width falls inside the closed desktop band [1024, 1279]. */
export function isDesktopWidth(widthPx: number): boolean {
  return classifyPlatformWidth(widthPx) === "desktop";
}

/** True when width is in the wide band [1280, ∞). */
export function isWideWidth(widthPx: number): boolean {
  return classifyPlatformWidth(widthPx) === "wide";
}

/**
 * Validates that platform bands are contiguous with no gaps or overlaps.
 * Throws if invariant is violated — for tests and startup assertions only.
 */
export function assertPlatformBandsContiguous(): void {
  const boundaries = [
    BREAKPOINT_PX.mobileMax + 1,
    BREAKPOINT_PX.tabletMax + 1,
    BREAKPOINT_PX.desktopMax + 1,
  ];

  for (let i = 0; i < boundaries.length; i++) {
    const atBoundary = boundaries[i];
    const prevPlatform = classifyPlatformWidth(atBoundary - 1);
    const nextPlatform = classifyPlatformWidth(atBoundary);
    const expectedNext = PLATFORM_ORDER[i + 1];
    if (nextPlatform !== expectedNext) {
      throw new Error(
        `Platform band gap at ${atBoundary}px: expected ${expectedNext}, got ${nextPlatform}`,
      );
    }
    if (i === 0 && prevPlatform !== "mobile") {
      throw new Error(`Expected mobile before ${atBoundary}px, got ${prevPlatform}`);
    }
  }
}
