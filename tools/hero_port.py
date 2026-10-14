#!/usr/bin/env python3
"""Regenerate the animated hero's scripts and assets from Kyu Kim's hero lab.

    python3 tools/hero_port.py UPSTREAM_HERO_LAB [--commit SHA] [--check]

UPSTREAM_HERO_LAB is project/hero-stage/hero-lab in a checkout of richardli-design/mock-shop-lp. The script only
reads files there; it never runs anything from that repository (not even git). Under this repository's hero/ it
writes:

  intro.js                   the lab's inline <head> script (classic; index.html loads it synchronously in <head>)
  field.js                   the lab's <script type="module"> (vendor/RoomEnvironment.js inlined into it)
  vendor/three.module.min.js the lab's vendored three.js, byte for byte
  vendor/LICENSE.txt         three.js's licence (the lab's vendor/LICENSE, renamed so its type follows from its name)
  scrim.svg                  the lab's option-3/scrim.svg, byte for byte
  products/NN.webp           every product photo the module can ask for (its PHOTOS and MODELS tables), byte for byte
  MANIFEST.sha256            the sha256 of each file above, with the upstream commit and pin they come from, for a
                             consumer that takes them without the lab (the Rails landing's re-sync); `shasum -a 256
                             -c hero/MANIFEST.sha256` from the repository's root checks them

Files under hero/ that it does not generate are removed, but hero.css, which is ported by hand (HERO.md).

Each change to the two scripts is a literal substitution that must match exactly once in the upstream text, so an
upstream edit under one of them stops the script rather than producing a silently different port. Each is listed,
with its upstream line and its reason, in the PORT NOTES comment written at the top of the file it changes. The
output depends only on the upstream bytes (no dates, no machine paths): running the script again reproduces the
same files byte for byte. --check compares instead of writing and exits 1 if anything differs.

Then the two scripts are checked against what the Rails page's CSP and this page's markup allow, outside the anchors
too (check_script): no static import or export, no bare 'three' specifier, exactly one import() (field.js; none in
intro.js), none of the lab's own hooks (getElementById('hero'), .copy, .hero-in), and none of fetch(,
XMLHttpRequest, new Worker, eval(, new Function, .innerHTML, document.write, setAttribute('style'. A hit stops the
script with the file, line and text.

The upstream commit is pinned here as the sha256 of every upstream file the port reads or copies (PIN: index.html,
RoomEnvironment.js, three.js, its licence, the scrim and the 89 photos); nothing is read from the checkout's git. If
any file differs, the script stops and lists them; review the change, rerun with --commit <sha> so the headers name
the commit the files came from, then update PIN_COMMIT and PIN (the run prints the new lines).
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / 'hero'
HAND_PORTED = 'hero.css'
UPSTREAM = 'richardli-design/mock-shop-lp'
LAB = 'project/hero-stage/hero-lab'
PIN_COMMIT = '1914c8e'   # R19, "hero particle cloud, all 17 models" (the hero is unchanged at main fbc0168)
# sha256 of every upstream file the port reads or copies, at PIN_COMMIT (lab-relative paths)
PIN = {
    'index.html': 'be04a48fb933b4146b4fa27071f1bcdc865ab4449307c1bcf640ad6eec76e78a',
    'vendor/RoomEnvironment.js': '85869bdd22f7cf0b22e68dcefe6cb710480af0f5c901a76f7a7764fd07fc8014',
    'vendor/three.module.min.js': '08fd7545d13d2c7fb65ab691530a802dafefd638596501854f267d0fb13c39e7',
    'vendor/LICENSE': '4c40a1ef62450b857c3b2aaf294936304cd552d965fbcd9d32d4c5bcf4ba4454',
    'option-3/scrim.svg': 'c5634b166844ac44bf0aff68281646f962cd5a9b83d93d3633dcc11e932063d9',
    'products/00.webp': '31412089e8a18927157ea774eeeef902364f4d8c710f7e15f23d7988dab66a1a',
    'products/01.webp': '25905c6adae208375e877bda4029e8c0ac3d83b0f5c90aa6d4e4dfd4884000ae',
    'products/02.webp': '482f5a6cfa9251857c62b771ceb67471fb42ba2b33c3dd01dde99db7d31b716a',
    'products/03.webp': '7b7de94ad3ef83b4d331dd4ed1dec0390448d7785726c22ded3510252000e5cb',
    'products/04.webp': 'e25e7d53c5d2bc93f6314a26f0afbf957cb585908e8bd78efa30d150398a7a6c',
    'products/05.webp': '8a6d2916ff8d41cd218b01809d77f85d5e8c1783634a3f59a369a2c22214a5ae',
    'products/06.webp': '6f2efa31b11ccb7e32128eabd4fb2dd8c416008597e68482d9ca8afcb97d6600',
    'products/07.webp': 'fa3869908b5d1907991bfcf6a76a37f1abfa08ae74030f69ba6d75f698af137e',
    'products/08.webp': '2216c2d3ff23b405e5999badb23411ca3a2ed96b961b1abea07f45bac3b7fe17',
    'products/09.webp': '91d31f3ff160db7aeab54660478219203c9da0c9bc2779227075aaecbc06b5ee',
    'products/10.webp': '67f94fc65d00b0caeafba2d16cb3ea12f28336e9d5af3f38d62acc1e56d0e94b',
    'products/11.webp': 'a31f05f7073f7980b87c5333a30ac32da2f31dbb6ec033481dff9d62518192df',
    'products/12.webp': '40b0951c66816154f279ca7d251caa52fe73e5d464185bf7c80036d430edf0f5',
    'products/13.webp': '99d65d6cd96ffef642317b06974414f4c788a5469310d46b4fe63f2f947ab49f',
    'products/14.webp': '8c999b9b780690b50f0281f41c6512fdf9f60c403486ffaa409180e1502dfabd',
    'products/15.webp': 'e7d09df043289e355bf645080660d156413545b21fc67fe18856f71a93255f2d',
    'products/16.webp': 'eabc7b2d7dccde9a7335a8291bc8ff9a597a534601b5054fbe39b4b728857ffa',
    'products/17.webp': '03d386ad9d4ab0e4fcedfd8246841d5e0b7006fb7cad86585dc7dad872f147be',
    'products/18.webp': 'bfd673f7e1ef324ff89eddee10d5079f2dc403cecc194409038cd7378086d497',
    'products/19.webp': 'fad9a155c72428cece62bddd66c36bc3b9600c581dde8faf013331896c9c5c3d',
    'products/20.webp': 'b5c00ce4a508f21ed31bdf21bc927b47bf4bb59133824e4d3f14dec3d9b7fe8d',
    'products/21.webp': 'a3bf86f1d92fb5945aa16f07f0364fed63bb40fb94ae73c5a2903f80c73ebbae',
    'products/22.webp': '88f88fa5f57ea78b36ecf585f8ac8bb83175e6c63572d21f4dfac80dd168ef83',
    'products/23.webp': '997b7e306f2fd2358aa118b396c9f4fb5a8be29291978384aafbd38ed008d091',
    'products/24.webp': '2bc4b6da5be545f8dda1af789a45342406d5ec48ad7d2cd9eb5bf2c5e006c307',
    'products/25.webp': '7adc99234af72db07634d998d44764acc4f906fa19dcd9c8842f6f672861139f',
    'products/26.webp': '6a16a727e158f8a71efec15da43623d3512d1e2ac72f535496e11afc964d7661',
    'products/27.webp': '4e1bbd74917a116b350acb6b78cc11df656206e61feb62082bd81881f8fc96fd',
    'products/28.webp': '0932c20cb710d0f78c935dd5470065302a25b82b3bb01a3ddefb65e889cff9d8',
    'products/29.webp': '739efb017a2a2010e2a249bac48801129ce3712f92170654f5ec0b603ddcf1c3',
    'products/30.webp': 'ecc323d2f943eef1be98b50f5dbcc020405bdc00e4645fda3c8cfa729919eaf0',
    'products/31.webp': '030fb12f85e2b756657314e3e166cc73a3b9f42a2d0508a34dbec147bf8b5e28',
    'products/32.webp': 'ab7cfa187c8e49f5c1365c16035bee1e92b39d2f6612d653fe52fd5abb4220cb',
    'products/33.webp': 'eb72d4a5bf32d807293a0175ff7fb88df47a96ed51ade9ffb0033d95fb48ba80',
    'products/34.webp': '9c2fbee1066447103654d1c1eb5d866bd9460cdec0cd8d911ee3eb85382afd15',
    'products/35.webp': 'daae56eba0ee2d4e8afec9774fc58a8d11a1da860e49a7cb68ee3a80aa5b09c5',
    'products/36.webp': 'feb61d391c4c96c16fe682a08295e762f051708a20994ca5565db3d7b3ac9b00',
    'products/37.webp': '63ebc61cb9a17eb78a1c70917169f7c56b7749f4f30e4aef572a9699eebb487d',
    'products/38.webp': '80a5b0d36ed00350f062221a64e9c8c2357b50f99fab16fb86baa003e2f13b60',
    'products/39.webp': '1011a73937f840879ba6202a374eaa45a44e0f677024e4fabd2c06305b7e2c7d',
    'products/40.webp': '54e16e409d84eab1b8720c132a4cbb9b3012995eaa38c1543154b35a2c791a4c',
    'products/41.webp': 'b01e8e94fcf28ad4cd0d45c6b69c53f5d7738e163f1c5da37e87461527dcccb2',
    'products/42.webp': '86d0f439350806d9ab7ff5bdd0da138b56663f74e61603362fa7b276478d7466',
    'products/43.webp': '4d5c8b57bae288e547db22898e5343d33e341937fd96eb6b8b7b6162e60e852f',
    'products/44.webp': '003fd19b8d0bc662df900e30c93143fef56d5b0829f366edb95a39b1e885d3e6',
    'products/45.webp': '1153eaaf571d402d644e4b7822bb77870698ce018d002efcaf07d15eadbecad1',
    'products/46.webp': '69ec174555bc95a7f3fd99b1e06888ced23dd87ed831abee8dcf76fc3c4f4c86',
    'products/47.webp': '28077fcf2f8026696e8a9b5591599591d29b41f6c66f24b4de0a37ecaf0592c2',
    'products/48.webp': 'b027462eb77b5f42f39a1aa08d8395086e40c85f09a783c50591068781b6562d',
    'products/49.webp': 'bf3a8c9a86dbee74770d89e0b9772a8f6c53fa9ba00453db05e298f6199b3b31',
    'products/50.webp': '1e6187a358ceae542f1c061bcd2397811a6f2634eda9885790d4b2716c03c215',
    'products/51.webp': '9e261d68e529d35147ed0f8be3d3ea90a02e4426293acb44872b47e068d91d4f',
    'products/52.webp': 'd524f0ce26833e4855bb7701bfd3292459af1cd2fd2c5084e2160d3199efc997',
    'products/53.webp': 'ba7658eecabf811b49e2064d696cc6dc7c01912161093d39e6aa867768c3dfc7',
    'products/54.webp': 'b9084803a39645741828385666efe53bca810f09cb93d848e82539b00ffeaa60',
    'products/55.webp': '50f621f1cf251753581a8a095e45fc89fe7aa4cfebe3882beaf6f70924c2b2f2',
    'products/56.webp': 'b0e79b5898259526bb90a44513c2e2e6798ab1409372a2fddf8fadabd7ded4f7',
    'products/57.webp': 'edaea0e37b125518d2648ad6364d00cd5ca6a726a9d8984c6c91c93236462807',
    'products/58.webp': 'dec38294ff8555e6e91bf8a460733af854f04c617abbfbe58527e88090ebd53e',
    'products/59.webp': '6cdb93c98b4c5c32ad580603fe2cc78c9c07357616ea4657647e1079433925ba',
    'products/60.webp': '8fd4c2817397bd3a3d0a4d9ece4c33fde9a64a6449a97f567593cd530811a8ae',
    'products/61.webp': 'b07fc5774f38726ef1af5c8066bd4d5fac4903c124d85e8ec0de4107f12b4a1a',
    'products/62.webp': '175065276ff69b45a9f02b12511ff0ad22930479d0c8d6d57b9d4e7c8f230a0c',
    'products/63.webp': '038ca04091125fad0d0446187d7ef9b03fc64dd789e4f1032e29525fac97158c',
    'products/64.webp': '607c86ad4177d311e870fe65115d44a7ccf757dd413cb0b9b656aeedeeb460f0',
    'products/65.webp': '7906b127ad4976c0cb66de1c7d67790d3205d4a1dfb52e79cb94b2b20d435c5c',
    'products/66.webp': 'd85945ba60456f9109eb85828924425e02ff8565db4d8313be50efe33b5b232a',
    'products/67.webp': '20f2671158d97e5dfe4fa740079ed18d2873be72f233afa65c0e94dec18e3c81',
    'products/68.webp': '4e14ef7a4c0890402b0b31246c44e53f3a6d696d41042a910edc229e861ba0ba',
    'products/69.webp': '85d16c00aad88af09a4c603a0ae2bd9e0903ba8dce39c8d8e29f64791e495f2a',
    'products/70.webp': '64bf782f6c02d8099ac79f6109e6103c7be4388dd16c4e6a5ef28b550d4f1c73',
    'products/71.webp': 'f9918e9ff2afaffcc4d2fd16385ebd7fd92af75374f694c2d376b798f867dbf3',
    'products/72.webp': 'c288de31eff8b814f417e222c5ec67350d7543d971eb701924a45702386beefb',
    'products/73.webp': 'e64758a2379c97650a6c8736360eb02ee37a7c59acf8252fd4debe0e70bae9df',
    'products/74.webp': '7814c721235a06797284c12b63e627f0d694085848f642350ee6f88f9095df1d',
    'products/75.webp': 'c1593b1cda9a04527e309afbebcb152cda91e5a46f9e1ce67d1e42cc1ede61a1',
    'products/76.webp': '09436f208edc4129bb8e8db3468865290f1a4d28c87b0cd54326a25f87f7d8ea',
    'products/77.webp': 'f7afa9067d812bdcd2307e27c04a91cd6f3ae241ea566abeabae952267953c66',
    'products/78.webp': 'cd12d3608a0f008cb4fae1ddda2ed7ade3cec85e373349e1d2d52b066662a868',
    'products/79.webp': 'c3ad7170c8ac969a3af5fea49384f2eef3a2408c3011151a0c712dfbb1130133',
    'products/80.webp': '4116dc299e1aede1c41ad7ccfe13ee48a8e024172de49f593fbc101309a8df3f',
    'products/81.webp': 'ca9bf9f5d983346fcefb5875d8123aad68948ef810bf5792e5c38b4dae6ee285',
    'products/82.webp': '461235b531f09d4a3880c1e9e415880d39e280a2c027727442d96ea2fb695b84',
    'products/83.webp': '994502ce9b50e2c6e06f3c505791c39f260dbe2b6fb39bdfa6391d20baa00680',
    'products/84.webp': 'b389eab8a501dafb9bda63183180f8d9a6858bcc7d199485c91610f7e3042f93',
    'products/85.webp': 'b578d36a784aa7f50e0148081cc2f86dcc04505a57e078bf91dc2c4005bc07b7',
    'products/86.webp': 'ee59f3bf411fd8c51cdd9a54a935d298a084254b4e3025840a763a04c7563d8e',
    'products/87.webp': '61da665f24f3b95d0eeb04e031bb2cf66795ae967e2765b86f3e5e85386ca911',
    'products/88.webp': 'b862be0d2b3ac5f013472d709449a97019974f2b60b14e27b8da1f06e4dd6ce4',
}
FIXED = ['index.html', 'vendor/RoomEnvironment.js', 'vendor/three.module.min.js', 'vendor/LICENSE',
         'option-3/scrim.svg']


def die(msg):
    sys.exit('hero_port.py: ' + msg)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def element_body(lines, open_at, what):
    """The text between the opening tag on line index open_at and the next '</script>' line, with its 1-based
    first line number."""
    for end in range(open_at + 1, len(lines)):
        if lines[end] == '</script>':
            return '\n'.join(lines[open_at + 1:end]) + '\n', open_at + 2, end
    die('no </script> after the ' + what)


class Port:
    """Upstream text plus the asserted substitutions made to it, with their upstream lines for the notes."""

    def __init__(self, text, first_line):
        self.orig, self.text, self.first, self.notes = text, text, first_line, []

    def sub(self, old, new, *notes):
        """Replace old (exactly once upstream and in the port so far) by new; each note becomes a numbered PORT NOTES
        entry at old's upstream line."""
        for label, t in (('upstream', self.orig), ('the port so far', self.text)):
            if t.count(old) != 1:
                die('%d matches (want exactly 1) in %s for:\n%s' % (t.count(old), label, old))
        at = self.first + self.orig[:self.orig.index(old)].count('\n')
        end = at + old.rstrip('\n').count('\n')
        self.text = self.text.replace(old, new, 1)
        for note in notes:
            self.notes.append(('L%d' % at if end == at else 'L%d-%d' % (at, end), note))


