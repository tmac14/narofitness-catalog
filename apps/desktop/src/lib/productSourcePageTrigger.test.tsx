import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import {
  ProductSourcePagePopoverPanel,
  ProductSourcePageTrigger,
} from "@/components/products/ProductSourcePageTrigger";

describe("ProductSourcePageTrigger", () => {
  it("renders an accessible trigger button when source pages exist", () => {
    const html = renderToStaticMarkup(
      <ProductSourcePageTrigger source_page={30} source_pages={[30]} />,
    );
    expect(html).toContain('aria-label="Ver origen PDF"');
    expect(html).toContain('type="button"');
    expect(html).not.toContain("Sin página");
  });

  it("renders nothing when source_pages is empty", () => {
    const html = renderToStaticMarkup(
      <ProductSourcePageTrigger source_page={null} source_pages={[]} />,
    );
    expect(html).toBe("");
  });
});

describe("ProductSourcePagePopoverPanel", () => {
  it("renders single-page popover content as visible text", () => {
    const html = renderToStaticMarkup(
      <ProductSourcePagePopoverPanel body="Página 30" panelId="panel-1" titleId="title-1" />,
    );
    expect(html).toContain("Origen PDF");
    expect(html).toContain("Página 30");
    expect(html).toContain('role="dialog"');
  });

  it("renders multi-page popover content", () => {
    const html = renderToStaticMarkup(
      <ProductSourcePagePopoverPanel body="Páginas 38–40" panelId="panel-2" titleId="title-2" />,
    );
    expect(html).toContain("Páginas 38–40");
  });

  it("renders non-contiguous multi-page popover content", () => {
    const html = renderToStaticMarkup(
      <ProductSourcePagePopoverPanel body="Páginas 38, 40" panelId="panel-3" titleId="title-3" />,
    );
    expect(html).toContain("Páginas 38, 40");
    expect(html).not.toContain("38–40");
  });
});
