#!/usr/bin/env python3
"""Rasterise the flow's SVG icons to PNGs and measure their widths, for a page that serves no SVG file.

    python3 tools/flow_icons.py [--check]

The Rails landing's asset pipeline takes no SVG, so that page gives the flow a PNG of each of its SVG icons and sizes
it with CSS. This script makes both from flow/ as tools/flow_port.py writes it (flow/MANIFEST.sha256 must check), under
flow-icons/:

  <dir>/<name>.png  flow/assets/<dir>/<name>.svg drawn by Chromium on a transparent background, at three times
                    (rounded up) the largest size the flow draws the icon at on this page, in each direction: over a
                    played run of all three steps, the final frame of each other Start category and of every Build
                    theme, at 16 viewports from 320 to 2560 wide (the phones at three device pixels per CSS pixel).
                    A square SVG gets a square PNG.
  widths.txt        each icon's key, its width as Chromium lays the SVG out (CSS px, a whole number of 1/64px), and
                    how the flow sizes its <img>: "attributes" (a width or height attribute) or "intrinsic" (none:
                    unless flow.css sizes it, it takes the SVG's own size, which a page serving the PNG must give back)
  MANIFEST.sha256   the sha256 of each file above and of every file they were made from: each SVG, and flow/flow.css
                    and flow/flow.js, which decide how large the flow draws them. `shasum -a 256 -c
                    flow-icons/MANIFEST.sha256` from the repository's root checks both, so it fails once an input has
                    changed: rerun this script then.

It serves this repository on 127.0.0.1 for the run and drives Playwright's Chromium, headless and offline: Chromium
resolves no other host (OFFLINE), so the page's Google Fonts fail at once and its text takes local fonts, which do not
change how large the flow draws its icons (a run with the fonts drew the same files). It needs no network, but
playwright, with its Chromium, and Pillow. It stops if a page does not load, if an SVG is never drawn on the page, if
an icon's <img> has a width or height attribute in one place and not in another, or if a PNG has ink where its SVG
draws nothing or none where it draws. It warns where another run could draw a PNG a pixel off (near_step): the
largest size is sampled every 50 ms, so where a transform makes it, it can differ a little between runs. The output
depends on the inputs and on the Chromium that draws them (the manifest names it): --check makes everything again and
compares instead of writing, and exits 1 on a difference.
"""
import argparse
import base64
import functools
import hashlib
import http.server
import io
import math
import re
import sys
import threading
from importlib.metadata import version
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FLOW = REPO / 'flow'
OUT = REPO / 'flow-icons'
# viewports, CSS px; 'm': a phone (three device pixels per CSS pixel, touch)
SIZES = ['1440x900', '1280x800', '1024x768', '768x1024', '600x900', '601x900', '390x844m', '360x740m', '320x640m',
         '1920x1080', '2560x1440', '599x900m', '560x900m', '500x900m', '430x932m', '412x915m']
# (query, the Build theme pills to click once Build is on screen): every step played through, then the final frames
# of each other Start category and of every Build theme (reduced motion: instant switches)
RUNS = [('lab&play=all&speed=3', []), ('lab&final=1&cat=decor', []), ('lab&final=1&cat=beauty', []),
        ('lab&final=1&cat=sports', []), ('lab&final=1&rm=1', ['vib', 'bold', 'ele', 'tec'])]
