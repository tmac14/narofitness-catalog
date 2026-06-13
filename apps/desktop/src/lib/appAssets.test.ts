import { describe, expect, it } from "vitest";
import { APP_BRAND_LOGOS, APP_ICONS } from "./appAssets";

describe("appAssets", () => {
  it("resolves public asset paths under the Vite base URL", () => {
    expect(APP_ICONS.mark).toMatch(/icons\/app-mark\.png$/);
    expect(APP_BRAND_LOGOS.markMinimal).toMatch(
      /brand\/logos\/03_nr_mark_minimal_flat_white_green\.png$/,
    );
    expect(APP_BRAND_LOGOS.oneLineLockup).toContain("brand/logos/");
  });
});
