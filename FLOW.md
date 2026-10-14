# The animated flow (Start / Build / Test): handoff for the Rails port

> First draft (2026-10-14, branch `flow-animation`). It is written for the session that will move this page into the
> mock.shop Rails app, as HERO.md is for the hero. Everything marked *measured* was run in Playwright's bundled
> Chromium (headless) against this tree served by `python3 -m http.server` (or a gzip-serving copy where it says so),
> with Kyu's own composed page as the reference; items marked *unverified* were not run.

## What it is

The three feature steps under the hero are Kyu Kim's animated flow, round 23 (richardli-design/mock-shop-lp, branch
`kyu/flow-hero-latest` @ d931946, 2026-10-09, `project/flow-lab`): each step is a copy column, a visual and an
Agent terminal.

1. **Start**, "Tell your agent what you're selling": four category pills (Streetwear, Decor, Beauty, Sports), a deck
   of catalog cards that advances to the winning store, its product tiles, then the store's product page.
2. **Build**, "Design the storefront, not the data": the agent restyles the store to Technical, then four theme pills
   (Technical, Vibrant, Bold, Elegant) morph it into each theme, with that theme's prompt and reply in the terminal.
3. **Test**, "A cart that actually works": product page, cart drawer, checkout with the test card, thank-you page,
   driven by a drawn cursor.

Each step runs once when it scrolls into view (the prompt arrives, the checklist works line by line while the visual
plays that beat, the reply streams in), leaves its transcript up, and has a Replay button. Under 600px each step has
its own phone layout (the R21 phone frames; Test rebuilt from the R22 comps). Reduced motion shows every finished
frame at once. With JavaScript off the copy and the whole transcript read as text beside an empty visual frame.

R23 removed the fourth step, Launch. The page's own static START / BUILD / TEST / LAUNCH sections are gone with it:
the hero is followed by this flow, then the storefront preview, the CTA, the FAQ and the footer, unchanged.

## Files

| Path | Origin | Size (gzip -9) |
| --- | --- | --- |
| `flow/flow.js` | **generated**: upstream `flow-core.js`, `stages/start.js`, `stages/build.js`, `stages/test.js`, `flow.js`, concatenated in that order, 35 edits (F1-F6, S1-S10, B1-B9, T1-T4, L1-L6) | 290 KB (94 KB) |
| `flow/flow.css` | **generated**: upstream `flow.css`, `stages/start.css`, `stages/build.css`, `stages/test.css`, concatenated, 4 edits (C1-C4), then the port's `--flow-css` sentinel (C5) | 134 KB (33 KB) |
| `flow/head.js` | **generated**, not from upstream: `html.flow-on`, the flow's error listener and its load backstop | 4.2 KB (1.8 KB) |
| `flow/assets/{start,build,test,shell,video}/` | the 169 files the stages can ask for, byte for byte: 114 WebP, 55 SVG | 573 KB |
| `flow/assets.txt`, `flow/markup.html` | **generated**: the asset keys, one per line (what `--list-assets` prints), and the flow block `index.html` carries (what `--print-markup` prints) | 5.1 KB, 5.5 KB |
| `flow/MANIFEST.sha256` | **generated**: the sha256 of every file above, with the upstream commit and pin, so the Rails landing re-syncs from this repository without the lab ("Re-syncing") | 18 KB |
| `flow-icons/` | **generated** by `tools/flow_icons.py`, for the Rails landing, which serves no SVG file: a PNG of each SVG icon at three times the largest size the flow draws it at, `widths.txt` (each icon's own width) and `MANIFEST.sha256` (those files and what they were drawn from) | 33 KB (the PNGs 18 KB) |
| `tools/flow_port.py` | the generator (python3, stdlib only) | |
| `tools/flow_icons.py` | the icon rasteriser (python3 with Playwright, its Chromium and Pillow) | |
| `index.html` | the head hook, the stylesheet and font links, the three steps' markup, the script tag (below) | |

`flow/flow.js` and `flow/flow.css` start with a generated **PORT NOTES** comment: the upstream path and commit, the
sha256 of each upstream part, and every edit with its upstream file, line and reason. Each part keeps a banner naming
its upstream file, and every edit is marked `PORT (<id>)` in the code. Do not edit them by hand: change
`tools/flow_port.py` and rerun it ("Re-syncing").

Not ported: `glass.js` / `glass.css` (liquid glass: no element uses it in R23, and its dormant code writes a `<style>`,
`data:` URIs and a document-wide MutationObserver), the three product clips (`video/*.mp4`, 1.46 MB: off by default
in R23 and off for good here), 36 asset files no code names (Launch's film, the browser chrome gone since R11, Test's
pre-R22 checkout art, two non-teal glyphs; `DROPPED` in the generator lists each with its reason), the lab pages
(`index.html`, `stage-dev.html`) and `section.html`'s `<head>` with its inline script.

## Load order

Static site (`index.html`):

```html
<head>
  ...
  <link href="https://fonts.googleapis.com/css2?family=Inter...&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
  <link rel="stylesheet" href="hero/hero.css">
  <link rel="modulepreload" href="hero/vendor/three.module.min.js" fetchpriority="low">
  <script src="hero/intro.js"></script>
  <script src="flow/head.js"></script>
</head>
<body>
  ... hero ...
  <link rel="stylesheet" href="flow/flow.css" data-flow-css>
  <link href="https://fonts.googleapis.com/css2?family=Geist+Mono...&family=JetBrains+Mono:wght@700;800...&display=swap" rel="stylesheet">
  <section class="features flow" aria-label="How mock.shop works"> three article.fl-step </section>
  ... storefront, CTA, FAQ, footer, the icon sprite ...
  <script src="main.js"></script>
  <script type="module" src="hero/field.js" data-hero-field async fetchpriority="low"></script>
  <script async src="flow/flow.js" data-flow-script></script>
</body>
```

Why this order:
- `flow/head.js` is **parser-blocking** in `<head>`, so `html.flow-on` is set before the first paint (the checklist
  lines and the reply start hidden, as the steps play them). It replaces upstream's inline
  `document.documentElement.className = 'js'`, which a CSP refuses and which would wipe `hero-on` and the intro's
  classes; it uses `classList`.
- `flow/flow.css` and the flow's fonts link are in **`<body>`, just before the section**: in `<head>` they held up the
  hero's entrance (the flow analysis measured +101 ms on cable, +677 ms on slow 4G for the hero's `.go`). A body
  `<link>` is valid and still styles the section before it paints (Chrome holds the parser at it until it has loaded
  or failed, so nothing after it, the section included, is parsed before; *measured*: with the sheet answered 404
  after 2 s, its error came before the wrapper existed).