def wrap_var(names):
    """`var A = THREE.A, B = THREE.B, ...;` wrapped at 116 columns"""
    out, line = [], 'var '
    for i, n in enumerate(names):
        item = '%s = THREE.%s' % (n, n) + (';' if i == len(names) - 1 else ',')
        if len(line) + len(item) > 116:
            out.append(line.rstrip())
            line = '    '
        line += item + ' '
    return '\n'.join(out + [line.rstrip()]) + '\n'


def notes_block(port, title, lead, tail):
    out = ['/* ' + title, '', 'PORT NOTES'] + lead + ['']
    for i, (where, note) in enumerate(port.notes, 1):
        first, *rest = note.strip('\n').split('\n')
        out.append('%d. %s: %s' % (i, where, first))
        out += [' ' * len('%d. ' % i) + r if r else '' for r in rest]
    out += [''] + tail
    text = '\n'.join(('   ' + l if l else '').rstrip() if n else l for n, l in enumerate(out))
    if '*/' in text:
        die('a PORT NOTES line would close the comment early')
    return text + ' */\n\n'


# ---- what the two scripts may contain (check_script) ------------------------------------------------------------
BEFORE_REGEX = {'return', 'typeof', 'instanceof', 'in', 'of', 'new', 'delete', 'void', 'throw', 'case', 'do',
                'else', 'yield', 'await'}