SIZED_BY = ['flow/flow.css', 'flow/flow.js']
# Chromium resolves no host but the run's own server's, so nothing the page asks of the network can hold up a load.
OFFLINE = ['--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1']
# How near (in PNG pixels, at 3x) a sampled size may come to a whole PNG pixel before the run warns: about three times
# the largest spread seen between runs.
NEAR_STEP = 0.02
DRAWS = re.compile(rb'<(path|rect|circle|ellipse|line|polyline|polygon|image|text|use)\b')
# Injected before the page's scripts: every 50 ms, each flow icon <img> on screen, by its key, with the largest width
# and height it has had, laid out (CSS px, before transforms) or rendered (after them), the largest laid out alone
# (lw, lh), and whether it has a width or height attribute.
PROBE = r"""
(function () {
  var seen = {};
  window.__icons = seen;
  function scan() {
    var imgs = document.querySelectorAll('.flow img');
    for (var i = 0; i < imgs.length; i++) {
      var im = imgs[i], m = /\/flow\/(assets\/[a-z0-9-]+\/[a-z0-9-]+\.svg)(?:$|[?#])/.exec(im.currentSrc || im.src);
      if (!m) continue;
      var cs = getComputedStyle(im), w = parseFloat(cs.width), h = parseFloat(cs.height);
      if (cs.display === 'none' || !(w > 0 && h > 0)) continue;
      var r = im.getBoundingClientRect(), a = im.hasAttribute('width') || im.hasAttribute('height');
      var s = seen[m[1]] || (seen[m[1]] = { w: 0, h: 0, lw: 0, lh: 0, attrs: a, mixed: false });
      s.w = Math.max(s.w, w, r.width);
      s.h = Math.max(s.h, h, r.height);
      s.lw = Math.max(s.lw, w);
      s.lh = Math.max(s.lh, h);
      if (s.attrs !== a) s.mixed = true;
    }
  }
  setInterval(scan, 50);
  window.__iconScan = scan;
})();
"""
PAGE = ('<!doctype html><html><head><style>html,body{margin:0;background:transparent}%s</style></head>'
        '<body><img id="i" src="data:image/svg+xml;base64,%s"></body></html>')
LOADED = 'document.getElementById("i").complete && document.getElementById("i").naturalWidth > 0'


def die(msg):
    sys.exit('flow_icons.py: ' + msg)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read_inputs():
    """Every SVG under flow/assets/ and the files that size them (repository-relative path -> bytes), once flow/ is
    checked against flow/MANIFEST.sha256"""
    listing = FLOW / 'MANIFEST.sha256'
    if not listing.is_file():
        die('flow/MANIFEST.sha256 is missing: run tools/flow_port.py first')
    listed = dict(reversed(line.split('  ', 1)) for line in listing.read_text(encoding='utf-8').splitlines()
                  if not line.startswith('#'))
    bad = sorted(p for p, d in listed.items() if not (REPO / p).is_file() or sha((REPO / p).read_bytes()) != d)
    if bad:
        die('flow/ is not what tools/flow_port.py wrote (flow/MANIFEST.sha256): %s; rerun it' % ', '.join(bad))
    svgs = sorted(p for p in listed if p.startswith('flow/assets/') and p.endswith('.svg'))
    found = sorted(p.relative_to(REPO).as_posix() for p in (FLOW / 'assets').rglob('*.svg'))
    if found != svgs:
        die('flow/assets/ has SVGs flow/MANIFEST.sha256 does not list: %s' % ', '.join(sorted(set(found) - set(svgs))))
    return {p: (REPO / p).read_bytes() for p in svgs + SIZED_BY}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def probe(p, base):
    """key -> {'w', 'h': the largest CSS size the flow draws that icon at, 'lw', 'lh': the largest it lays it out at,
    'attrs', 'mixed'} over SIZES and RUNS"""
    from playwright.sync_api import Error as PlaywrightError
    seen = {}
    for size in SIZES:
        w, h = (int(x) for x in size.rstrip('m').split('x'))
        phone = size.endswith('m')
        for query, themes in RUNS:
            b = p.chromium.launch(channel='chromium', headless=True, args=OFFLINE)
            try:
                ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=3 if phone else 1,
                                    is_mobile=phone, has_touch=phone,
                                    reduced_motion='reduce' if 'rm=1' in query else 'no-preference')
                pg = ctx.new_page()
                pg.add_init_script(PROBE)
                errors = []
                pg.on('pageerror', lambda e: errors.append(str(e)))
                try:
                    pg.goto(base + '?' + query, wait_until='load')
                except PlaywrightError as e:
                    die('%s ?%s: the page did not load: %s' % (size, query, str(e).splitlines()[0]))
                if 'play=all' in query:
                    for _ in range(90):
                        pg.wait_for_timeout(500)
                        if pg.evaluate("[...document.querySelectorAll('.fl-step')].every(s => "
                                       "s.classList.contains('is-done'))"):
                            break
                    else:
                        die('%s ?%s: the steps had not finished after 45 s' % (size, query))
                    pg.wait_for_timeout(1500)
                else:
                    pg.wait_for_timeout(2500)
                if themes:
                    top = pg.evaluate("document.getElementById('build').getBoundingClientRect().top + scrollY")
                    pg.evaluate('y => scrollTo(0, y)', int(top) - 24)
                    pg.wait_for_timeout(600)
                    for t in themes:
                        pg.click('#build .build-pill[data-t="%s"]' % t)
                        pg.wait_for_timeout(700)
                pg.evaluate('window.__iconScan()')
                got = pg.evaluate('window.__icons')
            finally:
                b.close()
            if errors:
                die('%s ?%s: the page threw: %s' % (size, query, errors[0]))
            for k, v in got.items():
                s = seen.setdefault(k, {'w': 0, 'h': 0, 'lw': 0, 'lh': 0, 'attrs': v['attrs'], 'mixed': False})
                for d in ('w', 'h', 'lw', 'lh'):
                    s[d] = max(s[d], v[d])
                s['mixed'] = s['mixed'] or v['mixed'] or s['attrs'] != v['attrs']
            print('%-9s ?%-24s %2d icons' % (size, query, len(got)), flush=True)
    return seen