- `flow/flow.js` is **one async classic script, the last element of `<body>`**: never parser-blocking and never
  `defer`, because both hold DOMContentLoaded, which the hero's entrance waits for (upstream's six classic scripts
  cost the hero +229 ms of `.go` on cable, as the flow analysis measured). It only looks up elements before it (the
  steps, the wrapper), and it runs whenever it arrives, but **enhances nothing until `flow/flow.css` applies** (edit
  L5: the stylesheet's last rule sets `--flow-css: 1` on `:root`, C5). An async script does not wait for
  stylesheets; upstream's classic scripts did. On this page the parser cannot reach the script before the stylesheet
  is in anyway (the link holds it, and so does `main.js`, parser-blocking, which waits for the stylesheets before
  it), so L5 matters when the sheet fails (the flow goes off: "Fallbacks") and on a page laid out otherwise. It
  follows `hero/field.js`, which still only looks up elements before it.
- `data-flow-script` and `data-flow-css` mark the script and the stylesheet for head.js's error listener (Rails'
  digested names cannot be matched by path); flow.js's L5 also waits on the stylesheet's own `load`/`error` (without
  the mark it waits for the page's `load` event instead).
- No `<link rel="modulepreload">` for the flow: `hero/intro.js` takes the first modulepreload as three.js's URL.
- The page's first fonts link is unchanged; the flow adds its own families in a second one (see "Fonts").

*Measured* (median of 3, 1440x900, CDP throttling, cache off, ms; `dcl.py` from the flow analysis):

| | DOMContentLoaded | hero `.go` | flow ready | field on | load |
| --- | --- | --- | --- | --- | --- |
| gzip, cable: pristine 91ac37c | 220 | 663 | - | 1081 | 779 |
| gzip, cable: this page | 220 | 700 | 739 | 1208 | 1437 |
| gzip, slow 4G: pristine | 905 | 2028 | - | 4780 | 4438 |
| gzip, slow 4G: this page | 774 | 2026 | 3724 | 6014 | 7516 |
| uncompressed, cable: pristine | 312 | 677 | - | 1762 | 1234 |
| uncompressed, cable: this page | 580 | 706 | 1310 | 2264 | 2150 |
| uncompressed, slow 4G: pristine | 1623 | 2326 | - | 9005 | 7266 |
| uncompressed, slow 4G: this page | 4261 | 2238 | 7603 | 12922 | 12038 |

The hero's entrance keeps its time (on slow 4G both pages hit its 1.5 s fail-safe). Uncompressed, DOMContentLoaded
waits for `flow/flow.css` (134 KB raw): `main.js`, a parser-blocking script after it, runs only once the stylesheets
before it are in, so the hero's tabs and Copy button bind later on slow uncompressed links (gzip-served, no change).
The field boots later on slow links because the flow's eager bytes share the pipe (below, "Budget").

That table is the first build's. At 1440x900 most of the field's delay was Build's theme faces (B8's first margin let
them load at once there). *Measured* after B8's change, gzip-served, medians of 4 interleaved runs (the second
verification's `perf.py`): on slow 4G the field comes up at 4960 ms against 4772 on the pristine page (+0.19 s; the
first build: 6036 in the same runs) and the hero's `.go` at 2029 against 2020; on cable 1108 against 1056 ms. The
first view is 93 requests / 1.10 MB (the first build: 101 / 1.26 MB). The uncompressed rows were not re-measured.

Rails layout (a sketch, *unverified*), next to the hero's tags (HERO.md). `landing.js` already adds `html.js`, which
the flow does not use; it needs head.js's `flow-on`:

```erb
<%= javascript_include_tag "landing", preload_links_header: false %>
<%= javascript_include_tag "landing/hero/intro", preload_links_header: false %>
<%= javascript_include_tag "landing/flow/head", preload_links_header: false %>          <%# synchronous, in <head> %>
...
<%= stylesheet_link_tag "landing/flow/flow", data: { flow_css: "" }, preload_links_header: false %>   <%# in <body>, before the section %>
<section class="flow" aria-label="How mock.shop works" data-flow-assets="<%= flow_assets.to_json %>"> ... </section>
...
<%= javascript_include_tag "landing/flow/flow", async: true, crossorigin: "anonymous", data: { flow_script: "" }, preload_links_header: false %>  <%# last %>
```

`crossorigin: "anonymous"` matters wherever the script comes from another origin (the CDN host,
`https://cdn.shopify.com/shopifycloud/mock_shop/`, on every non-Cloudflare host): without it the browser mutes the
script's errors to `Script error.` with no file name, and head.js's listener cannot tie a parse error or a throw to
the flow. *Measured* with a cross-origin server and a throw injected before ready: before the fix `flow-on` stayed,
and every checklist line and reply stayed hidden; now head.js's load backstop takes `flow-on` off at the page's load
event (13/13 lines, 3/3 replies). With the attribute and the CDN's `access-control-allow-origin: *` (HERO.md,
measured on both CDN paths) the error is caught at once, as same-origin; a healthy cross-origin flow.js runs either
way (`data-flow="on"`). Never `use-credentials` (against ACAO `*` the script would fail CORS and not run).

## DOM contract

```html
<section class="features flow" aria-label="How mock.shop works">     <!-- the wrapper: any element with class flow -->
  <article class="fl-step" id="start" data-stage="start" data-prompt="load" aria-labelledby="start-h"
           data-section-name="start" data-viewable-component>
    <header class="fl-copy">
      <p class="fl-eye">Start</p>
      <h2 class="fl-h" id="start-h">Tell your agent what you're selling</h2>
      <p class="fl-body">...</p>
      <div class="fl-pills" role="group" aria-label="Category"></div>   <!-- Start and Build: the stage fills it -->
    </header>
    <div class="fl-show">
      <div class="fl-vis" aria-hidden="true"><div class="fl-vis-in"></div></div>   <!-- the stage draws in here -->
      <div class="fl-term">
        <div class="fl-bar"><span class="fl-lights" aria-hidden="true"><i></i><i></i><i></i></span>
          <span class="fl-title">Agent</span><span class="fl-bar-end"></span></div>  <!-- Replay goes in fl-bar-end -->
        <div class="fl-rule"></div>
        <div class="fl-model">
          <div class="fl-box"><p class="fl-prompt">PROMPT</p></div>
          <ul class="fl-list"><li class="fl-item">LINE</li> ...</ul>   <!-- 4, 4, 5 lines -->
          <p class="fl-reply">REPLY</p>
        </div>
      </div>
    </div>
  </article>
  ... build, test ...
</section>
<script async src="flow/flow.js" data-flow-script></script>               <!-- after the wrapper -->
```

