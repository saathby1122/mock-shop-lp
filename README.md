# mock.shop landing page

Static build of the new mock.shop landing page ("Sample Stores for Building With AI") from the Figma desktop
export. Plain HTML, CSS and vanilla JavaScript, no build step, hosted on GitHub Pages.

- Live: https://saathby1122.github.io/mock-shop-lp/
- Source of truth for the design: `reference/mockup-desktop.png` (1440 x 6529) and `reference/mockup-hero.png`
- What was measured and decided: `SPEC.md`
- Open questions and placeholders: `TODO.md`

## Files

| Path | What it is |
| --- | --- |
| `index.html`, `styles.css`, `main.js`, `favicon.svg` | The page |
| `assets/img/` | Imagery cut from the Figma export (1x) plus product grids built from live store data |
| `img/` | Re-cropped Build / Test / Launch preview panels used by the page (see `TODO.md`) |
| `assets/icons/` | SVG icons shared with the production landing page |
| `reference/` | Mockup frames and `stores.json` (data behind the Start pills) |
| `builds/` | The three candidate implementations the final page was chosen from (kept for reference) |

## Working on it

Open `index.html` directly in a browser, or serve the folder with any static server
(`python3 -m http.server`). Assets are referenced relatively so the page works from a sub-path.

To turn on the live storefront preview instead of the static screenshot, set `data-live="true"` on the
storefront preview container in `index.html` (see `TODO.md` for why it is off).

## Deploying

Pushing to `main` publishes the root of the repository through GitHub Pages (`.nojekyll` keeps Jekyll out of the
way). No build step.
