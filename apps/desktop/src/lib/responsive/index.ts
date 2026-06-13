export {
  BREAKPOINT_PX,
  LEGACY_TAILWIND_MIN_WIDTH_PX,
  PLATFORM_ORDER,
  TAILWIND_SEMANTIC_SCREENS,
  type Platform,
} from "./breakpoints";
export {
  assertPlatformBandsContiguous,
  classifyPlatformWidth,
  isDesktopWidth,
  isMobileWidth,
  isTabletWidth,
  isWideWidth,
} from "./platform";
export {
  allowsHorizontalScroll,
  resolveDataViewMode,
  type DataViewMode,
  type DataViewPolicyInput,
  type TableComplexity,
} from "./tablePolicy";
