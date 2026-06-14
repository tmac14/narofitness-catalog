/* eslint-disable @typescript-eslint/no-require-imports */
const CDP = require("chrome-remote-interface");

async function main() {
  const client = await CDP({ port: 9333 });
  const { Runtime, DOM, Input } = client;
  await Runtime.enable();
  await DOM.enable();

  const base = await Runtime.evaluate({
    expression: `(() => ({
      isElectron: !!window.narocatalog?.isElectron,
      dragRegion: getComputedStyle(document.querySelector('.app-topbar')).getPropertyValue('-webkit-app-region'),
      controlRegion: getComputedStyle(document.querySelector('.app-topbar__controls')).getPropertyValue('-webkit-app-region'),
      minimizeBtn: !!document.querySelector('[aria-label="Minimizar"]'),
      closeBtn: !!document.querySelector('[aria-label="Cerrar"]'),
      brandTitle: document.querySelector('.brand-lockup__title')?.innerText?.trim(),
      topbarHeight: getComputedStyle(document.querySelector('.app-topbar')).height,
    }))()`,
    returnByValue: true,
  });

  const minimizeRect = await Runtime.evaluate({
    expression: `(() => {
      const el = document.querySelector('[aria-label="Minimizar"]');
      const r = el.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height };
    })()`,
    returnByValue: true,
  });

  console.log("BASE:", JSON.stringify(base.result.value, null, 2));
  console.log("MINIMIZE_TARGET:", JSON.stringify(minimizeRect.result.value, null, 2));

  const { x, y } = minimizeRect.result.value;
  await Input.dispatchMouseEvent({ type: "mousePressed", x, y, button: "left", clickCount: 1 });
  await Input.dispatchMouseEvent({ type: "mouseReleased", x, y, button: "left", clickCount: 1 });

  await new Promise((r) => setTimeout(r, 500));

  const afterMinimize = await Runtime.evaluate({
    expression: "document.visibilityState",
    returnByValue: true,
  });
  console.log("AFTER_MINIMIZE_VISIBILITY:", afterMinimize.result.value);

  await client.close();
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