def laid_out(b, svg):
    """[width, height] an unsized <img> of svg lays out at, in CSS px: the SVG's own size as Chromium lays it out"""
    ctx = b.new_context(viewport={'width': 400, 'height': 400}, device_scale_factor=1)
    try:
        pg = ctx.new_page()
        pg.set_content(PAGE % ('', base64.b64encode(svg).decode('ascii')))
        pg.wait_for_function(LOADED)
        return pg.evaluate('(() => { const r = document.getElementById("i").getBoundingClientRect(); '
                           'return [r.width, r.height]; })()')
    finally:
        ctx.close()


def rasterise(b, svg, pw, ph):
    """svg as a pw x ph PNG on a transparent background, as an <img> of that many pixels draws it at dpr 1"""
    ctx = b.new_context(viewport={'width': max(pw, 64), 'height': max(ph, 64)}, device_scale_factor=1)
    try:
        pg = ctx.new_page()
        pg.set_content(PAGE % ('img{display:block;width:%dpx;height:%dpx}' % (pw, ph),
                               base64.b64encode(svg).decode('ascii')))
        pg.wait_for_function(LOADED)
        return pg.locator('#i').screenshot(omit_background=True, animations='disabled')
    finally:
        ctx.close()


def near_step(v, laid_out):
    """Whether another run could draw a PNG v device pixels (3x the largest size sampled) wide a pixel wider or
    narrower: a transform made v (it is more than laid_out, 3x the largest size laid out, which every run reaches), and
    it is within NEAR_STEP of the whole pixel above it, or of the one below it with laid_out not above that one"""
    if v <= laid_out + 1e-6:
        return False
    n = math.ceil(v - 1e-6)
    return n - v < NEAR_STEP or (v - (n - 1) < NEAR_STEP and laid_out <= n - 1)


def px(v, what):
    """v (CSS px) as written in widths.txt, once it is a whole number of 1/64px (the unit Chromium lays out in)"""
    if v * 64 != int(v * 64):
        die('%s: %r px is not a whole number of 1/64px' % (what, v))
    return ('%.6f' % v).rstrip('0').rstrip('.')


