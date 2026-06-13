import { describe, expect, it } from "vitest";

import { labelReason } from "./importLabels";

describe("labelReason", () => {
  it("formats unknown_color_value prefix with human label", () => {
    expect(labelReason("unknown_color_value:Azul Petróleo")).toBe(
      "Color no reconocido: Azul Petróleo",
    );
  });

  it("keeps known static reason labels", () => {
    expect(labelReason("missing_price")).toBe("Sin precio");
  });
});
