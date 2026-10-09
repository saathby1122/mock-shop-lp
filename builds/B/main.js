/* mock.shop landing page — build B. Vanilla JS, no dependencies. */
(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ------------------------------------------------------------------------
     Data (inlined so the page works from file:// and GitHub Pages alike)
     ------------------------------------------------------------------------ */
  const SNIPPETS = {
    prompt: 'Build me a storefront from a mock.shop store.\nStart at https://mock.shop/llms.txt',
    cli: 'npm i -g @shopify/cli && shopify store create preview',
    skill: 'npx skills add Shopify/shopify-ai-toolkit'
  };

  // From reference/stores.json plus the copy used in the Start transcript.
  const STORES = {
    streetwear: {
      name: 'VibePulse Studio',
      host: 'apparel-streetwear.mock.shop',
      storefront: 'https://apparel-streetwear.hydrogen.mock.shop/',
      products: 8, variants: 96, collections: 2,
      description: 'Curated streetwear essentials featuring heavy textures, sharp graphics, and limited-edition seasonal drops.',
      grid: 'assets/img/grid-streetwear.webp',
      gridAlt: 'Eight product photos from VibePulse Studio: heavyweight tees, hoodies, cargo pants, a utility jacket and a canvas cap',
      sell: 'oversized, heavyweight t\u2011shirts',
      catalog: 'a streetwear catalog',
      kinds: 'heavyweight tees and hoodies'
    },
    decor: {
      name: 'Havenly Nest',
      host: 'home-decor.mock.shop',
      storefront: 'https://home-decor.hydrogen.mock.shop/',
      products: 60, variants: 154, collections: 5,
      description: 'We offer a handpicked collection of sculptural decor, soft textiles, and artisanal accents to elevate your living space.',
      grid: 'assets/img/grid-decor.webp',
      gridAlt: 'Eight product photos from Havenly Nest: terracotta throw pillows, textured cushion covers and linen throws',
      sell: 'sculptural home decor and soft textiles',
      catalog: 'a home decor catalog',
      kinds: 'terracotta cushions and textured throws'
    },
    beauty: {
      name: 'Lumina Botanica',
      host: 'skincare.mock.shop',
      storefront: 'https://skincare.hydrogen.mock.shop/',
      products: 29, variants: 79, collections: 4,
      description: 'We blend potent clinical actives with soothing plant extracts to create simple, effective daily skincare rituals.',
      grid: 'assets/img/grid-beauty.webp',
      gridAlt: 'Eight product photos from Lumina Botanica: botanical cleansers, toners, mists and a renewal moisturizer',
      sell: 'botanical daily skincare',
      catalog: 'a skincare catalog',
      kinds: 'botanical cleansers and balancing toners'
    },
    sports: {
      name: 'VigorVibe Active',
      host: 'activewear-dropship.mock.shop',
      storefront: 'https://activewear-dropship.hydrogen.mock.shop/',
      products: 8, variants: 96, collections: 2,
      description: 'High-performance activewear and sleek gear designed to help you crush your workout with confidence and vibrant flair.',
      grid: 'assets/img/grid-sports.webp',
      gridAlt: 'Eight product photos from VigorVibe Active: sports bras, neon leggings, a cropped hoodie, a performance jacket and a running belt',
      sell: 'high-performance activewear',
      catalog: 'an activewear catalog',
      kinds: 'sports bras and leggings'
    }
  };

  // Build-step transcripts. "technical" is the one in the mock; the others are style-matched variants.
  const LOOKS = {
    technical: {
      prompt: 'Make my store feel fun and loud, like a sticker sheet. Sunny yellow background, chunky black outlines with hard drop shadows, rounded corners, a playful geometric font, and a coral pop for the buy button. Let the product photos swipe like a carousel.',
      result: 'Done. Your storefront now has a sticker-sheet look: a sunny yellow background, bold outlines with hard shadows, and coral buy buttons.'
    },
    vibrant: {
      prompt: 'Turn the volume up. Electric purple and lime, oversized type that fills the screen, product cards that tilt on hover, and a marquee of collection names running under the header.',
      result: 'Done. Your storefront is now electric purple and lime, with oversized headlines, tilting product cards and a scrolling marquee under the header.'
    },
    bold: {
      prompt: 'Go brutalist. Pure black and white, a heavy condensed display face in all caps, 2px rules between every section, and a single red accent reserved for the add to cart button.',
      result: 'Done. Your storefront is now black and white with heavy condensed caps, ruled sections and one red accent on the add to cart button.'
    },
    elegant: {
      prompt: 'Make it feel like a quiet boutique. Warm ivory background, a refined serif for headings, generous whitespace, thin hairline borders, and muted sage buttons with soft corners.',
      result: 'Done. Your storefront now has a boutique feel: an ivory background, serif headings, generous whitespace and muted sage buttons.'
    }
  };

  /* ------------------------------------------------------------------------
     Tabs + code well (hero and CTA share one state)
     ------------------------------------------------------------------------ */
  const snippets = $$('[data-snippet]');
  let currentTab = 'prompt';

  function renderTabs() {
    const code = SNIPPETS[currentTab];
    snippets.forEach((snippet) => {
      const tabs = $$('.tab', snippet);
      const well = $('[data-well]', snippet);
      const pre = $('[data-code]', snippet);
      tabs.forEach((tab) => {
        const on = tab.dataset.tab === currentTab;
        tab.setAttribute('aria-selected', on ? 'true' : 'false');
        tab.tabIndex = on ? 0 : -1;
        if (on && well) well.setAttribute('aria-labelledby', tab.id);
      });
      if (pre) {
        pre.textContent = code;
        pre.classList.toggle('is-single', !code.includes('\n'));
      }
    });
  }

  snippets.forEach((snippet) => {
    const tabs = $$('.tab', snippet);
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => {
        currentTab = tab.dataset.tab;
        renderTabs();
      });
      tab.addEventListener('keydown', (e) => {
        const keys = { ArrowRight: 1, ArrowLeft: -1, Home: -Infinity, End: Infinity };
        if (!(e.key in keys)) return;
        e.preventDefault();
        let next = i + keys[e.key];
        if (e.key === 'Home') next = 0;
        if (e.key === 'End') next = tabs.length - 1;
        next = (next + tabs.length) % tabs.length;
        currentTab = tabs[next].dataset.tab;
        renderTabs();
        tabs[next].focus();
      });
    });
  });

  /* ------------------------------------------------------------------------
     Copy buttons
     ------------------------------------------------------------------------ */
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext !== false && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(() => legacyCopy(text));
    }
    return Promise.resolve(legacyCopy(text));
  }

  function legacyCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;';
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
    document.body.removeChild(ta);
    if (!ok) throw new Error('copy failed');
    return ok;
  }

  $$('[data-copy]').forEach((btn) => {
    const label = $('[data-copy-label]', btn);
    const status = $('[data-copy-status]', btn);
    let timer = 0;
    btn.addEventListener('click', () => {
      copyText(SNIPPETS[currentTab]).then(() => {
        label.textContent = 'Copied';
        if (status) status.textContent = 'Copied to clipboard';
        clearTimeout(timer);
        timer = setTimeout(() => {
          label.textContent = 'Copy';
          if (status) status.textContent = '';
        }, 1500);
      }).catch(() => {
        if (status) status.textContent = 'Copy failed. Select the text and copy it manually.';
      });
    });
  });

  /* ------------------------------------------------------------------------
     Start pills: swap the store card + transcript
     ------------------------------------------------------------------------ */
  const startSection = $('[data-pills="store"]');
  if (startSection) {
    const card = $('[data-store-card]');
    const gridImg = $('[data-card-grid]');
    const ghostGrids = $$('[data-ghost-grid]');
    const name = $('[data-card-name]');
    const host = $('[data-card-host]');
    const desc = $('[data-card-desc]');
    const stats = $('[data-card-stats]');
    const term = $('[data-terminal="start"]');
    const prompt = term && $('[data-term-prompt]', term);
    const result = term && $('[data-term-result]', term);

    function statsHTML(s) {
      const dot = '<span class="store-card__dot">·</span>';
      return `<b>${s.products}</b> products ${dot} <b>${s.variants}</b> variants ${dot} <b>${s.collections}</b> collections`;
    }

    function renderStore(key) {
      const s = STORES[key];
      if (!s) return;
      $$('.pill', startSection).forEach((p) => p.setAttribute('aria-pressed', p.dataset.store === key ? 'true' : 'false'));
      gridImg.src = s.grid;
      gridImg.alt = s.gridAlt;
      ghostGrids.forEach((g) => { g.src = s.grid; });
      name.textContent = s.name;
      host.textContent = s.host;
      desc.textContent = s.description;
      stats.innerHTML = statsHTML(s);
      if (card) card.dataset.store = key;
      if (prompt) prompt.textContent = `I want to sell ${s.sell}.`;
      if (result) result.textContent = `Found ${s.name}, ${s.catalog} with ${s.kinds}. Your store is ready with its ${s.products} products and theme. Want to change the look next?`;
    }

    startSection.addEventListener('click', (e) => {
      const pill = e.target.closest('.pill');
      if (pill) renderStore(pill.dataset.store);
    });
  }

  /* ------------------------------------------------------------------------
     Build pills: swap the transcript (the preview image stays — TODO: per-look exports)
     ------------------------------------------------------------------------ */
  const buildSection = $('[data-pills="style"]');
  if (buildSection) {
    const term = $('[data-terminal="build"]');
    const prompt = term && $('[data-term-prompt]', term);
    const result = term && $('[data-term-result]', term);
    buildSection.addEventListener('click', (e) => {
      const pill = e.target.closest('.pill');
      if (!pill) return;
      const look = LOOKS[pill.dataset.style];
      if (!look) return;
      $$('.pill', buildSection).forEach((p) => p.setAttribute('aria-pressed', p === pill ? 'true' : 'false'));
      if (prompt) prompt.textContent = look.prompt;
      if (result) result.textContent = look.result;
    });
  }

  /* ------------------------------------------------------------------------
     Storefront preview: device toggle + live iframe over the fallback image
     ------------------------------------------------------------------------ */
  const frame = $('[data-frame]');
  if (frame) {
    const iframe = $('[data-iframe]', frame);
    const fallback = $('[data-fallback]', frame);
    const FALLBACKS = {
      desktop: { src: 'assets/img/storefront.webp', w: 1260, h: 751 },
      mobile: { src: 'assets/img/store-mobile.png', w: 780, h: 1688 }
    };

    if (iframe) {
      iframe.addEventListener('load', () => {
        // A lazy iframe fires load for about:blank before navigating; only reveal once a real document is in.
        if (iframe.src) frame.classList.add('is-loaded');
      });
      iframe.addEventListener('error', () => frame.classList.remove('is-loaded'));
    }

    $$('.device-toggle__btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const device = btn.dataset.device;
        $$('.device-toggle__btn').forEach((b) => b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'));
        frame.classList.toggle('is-mobile', device === 'mobile');
        const fb = FALLBACKS[device];
        if (fallback && fb && !fallback.src.endsWith(fb.src)) {
          fallback.src = fb.src;
          fallback.width = fb.w;
          fallback.height = fb.h;
        }
      });
    });
    // If the mobile capture is missing, keep the desktop image.
    const probe = new Image();
    probe.onerror = () => { FALLBACKS.mobile = FALLBACKS.desktop; };
    probe.src = FALLBACKS.mobile.src;
  }

  /* ------------------------------------------------------------------------
     FAQ: one open at a time (native <details name> where supported, JS elsewhere)
     ------------------------------------------------------------------------ */
  const faqItems = $$('[data-faq] details');
  faqItems.forEach((item) => {
    item.addEventListener('toggle', () => {
      if (!item.open) return;
      faqItems.forEach((other) => { if (other !== item && other.open) other.open = false; });
    });
  });

  renderTabs();
})();
