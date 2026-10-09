# builds/A - open items and deliberate choices

Open
- Build pills swap only the terminal transcript; the preview stays `panel-build.webp` until per-style exports exist.
- `img/panel-build/test/launch.webp` are 1x re-crops of the mock's panel interior (898x494, so the screenshot runs flush
  to the panel's bottom border like the mock; the 898x487 crops in `assets/img` stop 4px short). Swap in 2x exports
  from Figma when available (also `hero-bg.webp`, which is a 1x 1440x790 export and upscales 1.33x at 1920).
- Live storefront preview stays off (`data-live="false"` on `.store-frame`): the live store shows a cookie banner and a
  different theme than the design's screenshot, and logs its own analytics console error. Set it to "true" to enable.
  When on: a no-cors `fetch` probe gates the mount (offline / DNS / refused / corporate block keep the static capture
  instead of Chrome's error page), the iframe is inert (hidden from hit-testing, the tab order and the accessibility
  tree) until its `load`, a load that takes longer than 8 s is never revealed, and the iframe is sandboxed (scripts,
  same-origin, forms, popups; no top navigation). Chrome logs one console warning about that sandbox combination
  ("allow-scripts and allow-same-origin ... can escape"): it only applies to same-origin content, which the store is
  not; dropping `allow-same-origin` would strip the store's cookies and storage instead. An X-Frame-Options / CSP
  frame-ancestors refusal cannot be detected client-side: the browser would render its own refusal page inside the
  frame, so check the store's headers before turning the switch on. With the switch off none of this runs.

Deliberate
- Display headings (H1 64px, H2 56px) render at Inter weight 340 instead of the spec's 400: at 400 every heading has
  ~18% more ink than the comp (5px stems vs 4px at 64px) while all 400-weight body text matches within 1%. Tracking is
  eased (-.021em / -.010em) so the ink widths still land on the mock's. Likewise the store card title is 500 rather
  than 600 (same 177px ink width, the comp's title is a Medium).
- The three big blocks (black feature block, storefront container, CTA panel) use 48px top radii: the spec says 44 but
  the mock's corner curve fits r~48 on all three. The storefront frame keeps 20px.
- `storefront.webp` is 751 rows; the mock's frame covers rows 4273-5024 (752). Rather than resampling the capture by a
  row, the CTA panel's top edge sits on row 5024 and its padding-top is 128px, so everything below stays on the mock's rows.
- The CLI snippet renders at 13px mono with -.01em tracking (the other two at the spec's 14px) so the 54-column command
  stays on one line in the well's 418px text column (454px at 14px); the clipboard receives the plain command. Below
  640px the well stacks and every snippet soft-wraps at 14px.
- `favicon.svg` (build-local) is the spec's `assets/icons/shopify-bag.svg` mark with a `prefers-color-scheme` fill, so the
  tab icon is visible on dark tab strips; `assets/` is untouched.
- Terminal bullets render at 11.5px only at 1024-1279px, where the terminal is 320px wide, so
  "Checking stock: Slate sold out in XS to M" stays on one line. The TEST result's design line break (`.br-xl`) is
  hidden there as well. Below 1024 the terminal is full width and keeps the spec's 12px and `min-height: 360px`.
- Ghost card 2 uses the spec's .75 opacity on a `#c4c4c4` card rather than white: that reproduces the mock's ~#999 tone
  over the #171717 panel. Its thumbnails are filtered cells of the streetwear grid (lifted + contrast so they read as
  the mock's dark pants on light grey). Card 3 is clipped where it lies behind card 2 and hides its text block.
- The 1260px container needs 1356px (1260 + 2x48) of viewport; at 1280-1355 the margins stay 48px (spec: ">=1280 as
  mocked"), because a 1260 container at 1280 would leave 10px margins. Below 1356 the Start panel follows the other
  panels' 900:496 proportion (min 420px) and the card stack scales with it; the Build/Test/Launch crops cover the
  panel (the clipped edges are plain gradient). On phones (<640) those panels switch to 4:3 and zoom the crop 140% so
  the storefront screenshot fills the width.
- The storefront frame is a clip window: the desktop capture is sized from the container (`100cqw`), the phone capture is
  390px wide, and the toggle animates only the window while crossfading the two, so neither capture scales. On phones
  (<640) the frame starts in the mobile state and the device toggle is hidden: the 1260px desktop capture would be a
  27% thumbnail there.
- The stats row ("8 products · 96 variants · 2 collections") stays on one line in the two-column card (640-1279) and
  drops to 12px at 640-679, where the text column is a pixel or two short of the 13px row.
