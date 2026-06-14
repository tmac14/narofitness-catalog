import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import {
  ResponsiveCardFooter,
  ResponsiveCardHeader,
  ResponsiveCollapsiblePanel,
  ResponsiveDataCard,
  ResponsiveDataCardList,
  ResponsiveMetaGrid,
  ResponsiveMetaRow,
  ResponsiveTouchMenuTrigger,
} from "@/components/responsive/list";

describe("responsive list primitives", () => {
  it("renders card shell with even/odd stripes", () => {
    const even = renderToStaticMarkup(
      <ResponsiveDataCard index={0}>
        <span>Even</span>
      </ResponsiveDataCard>,
    );
    const odd = renderToStaticMarkup(
      <ResponsiveDataCard index={1}>
        <span>Odd</span>
      </ResponsiveDataCard>,
    );

    expect(even).toContain("responsive-data-card");
    expect(even).toContain("responsive-data-card--even");
    expect(odd).toContain("responsive-data-card--odd");
  });

  it("renders semantic row tint modifiers", () => {
    const html = renderToStaticMarkup(
      <ResponsiveDataCard index={0} modifierClass="responsive-data-card--only_a">
        <span>Tinted</span>
      </ResponsiveDataCard>,
    );
    expect(html).toContain("responsive-data-card--only_a");
  });

  it("renders meta grid rows", () => {
    const html = renderToStaticMarkup(
      <ResponsiveMetaGrid>
        <ResponsiveMetaRow label="Campo">Valor</ResponsiveMetaRow>
      </ResponsiveMetaGrid>,
    );
    expect(html).toContain("responsive-meta-grid");
    expect(html).toContain("responsive-meta-row");
    expect(html).toContain("Campo");
    expect(html).toContain("Valor");
  });

  it("renders list wrapper with divide-y class hook", () => {
    const html = renderToStaticMarkup(
      <ResponsiveDataCardList>
        <li>
          <ResponsiveDataCard index={0}>One</ResponsiveDataCard>
        </li>
      </ResponsiveDataCardList>,
    );
    expect(html).toContain("responsive-data-card-list__items");
  });

  it("renders header, footer, and touch menu trigger", () => {
    const html = renderToStaticMarkup(
      <ResponsiveDataCard index={0}>
        <ResponsiveCardHeader>Title</ResponsiveCardHeader>
        <ResponsiveCardFooter>Actions</ResponsiveCardFooter>
        <ResponsiveTouchMenuTrigger ariaLabel="Menu" />
      </ResponsiveDataCard>,
    );
    expect(html).toContain("responsive-data-card__header");
    expect(html).toContain("responsive-data-card__footer");
    expect(html).toContain("responsive-touch-menu-trigger");
    expect(html).toContain('aria-label="Menu"');
  });

  it("renders collapsible panel with aria-expanded", () => {
    const html = renderToStaticMarkup(
      <ResponsiveCollapsiblePanel
        panelId="test-panel"
        triggerLabel="Toggle"
        open={true}
        onOpenChange={() => {}}
        collapseEnabled={true}
      >
        <p>Panel body</p>
      </ResponsiveCollapsiblePanel>,
    );
    expect(html).toContain('aria-expanded="true"');
    expect(html).toContain('aria-controls="test-panel"');
    expect(html).toContain('id="test-panel"');
    expect(html).toContain("Panel body");
  });
});
