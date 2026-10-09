# mock.shop landing page — build spec (desktop, from Figma export)

Goal: a static landing page (plain HTML + CSS + vanilla JS, no build step) that reproduces
`reference/mockup-desktop.png` (1440 x 6529, 1x) as closely as possible at a 1440px viewport,
degrades gracefully down to 375px (a dedicated mobile design will come later), and deploys to
GitHub Pages at https://saathby1122.github.io/mock-shop-lp/ (so ALL asset paths are relative:
`assets/img/...`, never `/assets/...`).

Project root: `/Users/saathvik.byreddy/mock-shop-lp`
- `reference/mockup-desktop.png` — the full-page mockup (ground truth). `reference/mockup-hero.png` — hero frame (1440x790).
- `reference/stores.json` — real data for the four Start pills (name, host, description, counts, product titles).
- `assets/img/` — cut from the mockup at 1x (PNG + WebP): see "Assets" below.
- `assets/icons/*.svg` — official icons from the production landing page (20x20 viewBox; fills are `white`/`black` —
  inline them and use `fill="currentColor"` or swap fill as needed): `shopify-bag.svg` (nav mark, 30.9x35 viewBox),
  `shopify-bag-footer.svg` (36x40.75), `copy.svg`, `globe.svg`, `chevron-down.svg`, `plus.svg`, `minus.svg`, `docs.svg`, `close.svg`, `open.svg`.

## Tooling (use these, they exist and work)
- Python venv with Pillow/numpy/OpenCV/Playwright: `/tmp/mslp/venv/bin/python -I`
- Full-page screenshot via installed Chrome:
  `/tmp/mslp/venv/bin/python -I /tmp/mslp/tools/shot.py <index.html|url> <out.png> [--width 1440] [--height 900] [--click <css>]... [--eval <js>] [--viewport-only] [--mobile]`
  It prints JSON incl. document height and any JS console errors/page errors (must be empty).
- Band-by-band diff against the mockup:
  `/tmp/mslp/venv/bin/python -I /tmp/mslp/tools/compare.py <shot.png> /Users/saathvik.byreddy/mock-shop-lp/reference/mockup-desktop.png <outdir>`
  It reports, per section band, the best vertical offset and the mean absolute pixel difference, and writes
  `<band>-side.png` (left = mockup, right = yours) and `<band>-diff.png`. LOOK at the side-by-side images with the
  Read tool and fix what differs. Target: page height within ±40px of 6529; per-band diffs trending down; no band
  obviously mis-positioned. (Image-heavy bands never reach 0 because our assets are 1x crops; typography bands can.)
- Measuring text: Playwright `page.evaluate` + `getBoundingClientRect`, or crop the screenshot and measure ink.

