# TODO — placeholders, guesses and gaps to resolve

Everything below was decided by the implementer, not by the design. Replace or confirm each item.

## Content the mockup did not define
- **CLI and Skill tab snippets** — taken from the production landing page constants:
  `npm i -g @shopify/cli && shopify store create preview` and `npx skills add Shopify/shopify-ai-toolkit`.
- **Start pills (Decor / Beauty / Sports)** — real mock.shop stores picked from the public directory search:
  Havenly Nest (home-decor), Lumina Botanica (skincare), VigorVibe Active (activewear-dropship).
  Counts come from each store's API; thumbnails are each store's first 8 product images. The agent transcript for
  these pills is templated from the Streetwear one.
- **Build pills (Vibrant / Bold / Elegant)** — the design only shows the Technical preview, so the other three pills
  only swap the Agent transcript (written by the implementer). Previews for those styles are needed from design.
  Note: the mock's Build transcript describes a "sticker sheet / sunny yellow" look while the preview is the
  monochrome Technical store; kept exactly as designed.
- **FAQ** — the mock shows five "Question" placeholders. Five of the eight questions from the production FAQ were
  used; the catalog-choice answer was shortened. The three unused production questions: "Where can I find sample
  product data for an ecommerce store?", "Can I build a clothing store with size and color options?",
  "Is mock.shop a website builder?".
- **Link targets** — Read the docs → https://mock.shop/guides/ · "this link" in the Launch terminal →
  https://www.shopify.com/ · Start with this store → https://apparel-streetwear.hydrogen.mock.shop/ ·
  footer links → the production footer's Shopify legal URLs. The "USA | English" selector is decorative.

## Assets
- All imagery is cut from the 1x Figma export, so it is soft on retina screens. Export at 2x from Figma:
  hero background **without** the text layers (the current one was inpainted), the Build / Test / Launch preview
  panels (898x487 each), and the storefront screenshot (1260x751).
- The hero's floating products are a flat image; the design intent (3D hero) is not implemented.
- Storefront preview: desktop state uses the mock's screenshot; mobile state uses a live capture of the current
  store theme (which differs from the design's theme). The live iframe is available behind `data-live="true"` on
  the preview container but is off by default (cookie banner + theme drift).

## Design still to come
- **Mobile landing page** — the export only had the desktop frame (the "Mobile – One page" files are checkout
  mockups). The responsive behaviour below 1280px is an adaptation, to be replaced when the mobile design lands.

## Deliberate deviations from SPEC.md (the mockup pixels won over the spec numbers)
- Display headings render at Inter weight 340 with eased tracking (-0.021em / -0.010em) instead of 400 / -0.03em:
  at 400 every heading carried about 18% more ink than the comp while body text matched. The store-card title is
  500 rather than 600 and the nav brand is 14px. Ink widths land within 1 to 3px of the mockup.
- Panels and terminals are 496px tall (mock rows 1128 to 1623), not 488; the terminal header is 38px plus a 1px rule.
- The three big blocks use 48px top radii (the mock's curve fits 48, the spec said 44).
- The CLI snippet renders at 13px mono so the 54-column command stays on one line beside the Copy button; the
  clipboard still receives the plain command. Below 640px every snippet soft-wraps at 14px.
- The 1260px container needs a 1356px viewport; between 1280 and 1355 the side margins stay 48px, because a 1260
  container at 1280 would leave 10px margins.
- The Build / Test / Launch panels use `img/panel-*.webp` (898 x 494 re-crops that run flush to the panel's bottom
  border like the mock) instead of the 898 x 487 crops in `assets/img`. `favicon.svg` is the bag mark with a
  color-scheme-aware fill. Terminal bullets drop to 11.5px only at 1024 to 1279px where the terminal is 320px wide.
- On phones (under 640px) the storefront frame starts in the mobile state and the device toggle is hidden.

## Infrastructure
- Fonts load from Google Fonts (Inter with the optical-size axis, JetBrains Mono). Self-host if the page must
  work offline or without third-party requests.
- Hosted on GitHub Pages from the `main` branch root (`.nojekyll` present).
