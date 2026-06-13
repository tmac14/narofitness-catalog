import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const __dirname = dirname(fileURLToPath(import.meta.url));
const tokensPath = join(__dirname, "../../theme/narofitness-tokens.css");
const require = createRequire(import.meta.url);
const tailwindConfig = require("../../../tailwind.config.cjs") as {
  theme: {
    extend: {
      screens: Record<string, string | { min?: string; max?: string }>;
    };
  };
};

describe("UX 3.0 Phase 0 token smoke", () => {
  it("preserves catalogue-builder layout tokens unchanged", () => {
    const css = readFileSync(tokensPath, "utf8");
    expect(css).toContain("--builder-sidebar-width: 260px");
    expect(css).toContain("--editor-tab-min-height: 560px");
    expect(css).toContain("--builder-header-offset: 7.5rem");
    expect(css).toContain("--preview-canvas: #ffffff");
  });

  it("adds touch and safe-area tokens without altering builder keys", () => {
    const css = readFileSync(tokensPath, "utf8");
    expect(css).toContain("--touch-target-min: 2.75rem");
    expect(css).toContain("--touch-target-gap: 0.5rem");
    expect(css).toContain("--safe-area-inset-top: env(safe-area-inset-top, 0px)");
  });
});

describe("Tailwind semantic screens config", () => {
  it("extends screens without replacing legacy sm/md/lg/xl keys in config source", () => {
    expect(tailwindConfig.theme.extend.screens.mobile).toEqual({ max: "639px" });
    expect(tailwindConfig.theme.extend.screens.tablet).toEqual({
      min: "640px",
      max: "1023px",
    });
    expect(tailwindConfig.theme.extend.screens.desktop).toEqual({
      min: "1024px",
      max: "1279px",
    });
    expect(tailwindConfig.theme.extend.screens.wide).toBe("1280px");
  });

  it("does not define sm/md/lg/xl overrides in extend.screens", () => {
    const screens = tailwindConfig.theme.extend.screens;
    expect(screens).not.toHaveProperty("sm");
    expect(screens).not.toHaveProperty("md");
    expect(screens).not.toHaveProperty("lg");
    expect(screens).not.toHaveProperty("xl");
  });
});
