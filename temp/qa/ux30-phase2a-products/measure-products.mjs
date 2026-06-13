/** QA helper — paste expression body into browser evaluate_script per viewport */
export const MEASURE_PRODUCTS_EXPR = `(() => {
  const isVisible = (el) => {
    if (!el) return false;
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const cardsList = document.querySelector('.product-master-card-list');
  const cards = [...document.querySelectorAll('.product-master-card')].filter(isVisible);
  const table = document.querySelector('.product-list-table');
  const variantTable = document.querySelector('.product-variants-panel__table');
  const skeleton = document.querySelector('[class*="skeleton"], .animate-pulse');
  const primarySelectors = [
    '.product-master-card__variants-btn',
    '.product-master-card__menu-btn',
    '.product-master-card-list__sort-select',
    '.product-master-card-list__sort-dir',
    'button[aria-label="Ver origen PDF"]',
    '.product-variant-card__detail-btn',
  ];
  const smallTargets = [];
  for (const sel of primarySelectors) {
    for (const el of document.querySelectorAll(sel)) {
      if (!isVisible(el)) continue;
      const r = el.getBoundingClientRect();
      const minDim = Math.min(r.width, r.height);
      if (minDim > 0 && minDim < 44) {
        smallTargets.push({ sel, label: el.getAttribute('aria-label') || el.textContent?.trim()?.slice(0, 40), w: Math.round(r.width), h: Math.round(r.height) });
      }
    }
  }
  const pdfBadges = [...document.querySelectorAll('button[aria-label="Ver origen PDF"], [data-source-page]')].filter(isVisible).length;
  const pdfTriggers = [...document.querySelectorAll('button[aria-label="Ver origen PDF"]')].filter(isVisible).length;
  const multiVariantBtns = [...document.querySelectorAll('button[aria-label^="Mostrar"]')].filter(isVisible);
  let mode = 'unknown';
  if (isVisible(table)) mode = 'table';
  else if (isVisible(cardsList) || cards.length > 0) mode = 'cards';
  else if (document.body.textContent?.includes('Sin productos')) mode = 'empty';
  else if (document.body.textContent?.includes('No se pudieron')) mode = 'error';
  const dualMode = isVisible(table) && (isVisible(cardsList) || cards.length > 0);
  return {
    viewport: { w: innerWidth, h: innerHeight },
    mode,
    dualMode,
    cardCount: cards.length,
    tableVisible: isVisible(table),
    cardsListVisible: isVisible(cardsList),
    nestedVariantTable: isVisible(variantTable),
    horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
    scrollWidth: document.documentElement.scrollWidth,
    smallTargets,
    pdfTriggers,
    multiVariantBtnCount: multiVariantBtns.length,
    hasSortControls: !!document.querySelector('#products-card-sort') || !!document.querySelector('.product-list-table th'),
    paginationVisible: isVisible(document.querySelector('button[aria-label="Página siguiente"], button[disabled][aria-label="Página siguiente"]')),
  };
})()`;
