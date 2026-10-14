# TODO — placeholders, guesses and gaps to resolve

Everything below was decided by the implementer, not by the design. Replace or confirm each item.

## Content the mockup did not define
- **CLI and Skill tab snippets** — taken from the in-progress mock.shop landing code (not yet shipped):
  `npm i -g @shopify/cli && shopify store create preview` and `npx skills add Shopify/shopify-ai-toolkit`.
- **Start pills (Decor / Beauty / Sports)** — now Kyu's animated Start (see "Animated flow" below): its four
  categories, their stores (names, `*.mock.shop` hosts, counts, thumbnails) and transcripts are baked into
  `flow/flow.js` (upstream `stages/start.js`). The winners are VibePulse Studio (apparel-streetwear), Havenly Nest
  (home-decor), Bloom & Dew Botanicals (clean-beauty) and Summit Glider Gear (apparel-snowwear); whether each still
  matches the live store is unverified. The implementer-picked stores of the static page (`reference/stores.json`)
  are no longer used.
- **Build pills (Vibrant / Bold / Elegant)** — resolved by R23: four animated themes, each with its own prompt and
  reply, and the Technical prompt now describes the spec-sheet look its preview shows.
- **FAQ** — the mock shows five "Question" placeholders. Five of the eight questions drafted for the in-progress mock.shop landing
  (not yet shipped) were used; the catalog-choice answer was shortened. The three unused draft questions: "Where can I find sample
  product data for an ecommerce store?", "Can I build a clothing store with size and color options?",
  "Is mock.shop a website builder?".
- **Link targets** — Read the docs → https://mock.shop/guides/ · Start with this store →
  https://apparel-streetwear.hydrogen.mock.shop/ ·
  footer links → the Shopify legal URLs used by the in-progress landing footer. The "USA | English" selector is decorative.

## Assets
- All imagery is cut from the 1x Figma export, so it is soft on retina screens. Export at 2x from Figma:
  hero background **without** the text layers (the current one was inpainted) and the storefront screenshot
  (1260x751). (The Build / Test / Launch preview panels went with the static sections; the flow's own images are
  Kyu's, in `flow/assets/`.)
- The hero is now animated (see "Animated hero" below). The flat `assets/img/hero-bg.webp` stays as the picture
  for JS off, browsers without module scripts, `file://`, and whenever the field cannot run (`hero/field.js` or
  three.js failing to load or start).
- Storefront preview: desktop state uses the mock's screenshot; mobile state uses a live capture of the current
  store theme (which differs from the design's theme). The live iframe is available behind `data-live="true"` on
  the preview container but is off by default (cookie banner + theme drift).

## Design still to come
- **Mobile landing page** — the export only had the desktop frame (the "Mobile – One page" files are checkout
  mockups). The responsive behaviour below 1280px is an adaptation, to be replaced when the mobile design lands.
  The flow (Start / Build / Test) is the exception: it follows Kyu's R21 / R22 phone frames under 600px.

## Deliberate deviations from SPEC.md (the mockup pixels won over the spec numbers)
- Display headings render at Inter weight 340 with eased tracking (-0.021em / -0.010em) instead of 400 / -0.03em:
  at 400 every heading carried about 18% more ink than the comp while body text matched. The store-card title is
  500 rather than 600 and the nav brand is 14px. Ink widths land within 1 to 3px of the mockup.
- The three big blocks use 48px top radii (the mock's curve fits 48, the spec said 44).
- The CLI snippet renders at 13px mono so the 54-column command stays on one line beside the Copy button; the
  clipboard still receives the plain command. Below 640px every snippet soft-wraps at 14px.
- The 1260px container needs a 1356px viewport; between 1280 and 1355 the side margins stay 48px, because a 1260
  container at 1280 would leave 10px margins. The flow keeps Kyu's own gutters (`clamp(20px, 6.25vw, 90px)`, 16px
  under 600px): equal at 1440, 1920 and 768, but between 1024 and 1439px its left edge is inside the other sections'
  (80 vs 48px at 1280), and 16 vs 20px on phones.
- `favicon.svg` is the bag mark with a color-scheme-aware fill.
- On phones (under 640px) the storefront frame starts in the mobile state and the device toggle is hidden.

## Animated hero (Kyu Kim's hero lab, ported; details and the Rails handoff in `HERO.md`)
Done: the four layers of the design's animated hero (richardli-design/mock-shop-lp `project/hero-stage/hero-lab`,
commit 1914c8e) on this page's own hero. They are the stream of light with its room of 17 three.js products (pointer
pan, drag to tumble, photo cards without WebGL 2, a pause off screen), the copy's entrance with the headline forming
out of particles, the light running round the hero well's ring, and the scrim. `hero/field.js` and `hero/intro.js`
are generated from upstream by `tools/hero_port.py`; `hero/hero.css` is hand-ported. The copy's settled layout, every
other section and `main.js` were unchanged by the hero (the flow later replaced the feature sections and trimmed
`main.js`: below).
After the first review: the hero falls back to its static picture whenever `hero/field.js` cannot run (404, CSP, CORS,
a parse error, a throw before it boots, a page without the hero's markup), not only when three.js fails; field.js
loads `async` with `fetchpriority="low"`, so the copy's entrance no longer waits for its 400 KB (DOMContentLoaded
673 -> 197 ms on a cable profile); on phones the hero well holds its tallest snippet (ghost `<pre>`s, as the lab's
`.hghost`), so a tab switch no longer moves the headline; no console errors without WebGL 2; a pinch that starts on a
product zooms; the lab's knobs need `?lab`; the generator pins every upstream file and checks its output.
Left to decide or do:
- **Phone hero box (deliberate layout change, JS on, <=900px):** the hero becomes one screen tall (Kyu's phone box:
  844px at 390x844 instead of 646px) so the products have bands above the headline and below the well; everything
  below the hero moves down on phones. JS off keeps today's phone hero. The page's phone copy is taller than the lab's
  (454 vs 344px at 390x844), so the phone lanes are tighter (exit pX 1.53-1.67 vs the lab's 1.67-2.12; the next
  product fades in almost at home) and small phones show few products: mean near products on screen, port vs lab,
  375x667 0.12 vs 1.23, 360x740 0.46 vs 1.58, 390x844 1.46 vs 2.42, 412x915 1.85 vs 3.00. Replace with the mobile
  design when it lands, and retune then.