def scan_js(text, name):
    """(code, strings) for a script: the text with every comment blanked to spaces (newlines kept, so a line of code
    is the same line of the file), and (line, text) for every string and template literal. A small scanner: comments,
    '...' and "..." strings, `...` templates (and the code in their ${...}), and regex literals, told from a division
    by the token before them."""
    out, strings, stack = [], [], []
    i, n, depth, last = 0, len(text), 0, ''

    def line_of(k):
        return text.count('\n', 0, k) + 1

    def regex_ok():
        if not last:
            return True
        if last.startswith('id:'):
            return last[3:] in BEFORE_REGEX
        if last in ('num', 'str', 'regex'):
            return False
        return last[6:] not in ')]}'

    while i < n:
        c = text[i]
        if text.startswith('//', i):
            j = text.find('\n', i)
            j = n if j < 0 else j
            out.append(' ' * (j - i))
            i = j
        elif text.startswith('/*', i):
            j = text.find('*/', i + 2)
            if j < 0:
                die('%s line %d: a comment that never ends' % (name, line_of(i)))
            out.append(re.sub(r'[^\n]', ' ', text[i:j + 2]))
            i = j + 2
        elif c in '\'"':
            j = i + 1
            while j < n and text[j] != c:
                if text[j] == '\n':
                    die('%s line %d: a string that never ends' % (name, line_of(i)))
                j += 2 if text[j] == '\\' else 1
            strings.append((line_of(i), text[i + 1:j]))
            out.append(text[i:j + 1])
            i, last = j + 1, 'str'
        elif c == '`' or (c == '}' and stack and stack[-1] == depth):
            if c == '}':
                stack.pop()
            j = i + 1
            while j < n and text[j] != '`' and not text.startswith('${', j):
                j += 2 if text[j] == '\\' else 1
            if j >= n:
                die('%s line %d: a template literal that never ends' % (name, line_of(i)))
            strings.append((line_of(i), text[i + 1:j]))
            if text[j] == '`':
                out.append(text[i:j + 1])
                i, last = j + 1, 'str'
            else:
                stack.append(depth)
                out.append(text[i:j + 2])
                i, last = j + 2, 'punct:{'
        elif c == '/' and regex_ok():
            j, cls = i + 1, False
            while j < n and (cls or text[j] != '/'):
                if text[j] == '\n':
                    die('%s line %d: a regular expression that never ends' % (name, line_of(i)))
                if text[j] == '\\':
                    j += 1
                elif text[j] == '[':
                    cls = True
                elif text[j] == ']':
                    cls = False
                j += 1
            j += 1
            while j < n and (text[j].isalnum() or text[j] in '_$'):
                j += 1
            out.append(text[i:j])
            i, last = j, 'regex'
        elif c.isspace():
            out.append(c)
            i += 1
        elif c.isalpha() or c in '_$' or ord(c) > 127:
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] in '_$' or ord(text[j]) > 127):
                j += 1
            out.append(text[i:j])
            i, last = j, 'id:' + text[i:j]
        elif c.isdigit() or (c == '.' and text[i + 1:i + 2].isdigit()):
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] in '._'):
                j += 1
            out.append(text[i:j])
            i, last = j, 'num'
        else:
            depth += {'{': 1, '}': -1}.get(c, 0)
            out.append(c)
            i, last = i + 1, 'punct:' + c
    return ''.join(out), strings