## Design tokens (measured from the mockup)
Fonts (Google Fonts, load with the optical-size axis — this matters, Inter renders ~10% wider without it):
`<link href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">`
plus preconnects to fonts.googleapis.com and fonts.gstatic.com. `-webkit-font-smoothing: antialiased`.
- `--sans: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- `--mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace`

Colors:
- page background `#080b0c` (hero area, CTA/FAQ area). The four feature sections sit on a pure `#000000` block.
- footer band `#02090a`. storefront-preview container `#141a1a`.
- text white `#ffffff`; body/paragraph gray `#b3b3b3` (measured #b2b2b2–#b8b9b9); footer link gray `#a1a1aa`.
- accent green `#00f4b9` (eyebrows, terminal bullets + bullet dots).
- hairlines: `rgba(255,255,255,.12)` panel borders (#333 on #171717), `rgba(255,255,255,.2)` FAQ dividers & tab bar (#393c3d on #080b0c), pill border `rgba(255,255,255,.22)` (#515151 on #1a1a1a).
- preview panel bg `#171717` with a bottom fade: flat #171717 to ~75% height, then to `#0b0b0b` at the bottom edge (linear-gradient(180deg,#171717 0 74%,#0b0b0b 100%)).
- terminal body `#304b4f`; terminal header & prompt bubble `#24393d` (= rgba(0,0,0,.25) over body); terminal border `#356369`; window dots `#131e20`; title text `#a8e1ea`.
- code well bg `#141719`, border `1px solid rgba(0,244,185,.3)` (#0e5949) + soft glow `0 0 24px rgba(0,244,185,.12)`.
- pills: active bg #fff / text #000; inactive bg `#1a1a1a` / text #fff / 1px border rgba(255,255,255,.22).
- store card: white, title #000, domain `#6e7679`, description `#666666`, stats numbers #000 (600) + labels #666.
- device toggle: active circle `#2c3131`, inactive circle `#131313`, icons white. Buttons (Copy / Start with this store / FAQ plus): white bg, black text/icon.
Radii: pills & buttons fully rounded; panels/terminal 16px; code well 10px; copy button 8px; store card 10px; big blocks (black section block, storefront container, CTA panel) 44px top corners; storefront screenshot frame 20px top corners.

Type scale (verified in Chrome against mockup ink widths):
- H1 hero: 64px / line-height 1.08 / weight 400 / letter-spacing -0.03em / white / centered, 2 lines.
- H2 section: 56px / lh 1.1 / 400 / -0.02em / white. (same for "Now go make it yours" centered and "Frequently asked questions")
- Paragraph: 18px / lh 25px / 400 / #b3b3b3; section paragraphs max-width ~820px (they wrap to 2 lines as in the mock). Hero sub: 18px / 25px, max-width 740px, centered.
- Eyebrow: 16px / 500 / uppercase / normal tracking / #00f4b9.
- Pills, buttons, nav links, tabs, footer links: 16px. Pills 600; buttons 600; nav "Read the docs" 500 underlined; brand "mock.shop" 700 (renders a touch wide — use 15px or font-variation 'opsz' 32 if you want to match the 76px ink width); tabs 500; footer links 400.
- FAQ question: 27px / 400 / white. Card title 23px / 600 (ink width 177px for "VibePulse Studio"); card domain 15px mono #6e7679; card description 16px / lh 1.4 / #666; card stats 13px.
- Mono: code well 14px / lh 19px white; terminal text 12px / lh 16px white; terminal bullets 12px / lh 21px green; terminal title 15px #a8e1ea.

## Page structure and vertical layout at 1440 (mockup y positions; use as targets, not as absolute positioning)
Container: 1260px wide (90px side margins). Two-column feature grid inside it: preview panel 900px | gap 8px | terminal 352px.

1. NAV (over the hero, y 0–72): left: Shopify bag mark (white, 21x24 at x=90,y=24) + 10px gap + "mock.shop" (16px/700, white). Right: "Read the docs" (16px/500, white, underlined, 1px underline ~3px below baseline) ending at x=1348, linking to https://mock.shop/guides/. Items vertically centered at y≈36.
2. HERO (y 0–790, bg image `assets/img/hero-bg.webp` (png fallback) cover-positioned center, 1440x790 at 1x, background color #080b0c):
   - H1 "Sample Stores for" / "Building With AI" — line 1 cap-top y=229, line 2 y=298 (pitch 69px). Ink widths 462 / 403.
   - Sub (y 378–419, two lines): "No sign-up, no catalog to fill, no keys to manage. Point your AI agent at one of 100+ free sample stores and start building on real products, collections and carts." (break after "free")
   - Tabs (text y 467–481; 2px bottom border at y 490–491): "Prompt" (active: white text, white 2px underline) · "CLI" · "Skill" (inactive #b5b6b6, bar rgba(255,255,255,.2)). Tab padding 0 17px; tab row spans x 616–823, centered.
   - Code well (x 447–991 = 545 wide, y 509–570 = 62 tall, 17px gap below the tab bar): mono 14px two lines, white, padding-left 16px; text block vertically centered. Right inside: white "Copy" button (x 881–981, y 518–561 → 100x44, radius 8, inset 10px) with the copy icon (20px, black) + "Copy" 16px/600 black.
   - Hero background image already contains the floating 3D products and the star streaks; text region was inpainted dark.
3. BLACK BLOCK (y 790–4124, bg #000, 44px top-left/right radius so the hero's #080b0c shows in the corners). Contains four feature sections with this rhythm: eyebrow top at 872 / 1707 / 2540 / 3314 (≈88px after the previous panel bottom; 82px after the hero). Within a section: eyebrow (16px) → 20px → H2 (cap-top 31px below eyebrow top) → paragraph top 20px below the H2 descenders (eyebrow 872 → H2 903 → p 976 → pills 1044 → panels 1131). Pills row: 44px tall, 9px gaps, 27px below paragraph, 44px above the panels. Panels: 488px tall (y 1131–1619), 1px border rgba(255,255,255,.12), radius 16.
   Section copy:
   - START — "Tell your agent what you're selling" — "It finds the closest of 100+ catalogs, from graphic tees to espresso gear, each built the way merchants build theirs, and sets it up on a Shopify preview store. No signup or card needed." (break after "way") — pills: Streetwear (active) · Decor · Beauty · Sports.
   - BUILD — "Design the storefront, not the data" — "The catalog is handled, so you go straight to the brand: layout, type and colour. Prompt until it looks like the store you want." (break after "until it") — pills: Technical (active) · Vibrant · Bold · Elegant.
   - TEST — "A cart that actually works" — "Add items, pick variants and check out. Totals update through the same cart API a live store uses. Checkout is mocked, so nothing is charged." (break after "uses.") — no pills (panels start 46px below the paragraph).
   - LAUNCH — "Same storefront, real store" — "Your design, collections and menu carry over. Claim it, add your products and publish." — no pills.
4. PREVIEW PANELS (left, 900x488):
   - START panel: bg #171717 + bottom fade; a white store card (x 167–913 → 747 wide; y 1230–1408 → 179 tall; radius 10; padding 10px) with a 4x2 thumbnail grid image (285x162, `assets/img/grid-streetwear.webp`, radius 4) at left, then a 20px gap and text: title "VibePulse Studio", domain "apparel-streetwear.mock.shop" (mono), description, stats "8 products · 96 variants · 2 collections" (numbers bold). Behind/below it two more "result" cards, blurred and stacked (card 2: ~653px wide centered, peeking 1413–1480, blur 3px, opacity .75; card 3: ~591px wide, 1480–1528, blur 5px, opacity .45) — build them as real duplicate cards (e.g. "Urban Pulse Collective / streetwear-dropship.mock.shop / Curated streetwear essentials featuring oversized fits, gritty graphics, and high-energy urban style. / 8 products · 96 variants · 2 collections") with CSS filter blur + scale. The main card is vertically centered-ish (panel 1131–1619, card 1230–1408).
     Pills swap the card + terminal content (see Interactivity); data in reference/stores.json; grids `grid-decor.webp`, `grid-beauty.webp`, `grid-sports.webp`.
   - BUILD / TEST / LAUNCH panels: use the whole-panel crops `assets/img/panel-build.webp`, `panel-test.webp`, `panel-launch.webp` (898x487 each, they already include the gradient bg, the storefront screenshots, the Launch address pill + dotted globe) as `<img>` filling the panel (object-fit: cover; the panel's 1px border wraps them). Alt text describing the screenshot. (TODO for later: 2x exports from Figma.)
5. TERMINAL (right, 352x488, bg #304b4f, border 1px #356369, radius 16, overflow hidden):
   - Header 36px tall (#24393d): three 12px dots #131e20 at x 1019/1040/1061 (gap 9px, 20px from left), centered title "Agent" (mono 15px #a8e1ea).
   - Body padding 14px: prompt bubble (#24393d, radius 8, padding 9px 10px, mono 12px/16px white; a 16px copy icon bottom-right at 8px inset — in the Build terminal the prompt is 7 lines and the icon sits at the bottom right).
   - Then 24px gap, bullet list: 6px green dots (left edge 11px from the body's left padding edge, i.e. x≈1010 in the mock) + green mono 12px text starting 14px right of the dot; line pitch 21px.
   - Then 16px gap, result paragraph mono 12px/16px white. Links inside ("this link") underlined.
   Terminal copy:
   - START: prompt "I want to sell oversized, heavyweight t-shirts." bullets: Searching relevant catalogs / Creating preview store / Installing theme and copying catalog / Publishing products and menu. result: "Found VibePulse Studio, a streetwear catalog with heavyweight tees and hoodies. Your store is ready with its 8 products and theme. Want to change the look next?"
   - BUILD: prompt "Make my store feel fun and loud, like a sticker sheet. Sunny yellow background, chunky black outlines with hard drop shadows, rounded corners, a playful geometric font, and a coral pop for the buy button. Let the product photos swipe like a carousel." bullets: Reading theme settings / Updating colours and fonts background / Restyling buttons, borders and gallery / Pushing theme. result: "Done. Your storefront now has a sticker-sheet look: a sunny yellow background, bold outlines with hard shadows, and coral buy buttons."
   - TEST: prompt "Test the cart with the graphic tee, then try checkout." bullets: Checking stock: Slate sold out in XS to M / Adding Slate / L to cart / Filling in contact and shipping details / Paying with the test card / Placing order. result: "Cart and checkout both work. The order went through at $58.00 with the test card. Ready to launch?"
   - LAUNCH: prompt "I'm ready to launch. What's left?" bullets: Checking products, theme and menu / Getting your claim link. result: "Your store is ready. Claim it with this link, then add your products, pick a plan and turn off the password page to go live." ("this link" underlined, href https://www.shopify.com/)
6. STOREFRONT PREVIEW (y 4125–5025+, full-width container bg #141a1a, 44px top radius, sits directly under the black block; the CTA panel below overlaps it with its own 44px top radius starting at y=5025, so the container visually ends there):
   - Row at y 4205–4248: centered device toggle — two 44px circles 12px apart (desktop active #2c3131 with a white monitor icon 24px; mobile #131313 with a white phone icon ~14x18) — and right-aligned white pill button "Start with this store" (194x44, 16px/600 black) ending at x=1349, linking to https://apparel-streetwear.hydrogen.mock.shop/ (target _blank).
   - 24px below: the storefront frame (x 90–1350 = 1260 wide, top at y 4273, 20px top radius, overflow hidden) showing the VibePulse Studio home page, clipped at the bottom by the CTA panel (visible height 751px = 5024-4273).
     DEFAULT (static, faithful to the mock): desktop state shows `assets/img/storefront.webp` (1260x751, the mock's own screenshot); mobile state shows `assets/img/store-mobile.webp` (780x1688 = 2x capture of the live store at 390x844, cookie banner dismissed) inside a 390px-wide, 751px-tall frame centered in the container (object-fit: cover, object-position: top). Transition between states ~200ms.
     OPTIONAL live preview, OFF by default: a `data-live="false"` attribute on the preview container; when set to "true" (one-line switch), lazily create an `<iframe src="https://apparel-streetwear.hydrogen.mock.shop/" title="VibePulse Studio storefront preview">` sized to the current frame, keep the static image visible until the iframe's `load` event, then fade the iframe in. (Off by default because the live store currently shows a cookie-consent banner and a different theme than the design's screenshot.)
7. CTA PANEL (bg #080b0c, 44px top radius, from y 5025): H2 "Now go make it yours" centered (cap-top 5162), the same Tabs + code well + Copy button as the hero (tabs text y 5258, well y 5300–5361). Tab selection is shared between hero and CTA (one state).
8. FAQ (same bg): H2 "Frequently asked questions" left (cap-top 5500). Five rows, 125px tall each, 1px dividers rgba(255,255,255,.2) under each row (y 5699, 5824, 5949, 6074, 6199), first row top at 5574. Each row: question (27px/400 white, vertically centered) and a 44px white circle at the right (x 1306–1349) containing a thin black plus (`plus.svg`, 20px, 1px strokes). Use `<details>/<summary>` or button+aria-expanded; open state rotates the plus 45° (or swaps to minus.svg) and reveals the answer (18px/25px #b3b3b3, max-width ~900px, 24px padding-bottom). Only one open at a time.
   Questions/answers (real copy from the production FAQ):
   1. "How can I build an online store before I have products?" — "Point your storefront at mock.shop and build against a catalog that already exists. It serves real products, images, collections, variants and carts over an auth-free GraphQL API, so the whole shop can be built and reviewed before you have a single product of your own. When your real catalog is ready, swap the endpoint and the queries keep working."
   2. "Do I need a Shopify account or API key to use mock.shop?" — "No. mock.shop is auth-free: no account, no API key, no access token and no setup. The single exception is metafields, which need the header X-Shopify-Storefront-Access-Token: public, the same header a real store expects." (render the header name in mono)
   3. "How do I choose a sample catalog for my store?" — "Pick the store whose products look like what you are selling. Every store describes its own catalog at https://<store>.mock.shop/llms.txt, so an agent can read the list and choose for you. The directory at https://mock.shop/llms.txt lists them all."
   4. "Can I use mock.shop with an AI coding tool?" — "Yes, and it is the fastest way in. Copy the prompt at the top of this page into Claude Code, Cursor, or any agent that can write files, and it will scaffold a storefront wired to mock.shop. Because there is no auth step, the agent can query the API and keep iterating on its own."
   5. "What can I test with mock.shop?" — "Anything that reads a storefront: product and collection pages, search and filtering, variant pickers, cart add, update and remove, and the hand-off to checkout. The endpoint mirrors the Shopify Storefront API, so what holds here still holds when the same queries point at a real store."
9. FOOTER (band bg #02090a, y 6328–6529 = 200px tall, content vertically centered at y≈6428): left `shopify-bag-footer.svg` (36x41, white) at x=90 linking to https://www.shopify.com; right-aligned row ending at x=1348, 16px, gap 44px: "🌐 USA | English ⌄" (globe icon 20px + white text + chevron-down icon; a non-functional button) then links in #a1a1aa: Terms of service → https://www.shopify.com/legal/terms · Legal → https://www.shopify.com/legal · Privacy policy → https://www.shopify.com/legal/privacy · Sitemap → https://www.shopify.com/sitemap · Privacy Choices → https://privacy.shopify.com/en.

## Interactivity (vanilla JS, no dependencies; everything must also be reachable by keyboard)
- Tabs (hero + CTA share one state; role="tablist"): Prompt → "Build me a storefront from a mock.shop store.\nStart at https://mock.shop/llms.txt" (two lines exactly as shown). CLI → `npm i -g @shopify/cli && shopify store create preview`. Skill → `npx skills add Shopify/shopify-ai-toolkit`. The well keeps its 62px height (single-line snippets vertically centered).
- Copy button: `navigator.clipboard.writeText` of the current snippet (prompt copies with the real newline); on success swap label to "Copied" for 1.5s (keep the button width stable). Fallback to a hidden textarea + execCommand if clipboard is unavailable.
- Start pills: switch active pill; swap the main card (grid image, title, host, description, counts from stores.json: streetwear=VibePulse Studio 8/96/2; decor=Havenly Nest …; beauty=Lumina Botanica …; sports=VigorVibe Active …) and the terminal transcript: prompt "I want to sell <category phrase>." (oversized, heavyweight t-shirts / sculptural home decor and soft textiles / botanical daily skincare / high-performance activewear), bullets unchanged, result "Found <Name>, a <category> catalog with <two product kinds>. Your store is ready with its <N> products and theme. Want to change the look next?". Inline the data as a JS object (no fetch) so file:// works.
- Build pills: switch active pill and swap the terminal prompt + result to a style-matched variant (write 4 short, plausible transcripts; keep the Technical one exactly as in the mock). The preview image stays (flag in TODO).
- Device toggle: see section 6 (static image swap by default; live iframe only when data-live="true"); aria-pressed on the two buttons.
- FAQ accordion: one open at a time, animated height is optional, must work without JS if using <details>.
- Respect `prefers-reduced-motion`. No console errors. No layout shift when fonts load (set font-display swap and reserve sizes).

## Responsive (desktop-first; mobile design will be supplied later — do a sane adaptation, not a redesign)
- ≥1280: as mocked, container 1260 centered (margins grow on wider screens; cap the container at 1260).
- 1024–1279: container = 100% − 2×48px; feature grid becomes preview (flex 1) + terminal 320px.
- <1024: stack terminal under the preview panel (full width, min-height 360); H1 48px, H2 40px; hero bg still cover.
- <640: side padding 20px; pills wrap; store card stacks grid above text; FAQ question 20px; footer stacks (logo, then links wrapped). No horizontal scrolling at 375px.

## Accessibility & quality bar
- Semantic landmarks (header/nav, main, section with aria-labelledby, footer). One h1. Alt text on images; decorative icons aria-hidden.
- Focus-visible rings on all controls (2px #00f4b9 outline, offset 2px). Contrast: body gray on black passes AA.
- `<html lang="en">`, `<meta name="viewport">`, `<title>mock.shop — Sample Stores for Building With AI</title>`, meta description, favicon (`assets/icons/shopify-bag.svg`), Open Graph title/description.
- `.nojekyll` file in the published root. No external JS. Total page weight under ~2.5MB (use the .webp assets with <picture> png fallback or just .webp — Chrome/Safari/Firefox all support WebP).

## Assets (all in assets/img; sizes at 1x)
hero-bg.{webp,png,jpg} 1440x790 · panel-start.webp 898x487 (reference only; build the Start panel in HTML) · panel-build.webp, panel-test.webp, panel-launch.webp 898x487 · start-grid.{png,webp} 285x162 (= grid-streetwear) · grid-streetwear/decor/beauty/sports.{png,webp} 285x162 · storefront.{png,webp} 1260x751 (mock crop; the desktop state) · store-mobile.{png,webp} 780x1688 (live capture at 390x844 @2x, cookie banner dismissed; the mobile state) · build-screenshot.png 640x458, test-screenshot.png 640x400, launch-screenshot.png 640x421 (inner screenshots only, optional).