The three articles are upstream's `section.html` lines 32-120 **verbatim**, apart from `data-section-name` and
`data-viewable-component` on each (Dux); `tools/flow_port.py` checks that `index.html` carries exactly that
(`--print-markup` prints it). What each part requires:
- **The wrapper** is one element with class `flow` around the steps. It is not a second `<main>` (upstream's is a
  `<main class="flow">`; the page has `main#main`). Here it is also `.features`, which keeps the page's black block
  and its 48px top radius; `.flow`'s padding wins by load order (flow.css comes later, same specificity). Rails: a
  `div.flow`, or a `section` with an `aria-label`. It may carry `data-flow-assets` (below); flow.js sets
  `data-flow="on"` on it once every step is mounted, and `"off"` (as head.js does) whenever the flow does not run:
  a failed script or stylesheet, or a browser head.js leaves off.
- **The stylesheet** `flow/flow.css` must apply before flow.js enhances anything: its last rule,
  `:root { --flow-css: 1; }`, is what flow.js waits for (L5). Mark its `<link>` with `data-flow-css` (head.js turns
  the flow off on its `error`; L5 waits on its `load`). If Rails bundles the flow's CSS into another file, keep that
  rule last in it.
- **`data-stage`** names the stage (`start`, `build`, `test`); **`data-prompt="load"`** makes the prompt arrive whole
  instead of being typed (all three).
- **The text is read from the markup once**: the prompt is `.fl-prompt`'s text (trimmed), each line an `li`'s
  `textContent` (keep each `li` on one line in ERB: it is not trimmed), the reply the child nodes of `.fl-reply` (text
  split into words; elements and `<br>` kept). Start's other categories and Build's themes keep their prompts and
  replies in `stages/start.js` (CATEGORIES) and `stages/build.js` (COPY): the server renders only the defaults
  (Streetwear, Technical), and Build's default prompt and reply equal `COPY.tec` (a Rails test should pin that).
- **Nothing in the markup has a `style` attribute**, and the scripts write styles only through CSSOM.

