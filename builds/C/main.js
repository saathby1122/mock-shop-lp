/* mock.shop landing page — build C
   All swappable content lives in DATA; the HTML skeleton already shows the
   default state, so the page is complete without JS. */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ data */
  var DATA = {
    snippets: {
      prompt: { label: 'Prompt', text: 'Build me a storefront from a mock.shop store.\nStart at https://mock.shop/llms.txt' },
      cli:    { label: 'CLI',    text: 'npm i -g @shopify/cli && shopify store create preview' },
      skill:  { label: 'Skill',  text: 'npx skills add Shopify/shopify-ai-toolkit' }
    },

    /* reference/stores.json, inlined so file:// works, plus the copy that
       drives the Start terminal for each pill. */
    stores: {
      streetwear: {
        pill: 'Streetwear', name: 'VibePulse Studio', host: 'apparel-streetwear.mock.shop',
        storefront: 'https://apparel-streetwear.hydrogen.mock.shop/',
        products: 8, variants: 96, collections: 2,
        collectionTitles: ['Concrete Core Essentials', 'Urban Utility Gear'],
        firstProducts: ['Heavyweight Graphic Tee in Smoke Cotton', 'Heavyweight Cotton T-Shirt', 'Soft Grey Hoodie', 'Heavyweight Hoodie', 'Slate Gray Streetwear Pants', 'Oversized Cargo Pants', 'Oversized Fit Streetwear Jacket', 'Topo-Lined Canvas Utility Cap'],
        description: 'Curated streetwear essentials featuring heavy textures, sharp graphics, and limited-edition seasonal drops.',
        grid: 'assets/img/grid-streetwear.webp',
        phrase: 'oversized, heavyweight t-shirts', category: 'streetwear', kinds: 'heavyweight tees and hoodies'
      },
      decor: {
        pill: 'Decor', name: 'Havenly Nest', host: 'home-decor.mock.shop',
        storefront: 'https://home-decor.hydrogen.mock.shop/',
        products: 60, variants: 154, collections: 5,
        collectionTitles: ['Sun-Drenched Living', 'Sculptural Surfaces', 'Reflective Spaces', 'Organized Calm', 'Ritual Illumination'],
        firstProducts: ['Terracotta Throw Pillow', 'Textured Cushion Cover in Clay', 'Handcrafted Terracotta Cushion', 'Terracotta Throw Pillow', 'Terracotta Clay Cushion', 'Terracotta Throw Pillow', 'Burnt Terracotta Linen Throw', 'Luxurious Textured Throw Blanket'],
        description: 'We offer a handpicked collection of sculptural decor, soft textiles, and artisanal accents to elevate your living space.',
        grid: 'assets/img/grid-decor.webp',
        phrase: 'sculptural home decor and soft textiles', category: 'home decor', kinds: 'terracotta cushions and linen throws'
      },
      beauty: {
        pill: 'Beauty', name: 'Lumina Botanica', host: 'skincare.mock.shop',
        storefront: 'https://skincare.hydrogen.mock.shop/',
        products: 29, variants: 79, collections: 4,
        collectionTitles: ['Daily Botanical Purification', 'Luminous Clinical Hydration', 'Targeted Botanical Restoration', 'Essential Protection Rituals'],
        firstProducts: ['Botanical Cleanser in Clear Pump Bottle', 'Daily Renewal Cleanser With Salicylic Acid', 'Botanical renewal cleanser with green tea', 'Botanical Cleansing Toner', 'Soothing sage balancing toner', 'Calm Balance Mist Toner', 'Sage Leaf Toner', 'Renewal Moisturizer with Brightening Actives'],
        description: 'We blend potent clinical actives with soothing plant extracts to create simple, effective daily skincare rituals.',
        grid: 'assets/img/grid-beauty.webp',
        phrase: 'botanical daily skincare', category: 'skincare', kinds: 'botanical cleansers and toners'
      },
      sports: {
        pill: 'Sports', name: 'VigorVibe Active', host: 'activewear-dropship.mock.shop',
        storefront: 'https://activewear-dropship.hydrogen.mock.shop/',
        products: 8, variants: 96, collections: 2,
        collectionTitles: ['Kinetic Compression Series', 'Velocity Layering Essentials'],
        firstProducts: ['Electric Blue Sports Bra', 'Cropped Sports Bra with Graffiti Print', 'Lime Green Athleisure Leggings', 'Fitted Leggings in Neon Lemon', 'Sunbeam Cropped Workout Hoodie', 'Mint Green Activewear Top', 'Violet Zip-Front Performance Jacket', 'Ergonomic Running Belt'],
        description: 'High-performance activewear and sleek gear designed to help you crush your workout with confidence and vibrant flair.',
        grid: 'assets/img/grid-sports.webp',
        phrase: 'high-performance activewear', category: 'activewear', kinds: 'sports bras and leggings'
      }
    },

    startSteps: ['Searching relevant catalogs', 'Creating preview store', 'Installing theme and copying catalog', 'Publishing products and menu'],

    buildSteps: ['Reading theme settings', 'Updating colours and fonts background', 'Restyling buttons, borders and gallery', 'Pushing theme'],
    build: {
      technical: {
        pill: 'Technical',
        prompt: 'Make my store feel fun and loud, like a sticker sheet. Sunny yellow background, chunky black outlines with hard drop shadows, rounded corners, a playful geometric font, and a coral pop for the buy button. Let the product photos swipe like a carousel.',
        result: 'Done. Your storefront now has a sticker-sheet look: a sunny yellow background, bold outlines with hard shadows, and coral buy buttons.'
      },
      vibrant: {
        pill: 'Vibrant',
        prompt: 'Make it bright and electric. Cobalt blue background, white headlines with a thick lime highlighter underline, oversized product photos edge to edge, and a hot pink buy button. Run a marquee of the collection names across the top.',
        result: 'Done. Your storefront is now electric: a cobalt background, lime-underlined headlines, edge-to-edge photos and a hot pink buy button.'
      },
      bold: {
        pill: 'Bold',
        prompt: 'Go brutalist. Pure black background, huge condensed white headlines, thick white rules between sections, square corners everywhere, and a red buy button. Show the product photos in high-contrast black and white.',
        result: 'Done. Your storefront is now brutalist: black background, huge condensed headlines, hard white rules and a red buy button.'
      },
      elegant: {
        pill: 'Elegant',
        prompt: 'Make it quiet and premium. Warm ivory background, a classic serif for headings, generous whitespace, hairline borders, muted charcoal text, and a small-caps buy button in deep green. Let the photos breathe with wide margins.',
        result: 'Done. Your storefront now feels premium: an ivory background, serif headings, hairline borders and a deep green small-caps buy button.'
      }
    }
  };

  /* ------------------------------------------------------------ helpers */
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var FADE = reduceMotion ? 0 : 150;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* fade a .swap element out, mutate, fade back in (150ms crossfade) */
  function crossfade(el, mutate) {
    if (!el) { mutate(); return; }
    if (!FADE) { mutate(); return; }
    el.classList.add('is-fading');
    window.setTimeout(function () {
      mutate();
      // force a frame so the opacity transition runs back in
      void el.offsetWidth;
      el.classList.remove('is-fading');
    }, FADE);
  }

  /* ---------------------------------------------------------- templates */
  var T = {
    card: function (s) {
      return '<img class="grid" src="' + esc(s.grid) + '" width="287" height="166" alt="Eight product photos from ' + esc(s.name) + '">' +
        '<div class="meta">' +
          '<h3 class="name">' + esc(s.name) + '</h3>' +
          '<p class="host">' + esc(s.host) + '</p>' +
          '<p class="desc">' + esc(s.description) + '</p>' +
          '<p class="stats">' +
            '<span><b>' + s.products + '</b> products</span><span class="dot" aria-hidden="true">·</span>' +
            '<span><b>' + s.variants + '</b> variants</span><span class="dot" aria-hidden="true">·</span>' +
            '<span><b>' + s.collections + '</b> collections</span>' +
          '</p>' +
        '</div>';
    },
    startPrompt: function (s) { return 'I want to sell ' + s.phrase + '.'; },
    startResult: function (s) {
      var article = /^[aeiou]/i.test(s.category) ? 'an' : 'a';
      return 'Found ' + s.name + ', ' + article + ' ' + s.category + ' catalog with ' + s.kinds +
        '. Your store is ready with its ' + s.products + ' products and theme. Want to change the look next?';
    },
    steps: function (list) {
      return list.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('');
    }
  };

  /* ------------------------------------------------------------- tabs */
  /* hero + CTA share one state: role=tablist, roving tabindex, arrow keys */
  function initTabs() {
    var lists = $$('[data-tabs]');
    if (!lists.length) return;
    var current = 'prompt';

    function select(key, focusList) {
      if (!DATA.snippets[key]) return;
      current = key;
      lists.forEach(function (list) {
        $$('.tab', list).forEach(function (tab) {
          var on = tab.dataset.tab === key;
          tab.setAttribute('aria-selected', on ? 'true' : 'false');
          tab.tabIndex = on ? 0 : -1;
          if (on && focusList === list) tab.focus();
        });
        var wrap = list.closest('.snippet');
        var code = wrap && $('code', wrap);
        var panel = wrap && $('.well', wrap);
        if (code) code.textContent = DATA.snippets[key].text;
        if (panel) panel.setAttribute('aria-labelledby', $('.tab[aria-selected="true"]', list).id);
        var copy = wrap && $('.copy', wrap);
        if (copy) copy.setAttribute('aria-label', 'Copy the ' + DATA.snippets[key].label + ' snippet');
      });
    }

    lists.forEach(function (list) {
      list.addEventListener('click', function (e) {
        var tab = e.target.closest('.tab');
        if (tab) select(tab.dataset.tab);
      });
      list.addEventListener('keydown', function (e) {
        var tabs = $$('.tab', list);
        var i = tabs.indexOf(document.activeElement);
        if (i < 0) return;
        var next = null;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = tabs[(i + 1) % tabs.length];
        else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = tabs[(i - 1 + tabs.length) % tabs.length];
        else if (e.key === 'Home') next = tabs[0];
        else if (e.key === 'End') next = tabs[tabs.length - 1];
        if (next) { e.preventDefault(); select(next.dataset.tab, list); }
      });
    });
    select(current);
    return { get: function () { return current; } };
  }

  /* ------------------------------------------------------------- copy */
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      // async clipboard first; fall back to the textarea trick if it is
      // unavailable or the permission is denied
      return navigator.clipboard.writeText(text).catch(function () { return legacyCopy(text); });
    }
    return legacyCopy(text);
  }

  function legacyCopy(text) {
    return new Promise(function (resolve, reject) {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.cssText = 'position:fixed;top:-1000px;left:-1000px;opacity:0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
      document.body.removeChild(ta);
      ok ? resolve() : reject(new Error('copy failed'));
    });
  }

  function initCopy() {
    $$('.copy').forEach(function (btn) {
      var label = $('.copy-label', btn);
      var timer = null;
      btn.addEventListener('click', function () {
        var wrap = btn.closest('.snippet');
        var code = wrap && $('code', wrap);
        var text = code ? code.textContent : '';
        copyText(text).then(function () {
          btn.dataset.copied = 'true';
          if (label) label.textContent = 'Copied';
          var live = $('#copy-status');
          if (live) live.textContent = 'Copied to clipboard';
          window.clearTimeout(timer);
          timer = window.setTimeout(function () {
            delete btn.dataset.copied;
            if (label) label.textContent = 'Copy';
            if (live) live.textContent = '';
          }, 1500);
        }).catch(function () {
          if (label) label.textContent = 'Copy';
        });
      });
    });
  }

  /* ------------------------------------------------- pill groups (Start) */
  function setPressed(group, active) {
    $$('.pill', group).forEach(function (p) {
      p.setAttribute('aria-pressed', p === active ? 'true' : 'false');
    });
  }

  function initStart() {
    var section = $('#start');
    if (!section) return;
    var group = $('.pills', section);
    var card = $('.card.main', section);
    var prompt = $('.bubble p', section);
    var result = $('.result', section);
    var steps = $('.steps', section);
    var startBtn = $('#start-store');
    if (steps) steps.innerHTML = T.steps(DATA.startSteps);

    function show(key) {
      var s = DATA.stores[key];
      if (!s) return;
      crossfade(card, function () { card.innerHTML = T.card(s); });
      crossfade(prompt, function () { prompt.textContent = T.startPrompt(s); });
      crossfade(result, function () { result.textContent = T.startResult(s); });
      if (startBtn) startBtn.href = s.storefront;
    }

    group.addEventListener('click', function (e) {
      var pill = e.target.closest('.pill');
      if (!pill || pill.getAttribute('aria-pressed') === 'true') return;
      setPressed(group, pill);
      show(pill.dataset.store);
    });
  }

  /* ------------------------------------------------- pill groups (Build) */
  function initBuild() {
    var section = $('#build');
    if (!section) return;
    var group = $('.pills', section);
    var prompt = $('.bubble p', section);
    var result = $('.result', section);
    var steps = $('.steps', section);
    if (steps) steps.innerHTML = T.steps(DATA.buildSteps);

    group.addEventListener('click', function (e) {
      var pill = e.target.closest('.pill');
      if (!pill || pill.getAttribute('aria-pressed') === 'true') return;
      var v = DATA.build[pill.dataset.style];
      if (!v) return;
      setPressed(group, pill);
      crossfade(prompt, function () { prompt.textContent = v.prompt; });
      crossfade(result, function () { result.textContent = v.result; });
    });
  }

  /* ------------------------------------------------------ device toggle */
  function initDevice() {
    var frame = $('#store-frame');
    var toggle = $('.device-toggle');
    if (!frame || !toggle) return;
    var iframe = $('iframe', frame);

    if (iframe) {
      iframe.addEventListener('load', function () {
        // the fallback image stays visible until the live store has painted
        if (iframe.getAttribute('src')) frame.classList.add('is-live');
      });
      // lazy iframes may not load until scrolled near; a loaded iframe that
      // fired before we attached is handled by the readyState check below.
      try {
        if (iframe.contentWindow && iframe.contentDocument && iframe.contentDocument.readyState === 'complete' && iframe.contentDocument.location.href !== 'about:blank') {
          frame.classList.add('is-live');
        }
      } catch (err) { /* cross-origin: wait for load */ }
    }

    toggle.addEventListener('click', function (e) {
      var btn = e.target.closest('button');
      if (!btn) return;
      $$('button', toggle).forEach(function (b) { b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
      var mobile = btn.dataset.device === 'mobile';
      frame.classList.toggle('mobile', mobile);
      frame.setAttribute('data-device', mobile ? 'mobile' : 'desktop');
    });
  }

  /* --------------------------------------------------------------- faq */
  /* <details name="faq"> already gives native, keyboard-accessible,
     one-at-a-time behaviour. JS adds the height animation. */
  function initFaq() {
    var items = $$('.faq-item');
    if (!items.length) return;
    items.forEach(function (d) { d.classList.add(d.open ? 'is-open' : 'is-closed'); });

    function open(d) {
      d.open = true;
      d.classList.remove('is-closed');
      d.classList.add('is-animating');
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          d.classList.remove('is-animating');
          d.classList.add('is-open');
        });
      });
    }
    function close(d) {
      d.classList.remove('is-open');
      d.classList.add('is-animating');
      var box = $('.faq-a', d);
      var done = false;
      var finish = function () {
        if (done) return; done = true;
        box.removeEventListener('transitionend', finish);
        d.open = false;
        d.classList.remove('is-animating');
        d.classList.add('is-closed');
      };
      if (reduceMotion) { finish(); return; }
      box.addEventListener('transitionend', finish);
      window.setTimeout(finish, 350);
    }

    items.forEach(function (d) {
      var summary = $('summary', d);
      summary.addEventListener('click', function (e) {
        e.preventDefault();
        if (d.open && !d.classList.contains('is-animating')) { close(d); return; }
        if (d.open) return;
        items.forEach(function (o) { if (o !== d && o.open) close(o); });
        open(d);
      });
    });
  }

  /* -------------------------------------------------------------- boot */
  function boot() {
    document.documentElement.classList.add('js');
    initTabs();
    initCopy();
    initStart();
    initBuild();
    initDevice();
    initFaq();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