# (pattern on code with its comments blanked, what it is): never in either script
SINKS = [(r'\bfetch\s*\(', 'fetch('), (r'\bXMLHttpRequest\b', 'XMLHttpRequest'),
         (r'\bnew\s+(Shared)?Worker\b', 'new Worker'), (r'\beval\s*\(', 'eval('), (r'\bnew\s+Function\b', 'new Function'),
         (r'\.\s*innerHTML\b', '.innerHTML'), (r'\bdocument\s*\.\s*write(ln)?\b', 'document.write'),
         (r'\bsetAttribute\s*\(\s*[\'"`]style[\'"`]', "setAttribute('style'"),
         (r'\bgetElementById\s*\(\s*[\'"`]hero[\'"`]\s*\)', "the lab's getElementById('hero') hook"),
         (r'^\s*import\s*[\w{*\'"]', 'a static import'), (r'^\s*export\b', 'an export')]


def check_script(name, text, imports):
    """Stop on anything in a generated script that the Rails CSP, an importless module or this page's markup does not
    allow (see SINKS), on a bare 'three' specifier or one of the lab's own .copy / .hero-in hooks in a string, and
    unless the script has exactly `imports` dynamic import() calls."""
    code, strings = scan_js(text, name)
    lines, src = code.split('\n'), text.split('\n')
    for k, line in enumerate(lines, 1):
        for pat, what in SINKS:
            if re.search(pat, line):
                die('%s line %d: %s, which the port must not contain:\n%s' % (name, k, what, src[k - 1]))
    for k, s in strings:
        if re.fullmatch(r'three(/.*)?', s, re.S):
            die("%s line %d: the bare specifier '%s' (it needs an importmap, which the CSP refuses):\n%s"
                % (name, k, s, src[k - 1]))
        if re.search(r'\.(copy|hero-in)(?![\w-])', s):
            die("%s line %d: the lab's own hook '%s' (this page's are .hero__copy / .hero__inner):\n%s"
                % (name, k, s, src[k - 1]))
    calls = [k for k, line in enumerate(lines, 1) for _ in re.finditer(r'\bimport\s*\(', line)]
    if len(calls) != imports:
        die('%s: %d dynamic import() calls (lines %s), want exactly %d' % (name, len(calls), calls or '-', imports))


def three_revision(three_b):
    """three's REVISION, read from the vendored build (`const t="170"` ... `t as REVISION` when minified)"""
    t = three_b.decode('utf-8', 'replace')
    m = re.search(r'[{,]\s*([\w$]+)\s+as\s+REVISION\s*[,}]', t)
    name = m.group(1) if m else 'REVISION'
    v = re.search(r'(?:\b(?:const|let|var)\s+|,\s*)' + re.escape(name) + r'\s*=\s*[\'"](\d+[^\'"]*)[\'"]', t)
    if not v:
        die('vendor/three.module.min.js: no REVISION found')
    return v.group(1)


def read_sources(lab):
    """Every upstream file the port reads or copies (lab-relative path -> bytes), and the photo ids the module can
    ask for (its PHOTOS and MODELS tables)."""
    src = {}
    for k in FIXED:
        if not (lab / k).is_file():
            die('%s has no %s' % (lab, k))
        src[k] = (lab / k).read_bytes()
    text = src['index.html'].decode('utf-8')
    pm = re.search(r'\nvar PHOTOS = (\[\n.*?\n\]);\n', text, re.S)
    mm = re.search(r'\nvar MODELS = \[\n(.*?)\n\];\n', text, re.S)
    if not pm or not mm:
        die('PHOTOS / MODELS tables not found')
    ids = sorted({p[0] for p in json.loads(pm.group(1))} | set(re.findall(r"\bn: '(\d+)'", mm.group(1))))
    for i in ids:
        k = 'products/%s.webp' % i
        if not (lab / k).is_file():
            die('the module can ask for %s, which the lab does not have' % k)
        src[k] = (lab / k).read_bytes()
    return src, ids