What the scripts add:
- head.js: `flow-on` on `<html>`.
- flow.js, per step: `span.fl-typed` + `span.fl-caret` in the prompt, `button.fl-send` ("Copy prompt", two glyph
  `<img>`s) and `span.fl-copied[aria-live=polite]` in the box, a dot + spinner in each line, `button.fl-replay`
  ("Replay this step") in the bar; state classes `is-run`, `is-done`, `is-final` on the article, `is-ready |
  is-typing | is-typed | is-loading | is-sent` on `.fl-box`, `is-in | is-on | is-done` on the lines, `is-in` on the
  reply, `on` on its words; `--fl-s` / `--fl-x` on `.fl-vis-in` (the stage's scale to its frame). The stages build
  their visuals inside `.fl-vis-in`, and their pills inside `.fl-pills`: Start `span.start-pill[role=button]
  [tabindex=0][data-cat]` (the selected one `aria-current="true"`), Build `button.build-pill[data-t][aria-pressed]`
  (inert, `tabindex=-1`, until Build has played) plus an `aria-hidden` thumb.
- Globals: `window.FLOW` (the runtime; `FLOW.asset`, `FLOW.hydrate` are the port's) and `window.__flow` (each step's
  `{name, root, run, reset, final, S}`: `__flow[1].final()` paints Build's end frame).
- Ids: `start`, `build`, `test` (the articles), `start-h`, `build-h`, `test-h`, and Build's `build-fg<N>hi|lo`
  gradients. None collides with the page's.
- Document-global CSS names: the `:root` tokens `--fl-*`, `--ease-flow`, `--ease-emph` and the port's `--flow-css`,
  and eight `@keyframes`: `fl-load`, `fl-blink`, `fl-fire`, `fl-up`, `fl-rot`, `fl-dot`, `fl-shim`, `build-up` (none
  is the page's or the hero's; grep the Rails landing CSS for them before linking flow.css next to it).
- Document-level listeners: Start's `click` and `keydown` (its pills), `visibilitychange` (flow-core). One
  constructed style sheet in `document.adoptedStyleSheets` (Start's product-page positions).

## Asset URLs: `FLOW.asset()` and `data-flow-assets`

Every asset URL the flow builds is `FLOW.asset(key)`, the key being the file's path under `flow/`
(`assets/start/thumb-vp-1.webp`). Upstream built them from each stage script's own `document.currentScript` plus
`../assets/<stage>/`, and the shell's glyphs document-relative (`assets/shell/...`): one concatenated script has one
`currentScript`, and Propshaft serves every file under a digested name that no relative URL can know. So:

- `data-flow-assets` on the wrapper: an optional JSON object key -> URL, read once (Rails: `asset_path` of each key,
  as the hero's `data-products`). A missing key, invalid JSON, or a value with a quote, an angle bracket or white
  space (the URLs go into HTML strings) falls back, silently.
- The fallback is the key resolved against `flow/flow.js`'s own URL: on this site, `flow/assets/...`. **In Rails the
  fallback is an undigested `/assets/landing/flow/assets/...` URL, which Propshaft 404s**, so there the map must hold
  every key: pin it with a test against the generator's `--list-assets` (169 keys).
- Why a map and not Propshaft's `RAILS_ASSET_URL("...")` (1.3.2 compiles it in JavaScript: its
  `Propshaft::Compiler::JsAssetUrls`, read in the gem's source): it rewrites only a literal path, and the flow builds
  its names at run time (`'thumb-' + store + '-' + n + '.webp'`, `'pdp-' + category + '-' + icon + '.svg'`, ...), so
  it would mean turning upstream's code into 169 literals; and it writes `relative_url_root + "/assets/..."`, never the
  asset host, so on the CDN-served hosts the URLs would point at the page's own origin. `asset_path` in the view
  honours the asset host and needs no change to the code.
- The map's weight in the HTML (*measured* on this page with 8-hex digests): 18.2 KB of attribute with root-relative
  `/assets/...` URLs (14.8 KB of JSON, `&quot;`-escaped by ERB), 26.0 KB with absolute CDN URLs; gzipped, the page
  grows by 3.6 and 4.0 KB.
- Build's SVG strings also use same-document references, `stroke="url(#build-fg<N>hi)"` (its gradients): fragment-only
  and CSP-neutral; the generator allows exactly those. A Rails `url(` grep over the flow's JS must allow `url(#`.
- The clips' `data-src` stays its key (`assets/video/tee-front.mp4`): clips never load (`vidOff`), and Build reads
  the clip's name from it. Their posters go through `FLOW.asset`.
- Build pairs photos across themes by file name (`slotsOf`); with digested URLs (`tee-front-1a2b3c4d.webp`) that
  broke the morph's pairing, so the name now drops a `-<8 hex>` digest (edit B7). The generator asserts that no
  copied file ends in `-<8 hex>` itself.

*Measured* with every key mapped to a digested URL (`assets/x/name-<8 hex>.ext`, served by stripping the digest):
all 74 flow asset requests at load used the mapped URLs (none undigested); Start's, Test's and Build's frames
(Elegant and Bold after a switch) were identical to the run without a map (0 px); and with a probe in `slotsOf()`,
the names Build pairs by were identical to the unmapped run, while the same run with B7 reverted gave Elegant's
slots `tee-back-08e3ae79`-style names that pair with nothing.

A sketch (*unverified*; `FLOW_ASSETS` would be a committed list of the keys below, pinned by a test):

```erb
<% flow_assets = MockShop::Discovery::Landing::FLOW_ASSETS.to_h { |key| [key, asset_path("landing/flow/#{key.delete_prefix("assets/")}")] } %>
```

The keys (`flow/assets.txt` holds them one per line, as `python3 tools/flow_port.py <lab> --list-assets` prints them;
the Rails re-sync copies it):
- `assets/build/` (26): bold-cart.svg, bold-chevron.svg, bold-minus.svg, bold-next.svg, bold-plus.svg, bold-prev.svg,
  bold-search.svg, elegant-cart.svg, elegant-chevron.svg, elegant-minus.svg, elegant-plus.svg, elegant-search.svg,
  technical-cart.svg, technical-chevron.svg, technical-minus.svg, technical-plus.svg, technical-search.svg,
  tee-back.webp, tee-front.webp, tee-in-use.webp, vibrant-cart.svg, vibrant-chevron.svg, vibrant-minus.svg,
  vibrant-next.svg, vibrant-plus.svg, vibrant-search.svg
- `assets/shell/` (3): copy-vector-teal.svg, dot-teal.svg, send-image.svg
- `assets/start/` (127): thumb-{bd,ch,ee,hn,lg,sg,up,va,vp,vt,vv,zm}-{1..8}.webp (96), cleanser-dark.webp,
  cleanser-front.webp, cushion-front.webp, cushion-lifestyle.webp, cushion-side.webp, jacket-back.webp,
  jacket-front.webp, jacket-lifestyle.webp, pdp-{beauty,decor,sports,streetwear}-{cart,chevron,minus,plus,search}.svg
  (20), tee-back.webp, tee-front.webp, tee-lifestyle.webp
- `assets/test/` (10): drawer-icon-{minus,plus,trash,x}.svg, pdp-icon-{cart,chevron-down,minus,plus,search}.svg,
  tee-front.webp
- `assets/video/` (3): tee-back-poster.webp, tee-front-poster.webp, tee-in-use-poster.webp

At load, before any scrolling, the stages request 74 of them (264,837 B) at 1440x900 and 58 (256,744 B) at 390x844;
a Start pick brings in that category's deck and photos.

## CSP (measured)

Run with the policy as a response header: `default-src 'none'; script-src 'self'; style-src 'self'
https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self'` (the landing's shape, with Google
Fonts allowed so the fonts do not confound it), through six scenarios: the page scrolled through at 1440x900 and
390x844 with every Start category and Build theme picked, `?lab&play=all&speed=4` at both sizes, a 600px crossing
both ways, and reduced motion. **Every scenario had exactly one violation, the page's own** (the icon sprite's
`style="position:absolute"`, index.html:285, already in HERO.md's list), and none from the flow or the hero (the
same again after the second round of fixes, with `data-flow="on"` in every scenario).

The frames the CSP fixes are about, compared under that policy against Kyu's composed page without one
(`hero-stage/hero-lab/?final=1`), both heroes hidden so their layers do not differ: Start's end frame (the product
page), Test's thank-you page, Test's checkout at the shipping and at the payment beat, Build's scan light round the
boxes and its dotted frames. Mid-run frames were frozen at a trigger (every animation, SVG timeline, rAF and pending
timer stopped in the same task; the trigger's own animations set to the same time on both pages). **All 0 px at
1440x900 and at 390x844** (the payment beat is two frames 2,735 px apart that Kyu's own page alternates between;
every port run equals one of them exactly). With the fixes reverted on the same page, the same harness reported
11-61k px at max 180-219 and up to 283 violations from flow/flow.js.

What the flow needs from a policy: `script-src` for `flow/head.js` and `flow/flow.js`, `style-src` for
`flow/flow.css` (and, here, Google Fonts' CSS), `img-src` for its assets, `font-src` for its fonts. **No**
`'unsafe-inline'`, `'unsafe-eval'`, nonce, `connect-src`, `media-src`, `worker-src`, `blob:` or `data:`. The fixes:
- Upstream's inline `<script>` for `html.js` -> `flow/head.js` (external), `.js` -> `.flow-on` in the CSS (C2).
- `style="..."` inside HTML strings (Build's scan-light rects and dotted-frame SVG, Test's ~94 placed checkout and
  thank-you parts) -> `data-st="..."`, moved into the inline style through CSSOM by `FLOW.hydrate()` in the same task
  (F3, B5, B6, T3, T4). Without it, under any CSP without `'unsafe-inline'`, Test's checkout and thank-you collapse
  and Build's light and dots vanish.
- Start's `<style>` fallback for browsers without constructable style sheets -> removed (S7); head.js turns the flow
  on only where they exist.
- The clips' `fetch()` + `blob:` path -> removed (F4, F5).
- `innerHTML` stays (13 sites: constant templates and `esc()`-escaped data; the landing's policy has no Trusted
  Types). The generator stops on any new one.

**SVG icons and the Rails no-SVG rule.** 55 of the assets are SVG `<img>` icons, and #1484's `StaticAssetsTest`
fails any SVG on the asset load path. Options (a decision for the user):
1. A vetted exception for `landing/flow/` only: narrow the test to "no SVG outside landing/flow/, and each one there
   has no `<script`, `on*=`, `foreignObject`, `javascript:` or non-fragment href". The `<img>`s and the JS stay as
   they are (an SVG loaded as an image is its own document with scripts off; under the policy above it reports
   nothing, *measured* on this site). It reverses part of #1484's blanket rule.
2. Rasterise them to PNG at 3x and map the `.svg` keys to the PNGs in `data-flow-assets`: no policy change, but the
   pixels differ from the SVGs and regenerating needs a browser. The Rails landing took this one: `tools/flow_icons.py`
   draws the PNGs ("Re-syncing").
3. Inline SVG is not a fit: every file's root carries `style="display: block;"` (CSP), the Figma ids repeat across
   files (`Vector`, `clip0_0_4`), and the stage CSS targets `img` in those slots.

## Fonts

The flow renders in Inter (the page's own link; the same file as upstream's), JetBrains Mono 400/500 (the page's
link) **and 700/800** (Technical), Geist Mono 400/500 (the terminal's title and Replay), and Build's theme faces:
Space Grotesk 400/500/700 (Vibrant), Anton, Archivo Black and Archivo 400-700 (Bold), Instrument Serif and its italic,
Instrument Sans 500/600 and Newsreader 400 (Elegant). The second link loads exactly those (upstream's list less
Inter and the unused Permanent Marker). SF Pro (Default theme, Start's product page) is a system font, never loaded.

Build warmed all 19 theme faces at mount, so every visit downloaded them at load. Now (B8) the warm-up runs when
Build's article first comes on screen. The first version waited for it to come within one viewport, but Build's top
(1704px at 1440x900, 1920x1080 and 2560x1440, 1521px at 1024x768) is less than two viewport heights down at the
common desktop sizes, so there the faces still loaded at once, and on slow 4G (gzip, 1440x900) the hero's field came
up ~1 s later because of them. *Measured* now: 6 faces loaded 2.5 s after load at every size from 390x844 to
2560x1440 (Inter, JetBrains Mono 400/500/700/800 and Geist Mono 400, which the first view draws), all 20 once Build
is in view. So the faces the warm-up still fetches are Vibrant's, Bold's and Elegant's, which show only after
Build's scripted run (it ends on Technical, whose JetBrains Mono 700/800 are already in), once the pills are live;
Build plays when its visual's top crosses 72% of the viewport, after its copy column has come on screen. Under reduced
motion the pills are live at once, so a pick in the first moments after Build comes on screen can show a fallback
font briefly (`display=swap`) before the face arrives.

Rails self-hosts (Google Fonts is outside the landing's policy; numbers from the Rails analysis): JetBrains Mono
700/800 need only two more `@font-face` rules (the zone's variable file covers 100-800); eight families are new, about
185 KB of latin WOFF2 with their OFL files (Geist Mono 23 KB, Space Grotesk 22 KB, Instrument Serif 31 KB in two
files, Instrument Sans 30 KB, Newsreader 23 KB, Anton 12 KB, Archivo Black 10 KB, Archivo 35 KB). Put their
`@font-face` rules in a stylesheet of their own (or next to landing.css's, as the fonts PR does for Inter), **not**
in `flow/flow.css`: the generator refuses `@font-face` there (its output check), and Rails changes stay out of the
ported CSS so a re-sync reproduces it byte for byte.

## Knobs (behind `?lab`)

Upstream's, read only when the query has a `lab` parameter (as the hero's): `?lab&final=1` (every step at its
finished frame), `?lab&play=all|start|build|test` (start now, no scrolling), `?lab&step=<name>` (that step alone: the
others are removed from the page), `?lab&rm=1` (reduced motion), `?lab&speed=N` (faster sleeps),
`?lab&cat=decor|beauty|sports` (Start opens on that category). `?vid=1` (the clips) and `?glass=` are gone.
*Measured*: without `lab`, `?step=build`, `?final=1`, `?cat=decor`, `?play=all`, `?rm=1`, `?speed=8` and `?vid=1`
change nothing (three steps, the plain title, nothing final, Streetwear, speed 1, no MP4 requested); with it they
work. The check URL is `?lab&hold=8&final=1` (`hold` is the hero's and freezes the hero; it does not freeze the
flow).

## Fallbacks and modes

| Situation | What happens (measured unless noted) |
| --- | --- |
| JS off | copy, eyebrow, heading, body; the full prompt, every checklist line and the reply in the terminal, which grows to fit them (C3: upstream's fixed box, sized for the animated terminal that scrolls as it writes, hid Build's reply at 1024x768 and on phones, and lines of every step at 320, in a scroller with no visible scrollbar); an empty visual frame (upstream's); no pills, Replay or Copy prompt. Documents 5644 / 5367 / 4982 / 5636 / 5682px at 1440 / 1280 / 1024 / 768 / 390 (the terminals keep their height where the transcript fits) |
| `flow/flow.js` blocked, 404 or unparsable | head.js takes `flow-on` off, the wrapper gets `data-flow="off"`: the JS-off transcripts, nothing enhanced. The console has only the browser's load error (or the parse error itself) |
| `flow/flow.js` throws before it reports ready | `flow-on` off and `data-flow="off"`, so every line and reply shows (the terminals grow, C3). Steps mounted before the throw keep their enhanced terminals and still play when scrolled to; later ones stay static, and the step whose stage threw in `mount` keeps an empty prompt box (the shell empties it just before) with its lines and reply. head.js ties the error to the file by its URL, so the script must be same-origin or loaded with `crossorigin="anonymous"` from a CORS host ("Load order"); otherwise its load backstop turns the flow off at the page's load event (*measured*: cross-origin without the attribute, 13/13 lines and 3/3 replies shown after load) |
| `flow/flow.css` 404, blocked or failing | head.js takes `flow-on` off on the stylesheet's `error`; flow.js then enhances nothing (L1, `data-flow="off"`). Without the `data-flow-css` mark, or with a sheet that loads but lacks the sentinel (an older file, or one cut short), flow.js (L5) waits for the page's load event and turns the flow off then. The steps read as plain text in the page's own styles: 4397px at 1440, 4561 at 390, no sideways scroll (before L5 the stages built into the unstyled markup: a 38.6k px page, 1593px wide) |
| `flow/flow.css` late | flow.js waits for it (L5) and starts when it applies (*measured* with a 2.5 s delay, also with the link unmarked: `data-flow="on"` right after the sheet, frames identical to a normal load) |
| `flow/flow.js` never answers | `flow-on` stays, so the checklist lines and replies stay hidden (the prompts show) until the browser gives up on the request: the script holds the load event, so the backstop waits too |
| A browser without Web Animations' `getAnimations()`, `matchMedia` or constructable style sheets (Safari < 16.4, Firefox < 101) | no `flow-on`: flow.js does nothing but mark the wrapper `data-flow="off"` (L1), and the page shows the JS-off transcripts (*unverified* in those browsers; the gate is a feature test) |
| Reduced motion | every step at its final frame at load, Build's pills live at once, switches instant, no running animation; the site's global reduced-motion rule also stops Kyu's <=200ms micro-transitions |
| Crossing 600px | each stage rebuilds for the other layout, at its end frame once it has played, else at its mount frame (upstream's) |
| Opened from `file://` | the flow runs (classic scripts, assets from disk); the console has only the hero's four module CORS errors (HERO.md) |
| No IntersectionObserver | each step runs at once; Build's font warm-up runs at once (*unverified*) |

## Dux tags (for the Rails landing; inert here)

- Each `article.fl-step`: `data-section-name="start|build|test"` and `data-viewable-component` (markup).
- Start's pills: `data-component-name="store-pill-<category>"` and `data-component-extra-store="<the winning store's
  subdomain>"`: apparel-streetwear, home-decor, clean-beauty, apparel-snowwear (from the stage's own data; JS, S6).
- Build's pills: `data-component-name="style-pill-<technical|vibrant|bold|elegant>"` (JS, B3).
- Copy prompt and Replay: `data-component-name="copy-prompt"` / `"replay"` (JS, L3).
- One click per press: a Start pick dispatches one click, on its pill, by mouse and by Enter or Space (the stage
  calls the pill's `click()`, S10), and restarts the step through Replay's own handler without clicking Replay
  (`'fl-replay'` on the button, S9 and L6). Upstream clicked Replay, so Dux reported every pick as a Replay press
  too, and a key pick as that alone.

The pills and buttons are built in JS, so a Rails test can only grep `landing/flow/flow.js` for those templates.

## Budget (measured)

- **Bytes:** `flow/flow.js` 94 KB, `flow/flow.css` 33 KB, `flow/head.js` 1.8 KB gzipped (429 KB raw together:
  290,202 + 134,383 + 4,218 B, of which the three PORT NOTES comments are 21.3 KB). Images at load: 74 requests / 265 KB
  at 1440x900, 58 / 257 KB at 390x844 (all three stages mount at load, wherever the section is; upstream's
  behaviour). Fonts at load: 6 faces at every size, the theme faces only once Build comes on screen (above).
  index.html went from 9.0 to 8.1 KB gzipped, main.js from 19.0 to 11.4 KB raw, styles.css from 24.4 to 13.5 KB raw.
- **Timing:** "Load order". On slow links the field boots a little later (gzip, slow 4G, 1440x900: 4.96 s vs 4.77 s
  on the pristine page; 6.0 s before B8 waited for Build to come on screen): the flow's scripts, styles and images
  share the bandwidth with three.js and field.js.
- **At rest:** Build's clip watcher ran a requestAnimationFrame loop forever once Build had played, on or off screen,
  with nothing to drive (the clips are off); B4 stops it. *Measured* at `?final=1`, everything settled: 0 rAF
  callbacks a second here vs 60 on Kyu's page, with Build in view or off screen. Build's 4 Hz idle tick (on Vibrant,
  the carousel's swipe every 2.5 s) ran for the life of the page too, swiping with every step off screen; B9 runs it
  only while Build is on screen and the tab visible. *Measured* (every step played by scrolling, Vibrant picked, then
  every step off screen): 0 flow timers a second (was 4 intervals a second plus the swipes' timeouts) and 0.2 ms/s
  of main-thread work at 1440 (pristine page 0.1; it was 4.7), 0.7 ms/s on a 390@3x phone (pristine 0.1; it was
  14.8). In view the swipes keep upstream's cadence (gaps of 2500 and 2750 ms on both, the tick's 250 ms grid); back
  on screen the next comes ~1.4 s on (the 1.2 s that follows a switch, plus the tick), where upstream's carousel had
  carried on swiping unseen.
- **Heights:** the flow block is 2586px at 1440 (the old block 3335), so everything below moves up 749px. Documents:
  5780 / 5503 / 5033 / 6156 / 6410 at 1440 / 1280 / 1024 / 768 / 390 (JS off: 5644 / 5367 / 4982 / 5636 / 5682; the
  1024 and 390 ones grew by 85 and 55px when the fallback terminal grew to its transcript, C3).

## Re-syncing from upstream

```sh
python3 tools/flow_port.py /path/to/mock-shop-lp/project/flow-lab                  # writes flow/
python3 tools/flow_port.py /path/to/mock-shop-lp/project/flow-lab --check          # compares; exit 1 on a difference
python3 tools/flow_port.py /path/to/mock-shop-lp/project/flow-lab --print-markup   # the block index.html must carry
python3 tools/flow_port.py /path/to/mock-shop-lp/project/flow-lab --list-assets    # the data-flow-assets keys
python3 tools/flow_icons.py            # then flow-icons/, the icons for the Rails landing (Playwright and Pillow)
python3 tools/flow_icons.py --check    # draws them again and compares; exit 1 on a difference
```

- **What the Rails landing takes, and how.** Besides `flow.js`, `flow.css`, `head.js` and `assets/`, the generator
  writes (and `--check`s) `flow/assets.txt`, what `--list-assets` prints, `flow/markup.html`, what `--print-markup`
  prints, and `flow/MANIFEST.sha256`, every file's sha256 with the upstream commit and the pin (how many upstream
  files, and the sha256 of their listing; `shasum -a 256 -c flow/MANIFEST.sha256` from the root checks it), so the
  Rails landing re-syncs from this repository without the lab: the mock-shop zone's
  `bin/rails "landing:resync[/path/to/this/checkout]"` takes a clean, committed checkout, checks every file against
  the manifests, copies the scripts (by name, so a new one stops it), the stylesheet, the list and the WebPs byte for
  byte, and makes its Start, Build and Test partials from `flow/markup.html` (HERO.md's files too). The block round
  the three articles (the stylesheet and fonts links, the section) is mirrored by hand there, so when it changes that
  re-sync stops until the Rails side is redone.
- **The icons** (`tools/flow_icons.py`): the Rails landing serves no SVG file, so it takes a PNG of each SVG icon and
  gives it back its SVG's width with CSS. The script serves this checkout on 127.0.0.1 and plays the flow in
  Playwright's Chromium offline: Chromium resolves no other host, so the page's Google Fonts fail at once and the run
  needs no network (the fonts do not change how large the flow draws its icons; a run with them drew the same files).
  It plays all three steps through, then each other Start category's and every Build theme's final frame, at 16
  viewports from 320 to 2560 wide, the phones at dpr 3 (about 13 minutes), and writes `flow-icons/`: each SVG drawn at
  three times (rounded up) the largest size the flow draws it at, on a transparent background (a square SVG gets a
  square PNG); `widths.txt`, each icon's width as Chromium lays the SVG out (a whole number of 1/64px) and whether the
  flow sizes its `<img>` by a width or height attribute; and `MANIFEST.sha256`, the sha256 of those files and of what
  they were drawn from (every SVG, `flow/flow.css` and `flow/flow.js`). It stops on a page that does not load, on an
  SVG the page never draws, on an icon with a width or height attribute in one place and none in another, and on a
  PNG with ink where its SVG draws nothing or none where it draws. It warns where another run could draw a PNG a
  pixel off: where a transform makes an icon's largest size (sampled every 50 ms), within 0.02 PNG pixels of a whole
  one that the icon's laid-out size alone does not pass.
  `shasum -a 256 -c flow-icons/MANIFEST.sha256` fails once an input has changed: rerun the script then and commit
  `flow-icons/` with the change, because the Rails re-sync refuses icons that were not drawn from the `flow/` it
  takes. The PNGs depend on the Chromium that draws them (the manifest names it), so another Chromium can differ in
  antialiasing; `python3 -m playwright install chromium` gets Playwright's own.

- It reads the five scripts, the four stylesheets, `section.html` and the 169 assets, and executes nothing from that
  repository (not even git). The output depends only on the upstream bytes: a rerun reproduces the files byte for
  byte (`--check` exits 0, also from another working directory and another copy of the lab). Files under `flow/` it
  does not generate are removed.
- **The pin covers every file it reads or copies** (`PIN`: sha256 at d931946). If any differs, it stops and lists
  them; review the change, rerun with `--commit <sha>` (the headers then name that commit), and update `PIN_COMMIT`
  and `PIN` with the lines it prints. Every other file under upstream's `assets/` must be in `DROPPED`, so a new
  upstream asset stops it too, as does a file name spelled out in the code that it does not copy.
- Each edit is a literal substitution that must match exactly as often as stated, so an upstream change under one
  stops the script with the anchor it could not find.
- **The output is checked too** (outside the anchors; comments skipped by hero_port.py's JavaScript scanner): no
  static import, `import()` or export; none of `fetch(`, `XMLHttpRequest`, `EventSource`, `WebSocket`, `Worker`,
  `serviceWorker`, `importScripts`, `createObjectURL`, `Blob`, `eval(`, `Function` (`window.Function` too),
  `document.write`, `insertAdjacentHTML`, `.outerHTML`, `setAttribute('style'`, `createElement('style')`, `toDataURL`,
  `sendBeacon`, `localStorage`, `new Audio` or string timers; in a string, no `style=`, inline handler, `javascript:`,
  `data:` or `blob:` URL, `@import`, `srcset`, literal `src=` / `poster=` URL or `url()` other than `url(#...)`, and no
  `<style>`, `<link>`, `<script>`, `<iframe>`, `<frame>`, `<object>`, `<embed>`, `<audio>`, `<source>`, `<track>`,
  `<base>`, `<meta>` or `<form>`; every `src="` (or `src='`, or unquoted) concatenation followed by `FLOW.asset(`, every
  `.src` / `.poster` / `.srcset` assignment and `setAttribute` of one a `FLOW.asset()` URL, every literal
  `FLOW.asset()` key under `assets/`, every clip poster a `FLOW.asset()` URL; `location.search` and
  `document.currentScript` only in flow-core's part; `.innerHTML` exactly as often as upstream has it; and the
  timers that repeat (`setInterval`, `requestAnimationFrame`, `ctx.every`, `ctx.raf`) exactly as often as `LOOPS`
  lists them, each reviewed to stop at rest. The stylesheet: no `url(`, `@import`, `@font-face`, `@charset`, `data:`,
  absolute URL or `.js` selector, and `--flow-css` set only by its last rule. A hit stops it with the file, line and
  text.
- **index.html is checked, not written**: the head hook after intro.js, the flow block verbatim (the stylesheet's
  `data-flow-css` included), the script last in `<body>`, no modulepreload but three.js's. Edit index.html by hand
  (`--print-markup`) when the markup changes.
- Not generated: the page's own edits (`styles.css` kept `.features`' background and radius and lost the old
  sections' rules; `main.js` lost the Start / Build pill code and the image warming).

## How to verify

Use Playwright's bundled Chromium (`channel='chromium'`, headless). Serve this folder, a pristine copy of the page
before the port (`git archive 91ac37c`), and the upstream project (Kyu's composed page is
`hero-stage/hero-lab/index.html`). The scripts of this round are in `/tmp/hero-port/flow-build/checks/` (scratch, not
committed, may not survive); the per-section capture tools are the flow analysis's `cap.py` / `cmp.py`. Results of
this build:

1. **Console:** none, through a full scroll with every step played to its end at 1440x900, 1280x800, 768x1024 and
   390x844 (mobile), and at load and at `?lab&final=1` at 18 widths from 320 to 2560; no horizontal scroll anywhere;
   `data-flow="on"` everywhere.
2. **The flow matches Kyu's:** element screenshots of each step's final frame (`?lab&final=1` here, `?final=1` on the
   composed page), with both heroes hidden: **0 px** at 1440 and at 390 (mobile, dpr 3) for the three steps, each
   Start category and each Build theme (reduced motion: instant switches; and with motion, once the switch has
   settled: Technical's re-switch alone shows one 52px row at max 1 at 1440, with every element's rect, class and
   inline style in the stage identical). With the heroes running, 390 is 0 px too; at 1440 the steps differ by
   4.5-9.3k px at max 1-20, all in the visuals' gradient fades and one sub-pixel row: rects and computed styles are
   identical, and the same comparison with the heroes hidden is 0-1 px, so this is the two heroes' compositing, not the
   flow (Kyu's own composed page differs from his standalone section by as much). At the sizes where the stage is
   scaled (`--fl-s` below 1: 1024-1280, 600-768, 360) the heroes must be **removed** (`display: none`), not hidden: with
   a hero above the flow, even `visibility: hidden`, the stage rasterises differently, up to max 20-48 on photos and
   card edges (e.g. 1024, Build: one 392px row at max 48), as Kyu's own composed page does against his
   `flow-lab/section.html`; with both heroes removed, or against `section.html`, it is 0 px (the second verification
   measured 338 of 350 comparisons at 0). That is the hero's compositing, not a change to the flow. After the fixes
   (B8, B9, C3-C5, L5): 0 px at 1440 and 390 for the three steps and every Build theme, reduced motion and settled.
3. **The hero:** unchanged at its natural viewport (`?lab&hold=8`, the pristine page's baseline): 0 px at 1280, 1024,
   768 and 390. At 1440 the first build showed 12 isolated pixels at 1/255 in the scrim's blurred background in most
   loads, bisected to Build's theme fonts arriving while the hero settled (Build sat inside the warm-up's one-viewport
   margin at 1440x900); with the warm-up waiting for Build to come on screen (B8) no theme font loads during the
   hero's entrance, and the hero is 0 px at 1440 too: all 36 pairs of 6 port and 6 pristine runs, interleaved. At
   390 the port's runs equal 5 of the 6 pristine runs; the sixth pristine run differs by one pixel at 1/255 from the
   other pristine runs too (pristine's own noise).
4. **Below the flow:** per-section crops at `?lab&hold=8&final=1` against the pristine page position-matched
   (`cap.py --match`): join, CTA, FAQ and footer 0 px at every size; the storefront 4 / 4 / 6 / 0 / 0 px (its corner
   and bar pixels, max 18). JS off the same, plus the hero 0 px everywhere (the 390 FAQ's 10 px are the pristine
   page's own: pristine against pristine gives the same).
5. **Heights** as listed under "Budget", JS on and off.
6. **CSP** (above).
7. **Behaviour:** Start picks by click, Enter and Space (the category's prompt, store and reply), Replay, Copy prompt
   (the clipboard holds the prompt, "Copied" shows), Build inert until played, then a switch and a fast-forwarding
   second click, the 600px crossing both ways, reduced motion, the knobs with and without `?lab`, the failure modes
   (blocked, 404, parse error, a throw before ready, Build's mount throwing), `file://`, the Dux attributes, the tab
   order (31 stops at load: the flow's ten are Start's four pills, then Replay and Copy prompt per step; Build's four
   pills join once it has played), `data-flow-assets` with digested URLs, and the loops at rest. After the fixes: every
   failure mode again at 1440 and 390 (flow.js 404, aborted, reset, unparsable, cut short, throwing at the top, in
   Build's mount and just before ready, never answering; flow.css 404; head.js 404), flow.css or flow.js late (with
   the stylesheet's link marked and unmarked), a cross-origin flow.js with and without `crossorigin` (healthy and
   throwing), the selected Start pill's focus ring (now white, as the others'), and the swipe cadence.
8. **Generator:** `--check` exits 0; a fresh run into an empty tree, from another directory, with another copy of the
   lab reproduces `flow/` byte for byte; and it stops on each injected fault: 94 cases in the second round (a changed
   file or asset without `--commit`, a new or missing asset, an uncopied file name in the code, each forbidden
   construct, `data:` / `blob:` URLs, `<style>` / `<link>` / `<script>` / `<iframe>` in an HTML string, EventSource,
   WebSocket, a service worker, `window.Function`, `srcset`, a single-quoted or unquoted `src=` concatenation, a `.src`
   / `.poster` / `setAttribute('src', ...)` not from `FLOW.asset()`, a `FLOW.asset()` key outside `assets/`, a new
   `.innerHTML`, a new repeating timer (LOOPS), `location.search` or `currentScript` in a stage, `url(` / `@import` /
   `@font-face` / a `.js` selector in a stylesheet, a second `--flow-css`, moved anchors including B9, C3, C4 and L5)
   and on the index.html faults (no head hook, an extra modulepreload, edited markup, the script not last or `defer`,
   the flow's fonts link or the stylesheet's `data-flow-css` dropped, flow.css moved to `<head>`). `flow/assets.txt`
   and `flow/markup.html` are byte for byte what `--list-assets` and `--print-markup` print, `flow/MANIFEST.sha256`
   checks with `shasum -a 256 -c`, and adding the three changed no other file under `flow/`.
9. **Icons:** a fresh, offline `tools/flow_icons.py` run on the export (its `flow/` is baa9299's) drew the 55 PNGs byte
   for byte as the ones the Rails landing already served (drawn at 7180b85 by the scratch rasteriser this tool
   replaces) and as a run with the page's Google Fonts loaded, and its widths are the six that landing.css gives them
   (10.671875, 8.53125, 28 and 32px in Build and Test, 8.890625 and 7.109375px in Start; the shell's three glyphs
   have width and height attributes); a second run, `--check`, matched the first byte for byte.

## Known issues and open decisions

- **Kept verbatim (upstream behaviour):** the gutters `clamp(20px, 6.25vw, 90px)` (16px under 600px), so between 1024
  and 1439px the flow's left edge differs from the storefront's, CTA's and FAQ's (80 vs 48px at 1280); the 600px phone
  line; the JS-off empty visual frame; Start's pills are `span[role=button]`, not buttons; Replay is focusable while
  still invisible (before its step has run); Build's pills are inert until Build has played; Copy prompt has no
  fallback without the Clipboard API; the Sports reply names "StridePulse Active ... 30 products" while the winning
  card is Summit Glider Gear with 29 (`stages/start.js:352/354`); Test's reply still ends "Ready to launch?" with no
  Launch step.
- **Changes to Kyu's styling** (for the user and design to confirm): the selected Start pill's focus ring is white
  (C4; upstream's `currentColor` ring is black on the black section, so focusing the flow's first Tab stop showed
  nothing), and without the flow the terminal grows to its transcript instead of keeping its fixed box (C3).
- **Build's theme-font warm-up** waits for Build to come on screen (B8), not for it to come within one viewport as
  first decided: that margin did not defer the faces at 1440x900, 1920x1080 or 1024x768. Under reduced motion a theme
  picked in the first moments after Build comes on screen can show a fallback font briefly.
- **Slow uncompressed links:** DOMContentLoaded (and so main.js's tabs, Copy and FAQ handlers) waits for
  `flow/flow.css`; gzip-served it does not.
- **Left as they are** (found in verification, low): a `flow/flow.js` that arrives late inserts the Start and Build
  pill rows (136px at 1440), so a reader already below the flow sees the page move (layout shift ~0.1 at 1440 and
  1280 on slow 4G); the enhanced but idle flow costs ~20% more main-thread time on every hero frame than the static
  page (1,500+ elements and 9 more layers; mounting each stage only as it approaches would cut it and the 74 eager
  images, a change to upstream's behaviour); the "Copied" confirmation is an `aria-live` region whose text never
  changes, so screen readers announce nothing on copy and read "Copied" before any copy (upstream's); a `flow.js`
  that never answers keeps the checklist lines hidden ("Fallbacks").
- **Browsers without constructable style sheets** (Safari < 16.4, Firefox < 101) get the static transcripts, where
  upstream's `<style>` fallback would have run the flow (it cannot under the Rails CSP).
- **A throw before ready** leaves the steps mounted before it enhanced (see "Fallbacks"); a reload is the way back.
- **For the Rails lift** (the Rails analysis has the line-by-line list): the SVG decision above; self-hosting eight
  font families; Start's stores are baked into `stages/start.js` (names, `*.mock.shop` hosts, counts, thumbnails), so
  the live StartStores path and landing.yml's `start:` / `build:` go, and the winners differ from landing.yml's
  (Beauty is clean-beauty, Sports apparel-snowwear); Start's body copy hard-codes "100+" (Rails renders
  `store_count_words`); root_test.rb's counts, h2 list, Dux section list (no Launch: six shopify.com links), img-src
  and Start/Build/Test assertions change.