- **Fonts:** the page loads Inter and JetBrains Mono from Google Fonts with `display=swap`; the lab vendors them with
  `font-display:block`. intro.js's `document.fonts.load()` holds the first paint for the cross-origin faces (up to
  about 100 ms: 180-208 ms vs 92-128 ms for the static page), and the entrance starts ~80-100 ms later than the lab's.
  The intro waits for the faces for up to 1.5s; on a slow connection (slow 4G: faces at ~3.1 s) it starts on fallback
  glyphs and swaps mid-entrance (the headline's particles land on the fallback letter positions). Self-hosting the two
  faces, with a preload of Inter, fixes all of it (it is also the Rails plan).
- **The lab's knobs** now need `?lab` in the query (`?lab&hold=N`, `?lab=1&gl=0`, ...): a visitor's `?t=` cache-buster
  no longer changes the hero. Anyone can still open `?lab&hold=N` (it pauses every animation on the page).
- **Budget:** the hero adds about 325 KB gzipped (three.js 171 KB, field.js 140 KB, intro.js 8 KB, hero.css 6 KB) and
  about 1.14 MB uncompressed; HTML+CSS+JS goes from about 22 KB to about 347 KB gzipped (PLAN.md: 40 KB). First view
  goes from 420 KB to 720 KB (PLAN.md: 450 KB); the full page is the same 720 KB compressed but 1.59 MB raw
  (PLAN.md: 1.5 MB). The 89 product photos (1.65 MB, 87 KB at most each) load only without WebGL 2, a few at a time.
  With JS off only `hero/hero.css` and the 674-byte scrim are extra: Chromium blocks the three.js modulepreload when
  JavaScript is disabled (other engines unverified).
- **Steady state:** at 1440 the main thread spends ~20-30% more than the lab at the same room (the cards' per-frame
  changes re-layerize this whole long page); fine here, worth watching on low-end laptops.
- `hero.css`'s entrance uses fill-mode `backwards` (upstream: `both`), so the settled tab strip matches the page's;
  the price is a one-off ~0.5px settle of the strip as its entrance ends (accepted). The row's `will-change`
  (upstream's) puts the copy on its own layer: on Windows ClearType its text may lose subpixel antialiasing
  (unverified).
- Between 640 and 900px the field runs its phone layout scaled up, and products overshoot the room and blink out
  (as in the lab itself).
- Opened from `file://` the hero stays the static picture (modules cannot load there) and Chrome logs 4 CORS errors
  for `hero/field.js` and the three.js preload; serve the folder to see the animation. (The flow does run from
  `file://`: classic scripts.)
- With the flow on the page the hero's budget lines above grow (see "Animated flow").

## Animated flow (Kyu Kim's flow lab, round 23, ported; details and the Rails handoff in `FLOW.md`)
Done: the START / BUILD / TEST / LAUNCH sections are replaced by the design's animated Start, Build and Test
(richardli-design/mock-shop-lp `project/flow-lab`, commit d931946; R23 removed Launch, so the page's Launch section
is gone too). `flow/flow.js`, `flow/flow.css`, `flow/head.js` and `flow/assets/` are generated by
`tools/flow_port.py` (pinned, checked, `--check`); the three steps' markup in `index.html` is upstream's verbatim
plus Dux attributes. `main.js` lost the old Start / Build pill code and the image warming (it fetched four unused
grids); `styles.css` lost the old sections' rules; the root `img/` panels are deleted. The hero, the storefront
preview, the CTA, the FAQ and the footer are unchanged in themselves (they moved up 749px at 1440).
Port edits, all listed in the generated files' PORT NOTES: the knobs need `?lab`; no clips (posters are the stills),
so no fetch / blob; one asset helper (`FLOW.asset`, with `data-flow-assets` for Rails' digests); CSSOM instead of
`style=` in HTML strings (Test's checkout and thank-you, Build's scan light and dotted frames work under a strict CSP);
`html.flow-on` from an external head script with an error fallback (a failed `flow/flow.js` or `flow/flow.css`
leaves the transcripts readable, also when the script's error is a cross-origin one the browser mutes: a load-event
backstop) and the flow enhancing nothing until its stylesheet applies; without the flow the terminal grows to its
whole transcript (upstream's fixed box hid lines at 1024 and on phones); Build's idle frame loop stopped (nothing to
drive with the clips off) and its 4 Hz idle tick (Vibrant's carousel) running only while Build is on screen;
Build's theme-font warm-up waiting until Build comes on screen; the selected Start pill's focus ring white like the
others'; Dux names on the steps and the JS-built controls.
Changes to Kyu's styling to confirm with design: the selected Start pill's focus ring (white; upstream's
`currentColor` ring is black on black there, so focus was invisible on the flow's first Tab stop) and the JS-off
terminal that grows instead of clipping.
Kept verbatim (upstream behaviour; design or a11y may want to revisit):
- Kyu's gutters `clamp(20px, 6.25vw, 90px)` (above, "Deliberate deviations") and his 600px phone line.
- With JS off the visual frame is empty (the copy and the full transcript read; a still per step would need images).
- Start's pills are `span[role=button]` (with Enter / Space), not `<button>`s; each step's Replay is focusable while
  still invisible, before its step has run; Build's pills are inert (not tabbable) until Build has played; Copy prompt
  has no fallback without the Clipboard API (plain http, old browsers).
- The Sports reply names "StridePulse Active ... 30 products" while the winning card is Summit Glider Gear with 29
  (upstream `stages/start.js:352/354`).
- Test's reply still ends "Ready to launch?" although there is no Launch step any more: a copy question for design.
Left to decide or do:
- **Budget:** the flow adds ~128 KB gzipped of code (`flow.js` 93 KB, `flow.css` 33 KB, `head.js` 1.8 KB), 74 images
  / 265 KB at load at 1440 (58 / 257 KB at 390; every stage mounts at load) and up to 8 font families. Gzip-served,
  DOMContentLoaded and the hero's entrance keep their times; the field boots ~0.2 s later on slow 4G at 1440x900.
  Uncompressed, DOMContentLoaded waits for `flow/flow.css` (FLOW.md, "Load order").
- **Fonts:** a second Google Fonts link for the flow's families (Geist Mono, JetBrains Mono 700/800, Space Grotesk,
  Anton, Archivo, Archivo Black, Instrument Sans, Instrument Serif, Newsreader). Build's theme faces load only once
  Build comes on screen (decided first as "within one viewport", which did not defer them at 1440x900, 1920x1080 or
  1024x768, slowed the field ~1 s on slow 4G and nudged 12 hero pixels at 1440: FLOW.md, "Fonts").
- **Found in verification, left as they are** (FLOW.md, "Known issues"): a late `flow/flow.js` shifts the page under
  a reader below the flow when it inserts the pill rows; the idle enhanced flow costs ~20% more main-thread time per
  hero frame; the "Copied" live region never announces; a `flow/flow.js` that never answers keeps the step lines
  hidden; a stage whose mount throws leaves its prompt box empty.
- **Rails:** 55 of the flow's assets are SVG `<img>` icons and the app takes no SVG files: a vetted exception for
  `landing/flow/` or 3x PNGs (FLOW.md, "CSP"); eight more font families to self-host.
- Browsers without constructable style sheets (Safari < 16.4, Firefox < 101) get the static transcripts.

## Infrastructure
- Fonts load from Google Fonts (Inter with the optical-size axis, JetBrains Mono; the flow's own link adds Geist
  Mono, JetBrains Mono 700/800 and Build's theme families). Self-host if the page must work offline or without
  third-party requests.
- Hosted on GitHub Pages from the `main` branch root (`.nojekyll` present).