def build(src, ids, commit):
    index_b, roomenv_b, three_b = src['index.html'], src['vendor/RoomEnvironment.js'], src['vendor/three.module.min.js']
    lines = index_b.decode('utf-8').split('\n')
    head_sha = sha(index_b)
    rev = 'r' + three_revision(three_b)
    photos_sha = sha(''.join('%s  %s\n' % (sha(src[k]), k) for k in sorted(src) if k.startswith('products/'))
                     .encode('utf-8'))

    # ---- the two script elements ------------------------------------------------------------------------------
    try:
        style_end = lines.index('</style>')
        module_open = lines.index('<script type="module">')
    except ValueError as e:
        die('upstream layout changed: %s' % e)
    if lines[style_end + 1] != '<script>':
        die('the head script no longer follows </style>')
    intro_src, intro_first, intro_close = element_body(lines, style_end + 1, 'head script')
    field_src, field_first, field_close = element_body(lines, module_open, 'module script')
    if not intro_src.startswith('/* Set before first paint') or not intro_src.endswith('})(document.documentElement);\n'):
        die('the head script does not start and end as expected')
    if not field_src.startswith('/* ---- the field') or not field_src.endswith('\nplay();\n'):
        die('the module script does not start and end as expected')
    if field_src.count("'products/'") != 1:
        die('the module builds more than one products/ URL now')

    # ---- intro.js ---------------------------------------------------------------------------------------------
    intro = Port(intro_src, intro_first)
    intro.sub("(function (d) {\n",
              "(function (d) {\n"
              "  // PORT (edit 1): html.hero-on is the JS-on hook (hero/hero.css): the field draws the hero instead of the\n"
              "  // static picture. Set first, whatever the motion preference (the field still draws a still room then), and\n"
              "  // only where hero/field.js can run: a browser with module scripts, and not file:// (no modules there).\n"
              "  if ('noModule' in HTMLScriptElement.prototype && location.protocol !== 'file:') d.classList.add('hero-on');\n",
              "inserted as the IIFE's first statement, before the reduced-motion return: class hero-on on <html>\n"
              "when 'noModule' in HTMLScriptElement.prototype and location.protocol !== 'file:'. hero/hero.css shows\n"
              "the field's layers (and drops the static hero-bg.webp) only under it, so with JS off, without modules or\n"
              "from file:// the hero stays the static picture. It comes off again if hero/field.js itself fails (edit\n"
              "6), if three.js cannot load or if the page has no hero markup (hero/field.js).")
    intro.sub("  d.className = 'intro' + (innerWidth > 900 ? ' anim' : '');\n",
              "  d.classList.add('intro'); if (innerWidth > 900) d.classList.add('anim');\n",
              "`d.className = 'intro' + (innerWidth > 900 ? ' anim' : '')` -> classList.add of the same classes: the\n"
              "assignment wiped every other class on <html> (hero-on here; the Rails layout's js).")
    intro.sub("    var c = document.querySelector('.copy');\n",
              "    var c = document.querySelector('.hero .hero__copy');\n",
              "`.copy` -> `.hero .hero__copy`: the copy column is the page's own wrapper class (no .copy here).")
    intro.sub("c.querySelectorAll('h1 > span, .hg p, .mtabs, .hwell')",
              "c.querySelectorAll('h1 > span, .hero__sub, .tabs, .well')",
              "the entrance's parts `h1 > span, .hg p, .mtabs, .hwell` -> `h1 > span, .hero__sub, .tabs, .well`, inside\n"
              "the copy column: this page's headline lines, sub-line, tab strip and well (the same list as the\n"
              "entrance's :is() in hero/hero.css; the CTA's .tabs/.well are outside the column).")
    intro.sub("document.fonts.load('330 64px Inter'), document.fonts.load('16px \"JetBrains Mono\"')",
              "document.fonts.load('340 64px Inter'), document.fonts.load('400 14px \"JetBrains Mono\"')",
              "the faces awaited `330 64px Inter` / `16px \"JetBrains Mono\"` -> `340 64px Inter` /\n"
              "`400 14px \"JetBrains Mono\"`: this page's headline and well faces (Google Fonts, display=swap, where the\n"
              "lab vendors both with font-display:block). The 1.5s fail-safe is unchanged.")
    intro.sub("  // the light round the prompt box: teal unless ?glow=blue (see .hbeam)\n",
              "  // PORT (edit 6): if hero/field.js never gets the field going, the hero goes back to its static picture\n"
              "  // (hero-on off). Its <script data-hero-field> fires 'error' when the module cannot load (404, network, CSP,\n"
              "  // CORS); an uncaught error from it or from three.js (a parse error where there is no top-level await, a\n"
              "  // throw) reaches window as an ErrorEvent naming that file. Capture phase, because a script's own 'error'\n"
              "  // does not bubble; and only until the field reports boot (data-field=\"on\" on the hero). three's URL as\n"
              "  // field.js resolves it: #fl's data-three, else the modulepreload, else vendor/ next to field.js.\n"
              "  addEventListener('error', function (e) {\n"
              "    var s = document.querySelector('script[data-hero-field]'), f = document.getElementById('fl'),\n"
              "        h = f && f.closest('.hero'), p, u;\n"
              "    if (!s || (h && h.dataset.field === 'on')) return;\n"
              "    if (e.target !== s) {\n"
              "      if (!e.filename) return;\n"
              "      p = document.querySelector('link[rel=\"modulepreload\"]');\n"
              "      try { u = new URL(f && f.dataset.three || (p ? p.href : 'vendor/three.module.min.js'), s.src).href; }\n"
              "      catch (x) { u = ''; }\n"
              "      if (e.filename !== s.src && e.filename !== u) return;\n"
              "    }\n"
              "    d.classList.remove('hero-on');\n"
              "    if (h) h.dataset.field = 'off';\n"
              "  }, true);\n"
              "  // the light round the prompt box: teal unless ?glow=blue (see .hbeam)\n",
              "inserted after edit 1: a capture-phase window 'error' listener that gives the hero its static picture\n"
              "back (class hero-on off, data-field=\"off\" on the hero) when hero/field.js fails before it reports boot.\n"
              "Its element is index.html's <script type=\"module\" data-hero-field>: a load error (404, network, CSP,\n"
              "CORS) fires 'error' on it (e.target is the script; captured on window because it does not bubble), and a\n"
              "parse error (a module-capable engine without top-level await: Chrome/Firefox <= 88, Safari <= 14) or an\n"
              "uncaught throw (in the module or a callback of it, or inside three.js) is an ErrorEvent whose filename is\n"
              "that script's URL or three's. three's URL is resolved as field.js resolves it: #fl's data-three\n"
              "(against field.js's URL, like import()), else the modulepreload's href, else vendor/three.module.min.js\n"
              "next to field.js. Ignored once the hero has data-field=\"on\" (hero/field.js, edit 10), and for an\n"
              "ErrorEvent with no filename (a ResizeObserver loop note). Without it, a field.js that never ran left\n"
              "hero-on set: no picture and no field, an empty dark hero.")
    intro.sub("  if (/(^|&)glow=blue(&|$)/.test(location.search.slice(1))) d.setAttribute('data-glow', 'blue');\n",
              "  // PORT (edit 7): the lab's URL knobs only with ?lab in the query (?lab&glow=blue, ?lab&pt=0), as in field.js\n"
              "  var lab = /(^|&)lab(=|&|$)/.test(location.search.slice(1));\n"
              "  if (lab && /(^|&)glow=blue(&|$)/.test(location.search.slice(1))) d.setAttribute('data-glow', 'blue');\n",
              "the ?glow=blue knob, and ?pt=0 (edit 8), only with a `lab` parameter in the query (?lab&glow=blue,\n"
              "?lab=1&pt=0); a `lab` flag is set for both. The published page's visitors bring their own queries, and\n"
              "hero/field.js's knobs (?t=, a common cache-buster, among them) are behind the same flag (its edit 8).")
    intro.sub("  var pt = !/(^|&)pt=0(&|$)/.test(location.search.slice(1)) && !!window.CanvasRenderingContext2D;\n",
              "  var pt = !(lab && /(^|&)pt=0(&|$)/.test(location.search.slice(1))) && !!window.CanvasRenderingContext2D;\n",
              "`?pt=0` only with ?lab (edit 7): `!/(^|&)pt=0(&|$)/.test(...)` -> `!(lab && /(^|&)pt=0(&|$)/.test(...))`.")
    intro_out = notes_block(
        intro, 'hero/intro.js -- GENERATED by tools/hero_port.py; do not edit (change the generator and rerun it).',
        ['Upstream: %s, %s/index.html @ %s (Kyu Kim)' % (UPSTREAM, LAB, commit),
         '  sha256 %s' % head_sha,
         "  this file = its inline <head> script, lines %d-%d (the IIFE over document.documentElement), verbatim but for"
         % (intro_first, intro_close),
         '  the edits below. Classic script: index.html loads it synchronously in <head>, after the stylesheets (the',
         "  document.fonts.load() calls only match a face once the Google Fonts sheet is in), before first paint.",
         'Edits (upstream line: what and why):'],
        ['Verbatim otherwise: every constant (LT0 .42, SW .6, the 1.5s fail-safe, plain() at 4s, up to 640 letter points',
         '+ 60% round them, MY 100, MX <= 150, G 8), the ?pt=0 and ?glow=blue knobs (behind ?lab, edits 7-8), the .anim',
         "class (nothing reads it) and the beam's IntersectionObserver (.hb-off)."]) + intro.text

    # ---- field.js ---------------------------------------------------------------------------------------------
    renv = roomenv_b.decode('utf-8')
    m = re.match(r"(/\*\*\n(?: \*.*\n)+ \*/\n)\n(import \{([^}]*)\} from 'three';\n)\n", renv)
    if not m or renv.count("import ") != 1 or not renv.endswith('\nexport { RoomEnvironment };\n'):
        die('vendor/RoomEnvironment.js no longer has the expected header, import and export')
    names = [n.strip() for n in m.group(3).split(',') if n.strip()]
    renv_body = renv[m.end():-len('export { RoomEnvironment };\n')].rstrip('\n') + '\n'
    if 'class RoomEnvironment extends Scene' not in renv_body:
        die('vendor/RoomEnvironment.js: no class RoomEnvironment')
    renv_lines = renv.count('\n')

    field = Port(field_src, field_first)
    field.sub("import * as THREE from 'three';\nimport {RoomEnvironment} from './vendor/RoomEnvironment.js';\n",
              "// PORT (edit 1): the room, the module's one hook into the page, first: three's URL is on it. Without the\n"
              "// room, the hero round it, its row or its copy column (a page that loads this module but has no hero), the\n"
              "// hero keeps its static picture and the module stops here, quietly: no error, and nothing below runs.\n"
              "const room = document.getElementById('fl');\n"
              "{\n"
              "  const h = room && room.closest('.hero');\n"
              "  if (!h || !h.querySelector('.hero__inner') || !h.querySelector('.hero__copy')) {\n"
              "    document.documentElement.classList.remove('hero-on');\n"
              "    if (h) h.dataset.field = 'off';\n"
              "    await new Promise(function () {});\n"
              "  }\n"
              "}\n"
              "// three by dynamic import: #fl's data-three when the page gives one (Rails: the digested asset_path),\n"
              "// else the copy next to this file. If it cannot load (blocked, offline, refused by a CSP), the hero goes\n"
              "// back to its static picture and the module stops here, quietly: nothing below runs.\n"
              "let THREE;\n"
              "try {\n"
              "  THREE = await import(room.dataset.three || new URL('vendor/three.module.min.js', import.meta.url).href);\n"
              "} catch (e) {\n"
              "  document.documentElement.classList.remove('hero-on');\n"
              "  const h = room.closest('.hero');\n"
              "  if (h) h.dataset.field = 'off';\n"
              "  await new Promise(function () {});\n"
              "}\n"
              "/* RoomEnvironment, inlined: the lab's vendor/RoomEnvironment.js (three.js's\n"
              "   examples/jsm/environments/RoomEnvironment.js, shipped beside three " + rev + "; MIT, see vendor/LICENSE.txt),\n"
              "   verbatim from its header comment on, with its `import {...} from 'three'` taken off the namespace\n"
              "   above and its `export` dropped. */\n"
              "const RoomEnvironment = (function () {\n"
              + wrap_var(names) + "\n"
              + m.group(1) + "\n" + renv_body + "\nreturn RoomEnvironment;\n})();\n"
              "// PORT (edit 1): every product photo's URL, from one place (photos load only in the room without WebGL):\n"
              "// #fl's data-products, an optional JSON map of id -> URL (Rails: digested image_paths), read once;\n"
              "// else products/<id>.webp next to this file.\n"
              "var PRODUCTS = null;\n"
              "try { if (room.dataset.products) PRODUCTS = JSON.parse(room.dataset.products); } catch (e) { PRODUCTS = null; }\n"
              "function productSrc(id) {\n"
              "  var u = PRODUCTS && PRODUCTS[id];\n"
              "  return typeof u === 'string' && u ? u : new URL('products/' + id + '.webp', import.meta.url).href;\n"
              "}\n",
              "the static imports `import * as THREE from 'three'` and `import {RoomEnvironment} from\n"
              "'./vendor/RoomEnvironment.js'` -> `const room = #fl` hoisted (edit 2), a guard, then `THREE = await\n"
              "import(room.dataset.three || new URL('vendor/three.module.min.js', import.meta.url).href)` in a try/catch,\n"
              "then RoomEnvironment inlined, then productSrc(). Why: 'three' resolved through an inline importmap, which\n"
              "the Rails page's CSP (script-src without 'unsafe-inline') refuses, and Propshaft serves every asset under a\n"
              "digested name that a hard-coded relative URL cannot know, so the page passes the URL in (data-three) and\n"
              "the fallback is the copy next to this file (this static site). RoomEnvironment imported the bare\n"
              "specifier 'three' too, so it is inlined over the namespace (vendor/RoomEnvironment.js, %d lines,\n"
              "sha256 %s).\n"
              "The guard: with no #fl, or no .hero round it, or no .hero__inner or .hero__copy in that (a page that\n"
              "loads this module without the hero's markup), class hero-on comes off <html>, data-field=\"off\" goes on\n"
              "the hero if there is one, and the module stops as below; the lab threw a TypeError at its first hook.\n"
              "`let`, not an import binding: the namespace is the same object `import * as` gives, so THREE.x and\n"
              "__p3.THREE are unchanged. If the import fails: class hero-on comes off <html> (the\n"
              "static hero-bg.webp, no beam, no scrim), data-field=\"off\" goes on the section (if the room is still in\n"
              "one), and the module awaits a promise that never settles, so it stops with no uncaught error and no\n"
              "console output. Timing: three now starts loading when this module runs (index.html loads it async, so as\n"
              "soon as it has arrived) instead of while the page parses; index.html's <link rel=\"modulepreload\"> of the\n"
              "same URL brings the early fetch back.\n"
              "productSrc(id): #fl's data-products (an optional JSON map id -> URL, parsed once, in a try/catch), else\n"
              "new URL('products/' + id + '.webp', import.meta.url); see edit 6." % (renv_lines, sha(roomenv_b)))
    field.sub("    room = document.getElementById('fl'),\n", "",
              "`room = document.getElementById('fl'),` taken out of the var list: hoisted above the import as a const\n"
              "(edit 1), which needs it first. The lab's local names room (makeGL's `room = new RoomEnvironment()`, the\n"
              "dryer's `function room`) are function-scoped and shadow it, unchanged.")
    field.sub("    hero = document.getElementById('hero'),\n", "    hero = room.closest('.hero'),\n",
              "`hero = document.getElementById('hero')` -> `room.closest('.hero')`: this page's hero has no id (its\n"
              "markup is hooked on classes; the Rails markup has other ids).")
    field.sub("    hin = hero.querySelector('.hero-in'),\n", "    hin = hero.querySelector('.hero__inner'),\n",
              "`.hero-in` -> `.hero__inner`: the copy's row, which must be the copy column's offsetParent (hero/hero.css\n"
              "positions it under html.hero-on).")
    field.sub("    copy = hero.querySelector('.copy'),\n", "    copy = hero.querySelector('.hero__copy'),\n",
              "`.copy` -> `.hero__copy`: the copy column (800 wide at most, like the lab's), the vanishing point.")
    field.sub("  c.img.src = 'products/' + m[0] + '.webp';\n", "  c.img.src = productSrc(m[0]);\n",
              "`c.img.src = 'products/' + m[0] + '.webp'` -> `c.img.src = productSrc(m[0])` (edit 1): the photo URLs can\n"
              "be overridden per id for digested asset names; the only URL the module builds.")
    field.sub("addEventListener('resize', onResize);\n",
              "addEventListener('resize', onResize);\n"
              "// PORT (edit 7): the copy or the room can change size with no window resize (a late font swap re-wrapping\n"
              "// the sub-line, the room's width when a scrollbar comes or goes). Measure again then, at most once a frame.\n"
              "// A phone's snippet tab no longer does it: hero/hero.css holds the hero well at its tallest snippet, as the\n"
              "// lab's .hghost does. A window resize is onResize's own (above), and the observer's first report, the\n"
              "// sizes as they are, is only noted.\n"
              "if (window.ResizeObserver) (function () {\n"
              "  var seen = new Map(), vw = innerWidth, vh = innerHeight, rq = 0;\n"
              "  var ro = new ResizeObserver(function (es) {\n"
              "    var moved = false;\n"
              "    es.forEach(function (e) {\n"
              "      var b = e.borderBoxSize && e.borderBoxSize[0],\n"
              "          s = b ? b.inlineSize + 'x' + b.blockSize : e.contentRect.width + 'x' + e.contentRect.height;\n"
              "      if (seen.has(e.target) && seen.get(e.target) !== s) moved = true;\n"
              "      seen.set(e.target, s);\n"
              "    });\n"
              "    if (innerWidth !== vw || innerHeight !== vh) { vw = innerWidth; vh = innerHeight; return; }\n"
              "    if (moved && !rq) rq = requestAnimationFrame(function () { rq = 0; onResize(); });\n"
              "  });\n"
              "  ro.observe(copy);\n"
              "  ro.observe(room);\n"
              "})();\n",
              "inserted after `addEventListener('resize', onResize)`: a ResizeObserver on the copy column and the room\n"
              "that calls the module's own onResize() (at most once a frame, through requestAnimationFrame) when either\n"
              "changes size while the window does not; its first report, for each element, is only recorded. The lab\n"
              "only measured on resize, a device-ratio change and fonts.ready. A snippet tab on a phone used to be the\n"
              "main case; hero/hero.css now holds the hero well at its tallest snippet there (the lab's .hghost, with\n"
              "ghost texts in the markup), so the copy keeps its size and the observer stays quiet on a tab switch.")
    field.sub("    q = new URLSearchParams(location.search);\n",
              "    // PORT (edit 8): the lab's URL knobs only with ?lab in the query (?lab&hold=4, ?lab=1&gl=0): without it the\n"
              "    // field reads no query at all, so a visitor's ?t=<cache-buster> is not the lab's clock\n"
              "    q = new URLSearchParams(new URLSearchParams(location.search).has('lab') ? location.search : '');\n",
              "`q = new URLSearchParams(location.search)` -> the query only when it has a `lab`\n"
              "parameter, else an empty one: every knob (?hold= ?t= ?seed= ?gl=0 ?stream=0 ?stars=0 ?fit=0 ?hit=1 and the\n"
              "number knobs) reads q, so without ?lab the field runs as with no query. On the published page\n"
              "?t=<unix time> is a common cache-buster and was the lab's clock: the room jumped 600s ahead, the entrance\n"
              "never played and the boot ran as one ~400ms task. hero/intro.js's ?pt=0 and ?glow=blue are behind the\n"
              "same flag (its edits 7-8). window.__p3 stays.")
    field.sub("function makeGL() {\n  var cv = document.createElement('canvas'), r;\n",
              "function makeGL() {\n  var cv = document.createElement('canvas'), r;\n"
              "  // PORT (edit 9): three " + rev + " needs WebGL 2 and, where there is none, logs three console errors before it\n"
              "  // throws: ask a throwaway canvas first (none: the room's photo cards, as below), then let its context go\n"
              "  var pc = document.createElement('canvas').getContext('webgl2'), lc = pc && pc.getExtension('WEBGL_lose_context');\n"
              "  if (!pc) return null;\n"
              "  if (lc) lc.loseContext();\n",
              "inserted at the top of makeGL: a probe of a throwaway canvas for 'webgl2'.\n"
              "None: return null (the photo-card room, upstream's own no-WebGL path) before three is touched; else\n"
              "release the probe's context with WEBGL_lose_context. three " + rev + "'s WebGLRenderer needs WebGL 2;\n"
              "without it (WebGL off, no GPU, a WebGL 1-only browser) it logged 'A WebGL context could not be\n"
              "created' twice and 'Error creating WebGL context' once (console.error) before it threw into the catch.")
    field.sub("               boot: function () { return {ms: BOOTMS, soff: SOFF, rigs: RIGMS.slice()}; }};\nplay();\n",
              "               boot: function () { return {ms: BOOTMS, soff: SOFF, rigs: RIGMS.slice()}; }};\nplay();\n"
              "// PORT (edit 10): booted. The hero says so, and from here on hero/intro.js's listener (its edit 6) leaves the\n"
              "// field alone: it takes the static picture back only for a field that never got going.\n"
              "if (document.documentElement.classList.contains('hero-on')) hero.dataset.field = 'on';\n",
              "appended after the module's last statement: data-field=\"on\" on the hero\n"
              "once the field has booted (its rigs built, the room started), unless the page has already given up on\n"
              "it (no hero-on). hero/intro.js's error listener (its edit 6) stops at that mark; before it, an error\n"
              "from this file or from three.js brings the static picture back.")
    field.sub("    if (!BOOT) { sRaf = 0; return; }\n",
              "    // PORT (edit 11): the page gave up on the field (no hero-on, hero/intro.js's edit 6): this loop stops too\n"
              "    if (!BOOT || !document.documentElement.classList.contains('hero-on')) { sRaf = 0; return; }\n",
              "the stream's boot-time loop (sTick) also stops when <html> has lost hero-on: `if (!BOOT)` ->\n"
              "`if (!BOOT || !...classList.contains('hero-on'))`. It runs on its own requestAnimationFrame while the\n"
              "products are built and stops at BOOT = false; a throw at the module's top level after it started leaves\n"
              "BOOT true for good, and the loop drew the stream on, 60 frames a second (about 14ms of main thread a\n"
              "second, measured), behind the static picture that edit 6 had brought back. A field that throws inside a\n"
              "callback and boots on anyway is stopped by hero/hero.css instead (#fl display:none without hero-on, so\n"
              "its IntersectionObserver pauses it).")
    field_out = notes_block(
        field, 'hero/field.js -- GENERATED by tools/hero_port.py; do not edit (change the generator and rerun it).',
        ['Upstream: %s, %s/index.html @ %s (Kyu Kim)' % (UPSTREAM, LAB, commit),
         '  sha256 %s' % head_sha,
         '  this file = its <script type="module"> body, lines %d-%d, verbatim but for the edits below. ES module:'
         % (field_first, field_close),
         '  index.html loads it last in <body>: <script type="module" src="hero/field.js" data-hero-field async',
         '  fetchpriority="low"> (async: the page and its copy do not wait for it).',
         'Vendored beside it, byte for byte: vendor/three.module.min.js (three %s, MIT,' % rev,
         '  sha256 %s) and its licence, vendor/LICENSE.txt;' % sha(three_b),
         '  products/: the %d photos it can ask for (%s to %s); the sha256 of their `sha256sum` listing is'
         % (len(ids), ids[0], ids[-1]),
         '  %s.' % photos_sha,
         '  tools/hero_port.py pins the sha256 of every upstream file it reads or copies.',
         'Edits (upstream line: what and why):'],
        ['Verbatim otherwise: the knobs (behind ?lab, edit 8: ?hold= ?t= ?seed= ?gl=0 ?stream=0 ?stars=0 ?fit=0 ?hit=1 and',
         'the number knobs), window.__p3, every timing and model, the lanes, the reduced-motion still frame, the no-WebGL',
         'photo cards, the 900px phone switch and the IntersectionObserver pause.']) + field.text

    check_script('hero/intro.js', intro_out, 0)
    check_script('hero/field.js', field_out, 1)

    files = {
        'intro.js': intro_out.encode('utf-8'),
        'field.js': field_out.encode('utf-8'),
        'vendor/three.module.min.js': three_b,
        'vendor/LICENSE.txt': src['vendor/LICENSE'],
        'scrim.svg': src['option-3/scrim.svg'],
    }
    for i in ids:
        files['products/%s.webp' % i] = src['products/%s.webp' % i]
    files['MANIFEST.sha256'] = manifest(files, src, commit)
    return files


