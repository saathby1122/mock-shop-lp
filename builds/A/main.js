/* mock.shop landing page — vanilla JS, no dependencies. Works from file:// (data is inlined). */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ data */

  // Mirrors reference/stores.json plus the copy used by the Start transcript.
  var STORES = {
    streetwear: {
      name: 'VibePulse Studio',
      host: 'apparel-streetwear.mock.shop',
      storefront: 'https://apparel-streetwear.hydrogen.mock.shop/',
      products: 8, variants: 96, collections: 2,
      description: 'Curated streetwear essentials featuring heavy textures, sharp graphics, and limited-edition seasonal drops.',
      grid: 'assets/img/grid-streetwear.webp',
      alt: 'Eight product photos from VibePulse Studio: graphic tees, hoodies, cargo pants, a jacket and a cap',
      phrase: 'oversized, heavyweight t-shirts',
      category: 'a streetwear catalog',
      kinds: 'heavyweight tees and hoodies'
    },
    decor: {
      name: 'Havenly Nest',
      host: 'home-decor.mock.shop',
      storefront: 'https://home-decor.hydrogen.mock.shop/',
      products: 60, variants: 154, collections: 5,
      description: 'We offer a handpicked collection of sculptural decor, soft textiles, and artisanal accents to elevate your living space.',
      grid: 'assets/img/grid-decor.webp',
      alt: 'Eight product photos from Havenly Nest: terracotta cushions, textured throws and linen pillows',
      phrase: 'sculptural home decor and soft textiles',
      category: 'a home decor catalog',
      kinds: 'terracotta cushions and textured throws'
    },
    beauty: {
      name: 'Lumina Botanica',
      host: 'skincare.mock.shop',
      storefront: 'https://skincare.hydrogen.mock.shop/',
      products: 29, variants: 79, collections: 4,
      description: 'We blend potent clinical actives with soothing plant extracts to create simple, effective daily skincare rituals.',
      grid: 'assets/img/grid-beauty.webp',
      alt: 'Eight product photos from Lumina Botanica: botanical cleansers, toners and moisturizers in pump bottles',
      phrase: 'botanical daily skincare',
      category: 'a skincare catalog',
      kinds: 'botanical cleansers and balancing toners'
    },
    sports: {
      name: 'VigorVibe Active',
      host: 'activewear-dropship.mock.shop',
      storefront: 'https://activewear-dropship.hydrogen.mock.shop/',
      products: 8, variants: 96, collections: 2,
      description: 'High-performance activewear and sleek gear designed to help you crush your workout with confidence and vibrant flair.',
      grid: 'assets/img/grid-sports.webp',
      alt: 'Eight product photos from VigorVibe Active: sports bras, leggings, a cropped hoodie and a running belt',
      phrase: 'high-performance activewear',
      category: 'an activewear catalog',
      kinds: 'sports bras and performance leggings'
    }
  };

  // Build-section transcripts. "technical" is the one shown in the mockup.
  var STYLES = {
    technical: {
      prompt: 'Make my store feel fun and loud, like a sticker sheet. Sunny yellow background, chunky black outlines with hard drop shadows, rounded corners, a playful geometric font, and a coral pop for the buy button. Let the product photos swipe like a carousel.',
      result: 'Done. Your storefront now has a sticker-sheet look: a sunny yellow background, bold outlines with hard shadows, and coral buy buttons.'
    },
    vibrant: {
      prompt: 'Make it feel electric: a deep violet background, neon lime accents, oversized rounded type and big saturated product photos that fill the screen. Keep the nav minimal.',
      result: 'Done. Your storefront now sits on a violet base with neon lime accents, oversized rounded headings and full-bleed product photos.'
    },
    bold: {
      prompt: 'Go loud and graphic: black background, huge condensed uppercase headlines, red for the buy button, thick white rules between sections and no rounded corners anywhere.',
      result: 'Done. Your storefront is now black with huge condensed headlines, thick white rules and a red buy button. Sharp corners throughout.'
    },
    elegant: {
      prompt: 'Make it feel like a quiet luxury label: warm ivory background, a high-contrast serif for headings, generous whitespace, thin hairline borders and a near-black buy button.',
      result: 'Done. Your storefront now has an ivory canvas, serif headings with generous spacing, hairline borders and a near-black buy button.'
    }
  };

  var SNIPPETS = {
    prompt: 'Build me a storefront from a mock.shop store.\nStart at https://mock.shop/llms.txt',
    cli: 'npm i -g @shopify/cli && shopify store create preview',
    skill: 'npx skills add Shopify/shopify-ai-toolkit'
  };

  /* --------------------------------------------------------------- helpers */

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  // Roving-tabindex arrow-key navigation for a role="tablist" element.
  function enableArrowKeys(list, onActivate) {
    list.addEventListener('keydown', function (e) {
      var tabs = $$('[role="tab"]', list);
      var i = tabs.indexOf(document.activeElement);
      if (i < 0) return;
      var next = null;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = tabs[(i + 1) % tabs.length];
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = tabs[(i - 1 + tabs.length) % tabs.length];
      else if (e.key === 'Home') next = tabs[0];
      else if (e.key === 'End') next = tabs[tabs.length - 1];
      if (!next) return;
      e.preventDefault();
      next.focus();
      onActivate(next);
    });
  }

  function markSelected(tabs, active) {
    tabs.forEach(function (t) {
      var on = t === active;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      if (on) t.removeAttribute('tabindex'); else t.setAttribute('tabindex', '-1');
    });
  }

  /* ---------------------------------------------- snippet tabs (hero + CTA) */

  var currentSnippet = 'prompt';
  var tabLists = $$('[data-tabs="snippet"]');
  var wells = $$('[data-well]');

  function setSnippet(key) {
    if (!SNIPPETS[key]) return;
    currentSnippet = key;
    tabLists.forEach(function (list) {
      var tabs = $$('[role="tab"]', list);
      var active = tabs.filter(function (t) { return t.getAttribute('data-tab') === key; })[0];
      markSelected(tabs, active);
      var panelId = active && active.getAttribute('aria-controls');
      var panel = panelId && document.getElementById(panelId);
      if (panel && active) panel.setAttribute('aria-labelledby', active.id);
    });
    wells.forEach(function (well) {
      var code = $('[data-snippet]', well);
      if (code) code.textContent = SNIPPETS[key];
      well.setAttribute('data-snippet-key', key);
    });
  }

  tabLists.forEach(function (list) {
    list.addEventListener('click', function (e) {
      var tab = e.target.closest('[role="tab"]');
      if (tab && list.contains(tab)) setSnippet(tab.getAttribute('data-tab'));
    });
    enableArrowKeys(list, function (tab) { setSnippet(tab.getAttribute('data-tab')); });
  });

  /* ---------------------------------------------------------- copy button */

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext !== false && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () { return legacyCopy(text); });
    }
    return legacyCopy(text);
  }

  function focusQuietly(el) {
    if (!el || !el.focus) return;
    try { el.focus({ preventScroll: true }); } catch (err) { el.focus(); }
  }

  function legacyCopy(text) {
    return new Promise(function (resolve, reject) {
      var prev = document.activeElement;
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.setAttribute('aria-hidden', 'true');
      ta.tabIndex = -1;
      ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;padding:0;border:0;opacity:0;';
      document.body.appendChild(ta);
      // focus + setSelectionRange rather than select(): select() can scroll iOS to the textarea
      focusQuietly(ta);
      ta.setSelectionRange(0, text.length);
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
      document.body.removeChild(ta);
      // the textarea took focus; hand it back so keyboard and screen-reader users keep their place
      if (prev && prev !== document.body) focusQuietly(prev);
      ok ? resolve() : reject(new Error('copy failed'));
    });
  }

  $$('[data-copy]').forEach(function (btn) {
    var label = $('[data-copy-label]', btn);
    var well = btn.closest('[data-well]');
    var status = well && $('[data-copy-status]', well); // role=status: a name change on the focused button is not announced
    var code = well && $('[data-snippet]', well);
    var timer = null;

    function announce(msg) {
      if (!status) return;
      status.textContent = '';
      setTimeout(function () { status.textContent = msg; }, 50); // clear first so a repeated message is re-announced
    }
    function reset() {
      if (label) label.textContent = 'Copy';
      btn.classList.remove('is-copied');
      btn.setAttribute('aria-label', 'Copy to clipboard');
      if (status) status.textContent = '';
    }

    btn.addEventListener('click', function () {
      clearTimeout(timer);
      copyText(SNIPPETS[currentSnippet]).then(function () {
        if (label) label.textContent = 'Copied';
        btn.classList.add('is-copied');
        btn.setAttribute('aria-label', 'Copied to clipboard');
        announce('Copied to clipboard');
        timer = setTimeout(reset, 1500);
      }).catch(function () {
        reset();
        announce('Copy failed. Select the text and press Ctrl/Cmd+C');
        // leave the snippet selected so a manual copy is one keystroke away
        try {
          if (code && window.getSelection) {
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.selectAllChildren(code);
          }
        } catch (err) { /* selection is best-effort */ }
        timer = setTimeout(function () { if (status) status.textContent = ''; }, 4000);
      });
    });
  });

  /* ---------------------------------------------------------- Start pills */

  var startPills = $('[data-pills="store"]');
  var mainCard = $('[data-card="main"]');
  var startTerminal = $('[data-terminal="start"]');

  function setStore(key) {
    var s = STORES[key];
    if (!s) return;
    if (startPills) {
      var tabs = $$('[role="tab"]', startPills);
      markSelected(tabs, tabs.filter(function (t) { return t.getAttribute('data-store') === key; })[0]);
    }
    if (mainCard) {
      var grid = $('[data-field="grid"]', mainCard);
      if (grid) { grid.src = s.grid; grid.alt = s.alt; }
      var fields = { name: s.name, host: s.host, description: s.description, products: s.products, variants: s.variants, collections: s.collections };
      Object.keys(fields).forEach(function (f) {
        var el = $('[data-field="' + f + '"]', mainCard);
        if (el) el.textContent = String(fields[f]);
      });
    }
    if (startTerminal) {
      var prompt = $('[data-term="prompt"]', startTerminal);
      var result = $('[data-term="result"]', startTerminal);
      if (prompt) prompt.textContent = 'I want to sell ' + s.phrase + '.';
      if (result) result.textContent = 'Found ' + s.name + ', ' + s.category + ' with ' + s.kinds + '. Your store is ready with its ' + s.products + ' products and theme. Want to change the look next?';
    }
  }

  if (startPills) {
    startPills.addEventListener('click', function (e) {
      var pill = e.target.closest('[data-store]');
      if (pill) setStore(pill.getAttribute('data-store'));
    });
    enableArrowKeys(startPills, function (pill) { setStore(pill.getAttribute('data-store')); });
  }

  /* ---------------------------------------------------------- Build pills */

  var buildPills = $('[data-pills="style"]');
  var buildTerminal = $('[data-terminal="build"]');

  function setStyle(key) {
    var st = STYLES[key];
    if (!st) return;
    if (buildPills) {
      var tabs = $$('[role="tab"]', buildPills);
      markSelected(tabs, tabs.filter(function (t) { return t.getAttribute('data-style') === key; })[0]);
    }
    if (buildTerminal) {
      var prompt = $('[data-term="prompt"]', buildTerminal);
      var result = $('[data-term="result"]', buildTerminal);
      if (prompt) prompt.textContent = st.prompt;
      if (result) result.textContent = st.result;
    }
    // TODO: swap the Build preview image per style once per-style exports exist.
  }

  if (buildPills) {
    buildPills.addEventListener('click', function (e) {
      var pill = e.target.closest('[data-style]');
      if (pill) setStyle(pill.getAttribute('data-style'));
    });
    enableArrowKeys(buildPills, function (pill) { setStyle(pill.getAttribute('data-style')); });
  }

  /* ------------------------------------------------ storefront preview frame */
  // Static captures by default (faithful to the design): the frame holds both the desktop and the
  // phone capture, and the toggle crossfades them while the frame itself animates (styles.css), so
  // neither capture ever scales. The live store is only requested when the frame carries
  // data-live="true": the iframe is then created lazily near the viewport, kept underneath the
  // captures until its load event and faded in. With data-live="false" nothing third-party is
  // fetched and the frame has no extra tab stop.

  var frame = $('.store-frame');
  var frameImgs = frame ? $$('.store-frame__img', frame) : [];
  var deviceBtns = $$('.device-btn');

  function preload(src) {
    if (!src) return;
    var img = new Image();
    img.src = src;
  }

  function setDevice(device) {
    if (!frame) return;
    var mobile = device === 'mobile';
    frame.classList.toggle('is-mobile', mobile);
    frame.setAttribute('data-device', mobile ? 'mobile' : 'desktop');
    deviceBtns.forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-device') === device ? 'true' : 'false');
    });
    frameImgs.forEach(function (img) {
      // Only the visible capture stays in the accessibility tree (none once the live store is showing: its
      // iframe title names the storefront).
      if (img.getAttribute('data-device') === device && !frame.classList.contains('is-loaded')) img.removeAttribute('aria-hidden');
      else img.setAttribute('aria-hidden', 'true');
    });
  }

  deviceBtns.forEach(function (b) {
    b.addEventListener('click', function () { setDevice(b.getAttribute('data-device')); });
  });

  // Phones: the 1260px desktop screenshot is illegible at ~350px wide, so show the phone capture there
  // (styles.css hides the toggle at that width; this also catches a window resized down to phone width).
  var phoneQuery = window.matchMedia ? window.matchMedia('(max-width: 639px)') : null;
  if (frame && phoneQuery) {
    if (phoneQuery.matches) setDevice('mobile');
    if (phoneQuery.addEventListener) phoneQuery.addEventListener('change', function (e) { if (e.matches) setDevice('mobile'); });
  }

  var LIVE_SRC = (frame && frame.getAttribute('data-live-src')) || 'https://apparel-streetwear.hydrogen.mock.shop/';
  var LIVE_REVEAL_TIMEOUT = 8000;

  function mountLiveFrame() {
    if (!frame || frame.getAttribute('data-live') !== 'true' || $('.store-frame__iframe', frame)) return;
    var ifr = document.createElement('iframe');
    ifr.className = 'store-frame__iframe';
    ifr.title = frame.getAttribute('data-live-title') || 'Storefront preview';
    // Out of the tab order and the accessibility tree until the store has actually rendered (styles.css also
    // keeps it out of hit-testing until then).
    ifr.setAttribute('aria-hidden', 'true');
    ifr.tabIndex = -1;
    // The store keeps its scripts, cookies and forms, but cannot navigate this page away (no allow-top-navigation).
    ifr.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox');
    ifr.referrerPolicy = 'strict-origin-when-cross-origin';
    var expired = false;
    var expiry = setTimeout(function () { expired = true; }, LIVE_REVEAL_TIMEOUT);
    ifr.addEventListener('load', function () {
      clearTimeout(expiry);
      // Reveal only a real document that arrived in time: a stalled store keeps the design capture
      // instead of swapping it for a half-rendered page.
      if (expired || !ifr.getAttribute('src')) return;
      frame.classList.add('is-loaded');
      ifr.removeAttribute('aria-hidden');
      ifr.removeAttribute('tabindex');
      frameImgs.forEach(function (img) { img.setAttribute('aria-hidden', 'true'); }); // the iframe's title now names the storefront
    });
    ifr.src = LIVE_SRC;
    frame.appendChild(ifr);
  }

  // Chrome navigates an unreachable iframe to its own error page and still fires `load`, which would fade a
  // sad-face page in over the capture. An opaque no-cors fetch resolves whenever the host answers at all and
  // rejects on network errors (offline, DNS, refused, corporate block), so only mount when it resolves.
  // X-Frame-Options / CSP frame-ancestors refusals cannot be detected from here (noted in TODO.md).
  function mountLiveFrameIfReachable() {
    if (!window.fetch) { mountLiveFrame(); return; }
    fetch(LIVE_SRC, { mode: 'no-cors', cache: 'no-store' }).then(mountLiveFrame, function () { /* keep the static capture */ });
  }

  if (frame && frame.getAttribute('data-live') === 'true') {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        if (entries.some(function (e) { return e.isIntersecting; })) {
          io.disconnect();
          mountLiveFrameIfReachable();
        }
      }, { rootMargin: '400px 0px' });
      io.observe(frame);
    } else {
      mountLiveFrameIfReachable();
    }
  }

  /* ------------------------------------------------------- image warming */

  // Warm the other three catalog grids after load so the first Start pill switch does not flash.
  window.addEventListener('load', function () {
    setTimeout(function () {
      var current = mainCard && $('[data-field="grid"]', mainCard);
      var shown = current ? current.getAttribute('src') : '';
      Object.keys(STORES).forEach(function (k) {
        if (STORES[k].grid !== shown) preload(STORES[k].grid);
      });
    }, 1000);
  });

  /* ------------------------------------------------------------------- FAQ */

  var faqItems = $$('[data-faq] details');
  faqItems.forEach(function (item) {
    item.addEventListener('toggle', function () {
      if (!item.open) return;
      faqItems.forEach(function (other) { if (other !== item && other.open) other.open = false; });
    });
  });
})();
