import { describe, expect, it } from "vitest";
import { formatCategoryPath, labelMappingStatus, labelProposalSource } from "./importMappingLabels";

describe("importMappingLabels", () => {
  it("labelMappingStatus returns Spanish labels", () => {
    expect(labelMappingStatus("unmapped")).toBe("Sin asignar");
    expect(labelMappingStatus("ambiguous")).toBe("Necesita revisión");
  });

  it("labelProposalSource maps known sources", () => {
    expect(labelProposalSource("rule")).toBe("Regla automática");
    expect(labelProposalSource("unknown_key")).toBe("unknown key");
  });

  it("formatCategoryPath formats slugs as breadcrumbs", () => {
    expect(formatCategoryPath("gimnasio/pesas")).toBe("gimnasio › pesas");
    expect(formatCategoryPath("solo")).toBe("solo");
  });
});
