import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { ProductSourcePageBadge } from "@/components/products/ProductSourcePageBadge";

describe("ProductSourcePageBadge", () => {
  it("renders single-page label as visible text", () => {
    const html = renderToStaticMarkup(
      <ProductSourcePageBadge source_page={38} source_pages={[38]} />,
    );
    expect(html).toContain("PDF p.38");
    expect(html).not.toContain("Sin página");
  });

  it("renders contiguous multi-page label", () => {
    const html = renderToStaticMarkup(
      <ProductSourcePageBadge source_page={null} source_pages={[38, 39, 40]} />,
    );
    expect(html).toContain("PDF p.38–40");
  });

  it("renders non-contiguous multi-page label without implying a range", () => {
    const html = renderToStaticMarkup(
      <ProductSourcePageBadge source_page={null} source_pages={[38, 40]} />,
    );
    expect(html).toContain("PDF p.38, 40");
    expect(html).not.toContain("38–40");
  });

  it("renders nothing when source_pages is empty", () => {
    const html = renderToStaticMarkup(
      <ProductSourcePageBadge source_page={null} source_pages={[]} />,
    );
    expect(html).toBe("");
  });

  it("includes visible label text, not only title attribute", () => {
    const html = renderToStaticMarkup(
      <ProductSourcePageBadge source_page={38} source_pages={[38]} />,
    );
    const textBetweenTags = html.replace(/<[^>]+>/g, "").trim();
    expect(textBetweenTags).toBe("PDF p.38");
  });
});