def manifest(files, src, commit):
    """hero/MANIFEST.sha256: a header, then `<sha256>  hero/<path>` for every other file the port writes, sorted (the
    format `shasum -a 256 -c` reads; it skips the # lines)"""
    pin = sha(''.join('%s  %s\n' % (sha(src[k]), k) for k in sorted(src)).encode('utf-8'))
    head = ['hero/MANIFEST.sha256 -- GENERATED by tools/hero_port.py; do not edit (change the generator and rerun it).',
            'Each file it writes under hero/ (all but the hand-ported hero.css), by sha256, for a consumer that takes',
            "them without the lab (the Rails landing's re-sync); `shasum -a 256 -c hero/MANIFEST.sha256`, from the",
            "repository's root, checks them. \"upstream\" names the lab and its commit, \"pin\" the upstream files the port",
            'read (PIN): how many, and the sha256 of their `<sha256>  <path>` listing.',
            'upstream: %s %s @ %s' % (UPSTREAM, LAB, commit),
            'pin: %d files, %s' % (len(src), pin)]
    return (''.join('# %s\n' % line for line in head) +
            ''.join('%s  hero/%s\n' % (sha(files[k]), k) for k in sorted(files))).encode('utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('upstream', type=Path, help='project/hero-stage/hero-lab of richardli-design/mock-shop-lp')
    ap.add_argument('--commit', help='the upstream commit, needed when any upstream file differs from the pinned one')
    ap.add_argument('--check', action='store_true', help='compare with hero/ instead of writing; exit 1 on a difference')
    a = ap.parse_args()
    lab = a.upstream.resolve()
    src, ids = read_sources(lab)
    got = {k: sha(v) for k, v in src.items()}
    changed = sorted(k for k in set(got) | set(PIN) if got.get(k) != PIN.get(k))
    if changed and not a.commit:
        die('%d upstream file(s) differ from the pinned %s:\n%s\nreview the change, then rerun with --commit <its commit>'
            % (len(changed), PIN_COMMIT, '\n'.join('  %s: %s, pinned %s' % (k, got.get(k, 'not read'),
                                                                          PIN.get(k, 'not pinned')) for k in changed)))
    commit = a.commit or PIN_COMMIT
    files = build(src, ids, commit)
    if changed:
        print('upstream at %s differs from the pin in %d file(s); once the port is reviewed, set PIN_COMMIT = %r and '
              'these PIN lines:' % (commit, len(changed), commit))
        for k in sorted(got):
            print("    '%s': '%s'," % (k, got[k]))

    present = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()) if OUT.is_dir() else []
    stale = [k for k in present if k not in files and k != HAND_PORTED]
    differ = [k for k, v in files.items() if not (OUT / k).is_file() or (OUT / k).read_bytes() != v]
    if a.check:
        for k in differ:
            print('differs: hero/' + k)
        for k in stale:
            print('not generated: hero/' + k)
        print('%d files, %d differ, %d stale' % (len(files), len(differ), len(stale)))
        sys.exit(1 if differ or stale else 0)
    for k in differ:
        (OUT / k).parent.mkdir(parents=True, exist_ok=True)
        (OUT / k).write_bytes(files[k])
    for k in stale:
        (OUT / k).unlink()
    for d in sorted({p for p in OUT.rglob('*') if p.is_dir()}, key=lambda p: -len(p.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    print('hero/: %d files (%d written, %d already identical), %d stale removed; upstream %s, %d photo ids %s..%s'
          % (len(files), len(differ), len(files) - len(differ), len(stale), commit, len(ids), ids[0], ids[-1]))


if __name__ == '__main__':
    main()