def build(inputs):
    from PIL import Image, __version__ as pillow
    from playwright.sync_api import sync_playwright
    svgs = sorted(k for k in inputs if k.endswith('.svg'))
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(REPO)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            seen = probe(p, 'http://127.0.0.1:%d/' % httpd.server_address[1])
            missing = [k for k in svgs if k[len('flow/'):] not in seen]
            if missing:
                die('never drawn on the page, so no size to draw it at: %s' % ', '.join(missing))
            mixed = sorted(k for k, v in seen.items() if v['mixed'])
            if mixed:
                die('drawn with a width or height attribute in one place and without in another: %s' % ', '.join(mixed))
            files, rows = {}, []
            b = p.chromium.launch(channel='chromium', headless=True, args=OFFLINE)
            try:
                chromium = b.version
                for k in svgs:
                    key, svg = k[len('flow/'):], inputs[k]
                    iw, ih = laid_out(b, svg)
                    largest = seen[key]
                    pw, ph = math.ceil(3 * largest['w'] - 1e-6), math.ceil(3 * largest['h'] - 1e-6)
                    near = ['%.6f' % (3 * largest[d]) for d in ('w', 'h')
                            if near_step(3 * largest[d], 3 * largest['l' + d])]
                    if near:
                        print('warning: %s is drawn up to %.6fx%.6f px, %s at 3x: so near a whole pixel that another '
                              'run could draw its PNG a pixel off' % (key, largest['w'], largest['h'], ' and '.join(near)),
                              flush=True)
                    if iw == ih:
                        pw = ph = max(pw, ph)
                    im = Image.open(io.BytesIO(rasterise(b, svg, pw, ph))).convert('RGBA')
                    if im.size != (pw, ph):
                        die('%s: drew %dx%d, not %dx%d' % (k, im.size[0], im.size[1], pw, ph))
                    if (im.getextrema()[3][1] > 0) != bool(DRAWS.search(svg)):
                        die('%s: the PNG has %s' % (k, 'ink where the SVG draws nothing' if im.getextrema()[3][1]
                                                     else 'no ink where the SVG draws'))
                    buf = io.BytesIO()
                    im.save(buf, 'PNG', optimize=True)
                    files['flow-icons/' + key[len('assets/'):-len('.svg')] + '.png'] = buf.getvalue()
                    rows.append('%s %s %s' % (key, px(iw, k), 'attributes' if largest['attrs'] else 'intrinsic'))
                    print('%-34s svg %sx%s px, drawn up to %.4fx%.4f -> %dx%d PNG' % (
                        key, px(iw, k), px(ih, k), largest['w'], largest['h'], pw, ph), flush=True)
            finally:
                b.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    files['flow-icons/widths.txt'] = (
        '# flow-icons/widths.txt -- GENERATED by tools/flow_icons.py; do not edit (rerun it).\n'
        "# <key> <width> <sizing>: each flow SVG icon, the width Chromium lays the SVG out at (CSS px, a whole number of\n"
        '# 1/64px), and how the flow sizes its <img>: "attributes" (a width or height attribute) or "intrinsic" (none:\n'
        "# unless flow.css sizes it, it takes the SVG's own size, which a page serving its PNG must give it back).\n"
        + ''.join(row + '\n' for row in rows)).encode('utf-8')
    head = ['flow-icons/MANIFEST.sha256 -- GENERATED by tools/flow_icons.py; do not edit (rerun it).',
            'Each file it writes under flow-icons/, and each file those were made from (every SVG under flow/assets/,',
            'and flow/flow.css and flow/flow.js, which decide how large the flow draws them), by sha256. `shasum -a 256',
            "-c flow-icons/MANIFEST.sha256`, from the repository's root, checks both: once an input has changed it",
            'fails, and the script is due to be rerun.',
            'drawn by: Chromium %s (Playwright %s), saved by Pillow %s' % (chromium, version('playwright'), pillow)]
    listed = {**files, **inputs}
    files['flow-icons/MANIFEST.sha256'] = (''.join('# %s\n' % line for line in head) + ''.join(
        '%s  %s\n' % (sha(listed[k]), k) for k in sorted(listed))).encode('utf-8')
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--check', action='store_true', help='make everything again and compare with flow-icons/ instead '
                                                          'of writing; exit 1 on a difference')
    a = ap.parse_args()
    try:
        import PIL  # noqa: F401
        import playwright  # noqa: F401
    except ImportError as e:
        die('needs playwright (and its Chromium: python3 -m playwright install chromium) and Pillow: %s' % e)
    inputs = read_inputs()
    files = build(inputs)
    if read_inputs() != inputs:
        die('flow/ changed during the run; run it again')
    present = sorted(p.relative_to(REPO).as_posix() for p in OUT.rglob('*') if p.is_file()) if OUT.is_dir() else []
    stale = [k for k in present if k not in files]
    differ = [k for k in files if not (REPO / k).is_file() or (REPO / k).read_bytes() != files[k]]
    if a.check:
        for k in differ:
            print('differs: ' + k)
        for k in stale:
            print('not generated: ' + k)
        print('%d files, %d differ, %d stale' % (len(files), len(differ), len(stale)))
        sys.exit(1 if differ or stale else 0)
    for k in differ:
        (REPO / k).parent.mkdir(parents=True, exist_ok=True)
        (REPO / k).write_bytes(files[k])
    for k in stale:
        (REPO / k).unlink()
    for d in sorted({p for p in OUT.rglob('*') if p.is_dir()}, key=lambda p: -len(p.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    print('flow-icons/: %d files (%d written, %d already identical), %d stale removed; %d icons'
          % (len(files), len(differ), len(files) - len(differ), len(stale), len(files) - 2))


if __name__ == '__main__':
    main()
