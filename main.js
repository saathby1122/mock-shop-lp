/* mock.shop landing page — vanilla JS, no dependencies. Works from file:// (data is inlined). */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ data */

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

  /* ------------------------------------------------------------------- FAQ */

  var faqItems = $$('[data-faq] details');
  faqItems.forEach(function (item) {
    item.addEventListener('toggle', function () {
      if (!item.open) return;
      faqItems.forEach(function (other) { if (other !== item && other.open) other.open = false; });
    });
  });
})();
