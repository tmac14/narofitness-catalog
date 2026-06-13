/**
 * Read-only QA helper — queries Electron TitleBar via CDP (port 9333).
 * Artifact only; not part of app source.
 */
const CDP_PORT = 9333;

async function getTargetWsUrl() {
  const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`);
  const targets = await res.json();
  const page = targets.find((t) => t.type === "page");
  if (!page?.webSocketDebuggerUrl) throw new Error("No Electron page target on CDP");
  return page.webSocketDebuggerUrl;
}

function cdpSession(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let id = 0;
    const pending = new Map();

    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && pending.has(msg.id)) {
        const { resolve: res, reject: rej } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) rej(new Error(JSON.stringify(msg.error)));
        else res(msg.result);
      }
    });

    ws.addEventListener("open", () => resolve({
      send(method, params = {}) {
        const msgId = ++id;
        return new Promise((res, rej) => {
          pending.set(msgId, { resolve: res, reject: rej });
          ws.send(JSON.stringify({ id: msgId, method, params }));
        });
      },
      close() {
        ws.close();
      },
    }));

    ws.addEventListener("error", reject);
  });
}

const titleBarExpr = `(() => {
  const titleBar = document.querySelector('.titlebar-drag');
  const buttons = [...document.querySelectorAll('.titlebar-no-drag button')];
  const title = document.querySelector('.titlebar-drag span.truncate, .titlebar-drag .truncate');
  return {
    isElectron: !!window.narocatalog?.isElectron,
    titleBarVisible: !!titleBar && titleBar.getBoundingClientRect().height > 0,
    titleText: title?.textContent?.trim()?.slice(0, 80) || null,
    titleOverflow: title ? title.scrollWidth > title.clientWidth + 1 : null,
    buttons: buttons.map((b) => {
      const r = b.getBoundingClientRect();
      return {
        label: b.getAttribute('aria-label'),
        width: Math.round(r.width),
        height: Math.round(r.height),
      };
    }),
  };
})()`;

async function measureAtWidth(session, width, height) {
  await session.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await new Promise((r) => setTimeout(r, 300));
  const { result } = await session.send("Runtime.evaluate", {
    expression: titleBarExpr,
    returnByValue: true,
  });
  return { viewport: `${width}x${height}`, ...result.value };
}

async function main() {
  const wsUrl = await getTargetWsUrl();
  const session = await cdpSession(wsUrl);
  try {
    await session.send("Runtime.enable");
    const tablet = await measureAtWidth(session, 768, 1024);
    const desktop = await measureAtWidth(session, 1024, 768);
    const wide = await measureAtWidth(session, 1440, 900);
    const out = { tablet, desktop, wide, checkedAt: new Date().toISOString() };
    console.log(JSON.stringify(out, null, 2));
  } finally {
    session.close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
