#!/usr/bin/env python3
"""Regenerate Kyu Kim's animated Start / Build / Test flow from the designers' flow lab.

    python3 tools/flow_port.py UPSTREAM_FLOW_LAB [--commit SHA] [--check] [--print-markup] [--list-assets]

UPSTREAM_FLOW_LAB is project/flow-lab in a checkout of richardli-design/mock-shop-lp. The script only reads files
there; it never runs anything from that repository (not even git). Under this repository's flow/ it writes:

  flow.js     one classic script: flow-core.js, stages/start.js, stages/build.js, stages/test.js and flow.js,
              concatenated in section.html's load order (glass.js left out: no element uses it in R23), each part
              under a banner naming its upstream file; index.html loads it async, last in <body>
  flow.css    one stylesheet: flow.css, stages/start.css, stages/build.css and stages/test.css, concatenated
              (glass.css left out), then the port's --flow-css sentinel (C5); index.html links it in <body>, just
              before the flow's section
  head.js     the flow's <head> hook (html.flow-on, an error listener and a load backstop); not from upstream,
              written from this file
  assets/...  every file the stages can ask for (the 169 under assets/ named by the code, MP4 clips excluded), byte
              for byte
  assets.txt  the keys of those files, one per line, as --list-assets prints them
  markup.html the flow block index.html must carry, as --print-markup prints it
  MANIFEST.sha256
              the sha256 of each file above, with the upstream commit and pin they come from, for a consumer that
              takes them without the lab (the Rails landing's re-sync); `shasum -a 256 -c flow/MANIFEST.sha256` from
              the repository's root checks them

Files under flow/ that it does not generate are removed.

Each change to the upstream text is a literal substitution that must match exactly as often as stated (once, unless
the edit says otherwise) in the upstream text, so an upstream edit under one of them stops the script rather than
producing a silently different port. Each is listed, with its upstream file and line and its reason, in the PORT NOTES
comment at the top of the file it changes, and marked in the code with `PORT (<id>)`. The output depends only on the
upstream bytes (no dates, no machine paths): running the script again reproduces the same files byte for byte.
--check compares instead of writing and exits 1 if anything differs.

The outputs are then checked, outside the anchors too (check_js, check_css): no static import, import() or export; none
of fetch(, XMLHttpRequest, EventSource, WebSocket, Worker, serviceWorker, importScripts, createObjectURL, Blob, eval(,
Function, document.write, insertAdjacentHTML, .outerHTML, setAttribute('style', createElement('style'), toDataURL,
sendBeacon, localStorage, new Audio, string timers; in a string, no style=, inline on...= handler, javascript:, data:
or blob: URL, @import, srcset, literal src=/poster= URL, url() but a #fragment, and no <style>, <link>, <script>,
<iframe>, <frame>, <object>, <embed>, <audio>, <source>, <track>, <base>, <meta> or <form>; every src=" (or src=') a
string ends on followed by FLOW.asset(, every .src / .poster / .srcset assignment and setAttribute of one a
FLOW.asset() URL, every FLOW.asset() literal key a path under assets/, every FLOW.video() poster a FLOW.asset() URL;
location.search and document.currentScript read in flow-core.js's part only; .innerHTML only as often as upstream has
it; and the timers that repeat (setInterval, requestAnimationFrame, ctx.every, ctx.raf) only as often as LOOPS says,
each reviewed to stop at rest (B4, B9). The stylesheet has no url(, @import, @font-face, data:, http(s):// or .js
selector left. A hit stops the script with the file, line and text. Comments are skipped by a small JavaScript scanner
(scan_js, the one in tools/hero_port.py).

index.html is not written: it is checked (the head hook after hero/intro.js, the stylesheet (data-flow-css) and the
flow's own Google Fonts link before the section, section.html's three steps verbatim apart from the listed edits, the
script last in <body>, no other modulepreload than three.js's). --print-markup prints the expected flow block;
--list-assets prints the asset keys (the data-flow-assets map's, for the Rails page). flow/markup.html and
flow/assets.txt hold the same, so the Rails page takes them from this repository without the lab.

The upstream commit is pinned here as the sha256 of every upstream file the port reads or copies (PIN: the five
scripts, the four stylesheets, section.html and the 169 assets); nothing is read from the checkout's git. Every other
file under upstream's assets/ must be listed in DROPPED, so a new upstream asset stops the script too. If any file
differs, the script stops and lists them; review the change, rerun with --commit <sha> so the headers name the commit
the files came from, then update PIN_COMMIT and PIN (the run prints the new lines).
"""
import argparse
import hashlib
import re
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / 'flow'
INDEX = REPO / 'index.html'
UPSTREAM = 'richardli-design/mock-shop-lp'
LAB = 'project/flow-lab'
PIN_COMMIT = 'd931946'   # R23, kyu/flow-hero-latest (2026-10-09): Start, Build, Test; the Launch step removed
# sha256 of every upstream file the port reads or copies, at PIN_COMMIT (flow-lab-relative paths). The assets/ keys
# are the files flow/assets/ gets (COPY below).
PIN = {
    'flow-core.js': '16f4cc587eadf86054592994fa6d9c7b3bbf73486073688becce699dfc896fac',
    'stages/start.js': 'ddcc4b51e8c16503586fab09533900ecff7012463e73377c40958bda68c60e87',
    'stages/build.js': '8a2a974a097e7ca596720670cee878245033e2f11a46a7ecb62f4d6835fea9b4',
    'stages/test.js': '1dfa92b74aef2ee357ec3f41d630009ec9f968b04fd105126f1dbf52c99a4c31',
    'flow.js': '3af7a7810117079d183be0bd082a01b90876aa59e2e020822e4a33cce8a92c4c',
    'flow.css': '47f611ca0e3028c43391af6fe859722399ce7c53507914cb0e9b6b7c879a24fa',
    'stages/start.css': 'e94dd366c884120d917d41a7828f2c1b8fe598fb3cd04ad5889ad657d7790dfe',
    'stages/build.css': '72d6eaa42315acd789ae95a9118c68bf57ae8b50544726c8842bc97980b380fa',
    'stages/test.css': '44b57fe0550262a376208bee7bee1ad9ad9fd08448e5f46ef8c09516d14194a1',
    'section.html': '42851bba6c8a103ddec63dba12f3af996f404bb0e9341bb7ac4ab3429398c845',
    'assets/build/bold-cart.svg': '608edbb724ca3082e2c6db475595a30f22d6e9911da095ded6082aec1dc7ed2f',
    'assets/build/bold-chevron.svg': 'a7bfd017065972ee6bc4b01eaa27faad3ee8348406803916c8caf27e8787f5a9',
    'assets/build/bold-minus.svg': 'd450e24b13e34891de8571f716c1b8a72b2433038ee2b15d25efd978936b84da',
    'assets/build/bold-next.svg': '320e3b00ec7afed876803a23173e192ba985efd850c62f9ad0f2b4b3357a6755',
    'assets/build/bold-plus.svg': '9390adb9ccb227dbd035d0aa9a7a44cb50bdf66cd64d9c398baf8dd991925e52',
    'assets/build/bold-prev.svg': '1d590e81ce1730a742b954cb7366e214607cb606941e28416214ee755793105c',
    'assets/build/bold-search.svg': 'be57c349930911753246973ca36a477871c3cb61417a27148c6fe8b097b959bd',
    'assets/build/elegant-cart.svg': '85d68e1e50fb7f293e2d4d9c6d2200ce7bdb39e844f201acd83d44adb0410eed',
    'assets/build/elegant-chevron.svg': '7d8856f40f7a664dcc951e13dbb31d01a9ae3ecb303bcb0d84e49b9f9b5bb638',
    'assets/build/elegant-minus.svg': '30535c7d83cac1dc798eaa86f1ff58696e05fb50a4b991a48a02cd0bb4689835',
    'assets/build/elegant-plus.svg': '70edd4e4f8bde9fe518970719dd19588080eabe89bdc3a1d5d340744f5bca08c',
    'assets/build/elegant-search.svg': '9ac8e7c35897e66c73d59ac0af8e5cf2c60e96c1f57855e9e0c596f7ad822ec4',
    'assets/build/technical-cart.svg': '3c567deb5ee44de3468247018f8b0f6aaa08b0f8bc7a268eff3265061bce3397',
    'assets/build/technical-chevron.svg': '221ff5eb85bba6b7c638c79abf183f8f0c8c872eb3288622751f3506cd0cc1ed',
    'assets/build/technical-minus.svg': '61fb3f9a6fa12f65bea6f81252b2ce2d9387fde2c50c706fe985ae2969e80eda',
    'assets/build/technical-plus.svg': '071e21bf895bab4a2b59ff726d67e98a98ac012a3b509ba09feb9688730bf884',
    'assets/build/technical-search.svg': 'f70e409bc8fda94491b3fd9ef78c043feb3cda1d5f2d4ea0e614aad0b61d3e74',
    'assets/build/tee-back.webp': '6a878626467ff2c9293832bc57f4a2118dea59657620f099efd24ee71421a1f7',
    'assets/build/tee-front.webp': 'e4b9b033c8bb62de07d2e049f6c40009111024c2259d5b7127e2c29fc400e475',
    'assets/build/tee-in-use.webp': 'abf169f679d4d273bf8d479adeef57abd1a3813e7674b4ba80bae4236b9901ac',
    'assets/build/vibrant-cart.svg': 'b6228d458607a9e035fec1eeb5ce372c1f040754e4d2c125c05795b064e1daea',
    'assets/build/vibrant-chevron.svg': '5da5da79052a001d2618bc183a875307b06d1edaf07673065917335bb6585931',
    'assets/build/vibrant-minus.svg': '8c772e7004e4803f3f8898364c44d618fe39c805e07c7f007f37f42c80642af6',
    'assets/build/vibrant-next.svg': 'b61825ee01a8b9b7126939e4be2ff398fa243161bac82c0c369f8ea1adc3f08c',
    'assets/build/vibrant-plus.svg': 'ce0cd3043e539a09ef9cc050ddb0c6d3ebde0f9758218f0ab7b9af862f19aabc',
    'assets/build/vibrant-search.svg': 'ef7cba1c6c302edcbf3c54c02d03b66af4f629f658a2125dc7bf7aa2a8e658d4',
    'assets/shell/copy-vector-teal.svg': '7b9c76ec47d9c43ece4534bc7bf13fba186be248c3ce008865c513d38afd235d',
    'assets/shell/dot-teal.svg': '4783a0e1fc18506360fa734ae3a652d0cceb305bb2d115b3c3ec3a336167fc79',
    'assets/shell/send-image.svg': 'cfff6036572ea65060ed4b24afc5aab8a7c3b7b92fb22297e484b1bcfd03efea',
    'assets/start/cleanser-dark.webp': 'eefc4fcd4cb613e18971621145235c425a9394d2a50fe41efa87c40e73b5c253',
    'assets/start/cleanser-front.webp': 'edffbdb2c733760d78c0bcbd3c371688401ab43a3d0f1b8b5b809c87716ccf1f',
    'assets/start/cushion-front.webp': '0fc1a74084b36a920247800e338a2e181f9afec89219204e3771de7bf38c4826',
    'assets/start/cushion-lifestyle.webp': '1a49dc80f586b0b77f660f41ad98c81b7096934071ef35d97d92101dafa9bf1b',
    'assets/start/cushion-side.webp': '8a8e761eff65f89a50763f2f07b5652807c1f5492b814e68655f8b2a71d008da',
    'assets/start/jacket-back.webp': '236e424e9015ccd5f1b27a953d381eee98d057f34b1b2685ebce4e2ce58b2fd3',
    'assets/start/jacket-front.webp': 'f498e91eed822ebd63ffcf4dc6203760fcfd660497fc50b743fb523e8545edef',
    'assets/start/jacket-lifestyle.webp': 'c82c8a38f00a7017b7cb2d364a3d1ee2fa1e002fffe0a4fe620ab9bba95c112c',
    'assets/start/pdp-beauty-cart.svg': '290f886469a2204f987cfc03064c13d5ce582f5c95c8a467fe518d65e88572d3',
    'assets/start/pdp-beauty-chevron.svg': '75ee65eb3721fccb96fc922c3ba777e3f377fed8048f386562a3b1d0b6bc4f0b',
    'assets/start/pdp-beauty-minus.svg': '6f7983079fad5eb77b9ea85b17a73161f425b4828e05a16e5e405dd2fdfea48d',
    'assets/start/pdp-beauty-plus.svg': '18e13f8b548525d848dbec8831f0832dab130ce2f47570a044d3d4324170268c',
    'assets/start/pdp-beauty-search.svg': 'bd89521f10de7258574d868f7e288daf2f7117f1b60778c2a2d77057c7449232',
    'assets/start/pdp-decor-cart.svg': 'd811dfce737f078eab0b10e9b4fc6f015c139f496ae78135d2984bd4c483c366',
    'assets/start/pdp-decor-chevron.svg': '75ee65eb3721fccb96fc922c3ba777e3f377fed8048f386562a3b1d0b6bc4f0b',
    'assets/start/pdp-decor-minus.svg': '6f7983079fad5eb77b9ea85b17a73161f425b4828e05a16e5e405dd2fdfea48d',
    'assets/start/pdp-decor-plus.svg': '18e13f8b548525d848dbec8831f0832dab130ce2f47570a044d3d4324170268c',
    'assets/start/pdp-decor-search.svg': 'e07c16de9dd1843ec9a2134d8f3b2729ab7815aa1988039287ddac22c20f9c49',
    'assets/start/pdp-sports-cart.svg': '7c7f186fe6b8d72d84c50f5758dd923b7b3bbe1893ed8c34f49191b2673ef696',
    'assets/start/pdp-sports-chevron.svg': '75ee65eb3721fccb96fc922c3ba777e3f377fed8048f386562a3b1d0b6bc4f0b',
    'assets/start/pdp-sports-minus.svg': '6f7983079fad5eb77b9ea85b17a73161f425b4828e05a16e5e405dd2fdfea48d',
    'assets/start/pdp-sports-plus.svg': '18e13f8b548525d848dbec8831f0832dab130ce2f47570a044d3d4324170268c',
    'assets/start/pdp-sports-search.svg': '42c563276c09f107a0766929104baed0d44d81b0488b9600cdefa1f101dd73ce',
    'assets/start/pdp-streetwear-cart.svg': '4a25e4158504f913428fe4d26543e59a13f5dee00d2d579161a249be32e8f835',
    'assets/start/pdp-streetwear-chevron.svg': '75ee65eb3721fccb96fc922c3ba777e3f377fed8048f386562a3b1d0b6bc4f0b',
    'assets/start/pdp-streetwear-minus.svg': '6f7983079fad5eb77b9ea85b17a73161f425b4828e05a16e5e405dd2fdfea48d',
    'assets/start/pdp-streetwear-plus.svg': '18e13f8b548525d848dbec8831f0832dab130ce2f47570a044d3d4324170268c',
    'assets/start/pdp-streetwear-search.svg': 'f6613b856d0a11187f33a2f331d63bb9f58f990f205b3c7575e436061e6bb39e',
    'assets/start/tee-back.webp': '77abb31abe46cb6293bffe1641336d2614ad39bfdf787c3949c0f0a519815631',
    'assets/start/tee-front.webp': 'e85734d809b1a68e915119df32bfaacea5dbe72e58a2249483c14449a13c273e',
    'assets/start/tee-lifestyle.webp': '61a935113444e145125d650814f296313c494378de4086dee2da518a62a5beb3',
    'assets/start/thumb-bd-1.webp': 'f12afb7c4155c11b3fb6fc13c852ca1ba4385f265eec88202603c30cc0ba19ba',
    'assets/start/thumb-bd-2.webp': 'a0c2eaa8bcefd72ff694530c2c7854778d960115a9f382c9e3866cfa79a49828',
    'assets/start/thumb-bd-3.webp': '842b53183b0dbb79f5acda0cfb831ddc4503c424c608a822774358453a67da1a',
    'assets/start/thumb-bd-4.webp': 'c47042edceb5bf79fa680805c90df20987ed44969779a9af31b5f7c12ff4510e',
    'assets/start/thumb-bd-5.webp': 'db4860d371551cddaeb23b71c371cb5138b72a63c3ccba99dcc6c1cb8f43d287',
    'assets/start/thumb-bd-6.webp': '60f8c69aa8dba52b4a4fd99514ba6817b892923a5627905a70671d252718e673',
    'assets/start/thumb-bd-7.webp': '8a6cddae0836055cf1e521cd7d940cf35d46cb3b8b53ba896073d6990d537fc5',
    'assets/start/thumb-bd-8.webp': '619cb7a415fab916655dabbceb09cf02eeaea68a211648f5782cf0b149aa436e',
    'assets/start/thumb-ch-1.webp': 'f4c54a266e22987d71ec7c05b96aaefdb6c098a9528b795ca43b6a93739320e8',
    'assets/start/thumb-ch-2.webp': '49ebedd747b91f88f19c1c033ced9c0c2bf310268294471d4a285c2bf97fef4b',
    'assets/start/thumb-ch-3.webp': '24bc76889e1948d5bb25a60256bb6c3e5e34efe66f922aeb451159ac02b9b94c',
    'assets/start/thumb-ch-4.webp': 'ce2f4e0243caa324d498014f64d852ad3e3ec49857aa367e34dbd9211be39c88',
    'assets/start/thumb-ch-5.webp': '8f2c456a3893fcba99c61cce8c701ae887ed1198676968b1eba552eed3a2ef79',
    'assets/start/thumb-ch-6.webp': '9f89f86b7aaea9e0e8654a246c4f902b308e987d4859b22dcd14c03204d3088d',
    'assets/start/thumb-ch-7.webp': 'f11772ea1f1e911fdb1584d35b9d7f23247fe6d1aba18d9b273ed99452b53c06',
    'assets/start/thumb-ch-8.webp': '4377db7c8f2063fd594e99b8ed395b5061600f85f3d43539ce891496b210f807',
    'assets/start/thumb-ee-1.webp': '060584b0d5998a125a188c130aeab01a4463078febf2d950df15f7b08c628c91',
    'assets/start/thumb-ee-2.webp': 'f0daf98c370c93a9ad5f407b124c2e02a6513d2259069e5058714c6c5e9f9c69',
    'assets/start/thumb-ee-3.webp': '03430be206ba24ac7ae8ed57702e1f243e1e2b461e9b7d08c7cfe47acfe59b50',
    'assets/start/thumb-ee-4.webp': '35d442e11b07be1d4fac418b93e0c688c1520f096faa937845d1b52406cf6170',
    'assets/start/thumb-ee-5.webp': 'b277c1a409abd42ea28fa8165965cb36a823c7e2ac700048c87352f1618674d5',
    'assets/start/thumb-ee-6.webp': 'fbb4c276800bb509a15e3f924503d44ba90fca214781283dce9fba26fdfb5e14',
    'assets/start/thumb-ee-7.webp': '5505eeadda22f1e154e49ceec899b8c49aa55caae7d7c4c45a59e627244b87e3',
    'assets/start/thumb-ee-8.webp': 'edd1273e30945a17b1b95ece7d9df6951f5699df74d5a9e3ca145d1785196331',
    'assets/start/thumb-hn-1.webp': 'cf1eae503a9e4cf78b9adfb5f4174eb683e4b7741d9cf052ff989fc3e278861a',
    'assets/start/thumb-hn-2.webp': 'acaf375fa2a8901900a6fe8a5ca9004ff4c4c886e3927fe544cd6900d2e2d063',
    'assets/start/thumb-hn-3.webp': '9002c26b88ddd4ebcf21d0bd1b26b1797df6fe63bff60f6d01a1ce052987d590',
    'assets/start/thumb-hn-4.webp': '36c99d315628b5ba657a9c4aaf9c3a581e0c42e6b5821e96c1448ebd6389aac0',
    'assets/start/thumb-hn-5.webp': 'd067fdbe8d8d2679d1873c780ceee636df367b3c94840e53adb5752b18e7ada6',
    'assets/start/thumb-hn-6.webp': '0b49354bace530b3c4be44d8c061946911e809fea6b353f69fb1b0726a9314ef',
    'assets/start/thumb-hn-7.webp': '31a8be0c95b1db4f4cf1d837b485e79b590b5ef6eb1785256c8a36336ba1967c',
    'assets/start/thumb-hn-8.webp': '514c2f1e4d8524e5d851375b9051d2226ec31ecc5a658ef2c69d7be65bec98bc',
    'assets/start/thumb-lg-1.webp': '0eded089fc84b3dc14cc24ee3e5da20dc8f6ad4dbd8b6c7f53f6de62ebd2b611',
    'assets/start/thumb-lg-2.webp': '74f969cfb1adfa17906f3e50426c1b264e4a7d567da8a5d5d8343bd25a02cc82',
    'assets/start/thumb-lg-3.webp': '24f34a8d1df6dfa3d3e04a22bf3ea8134e16f5df6fc3d63a168d24cdb7e9cec1',
    'assets/start/thumb-lg-4.webp': 'df19fbad0923f856f4805cca86e4adb8397e5515182b6fea78820673e7338c86',
    'assets/start/thumb-lg-5.webp': '9f208fe533eb6528fde9c728172c0ef952ad274fb815c3e8c1bd3fc0bb3f9f0b',
    'assets/start/thumb-lg-6.webp': '9dd579a963ad004950503451bc613fa50250bc895b47782cc8d16fcc61a4051d',
    'assets/start/thumb-lg-7.webp': 'd56994470a668815098ce041fdc7061926d6316d4b1009a3722770bacd0040eb',
    'assets/start/thumb-lg-8.webp': '98db885edd567dc8bcd4f4b97c524cc3d30b464bea9410088ca5692cd7217aa7',
    'assets/start/thumb-sg-1.webp': '3c0f0292f734ea2b5cfdf7e2353102d30b1b8d525b35a894dde0a0e4ce43194e',
    'assets/start/thumb-sg-2.webp': '1b530b06ccee3b966070cf2af98055aef0686c85742b67e5f9f8929e4a45dd8b',
    'assets/start/thumb-sg-3.webp': 'c9f515a302dfc77ba8779d312c73939a5f83a3a52219327adccd69f24c5d3755',
    'assets/start/thumb-sg-4.webp': '3954c003a65d04937f73b902b2d2309ab3b97e52ec69ee1af13b5fffce5fb9e6',
    'assets/start/thumb-sg-5.webp': '50dd456adc6afa30aa9b495bcd2e4d396cd975a362804414ac56ae867cb1040b',
    'assets/start/thumb-sg-6.webp': '9377a08e782101b3ca68ef81548974279e1ea925d306ad4354e70b60c470b91b',
    'assets/start/thumb-sg-7.webp': 'ca382a862dfd6ace60e8ff23854418f88ddceee545af94aa37fe1e86491fcf13',
    'assets/start/thumb-sg-8.webp': 'd1f89875d37bdd275ca037e6560300a4cf6c06b0cfeeb929758a0fa60a7b359f',
    'assets/start/thumb-up-1.webp': '337adbab4cf6f2cdc13f5686f834c4f0cf8496c5d8519fea32e2662f84c7c951',
    'assets/start/thumb-up-2.webp': '2d259ec75e2a42ddb7d7858ab0d5448d3646482cf812adfd1860cee0d01612ba',
    'assets/start/thumb-up-3.webp': '0131306eb7b6b0d5c0da39391b6c41987f51a7ed44405647fba8191c410f1605',
    'assets/start/thumb-up-4.webp': '32d4ea8781dd4c5cba81ac43633c5b4dc6ec4b654268ced156a583fc58c9b8e1',
    'assets/start/thumb-up-5.webp': '4b12b30761bb378882d6d3969f9c4b3ba837e98ba95e69fb39a88e4ae5e98bec',
    'assets/start/thumb-up-6.webp': '6e6183dc786f697cf33d54dd7e2a8b3c5b5a05ba7d9e76524aa16b9bc99df008',
    'assets/start/thumb-up-7.webp': '9a853452a2465b8fcdffd05c0000b9d6344c900944bcb457d0735b15c586e502',
    'assets/start/thumb-up-8.webp': '9d32f8a4f5127ba275eba9d3b7d8333685c2b4ff7fa0e5b5405639e762c40982',
    'assets/start/thumb-va-1.webp': 'c5d1ad8b28a685746c7157a8bdce7af6dba66722da48f7756b236ab0edeab2ab',
    'assets/start/thumb-va-2.webp': '9cad1dfe44722431dc7f7dc8cce202f39d7ca199c53fa513ee514e6b298bf086',
    'assets/start/thumb-va-3.webp': 'a163bfb2354854463206febc1b17508a1385aef2338f675b553675b78126f806',
    'assets/start/thumb-va-4.webp': 'e8f8d489ad82114db73e8b0674c6dfb20566de1e2f43a7e0cc8dd3958d5e2370',
    'assets/start/thumb-va-5.webp': '909b4a8254415a4c7277df57185d467195aff92d49f0ccbe65da1ebf7ba9f41e',
    'assets/start/thumb-va-6.webp': '15a3d1c1c6b66f5d7fc0a13b5856bcb7595a55b6ba549f0a7415fed0bb3106d0',
    'assets/start/thumb-va-7.webp': '1fc50d77855b419906b267c026ec6c2cb33e165685feb92f02ecbe33b9c7a7e9',
    'assets/start/thumb-va-8.webp': 'da265b6b0bd9da35f30346347e26420a3781759564e5bc06e568a0a52385f2b0',
    'assets/start/thumb-vp-1.webp': '40c969ac4ad22d4536d2321eae6fd4e7ca9825f7380687bb48fc305e27f4a84d',
    'assets/start/thumb-vp-2.webp': '28e37ec4b476caff5d8e88083a0c7a775d728e9d39d6a972f8d404df80ee01f7',
    'assets/start/thumb-vp-3.webp': '9d205e8f582863aba450127e5db64b79e2435d0041668f3397c4735491804b56',
    'assets/start/thumb-vp-4.webp': '90aaf776473887447fa560a408ca5a79964c143ea2ddf9ce0d301956393dbbac',
    'assets/start/thumb-vp-5.webp': '410a30b683eaf1754e29d5a71be285fd374261bacc39aa81b7983b4d32bce71e',
    'assets/start/thumb-vp-6.webp': '7ca2a1999f232ffbf71b9096aab530ca575764bce4965225cd3f1f8eb12b71ca',
    'assets/start/thumb-vp-7.webp': '7d9bd9c8e073715641a2608064bea2f274bb064fa9b43c9d3fa9278ace8d2173',
    'assets/start/thumb-vp-8.webp': '1910a138bb9f5e3b84d23dda6a4584561c2742f4d19b8fc73b6ec6c4eccdb484',
    'assets/start/thumb-vt-1.webp': '4e5cc54e2639198009f98d55bd69276538c5233ac545163e696653c29a802209',
    'assets/start/thumb-vt-2.webp': '9663a60007b3f360dd8539982ca87d3e9db5b1c580b1b66dcce2631dafc14263',
    'assets/start/thumb-vt-3.webp': '70442eea9d845032e363c69fe99421b85a67ed0e0d199d4dcdee697f799e78a2',
    'assets/start/thumb-vt-4.webp': 'dc2da04bd3d74fa0f109a23a42baf9560b8a9b37019fae6884eccbdc9b577116',
    'assets/start/thumb-vt-5.webp': '6c33a298510ee5f70340aeb72e7622d5e59f059cd8760d3d261294b255251649',
    'assets/start/thumb-vt-6.webp': '7211eb8089cbc40ed898695dfbf9a09855260d3bf71eadbc66c508221f717970',
    'assets/start/thumb-vt-7.webp': 'b50b37a0b9574c958a803cbd1da0efbe7da3f21967d333061d4f1bb7ec5fd623',
    'assets/start/thumb-vt-8.webp': 'f5737d4d04a56f7f0485ba9425506f80be4533494d6f15c889df0550ce73e2f4',
    'assets/start/thumb-vv-1.webp': 'dce8e61f14a6bc814c7d4b57d7cd513abeb6f39811197c4d17eaf7ad8c378c4e',
    'assets/start/thumb-vv-2.webp': 'b2e86fb4d92fc7478843c3526e145ddd37b7f8870484dba6f09f0acd3a343e91',
    'assets/start/thumb-vv-3.webp': '2b40b06465acb3426942f34cc4f207b91cef2ce5781a5ed2f52aa8340428eb48',
    'assets/start/thumb-vv-4.webp': '47f8061f68179205be4d5897e3e2ad80c79a1f0694a54e4f79b9f7194938329e',
    'assets/start/thumb-vv-5.webp': 'faa955585b3c4a5d1819a5668fd60fc8d95bb4416639ce451ca4c301f962ea3f',
    'assets/start/thumb-vv-6.webp': '14ad59a1c40d59f7be780f313f44a6f1b4972d8989fc58f20a99e7a065991c60',
    'assets/start/thumb-vv-7.webp': '8a157e71e16544944d7ebdc6b8c5d53a9d026e67cef4b94594defc6474c0520f',
    'assets/start/thumb-vv-8.webp': 'f9d57a451ca20ada2ac32bcf3c4cd256038f5b621f43e916fa9adb29e7b43f83',
    'assets/start/thumb-zm-1.webp': 'b5d2b538471e5f97993d5d84da8aeaa32f73514489c040019aa72906c8e721b2',
    'assets/start/thumb-zm-2.webp': '1d88c44d0f77a7dadaeae39038bad4c7b65baf0dd7397a8f0feb4d7143fae7c7',
    'assets/start/thumb-zm-3.webp': '9e58c2b5498da7d25d145b8a0a81bccae5453464509e713c0cbc8adfc4fe80ae',
    'assets/start/thumb-zm-4.webp': 'b881ffd708c2f4ab531d99b9fca55cca44b71b4cf8c428292a69fd001ffb51c0',
    'assets/start/thumb-zm-5.webp': 'b9d047bee5025f238231e6ad4ae8bfbe85eb17005305b428315d713ac232a740',
    'assets/start/thumb-zm-6.webp': '718ae26fb5d69fbf6b9826ffc2c0fb2cf46cfe70dc645d3a420c3b98d4f7d283',
    'assets/start/thumb-zm-7.webp': '13db4f6b0c4f3e02944b49c45f8baa94c9104e62df0fc43b6b5f7d48a463fdc6',
    'assets/start/thumb-zm-8.webp': '54781e5454a9b99d07c7781b5a043ab7c26b8aa69d68899b76ab96fbacd61c95',
    'assets/test/drawer-icon-minus.svg': '6983a522e32f4b61aafc91552a6da313e7c36f957621ebdb020f862bacbca10a',
    'assets/test/drawer-icon-plus.svg': '9861510624be25eb0861d6ffe19176780044bb4108a3fbb3628895822fafed28',
    'assets/test/drawer-icon-trash.svg': 'f703791c1f04d7afe814c363c1c598061ce316538d7d4cf8e366df12f2efcaec',
    'assets/test/drawer-icon-x.svg': 'd3c61f88f07761f595ec1d6485498282a2437aeaa5e32367fbb60392f945d92c',
    'assets/test/pdp-icon-cart.svg': '3c567deb5ee44de3468247018f8b0f6aaa08b0f8bc7a268eff3265061bce3397',
    'assets/test/pdp-icon-chevron-down.svg': '221ff5eb85bba6b7c638c79abf183f8f0c8c872eb3288622751f3506cd0cc1ed',
    'assets/test/pdp-icon-minus.svg': '61fb3f9a6fa12f65bea6f81252b2ce2d9387fde2c50c706fe985ae2969e80eda',
    'assets/test/pdp-icon-plus.svg': '071e21bf895bab4a2b59ff726d67e98a98ac012a3b509ba09feb9688730bf884',
    'assets/test/pdp-icon-search.svg': 'f70e409bc8fda94491b3fd9ef78c043feb3cda1d5f2d4ea0e614aad0b61d3e74',
    'assets/test/tee-front.webp': '0b6bb191ef0a0c5cc469731b424c3361c7dc6a93c1c8ca1e5dd9624b290227c1',
    'assets/video/tee-back-poster.webp': '4da0fe2e782f113eef71b1f0e82135994f88dfb552c806e525e64e804506d8b8',
    'assets/video/tee-front-poster.webp': 'ce53679a8eda5926551b54af551319345de1633eb583550700e61b7675fb03ab',
    'assets/video/tee-in-use-poster.webp': 'aebf9de70d8013fb70911e3ef3ca053d1d27beb2fea67d8381edc36e077cf1cd',
}
JS_PARTS = ['flow-core.js', 'stages/start.js', 'stages/build.js', 'stages/test.js', 'flow.js']   # section.html:123-128
CSS_PARTS = ['flow.css', 'stages/start.css', 'stages/build.css', 'stages/test.css']             # section.html:11-14
FIXED = JS_PARTS + CSS_PARTS + ['section.html']
COPY = sorted(k for k in PIN if k.startswith('assets/'))
# every other file under upstream's assets/, and why the port leaves it out
DROPPED = {}
for _why, _names in [
        ("the product clips: off by default in R23 and off for good here (flow-core.js's F4); the posters are the "
         "stills", ['video/tee-back.mp4', 'video/tee-front.mp4', 'video/tee-in-use.mp4']),
        ("Launch's film (launch.js, gone in R23)", ['video/hero-wall-jacket.mp4', 'video/hero-wall-jacket-poster.webp']),
        ("the browser chrome, gone since R11", ['build/chrome-back.svg', 'build/chrome-fwd.svg', 'build/chrome-lock.svg',
                                                'start/chrome-back.svg', 'start/chrome-forward.svg', 'start/chrome-lock.svg',
                                                'test/chrome-back.svg', 'test/chrome-forward.svg', 'test/chrome-lock.svg']),
        ("Test's earlier checkout and thank-you art, replaced by R22's", [
            'test/co-bag.svg', 'test/co-checkmark.svg', 'test/co-chevron-down.svg', 'test/co-gpay-logo.svg',
            'test/co-lock.svg', 'test/co-magnify.svg', 'test/co-pay-amex.svg', 'test/co-pay-mastercard.svg',
            'test/co-pay-visa.svg', 'test/co-paypal-logo.svg', 'test/co-paypal-wallet.svg', 'test/co-question-summary.svg',
            'test/co-question.svg', 'test/co-shop-logo.svg', 'test/ty-check-circle.svg', 'test/ty-icon-x.svg',
            'test/ty-map-ottawa.webp', 'test/ty-pay-visa.svg', 'test/ty-pin.svg', 'test/ty-tooltip.svg',
            'test/ty-zoom-controls.svg']),
        ("named by no code (Test shows these photos as the clips' posters; the shell's non-teal glyphs)", [
            'test/tee-back.webp', 'test/tee-in-use.webp', 'shell/copy-vector.svg', 'shell/dot.svg'])]:
    for _n in _names:
        DROPPED['assets/' + _n] = _why
# .innerHTML in each script, as upstream has it (constant templates or esc()-escaped data; the landing's CSP has no
# Trusted Types): a new one stops the script, to be reviewed
INNERHTML = {'flow-core.js': 0, 'stages/start.js': 2, 'stages/build.js': 7, 'stages/test.js': 1, 'flow.js': 3}
# the timers that repeat (setInterval, requestAnimationFrame, ctx.every, ctx.raf) in each script, each reviewed to stop
# at rest: flow-core.js's are ctx.every's and ctx.raf's own; build.js's are the clip watcher's ctx.raf (off: B4),
# drive()'s (it ends with its switch's clock) and the idle tick's ctx.every (on screen only: B9); test.js's is the
# cursor's (it ends when the hand lands). A new one stops the script, to be reviewed (does it run forever once its
# step has played?)
LOOPS = {'flow-core.js': 3, 'stages/start.js': 0, 'stages/build.js': 3, 'stages/test.js': 1, 'flow.js': 0}
# the flow's own Google Fonts families (index.html's first link, kept as it is, has Inter and JetBrains Mono 400/500):
# section.html:10's list less Inter (the same file as the page's) and Permanent Marker (no code uses it), JetBrains
# Mono only 700 and 800
FONTS_HREF = ('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500&family=Anton&family=Archivo+Black'
              '&family=Archivo:wght@400;500;600;700&family=Instrument+Sans:wght@500;600&family=Instrument+Serif:ital@0;1'
              '&family=JetBrains+Mono:wght@700;800&family=Newsreader:wght@400&family=Space+Grotesk:wght@400;500;700'
              '&display=swap')
SECTION_OPEN = '<section class="features flow" aria-label="How mock.shop works">'


def die(msg):
    sys.exit('flow_port.py: ' + msg)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def L(*lines):
    """lines joined, each ending in a newline"""
    return ''.join(x + '\n' for x in lines)


class Port:
    """Upstream text plus the asserted substitutions made to it, with their upstream lines for the notes."""

    def __init__(self, name, text):
        self.name, self.orig, self.text, self.notes = name, text, text, {}

    def sub(self, eid, old, new, note=None, count=1, lines=True):
        """Replace old (exactly `count` times upstream and in the port so far) by new. Edits sharing an id share one
        PORT NOTES entry (the note given with the first), listing every upstream line they touch (but those of a
        comment-only insertion, lines=False)."""
        for label, t in (('upstream', self.orig), ('the port so far', self.text)):
            if t.count(old) != count:
                die('%s, edit %s: %d matches (want %d) in %s for:\n%s' % (self.name, eid, t.count(old), count, label, old))
        k, where = 0, []
        for _ in range(count):
            k = self.orig.index(old, k)
            at = 1 + self.orig[:k].count('\n')
            end = at + old.rstrip('\n').count('\n')
            where.append('L%d' % at if end == at else 'L%d-%d' % (at, end))
            k += len(old)
        self.text = self.text.replace(old, new)
        e = self.notes.setdefault(eid, {'where': [], 'note': None})
        if lines:
            e['where'] += where
        if note:
            if e['note']:
                die('%s: two notes for edit %s' % (self.name, eid))
            e['note'] = note

    def entries(self):
        out = []
        for eid, e in self.notes.items():
            if not e['note']:
                die('%s: edit %s has no note' % (self.name, eid))
            out.append((eid, ', '.join(e['where']), e['note']))
        return out


WIDTH = 116   # PORT NOTES text width (the comment indents it by 3)


def wrap(text, first='', rest=''):
    """text as one paragraph, wrapped at WIDTH after `first` (then `rest`), never inside a word"""
    return textwrap.wrap(' '.join(text.split()), WIDTH, initial_indent=first, subsequent_indent=rest,
                         break_long_words=False, break_on_hyphens=False)


def comment_block(title, lead, entries, tail):
    """The PORT NOTES comment: the lead, then `<id>. <lines>: <note>` entries under their file, then the tail. Lead
    and tail items are paragraphs (wrapped), except those starting with two spaces (kept as they are)."""
    def paras(items):
        out = []
        for x in items:
            out += [x] if x.startswith('  ') else wrap(x)
        return out
    out = [title, '', 'PORT NOTES'] + paras(lead) + ['']
    for head, items in entries:
        if head:
            out.append(head)
        for eid, where, note in items:
            out += wrap(note, '%s. %s: ' % (eid, where), ' ' * (len(eid) + 2))
        out.append('')
    out += paras(tail)
    while out[-1] == '':
        out.pop()
    text = '\n'.join(('   ' + l if l else '').rstrip() if n else l for n, l in enumerate(out))
    if '*/' in text:
        die('a PORT NOTES line would close the comment early')
    return '/* ' + text + ' */\n'


# ---- what the outputs may contain --------------------------------------------------------------------------------
BEFORE_REGEX = {'return', 'typeof', 'instanceof', 'in', 'of', 'new', 'delete', 'void', 'throw', 'case', 'do',
                'else', 'yield', 'await'}


def scan_js(text, name):
    """(code, strings) for a script: the text with every comment blanked to spaces (newlines kept, so a line of code
    is the same line of the file), and (line, text) for every string and template literal. A small scanner: comments,
    '...' and "..." strings, `...` templates (and the code in their ${...}), and regex literals, told from a division
    by the token before them. (tools/hero_port.py's scan_js, verbatim.)"""
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


# (pattern on code with its comments blanked, what it is): in no output script
SINKS = [(r'\bfetch\s*\(', 'fetch('), (r'\bXMLHttpRequest\b', 'XMLHttpRequest'),
         (r'\bEventSource\b', 'an EventSource'), (r'\bWebSocket\b', 'a WebSocket'),
         (r'\b(Shared)?Worker\b', 'a Worker'), (r'\bserviceWorker\b', 'a service worker'),
         (r'\bimportScripts\b', 'importScripts'),
         (r'\bcreateObjectURL\b', 'createObjectURL'), (r'\bBlob\b', 'a Blob'),
         (r'\beval\s*\(', 'eval('), (r'(?<![\w$.])Function\s*\(', 'Function('), (r'\bnew\s+Function\b', 'new Function'),
         (r'\bFunction\b', 'the Function constructor (window.Function, globalThis.Function, ...)'),
         (r'\bdocument\s*\.\s*write(ln)?\b', 'document.write'), (r'\binsertAdjacentHTML\b', 'insertAdjacentHTML'),
         (r'\.\s*outerHTML\b', '.outerHTML'), (r'\bsetAttribute\s*\(\s*[\'"`]style[\'"`]', "setAttribute('style'"),
         (r'\bcreateElement\s*\(\s*[\'"`]style[\'"`]', "createElement('style')"), (r'\btoDataURL\b', 'toDataURL'),
         (r'\bsendBeacon\b', 'sendBeacon'), (r'\blocalStorage\b', 'localStorage'), (r'\bnew\s+Audio\b', 'new Audio'),
         (r'\bset(Timeout|Interval)\s*\(\s*[\'"`]', 'a string timer'),
         (r'(?<![\w$.])import\s*\(', 'import()'), (r'^\s*import\s*[\w{*\'"]', 'a static import'),
         (r'^\s*export\b', 'an export')]
# (pattern on a code line, what it is): an asset URL that does not come from FLOW.asset() (Rails serves every file
# under a digested name: such a URL 404s there)
NOT_ASSET = [(r'(?<![\w-])src=\\?["\']?["\'`]\s*\+(?!\s*FLOW\.asset\()', 'an src=" (or src=\') URL that does not come '
              'from FLOW.asset()'),
             (r'\.\s*(src|poster|srcset)\s*=(?!=)(?!\s*FLOW\.asset\()', 'a .src / .poster / .srcset not set to a '
              'FLOW.asset() URL'),
             (r'\bsetAttribute\s*\(\s*[\'"`](src|poster|srcset)[\'"`]\s*,(?!\s*FLOW\.asset\()', 'a setAttribute of '
              'src / poster / srcset not to a FLOW.asset() URL'),
             (r'\bFLOW\.asset\(\s*[\'"`](?!assets/)', 'a FLOW.asset() key that is not a path under assets/'),
             (r'FLOW\.video\(\s*[^,()]+,(?!\s*FLOW\.asset\()', 'a clip poster that does not come from FLOW.asset()')]
# (pattern in a string, what it is): HTML or URLs a page under the Rails landing's CSP refuses, or that bypass
# FLOW.asset()
IN_STRING = [(r'(?<![\w-])style\s*=', 'a style attribute in an HTML string (a CSP without unsafe-inline refuses it: '
              'use data-st and FLOW.hydrate)'),
             (r'(?<![\w-])on[a-z]+\s*=', 'an inline event handler in a string'), (r'javascript:', 'a javascript: URL'),
             (r'(?<![\w-])(data|blob):', 'a data: or blob: URL (the CSP allows neither)'),
             (r'<(style|link|script|iframe|frame|object|embed|audio|source|track|base|meta|form)\b',
              'an element the CSP refuses or that loads its own resource, in an HTML string'),
             (r'@import\b', 'an @import'), (r'(?<![\w-])srcset\s*=', 'a srcset (its URLs bypass FLOW.asset())'),
             (r'(?<![\w-])(src|poster)=\\?["\']?(?=[^"\'\\])', 'a literal src / poster URL in a string (asset URLs come '
              'from FLOW.asset())'),
             (r'url\((?!#)', 'a url() other than a same-document #fragment in a string')]


def check_js(name, text, parts=None):
    """Stop on anything in a generated script that the Rails landing's CSP (default-src 'none'; script, style, image
    and font sources the page's own) or the port's conventions do not allow. parts: [(upstream name, first line,
    last line)] of a concatenation, for the per-part rules."""
    code, strings = scan_js(text, name)
    lines, src = code.split('\n'), text.split('\n')

    def part_of(k):
        for p, a, b in parts or []:
            if a <= k <= b:
                return p
        return None

    def stop(k, what):
        p = part_of(k)
        die('%s line %d%s: %s:\n%s' % (name, k, ' (%s)' % p if p else '', what, src[k - 1]))

    inner, loops = {}, {}
    for k, line in enumerate(lines, 1):
        for pat, what in SINKS:
            if re.search(pat, line):
                stop(k, what + ', which the port must not contain')
        if re.search(r'\blocation\s*\.\s*search\b', line) and part_of(k) != 'flow-core.js':
            stop(k, 'location.search outside flow-core.js (every knob goes through FLOW.qs, behind ?lab)')
        if re.search(r'\bcurrentScript\b', line) and part_of(k) != 'flow-core.js':
            stop(k, "document.currentScript outside flow-core.js (in one concatenated file it is every part's)")
        for pat, what in NOT_ASSET:
            if re.search(pat, line):
                stop(k, what)
        n = len(re.findall(r'\.\s*innerHTML\b', line))
        if n:
            inner[part_of(k)] = inner.get(part_of(k), 0) + n
        n = len(re.findall(r'\bsetInterval\s*\(|\brequestAnimationFrame\s*\(|\.\s*(every|raf)\s*\(', line))
        if n:
            loops[part_of(k)] = loops.get(part_of(k), 0) + n
    for k, s in strings:
        for pat, what in IN_STRING:
            if re.search(pat, s, re.I):
                stop(k, what)
    want = {p: INNERHTML[p] for p, _, _ in parts} if parts else {None: 0}
    got = {p: inner.get(p, 0) for p in want}
    if got != want:
        die('%s: .innerHTML %s, want %s (review the new one, then update INNERHTML)' % (name, got, want))
    want = {p: LOOPS[p] for p, _, _ in parts} if parts else {None: 0}
    got = {p: loops.get(p, 0) for p in want}
    if got != want:
        die('%s: timers that repeat (setInterval, requestAnimationFrame, ctx.every, ctx.raf) %s, want %s (does the new '
            'one stop once its step is off screen or at rest? then update LOOPS)' % (name, got, want))


def strip_css_comments(t):
    return re.sub(r'/\*.*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group(0)), t, flags=re.S)


CSS_BANNED = [(r'url\(', 'url( (assets come through FLOW.asset in the scripts; Rails rewrites only url()s of files)'),
              (r'@import', '@import'), (r'@font-face', '@font-face (the fonts are index.html\'s Google Fonts links)'),
              (r'@charset', '@charset (one file of four)'), (r'data:', 'data:'), (r'https?://', 'an absolute URL'),
              (r'expression\s*\(', 'expression('), (r'javascript:', 'javascript:'), (r'(?<![\w-])behavior\s*:', 'behavior:'),
              (r'-moz-binding', '-moz-binding'), (r'(?<![\w-])\.js\b', 'a .js selector (the hook is .flow-on)'),
              (r'(?<![\w-])html\s*,\s*body\b', 'html, body (the page rules are :where(.flow)\'s)')]


def check_css(name, text):
    code = strip_css_comments(text)
    if code.count('{') != code.count('}'):
        die('%s: unbalanced braces' % name)
    for k, line in enumerate(code.split('\n'), 1):
        for pat, what in CSS_BANNED:
            if re.search(pat, line, re.I):
                die('%s line %d: %s, which the port must not contain:\n%s' % (name, k, what, text.split('\n')[k - 1]))


# ---- reading upstream ------------------------------------------------------------------------------------------
def read_sources(lab):
    """Every upstream file the port reads or copies (flow-lab-relative path -> bytes), after a census of assets/."""
    src = {}
    for k in FIXED + COPY:
        if not (lab / k).is_file():
            die('%s has no %s' % (lab, k))
        src[k] = (lab / k).read_bytes()
    if not (lab / 'assets').is_dir():
        die('%s has no assets/' % lab)
    found = sorted(p.relative_to(lab).as_posix() for p in (lab / 'assets').rglob('*') if p.is_file())
    new = [k for k in found if k not in PIN and k not in DROPPED]
    if new:
        die('upstream assets/ has %d file(s) the port neither copies nor drops:\n%s\nadd each to PIN (to copy it; '
            'rerun with --commit) or to DROPPED (with the reason)' % (len(new), '\n'.join('  ' + k for k in new)))
    # every file name the scripts spell out in a string must be one the port copies (the clips: one it drops)
    for k in JS_PARTS:
        _, strings = scan_js(src[k].decode('utf-8'), k)
        for line, s in strings:
            for m in re.finditer(r'(?<![\w{}.-])([\w{}][\w{}-]*\.(?:svg|webp|mp4|png|jpe?g|gif|avif))\b', s):
                names = [m.group(1).replace('{n}', str(i)) for i in range(1, 9)] if '{n}' in m.group(1) else [m.group(1)]
                for nm in names:
                    if not any(c.endswith('/' + nm) for c in COPY) and \
                            not any(c.endswith('/' + nm) and c.endswith('.mp4') for c in DROPPED):
                        die('%s line %d names %s, which the port does not copy' % (k, line, nm))
    for k in COPY:
        if re.search(r'-[0-9a-f]{8}\.(?:mp4|webp)$', k):
            die('%s ends like a digested name, which build.js (B7) would pair as another photo' % k)
    return src


# ---- the edits -------------------------------------------------------------------------------------------------
def port_flow_core(t):
    p = Port('flow-core.js', t)
    p.sub('F1',
          L("  var qs = new URLSearchParams(location.search);"),
          L("  // PORT (F1): the lab's URL knobs only with ?lab in the query (?lab&final=1, ?lab&step=build), as the hero's:",
            "  // without it the flow reads no query at all, so a visitor's ?step=, ?final= or ?cat= changes nothing",
            "  var qs = new URLSearchParams(new URLSearchParams(location.search).has('lab') ? location.search : '');"),
          "`var qs = new URLSearchParams(location.search)` -> the query only when it has a `lab` parameter, else an\n"
          "empty one (as hero/field.js, its edit 8). Every knob reads it, as FLOW.qs: ?rm= ?speed= here, ?step=\n"
          "?final= ?play= in flow.js, ?cat= in stages/start.js (its S5). On the published page a visitor's query\n"
          "reached them all, and ?step= removes the other two steps. ?lab&final=1 is the check URL.")
    p.sub('F2',
          L("  var stages = {};"),
          L("  var stages = {};",
            "  // PORT (F2): every asset URL the flow builds is FLOW.asset(key), key = the file's path under flow/",
            "  // ('assets/start/thumb-vp-1.webp'): from the wrapper's data-flow-assets, an optional JSON map key -> URL",
            "  // (Rails: digested asset paths), read once; else the key resolved against this script's own URL. A map value",
            "  // with a quote, an angle bracket or white space is ignored (the URLs go into HTML strings).",
            "  var ASSET_BASE = new URL('./', (document.currentScript && document.currentScript.src) || document.baseURI).href;",
            "  var ASSET_MAP;",
            "  function asset(key) {",
            "    if (ASSET_MAP === undefined) {",
            "      ASSET_MAP = null;",
            "      try {",
            "        var w = document.querySelector('.flow[data-flow-assets]');",
            "        if (w) ASSET_MAP = JSON.parse(w.getAttribute('data-flow-assets'));",
            "      } catch (e) { ASSET_MAP = null; }",
            "      if (!ASSET_MAP || typeof ASSET_MAP !== 'object') ASSET_MAP = null;",
            "    }",
            "    var u = ASSET_MAP && Object.prototype.hasOwnProperty.call(ASSET_MAP, key) ? ASSET_MAP[key] : null;",
            "    return typeof u === 'string' && /^[^\"'<>\\s]+$/.test(u) ? u : new URL(key, ASSET_BASE).href;",
            "  }",
            "  // PORT (F3): the stages' HTML strings say data-st=\"...\" where they had style=\"...\" (a style attribute parsed",
            "  // from markup is refused by a CSP without 'unsafe-inline'); hydrate() moves each into the element's inline",
            "  // style through CSSOM, which a CSP does not govern, in the same task (nothing paints in between)",
            "  function hydrate(root) {",
            "    [].forEach.call(root.querySelectorAll('[data-st]'), function (e) {",
            "      e.style.cssText = e.getAttribute('data-st');",
            "      e.removeAttribute('data-st');",
            "    });",
            "    return root;",
            "  }"),
          "inserted after `var stages = {}`: asset(key), FLOW.asset (F6), the URL of a file under flow/, key being\n"
          "its path there ('assets/start/thumb-vp-1.webp'). It reads the flow wrapper's data-flow-assets once\n"
          "(`.flow[data-flow-assets]`, an optional JSON map key -> URL: Rails passes digested asset paths, as the\n"
          "hero's data-products), else resolves the key against this script's own URL (document.currentScript, read\n"
          "here at load: flow/flow.js -> flow/assets/...). A missing key, bad JSON, or a value with a quote, an\n"
          "angle bracket or white space (the URLs go into HTML strings) falls back, silently. Upstream built URLs from\n"
          "each stage's own document.currentScript plus '../assets/<stage>/' (one script now, and wrong under\n"
          "Propshaft's digests) and, in flow.js, document-relative 'assets/shell/...' (which Kyu's composed page had\n"
          "edited to 'flow/assets/shell/...').")
    p.notes['F3'] = {'where': list(p.notes['F2']['where']), 'note':
                     "inserted after F2: hydrate(root), FLOW.hydrate (F6): every data-st=\"...\" attribute under root\n"
                     "becomes that element's inline style through CSSOM (style.cssText), then goes. stages/build.js (B5,\n"
                     "B6) and stages/test.js (T3, T4) write data-st where their HTML strings had style=\"...\": a style\n"
                     "attribute parsed from markup is refused by any CSP without 'unsafe-inline', the Rails landing's\n"
                     "included, which collapsed Test's checkout and thank-you pages and took Build's scan light and its\n"
                     "dotted frames. A CSSOM write is not governed by a CSP. The same declarations, in the same task."}
    p.sub('F4',
          L("  var vidOff = reduced || qs.get('vid') !== '1';"),
          L("  // PORT (F4): the clips stay off for good (R23's default: the posters are the stills); no ?vid=1, no MP4s",
            "  var vidOff = true;"),
          "`var vidOff = reduced || qs.get('vid') !== '1'` -> `var vidOff = true`: the product clips stay off, as\n"
          "R23 has them by default (\"The products are stills by default\", above); the ?vid=1 knob goes. The port\n"
          "ships no MP4 (tools/flow_port.py's DROPPED).")
    p.sub('F5',
          L("  var copies = {}, fetching = new WeakSet();   // copies: clip url -> promise of an object url",
            "  function loaded(v) {",
            "    if (v.getAttribute('src') != null) return true;",
            "    if (fetching.has(v)) return false;",
            "    fetching.add(v);",
            "    var u = new URL(v.getAttribute('data-src'), document.baseURI).href;   // one copy per clip, however a stage spells its url",
            "    if (!copies[u]) {",
            "      copies[u] = fetch(u).then(function (r) {",
            "        if (!r.ok) throw new Error(r.status + ' ' + u);",
            "        return r.blob();",
            "      }).then(function (b) { return URL.createObjectURL(b); });",
            "      copies[u].catch(function (e) { console.warn('flow clip: ' + (e && e.message || e)); });",
            "    }",
            "    // a clip that never arrives keeps its poster",
            "    copies[u].then(function (o) { fetching.delete(v); v.src = o; vsync(v); }, function () {});",
            "    return false;",
            "  }"),
          L("  // PORT (F5): loaded() fetched a clip and played it from a blob: URL; vidOff (F4) means it is never reached",
            "  function loaded(v) { return false; }"),
          "`copies`, `fetching` and loaded()'s body (fetch() of the clip, URL.createObjectURL) -> `function\n"
          "loaded(v) { return false; }`: vsync() calls it only for a clip that may play, which F4 rules out. No fetch()\n"
          "or blob: URL is left, so no connect-src or media-src is needed.")
    p.sub('F6',
          L("    qs: qs,"),
          L("    qs: qs,",
            "    asset: asset,       // PORT (F6): F2",
            "    hydrate: hydrate,   // PORT (F6): F3"),
          "window.FLOW gains `asset` (F2) and `hydrate` (F3).")
    return p


def port_start(t):
    p = Port('stages/start.js', t)
    p.sub('S1',
          L("  var SRC = document.currentScript && document.currentScript.src;",
            "  function dir(d) {",
            "    if (!SRC) return d.slice(3);",
            "    try { return new URL(d, SRC).href; } catch (e) { return d.slice(3); }",
            "  }",
            "  var BASE = dir('../assets/start/');",
            "  var VID = dir('../assets/video/');   // the product clips (FLOW.video)"),
          L("  // PORT (S1): asset keys (paths under flow/); FLOW.asset() makes the URLs where the markup is built",
            "  var BASE = 'assets/start/';",
            "  var VID = 'assets/video/';   // the product clips (FLOW.video)"),
          "the asset folders `dir('../assets/start/')`, `dir('../assets/video/')` and `dir('../assets/test/')`\n"
          "(each resolved against this script's document.currentScript) -> the keys 'assets/start/', 'assets/video/'\n"
          "and 'assets/test/'; SRC and dir() go. FLOW.asset() (flow-core.js F2) makes the URL where the markup is\n"
          "built (S2-S4, S8).")
    p.sub('S1',
          L("  var ICONS = dir('../assets/test/');"),
          L("  var ICONS = 'assets/test/';   // PORT (S1)"))
    p.sub('S2',
          "' src=\"' + BASE + file + '\">';",
          "' src=\"' + FLOW.asset(BASE + file) + '\">';   // PORT (S2)",
          "img(): `src=\"' + BASE + file + '\"` -> `src=\"' + FLOW.asset(BASE + file) + '\"`.")
    p.sub('S3',
          "src=\"' + ICONS + 'pdp-icon-' + n + '.svg\">' : ''; }",
          "src=\"' + FLOW.asset(ICONS + 'pdp-icon-' + n + '.svg') + '\">' : ''; }   // PORT (S3)",
          "icon() (SHOW_ICONS is false: nothing calls for these): the same, FLOW.asset(ICONS + 'pdp-icon-' + n +\n"
          "'.svg').")
    p.sub('S4',
          "(clip ? FLOW.video(VID + clip + '.mp4', VID + clip + '-poster.webp', 'start-clip') : '') + '</div>';\n",
          "(clip ? FLOW.video(VID + clip + '.mp4', FLOW.asset(VID + clip + '-poster.webp'), 'start-clip') : '') + '</div>';"
          "   // PORT (S4)\n",
          "tileHTML()'s clip (no category has clips in R23): the poster through FLOW.asset; the data-src stays the\n"
          "key (never fetched: flow-core.js F4).")
    p.sub('S5',
          L("  // ?cat=decor (beauty, sports) starts on that category (r18)",
            "  var ACTIVE = (function () { var m = /[?&]cat=([a-z]+)/.exec(location.search || '');"
            " return m && CATEGORIES[m[1]] ? m[1] : 'streetwear'; })();"),
          L("  // ?cat=decor (beauty, sports) starts on that category (r18)",
            "  // PORT (S5): read through FLOW.qs, so only with ?lab (flow-core.js F1)",
            "  var ACTIVE = (function () { var m = /^([a-z]+)/.exec(FLOW.qs.get('cat') || '');"
            " return m && CATEGORIES[m[1]] ? m[1] : 'streetwear'; })();"),
          "?cat= through FLOW.qs (behind ?lab, flow-core.js F1) instead of location.search:\n"
          "`/[?&]cat=([a-z]+)/.exec(location.search || '')` -> `/^([a-z]+)/.exec(FLOW.qs.get('cat') || '')`.")
    p.sub('S6',
          L("      var c = CATEGORIES[k], t = (c && c.label) || k.charAt(0).toUpperCase() + k.slice(1);"),
          L("      var c = CATEGORIES[k], t = (c && c.label) || k.charAt(0).toUpperCase() + k.slice(1);",
            "      // PORT (S6): the Dux names: the pill, and the store it opens (its winner's subdomain)",
            "      var w = c && c.cards && c.cards[c.winner], store = w ? String(w.url).split('.')[0] : k;"),
          "pillsHTML(): each pill also gets data-component-name=\"store-pill-<category>\" and\n"
          "data-component-extra-store=\"<its winning store's subdomain>\" (CATEGORIES[k].cards[winner].url up to its\n"
          "first dot: apparel-streetwear, home-decor, clean-beauty, apparel-snowwear), the names the Rails landing's\n"
          "Dux reports a click by. Nothing reads them here.")
    p.sub('S6',
          "' role=\"button\" tabindex=\"0\" data-cat=\"' + k + '\"><span class=\"start-pill-t\">'",
          "' role=\"button\" tabindex=\"0\" data-cat=\"' + k + '\"' +\n"
          "        ' data-component-name=\"store-pill-' + k + '\" data-component-extra-store=\"' + esc(store) + '\"><span class=\"start-pill-t\">'")
    p.sub('S7',
          L("    } catch (e) {",
            "      if (!REF_STYLE) { REF_STYLE = document.createElement('style'); document.head.appendChild(REF_STYLE); }",
            "      REF_STYLE.textContent = css;",
            "    }"),
          L("    } catch (e) {",
            "      // PORT (S7): no <style> element fallback (a CSP without 'unsafe-inline' refuses it): flow/head.js turns",
            "      // the flow on only where constructable style sheets exist",
            "      FLOW.swallow(e);",
            "    }"),
          "refSheet()'s fallback, a <style> element appended to <head> when constructable style sheets throw\n"
          "(Safari < 16.4, Firefox < 101, Chrome < 73), -> FLOW.swallow(e) (console.error): a CSP without\n"
          "'unsafe-inline' refuses a JS-made <style>, so under the Rails landing's the fallback could not work, and\n"
          "flow/head.js now turns the flow on only where constructable style sheets exist (there, the static\n"
          "transcripts show instead).")
    p.sub('S8',
          "var ic = function (k) { return '<img alt=\"\" draggable=\"false\" src=\"' + BASE + 'pdp-' + CAT_KEY + '-' + k + '.svg\">'; };",
          "var ic = function (k) { return '<img alt=\"\" draggable=\"false\" src=\"' + FLOW.asset(BASE + 'pdp-' + CAT_KEY + '-' + k + '.svg') + '\">'; };   // PORT (S8)",
          "the Reference PDP's icons, refHTML()'s and phRefHTML()'s ic() (the same line twice): FLOW.asset(BASE +\n"
          "'pdp-' + CAT_KEY + '-' + k + '.svg').", count=2)
    p.sub('S9',
          L("    var r = step.querySelector('.fl-replay');",
            "    if (r) r.click();"),
          L("    // PORT (S9): the restart through Replay's own handler (flow.js L6), not a click on the button, which every",
            "    // click listener saw: the Rails landing's Dux reported each pick as a Replay press too",
            "    var r = step.querySelector('.fl-replay');",
            "    if (r) r.dispatchEvent(new CustomEvent('fl-replay'));"),
          "pick() restarted the step with `r.click()` on the step's Replay button (`.fl-replay`): a click event that\n"
          "every click listener on the page saw, so the Rails landing's Dux reported each pick as a press of Replay\n"
          "(data-component-name=\"replay\", flow.js L3) as well as of the pill (measured on the Rails page: Decor by\n"
          "mouse sent `store-pill-decor` then `replay`; Beauty by Enter and Sports by Space, `replay` alone). ->\n"
          "`r.dispatchEvent(new CustomEvent('fl-replay'))`, an event of the flow's own (it does not bubble) that\n"
          "flow.js answers with Replay's click handler (its L6): the same restart at the same moment (a run, or\n"
          "final() under reduced motion), with no click.")
    p.sub('S10',
          L("    if (e.type === 'keydown') {",
            "      if (e.key !== 'Enter' && e.key !== ' ') return;",
            "      e.preventDefault();",
            "    }"),
          L("    if (e.type === 'keydown') {",
            "      if (e.key !== 'Enter' && e.key !== ' ') return;",
            "      e.preventDefault();",
            "      // PORT (S10): a key picks through the pill's click(), one click event as a mouse pick has; the pick runs",
            "      // on that click (below), once",
            "      p.click();",
            "      return;",
            "    }"),
          "onPick() picked on Enter or Space in its keydown path, so a key pick dispatched no click at all: Dux, which\n"
          "counts clicks, saw it only as S9's click on Replay. -> after preventDefault(), as upstream, the keydown path\n"
          "calls the pill's click() and returns: the pick runs on that click, through onPick()'s click path, once, and\n"
          "a key pick dispatches one click event, on the pill, as a mouse pick does (and as Enter on a <button>\n"
          "would).")
    return p


def port_build(t):
    p = Port('stages/build.js', t)
    p.sub('B1',
          L("  var SRC = document.currentScript && document.currentScript.src;",
            "  function dir(d) { try { return new URL(d, SRC || location.href).href; } catch (e) { return d.slice(3); } }",
            "  var A = dir('../assets/build/');",
            "  var V = dir('../assets/video/');   // the product clips (FLOW.video), shared with the other stages"),
          L("  // PORT (B1): asset keys (paths under flow/); FLOW.asset() makes the URLs in img() and clip()",
            "  var A = 'assets/build/';",
            "  var V = 'assets/video/';   // the product clips (FLOW.video), shared with the other stages"),
          "the asset folders `dir('../assets/build/')` and `dir('../assets/video/')` (resolved against this script's\n"
          "document.currentScript) -> the keys 'assets/build/' and 'assets/video/'; SRC and dir() go.")
    p.sub('B2',
          L("  function img(n) { return '<img src=\"' + A + n + '\" alt=\"\" draggable=\"false\">'; }",
            "  function clip(n) { return FLOW.video(V + n + '.mp4', V + n + '-poster.webp', 'build-clip'); }"),
          L("  // PORT (B2): the URLs from FLOW.asset(); a clip's data-src stays its key (never fetched: vidOff)",
            "  function img(n) { return '<img src=\"' + FLOW.asset(A + n) + '\" alt=\"\" draggable=\"false\">'; }",
            "  function clip(n) { return FLOW.video(V + n + '.mp4', FLOW.asset(V + n + '-poster.webp'), 'build-clip'); }"),
          "img(): `src=\"' + FLOW.asset(A + n) + '\"`; clip(): the poster through FLOW.asset, the data-src stays the\n"
          "key 'assets/video/<name>.mp4' (never fetched: flow-core.js F4; slotsOf() and mount() read the clip's name\n"
          "from it).")
    p.sub('B3',
          L("      return '<button type=\"button\" class=\"build-pill\" data-t=\"' + p[0] + '\" aria-pressed=\"false\" tabindex=\"-1\">' + p[1] + '</button>';"),
          L("      // PORT (B3): the Dux name, style-pill-<technical|vibrant|bold|elegant>",
            "      return '<button type=\"button\" class=\"build-pill\" data-t=\"' + p[0] + '\"' +",
            "        ' data-component-name=\"style-pill-' + ICON[p[0]] + '\" aria-pressed=\"false\" tabindex=\"-1\">' + p[1] + '</button>';"),
          "pillsHTML(): each button.build-pill also gets data-component-name=\"style-pill-<technical|vibrant|bold|\n"
          "elegant>\" (ICON[t]), the name the Rails landing's Dux reports a click by. Nothing reads it here.")
    p.sub('B4',
          L("    if (!E || FLOW.reduced || (E.clipTok && E.clipTok.ctx === ctx)) return;"),
          L("    // PORT (B4): no clip ever plays (vidOff), so no frame loop to drive them",
            "    if (!E || FLOW.reduced || FLOW.vidOff || (E.clipTok && E.clipTok.ctx === ctx)) return;"),
          "watchClips(): `|| FLOW.vidOff` in its first test. With the clips off, its requestAnimationFrame loop (60\n"
          "a second, syncClips() every 30 ms, forever once Build has played, on or off screen) had nothing to do; the\n"
          "flow analysis measured ~15 ms of script a second for it.")
    p.sub('B5',
          "'\" style=\"stroke:' + k[3] +",
          "'\" data-st=\"stroke:' + k[3] +",
          "run(), the light round each scan box: each <rect>'s `style=\"stroke:..;stroke-width:..;stroke-opacity:..;\n"
          "stroke-dasharray:..\"` -> `data-st=\"...\"`, hydrated (flow-core.js F3) right after the innerHTML. Under a\n"
          "CSP the light never drew (the rects kept only build.css's fill:none).")
    p.sub('B5',
          L("    }).join('') + '</svg>';",
            "    [].forEach.call(el.firstChild.children, function (rc, i) {"),
          L("    }).join('') + '</svg>';",
            "    FLOW.hydrate(el);   // PORT (B5)",
            "    [].forEach.call(el.firstChild.children, function (rc, i) {"))
    p.sub('B6',
          "'<svg class=\"build-fr-dots\" aria-hidden=\"true\" style=\"stroke-dasharray:0 '",
          "'<svg class=\"build-fr-dots\" aria-hidden=\"true\" data-st=\"stroke-dasharray:0 '",
          "frame(), the dotted frames: the <svg class=\"build-fr-dots\">'s `style=\"stroke-dasharray:0 <P>px\"` ->\n"
          "`data-st=\"...\"`, hydrated (flow-core.js F3) after the innerHTML. Under a CSP the dots drew as solid\n"
          "lines.")
    p.sub('B6',
          L("      '</svg>';",
            "    place(el, r);"),
          L("      '</svg>';",
            "    FLOW.hydrate(el);   // PORT (B6)",
            "    place(el, r);"))
    p.sub('B7',
          "      m = m && /([\\w-]+)\\.(?:mp4|webp)/.exec(m.getAttribute('data-src') || m.getAttribute('src') || '');\n",
          "      // PORT (B7): a digested photo name (Propshaft's name-<8 hex>.webp) pairs as its plain name\n"
          "      m = m && /([\\w-]+?)(?:-[0-9a-f]{8})?\\.(?:mp4|webp)/.exec(m.getAttribute('data-src') || m.getAttribute('src') || '');\n",
          "slotsOf() pairs the photos across themes by file name: `/([\\w-]+)\\.(?:mp4|webp)/` ->\n"
          "`/([\\w-]+?)(?:-[0-9a-f]{8})?\\.(?:mp4|webp)/`, so a digested URL (Propshaft: tee-front-1a2b3c4d.webp) pairs\n"
          "as tee-front. The same names here: tools/flow_port.py asserts no copied file ends in -<8 hex>.")
    p.sub('B8',
          L("  function mount(vis) {"),
          L("  // PORT (B8): the theme faces' warm-up, once, when the step comes on screen (at once without an",
            "  // IntersectionObserver or a step), not at page load",
            "  var WARM = null;",
            "  function warmNear(step, fn) {",
            "    if (WARM) return;",
            "    WARM = fn;",
            "    if (!step || !window.IntersectionObserver) { fn(); return; }",
            "    var io = new IntersectionObserver(function (es) {",
            "      if (!es.some(function (e) { return e.isIntersecting; })) return;",
            "      io.disconnect();",
            "      fn();",
            "    }, { rootMargin: '0px' });",
            "    io.observe(step);",
            "  }",
            "",
            "  function mount(vis) {"),
          "mount() warmed all 19 theme faces (document.fonts.load ...) at page load, wherever the step was: ~163 KB\n"
          "of Vibrant / Bold / Elegant faces competing with the hero. Now warmNear() (inserted before mount()) runs\n"
          "that warm-up once, when the step's first pixel comes on screen (IntersectionObserver on the article,\n"
          "rootMargin 0; at once without one or without a step). A margin of one viewport, the first choice, did not\n"
          "defer it where it mattered: Build's top (1704px at 1440x900 and 1920x1080, 1521 at 1024x768) is less than\n"
          "two viewport heights down the page, inside that margin at load, so the faces loaded at once and slowed the\n"
          "hero's field by ~1 s on slow 4G. The faces left to fetch are Vibrant's, Bold's and Elegant's, which\n"
          "show only after the scripted run, once the pills go live (the run ends on Technical, whose JetBrains Mono\n"
          "700/800 the first view has already loaded); Build plays when its visual's top crosses 72% of the\n"
          "viewport, after its copy column has come on screen. The fonts.ready re-seat of the pills is unchanged.")
    p.sub('B8',
          L("    if (document.fonts && document.fonts.load) {",
            "      ['700 10px \"Space Grotesk\"', '500 10px \"Space Grotesk\"', '400 10px \"Space Grotesk\"',"),
          L("    if (document.fonts && document.fonts.load) {",
            "      warmNear(step, function () {   // PORT (B8)",
            "      ['700 10px \"Space Grotesk\"', '500 10px \"Space Grotesk\"', '400 10px \"Space Grotesk\"',"))
    p.sub('B8',
          L("        try { document.fonts.load(f).catch(noop); } catch (e) {}",
            "      });",
            "      // the thumb is measured off Inter; re-seat it once webfonts land"),
          L("        try { document.fonts.load(f).catch(noop); } catch (e) {}",
            "      });",
            "      });   // PORT (B8)",
            "      // the thumb is measured off Inter; re-seat it once webfonts land"))
    p.sub('B9',
          L("      if (!ctx.reduced) ctx.every(250, function () { tick(ctx); });"),
          L("      if (!ctx.reduced) E.tickOff = tickOnScreen(ctx, vis);   // PORT (B9): the tick, on screen only"),
          "idle()'s `ctx.every(250, tick)`, a 4 Hz interval for the life of the page once Build had played (on\n"
          "Vibrant its carousel swiped every 2.5 s, six Web Animations each, with every step off screen), ->\n"
          "tickOnScreen(ctx, vis) (inserted after tick()): the same interval, but only while the step is on screen\n"
          "(an IntersectionObserver on the article) and the page visible (visibilitychange). Started at once, as\n"
          "upstream, so the in-view cadence is the same; stopped when the step leaves; back on screen it restarts with\n"
          "the next swipe ~1.2 s on (E.tSwipe as settle() sets it after a switch: the carousel resumes, it does not\n"
          "jump). teardownIdle() stops it (E.tickOff); so does the run's ctx going (kill()), which also clears the\n"
          "interval. Without an IntersectionObserver it runs as upstream. tools/flow_port.py's LOOPS counts the\n"
          "timers that repeat, so a new one stops the generator for review.")
    p.sub('B9',
          L("  function teardownIdle() {",
            "    if (!E) return;"),
          L("  // PORT (B9): idle()'s 4 Hz tick (on Vibrant, the carousel's swipe every 2.5 s) while the step is on screen",
            "  // and the page visible, not for the life of the page. Returns what stops it (teardownIdle()).",
            "  function tickOnScreen(ctx, vis) {",
            "    var step = (vis.closest && vis.closest('.fl-step')) || vis, seen = true, id = 0, first = true, io = null;",
            "    function sync() {",
            "      if (!ctx.alive() || !E) { stop(); return; }",
            "      var go = seen && !document.hidden;",
            "      if (go && !id) {",
            "        // back on screen: the next swipe ~1.2s on, as after a switch (settle())",
            "        if (!first && E.cur === 'vib') E.tSwipe = performance.now() - 1300 / ctx.speed;",
            "        first = false;",
            "        id = ctx.every(250, function () { tick(ctx); });",
            "      } else if (!go && id) { clearInterval(id); id = 0; }",
            "    }",
            "    function stop() {",
            "      if (id) clearInterval(id);",
            "      id = 0;",
            "      if (io) io.disconnect();",
            "      io = null;",
            "      document.removeEventListener('visibilitychange', sync);",
            "    }",
            "    sync();",
            "    if (window.IntersectionObserver) {",
            "      io = new IntersectionObserver(function (es) { seen = es[es.length - 1].isIntersecting; sync(); });",
            "      io.observe(step);",
            "    }",
            "    document.addEventListener('visibilitychange', sync);",
            "    return stop;",
            "  }",
            "",
            "  function teardownIdle() {",
            "    if (!E) return;",
            "    if (E.tickOff) { E.tickOff(); E.tickOff = null; }   // PORT (B9)"))
    return p


def port_test(t):
    p = Port('stages/test.js', t)
    p.sub('T1',
          L("  var BASE = (function () {",
            "    var s = document.currentScript && document.currentScript.src;",
            "    if (!s) return 'assets/test/';",
            "    try { return new URL('../assets/test/', s).href; } catch (e) { return 'assets/test/'; }",
            "  })();"),
          L("  // PORT (T1): the asset key (a path under flow/); FLOW.asset() makes the URLs in im() and clip()",
            "  var BASE = 'assets/test/';"),
          "BASE, `new URL('../assets/test/', document.currentScript.src)`, -> the key 'assets/test/' (VID follows\n"
          "it: 'assets/video/').")
    p.sub('T2',
          "' src=\"' + BASE + name +",
          "' src=\"' + FLOW.asset(BASE + name) +   // PORT (T2)",
          "im(): `src=\"' + FLOW.asset(BASE + name) + ...`; clip(): the poster through FLOW.asset, the data-src the\n"
          "key.")
    p.sub('T2',
          "FLOW.video(VID + name + '.mp4', VID + name + '-poster.webp', 'test-clip')",
          "FLOW.video(VID + name + '.mp4', FLOW.asset(VID + name + '-poster.webp'), 'test-clip')")
    p.sub('T3',
          "'<div class=\"' + cls + '\" style=\"left:' + px(x) + ';top:' + px(y) + ';width:' + px(w) +\n",
          "'<div class=\"' + cls + '\" data-st=\"left:' + px(x) + ';top:' + px(y) + ';width:' + px(w) +   // PORT (T3)\n",
          "box(), tx(), inp(), radio() and row(): `style=\"left:..;top:..;width:..;height:..\"` -> `data-st=\"...\"`,\n"
          "on the ~94 parts of the checkout and thank-you pages the comps place, hydrated in build() (T4).")
    p.sub('T3', "(w ? ' is-wrap' : '') + '\" style=\"left:' + px(x) + ';top:' + px(y) +\n",
          "(w ? ' is-wrap' : '') + '\" data-st=\"left:' + px(x) + ';top:' + px(y) +   // PORT (T3)\n")
    p.sub('T3', "'\"' : '') + ' style=\"left:' + px(x) + ';top:' + px(y) +\n",
          "'\"' : '') + ' data-st=\"left:' + px(x) + ';top:' + px(y) +   // PORT (T3)\n")
    p.sub('T3', "'<i class=\"test-radio\" style=\"left:' + px(x) + ';top:' + px(y) + '\"><b></b></i>'; }\n",
          "'<i class=\"test-radio\" data-st=\"left:' + px(x) + ';top:' + px(y) + '\"><b></b></i>'; }   // PORT (T3)\n")
    p.sub('T3', "(tot ? ' is-tot' : '') + '\" style=\"top:' + px(y) + '\"><span>' + a + '</span><span>' + b + "
                "'</span></div>';\n",
          "(tot ? ' is-tot' : '') + '\" data-st=\"top:' + px(y) + '\"><span>' + a + '</span><span>' + b + "
          "'</span></div>';   // PORT (T3)\n")
    p.sub('T4',
          L("    root.innerHTML = ph ? HTML_PH : HTML;"),
          L("    root.innerHTML = ph ? HTML_PH : HTML;",
            "    FLOW.hydrate(root);   // PORT (T4): the parts' places (T3), before anything paints"),
          "build(): FLOW.hydrate(root) (flow-core.js F3) right after `root.innerHTML = ph ? HTML_PH : HTML`. Under\n"
          "a CSP, without T3-T4, 62 parts lost their places and the thank-you page was an empty page with stray text\n"
          "(measured by the flow analysis).")
    return p


def port_shell(t):
    p = Port('flow.js', t)
    p.sub('L1',
          L("(function () {",
            "  'use strict';",
            "",
            "  var Q = FLOW.qs;"),
          L("(function shell() {   // PORT (L1): named, so that L5 can run it once the stylesheet applies",
            "  'use strict';",
            "",
            "  // PORT (L1): only where flow/head.js turned the flow on (html.flow-on). Without it nothing is enhanced and",
            "  // the page keeps its static transcripts; the wrapper says so (data-flow=\"off\"), if head.js could not yet.",
            "  if (!document.documentElement.classList.contains('flow-on')) {",
            "    var wrapOff = document.querySelector('.flow');",
            "    if (wrapOff && !wrapOff.hasAttribute('data-flow')) wrapOff.setAttribute('data-flow', 'off');",
            "    return;",
            "  }",
            "  var Q = FLOW.qs;"),
          "inserted at the top of the IIFE: return unless <html> has class flow-on, which flow/head.js sets in a\n"
          "browser with what the flow needs. Then nothing is enhanced, and the page keeps the static transcripts\n"
          "(flow.css's motion states are keyed on flow-on too: flow/flow.css's C2); the wrapper gets data-flow=\"off\"\n"
          "unless it has a data-flow already (head.js sets it when it takes flow-on off, but a flow/flow.css that\n"
          "fails does so before the parser, held at that stylesheet, has reached the wrapper). The IIFE is named\n"
          "`shell`, which L5 calls again once flow/flow.css applies.")
    p.sub('L2',
          "<img src=\"assets/shell/copy-vector-teal.svg\" width=\"12\" height=\"13\" alt=\"\"></span>' +\n",
          "<img src=\"' + FLOW.asset('assets/shell/copy-vector-teal.svg') + '\" width=\"12\" height=\"13\" alt=\"\"></span>' +"
          "   // PORT (L2)\n",
          "the shell's three glyphs: the document-relative `src=\"assets/shell/<glyph>.svg\"` -> `src=\"' +\n"
          "FLOW.asset('assets/shell/<glyph>.svg') + '\"` (flow-core.js F2).")
    p.sub('L2', "<img src=\"assets/shell/send-image.svg\" width=\"20\" height=\"20\" alt=\"\"></span></span>';\n",
          "<img src=\"' + FLOW.asset('assets/shell/send-image.svg') + '\" width=\"20\" height=\"20\" alt=\"\"></span></span>';"
          "   // PORT (L2)\n")
    p.sub('L2', "<img class=\"fl-dot\" src=\"assets/shell/dot-teal.svg\" width=\"6\" height=\"6\" alt=\"\"><span class=\"fl-spin\">"
                "</span>';\n",
          "<img class=\"fl-dot\" src=\"' + FLOW.asset('assets/shell/dot-teal.svg') + '\" width=\"6\" height=\"6\" alt=\"\">"
          "<span class=\"fl-spin\"></span>';   // PORT (L2)\n")
    p.sub('L3',
          L("    send.setAttribute('aria-label', 'Copy prompt');"),
          L("    send.setAttribute('aria-label', 'Copy prompt');",
            "    send.setAttribute('data-component-name', 'copy-prompt');   // PORT (L3): the Dux name"),
          "the Copy prompt and Replay buttons also get data-component-name=\"copy-prompt\" / \"replay\", the names\n"
          "the Rails landing's Dux reports a click by. Nothing reads them here.")
    p.sub('L3',
          L("    replay.setAttribute('aria-label', 'Replay this step');"),
          L("    replay.setAttribute('aria-label', 'Replay this step');",
            "    replay.setAttribute('data-component-name', 'replay');   // PORT (L3)"))
    p.sub('L4',
          L("  window.__flow = all;",
            "})();"),
          L("  window.__flow = all;",
            "  // PORT (L4): ready (every step enhanced and mounted): from here flow/head.js's error listener lets the flow be",
            "  var wrap = document.querySelector('.flow');",
            "  if (wrap) wrap.setAttribute('data-flow', 'on');",
            "})();"),
          "appended after `window.__flow = all`: data-flow=\"on\" on the wrapper (`.flow`), the flow's \"ready\".\n"
          "flow/head.js's error listener takes flow-on off for an error from this file before it, never after.")
    p.sub('L5',
          L("  var Q = FLOW.qs;",
            "  var T = {"),
          L("  // PORT (L5): and only once flow/flow.css applies (its last rule sets --flow-css on :root). This script is",
            "  // async, so it can run before a stylesheet still on its way, and with none the stages would build into",
            "  // unstyled markup. Until it applies the shell waits for the stylesheet's load or error",
            "  // (link[data-flow-css]) or the page's load, then runs again; if it still does not apply, the flow goes off",
            "  // as for an error (flow/head.js): no flow-on, data-flow=\"off\", the static transcripts.",
            "  if (!styled()) return;",
            "  function styled() {",
            "    var on = function () {",
            "      return getComputedStyle(document.documentElement).getPropertyValue('--flow-css').trim() === '1';",
            "    };",
            "    if (on()) return true;",
            "    var css = document.querySelector('link[data-flow-css]'), done = false;",
            "    var later = function () {",
            "      if (done) return;",
            "      done = true;",
            "      if (on()) { shell(); return; }",
            "      document.documentElement.classList.remove('flow-on');",
            "      var w = document.querySelector('.flow');",
            "      if (w) w.setAttribute('data-flow', 'off');",
            "    };",
            "    if (document.readyState === 'complete') later();",
            "    else {",
            "      if (css) { css.addEventListener('load', later); css.addEventListener('error', later); }",
            "      addEventListener('load', later);",
            "    }",
            "    return false;",
            "  }",
            "  var Q = FLOW.qs;",
            "  var T = {"),
          "inserted after L1: unless flow/flow.css applies (its last rule, flow/flow.css's C5, sets `--flow-css: 1`\n"
          "on :root), the shell returns and runs again (shell(), L1) once the stylesheet's link[data-flow-css] fires\n"
          "load or error, or the page's load event comes (which waits for every stylesheet); if the sheet still does\n"
          "not apply, it takes flow-on off and sets data-flow=\"off\", as flow/head.js does for a failed script. This\n"
          "script is async (section.html's were classic scripts after the stylesheets, which wait for them), so it\n"
          "can run before the stylesheet has arrived; and with flow/flow.css failing, the stages built into unstyled\n"
          "markup (measured at 1440x900: a 38.6k px page, 1593px wide).")
    p.sub('L6',
          L("    replay.addEventListener('click', function () {",
            "      if (FLOW.reduced) final(); else run();",
            "    });"),
          L("    // PORT (L6): Replay's handler, named, for its click and for 'fl-replay', the event stages/start.js's pick()",
            "    // (its S9) sends the button to restart the step without a click (one analytics would count as a press)",
            "    function replayStep() {",
            "      if (FLOW.reduced) final(); else run();",
            "    }",
            "    replay.addEventListener('click', replayStep);",
            "    replay.addEventListener('fl-replay', replayStep);"),
          "Replay's click handler, `function () { if (FLOW.reduced) final(); else run(); }`, -> the same body as a\n"
          "named function, replayStep(), which also answers 'fl-replay' on the button: the event stages/start.js's\n"
          "pick() sends it (its S9) to restart the step, where upstream clicked the button, a click the Rails\n"
          "landing's Dux counted as a press of Replay. A click on Replay runs it as before.")
    return p


def port_css(name, t):
    p = Port(name, t)
    if name == 'flow.css':
        p.sub('C1',
              L("html, body { margin: 0; background: var(--fl-bg); color: var(--fl-ink);"),
              L("/* PORT (C1): the page rules are the wrapper's, at zero specificity, on the browser's defaults (Kyu's",
                "   composition, hero-stage/hero-lab) */",
                ":where(.flow) { margin: 0; background: var(--fl-bg); color: var(--fl-ink); font-size: medium; line-height: normal;"),
              "`html, body {` -> `:where(.flow) {`, plus `font-size: medium; line-height: normal;`: Kyu's own\n"
              "composition of the flow with the hero (hero-stage/hero-lab/index.html:887-888 and its flow/flow.css:37).\n"
              "Verbatim the rule painted the whole page black (the FAQ shows the body's #080b0c) and squared the\n"
              "join's notches; and the steps were drawn on the browser's default font size and line height, not the\n"
              "site's 16px / 1.5 body.")
        p.sub('C2', '.js .fl-step', '.flow-on .fl-step',
              "`.js .fl-step` -> `.flow-on .fl-step` in every motion-state selector (8 here, 7 in stages/build.css): "
              "the checklist lines and the reply hide until they play only under flow/head.js's flow-on, which comes "
              "off when flow/flow.js fails to load or run, so the transcripts stay readable. section.html set html.js "
              "with an inline script, which a CSP refuses, by `className =`, which wiped the hero's classes.", count=8)
        p.sub('C2',
              L("/* ---------- motion states (JS only) ---------- */"),
              L("/* ---------- motion states (JS only) ---------- */",
                "/* PORT (C2): keyed on html.flow-on (flow/head.js), not html.js */"), lines=False)
        p.sub('C3',
              L(".fl-model::-webkit-scrollbar { display: none; }"),
              L(".fl-model::-webkit-scrollbar { display: none; }",
                "/* PORT (C3): without the flow (JavaScript off, flow/flow.js failed, a browser flow/head.js leaves off) the",
                "   terminal grows to the whole transcript: its box no longer clips a transcript taller than it with no",
                "   visible scroll (the model is not a scroller then, nor a Tab stop) */",
                "html:not(.flow-on) .fl-term { contain: none; }",
                "html:not(.flow-on) .fl-model { flex: none; overflow: visible; }"),
              "without flow-on (JavaScript off, flow/flow.js failed or gated off by flow/head.js) the terminal grows to\n"
              "its transcript: `html:not(.flow-on) .fl-term { contain: none }` and `.fl-model { flex: none; overflow:\n"
              "visible }`, after `.fl-model::-webkit-scrollbar`; under the phone and tablet widths' fixed heights (340px,\n"
              "300px, Build 324px) the same heights become min-heights (`height: auto; min-height: ...`, after each), so\n"
              "the box never shrinks. Upstream's box is sized for the animated terminal, which scrolls as it writes:\n"
              "with the whole static transcript in it, Build's reply sat below the box at 1024x768, Build's was cut on\n"
              "phones, and at 320 every step lost lines, in a box with its scrollbar hidden (and each one an unlabelled\n"
              "Tab stop). With flow-on nothing changes.")
        p.sub('C3',
              L("  .fl-term { height: 340px; }"),
              L("  .fl-term { height: 340px; }",
                "  html:not(.flow-on) .fl-term { height: auto; min-height: 340px; }   /* PORT (C3) */"))
        p.sub('C3',
              L("  .fl-term { height: 300px; border-radius: 16px; }",
                '  .fl-step[data-stage="build"] .fl-term { height: 324px; }'),
              L("  .fl-term { height: 300px; border-radius: 16px; }",
                '  .fl-step[data-stage="build"] .fl-term { height: 324px; }',
                "  html:not(.flow-on) .fl-term { min-height: 300px; }   /* PORT (C3) */",
                '  html:not(.flow-on) .fl-step[data-stage="build"] .fl-term { height: auto; min-height: 324px; }'))
    elif name == 'stages/start.css':
        p.sub('C4',
              L('.fl-step[data-stage="start"] .start-pill[data-cat]:focus-visible { outline: 2px solid currentColor; '
                'outline-offset: 2px; }'),
              L('.fl-step[data-stage="start"] .start-pill[data-cat]:focus-visible { outline: 2px solid currentColor; '
                'outline-offset: 2px; }',
                '/* PORT (C4): the selected pill\'s ring white like the others\' (its currentColor is its black text) */',
                '.fl-step[data-stage="start"] .start-pill.start-sel[data-cat]:focus-visible { outline-color: #fff; }'),
              "the selected pill's focus ring: upstream rings a focused pill in its currentColor, which on the\n"
              "selected one (white, black text) is black, drawn outside it on the black section, so focusing it showed\n"
              "nothing (0 px changed; it is the flow's first Tab stop). Added after it:\n"
              "`.start-pill.start-sel[data-cat]:focus-visible { outline-color: #fff }`, the colour every other pill's\n"
              "ring has. A change to Kyu's styling, for WCAG 2.4.7.")
    elif name == 'stages/build.css':
        p.sub('C2', '.js .fl-step', '.flow-on .fl-step',
              "the same, the 7 build-up and dimmed-line selectors of the list of changes.", count=7)
        p.sub('C2',
              L('.fl-step[data-stage="build"] .fl-box.is-loading .fl-prompt { animation: none; }'),
              L('.fl-step[data-stage="build"] .fl-box.is-loading .fl-prompt { animation: none; }',
                '/* PORT (C2): keyed on html.flow-on (flow/head.js), not html.js */'), lines=False)
    return p


HEAD_JS = L(
    "(function (d) {",
    "  'use strict';",
    "  // 1. the flow's JS-on hook, only where it can run: Web Animations with getAnimations(), matchMedia, and",
    "  //    constructable style sheets (stages/start.js's Reference PDP, its S7)",
    "  var ok = false;",
    "  try {",
    "    ok = typeof window.matchMedia === 'function' && 'animate' in Element.prototype && 'getAnimations' in Element.prototype &&",
    "      'adoptedStyleSheets' in Document.prototype && typeof CSSStyleSheet === 'function' && 'replaceSync' in CSSStyleSheet.prototype;",
    "  } catch (e) { ok = false; }",
    "  if (!ok) return;",
    "  d.classList.add('flow-on');",
    "  // the static transcripts back (flow-on off), unless the flow has reported ready (data-flow=\"on\" on the wrapper)",
    "  function off() {",
    "    var f = document.querySelector('.flow');",
    "    if (!d.classList.contains('flow-on') || (f && f.getAttribute('data-flow') === 'on')) return;",
    "    d.classList.remove('flow-on');",
    "    if (f) f.setAttribute('data-flow', 'off');",
    "  }",
    "  // 2. if flow/flow.js or flow/flow.css cannot load (404, network, CSP: 'error' on its <script data-flow-script>",
    "  // or <link data-flow-css>), or flow.js fails to parse or throws (an ErrorEvent naming that file). Capture",
    "  // phase, because an element's own 'error' does not bubble.",
    "  addEventListener('error', function (e) {",
    "    var t = e.target, s;",
    "    if (t && t.nodeType === 1) {",
    "      if (t.hasAttribute('data-flow-script') || t.hasAttribute('data-flow-css')) off();",
    "      return;",
    "    }",
    "    s = document.querySelector('script[data-flow-script]');",
    "    if (s && e.filename && e.filename === s.src) off();",
    "  }, true);",
    "  // 3. and if it has still not reported ready by the page's load event (which waits for async scripts): an error",
    "  // the listener cannot tie to the file, as a cross-origin script's without CORS (muted to 'Script error.', no",
    "  // file name), or a script that ran and did nothing. A task later, so flow.js's own load handler runs first.",
    "  addEventListener('load', function () {",
    "    setTimeout(function () { if (document.querySelector('script[data-flow-script]')) off(); }, 0);",
    "  });",
    "})(document.documentElement);")


def articles(section_html):
    """section.html's three steps (its lines 32-120), with the listed markup edits (Dux attributes on each article)."""
    lines = section_html.split('\n')
    try:
        a = lines.index('  <article class="fl-step" id="start" data-stage="start" data-prompt="load" aria-labelledby="start-h">')
        b = lines.index('</main>')
    except ValueError as e:
        die('section.html layout changed: %s' % e)
    if lines[a - 2] != '<main class="flow" aria-label="How mock.shop works">' or lines[a - 1] != '' or lines[b - 1] != '':
        die('section.html: the steps no longer sit alone in <main class="flow">')
    block = '\n'.join(lines[a:b - 1])
    out = block
    for step in ('start', 'build', 'test'):
        tag = '<article class="fl-step" id="%s" data-stage="%s" data-prompt="load" aria-labelledby="%s-h">' % (step, step, step)
        if out.count(tag) != 1:
            die('section.html: no single %s article tag' % step)
        out = out.replace(tag, tag[:-1] + ' data-section-name="%s" data-viewable-component>' % step)
    if out.count('<article ') != 3 or out.count('</article>') != 3 or ' style=' in out:
        die('section.html: the steps changed shape')
    return out


def flow_block(section_html):
    arts = articles(section_html)
    return ('  <link rel="stylesheet" href="flow/flow.css" data-flow-css>\n'
            '  <link href="%s" rel="stylesheet">\n'
            '  %s\n\n%s\n\n  </section>\n' % (FONTS_HREF, SECTION_OPEN, arts))


def check_index(html, section_html):
    """What index.html must have for the flow; returns a list of problems."""
    bad = []
    if html.count('<script src="flow/head.js"></script>') != 1 or \
            '<script src="hero/intro.js"></script>\n  <script src="flow/head.js"></script>\n' not in html:
        bad.append('<script src="flow/head.js"></script> once, on the line after hero/intro.js')
    if html.count(flow_block(section_html)) != 1:
        bad.append('the flow block (python3 tools/flow_port.py <lab> --print-markup) once, verbatim')
    if not html.rstrip().endswith('<script async src="flow/flow.js" data-flow-script></script>\n</body>\n</html>') or \
            html.count('flow/flow.js') != 1:
        bad.append('<script async src="flow/flow.js" data-flow-script></script> as the last element of <body>')
    if html.count('rel="modulepreload"') != 1:
        bad.append('no <link rel="modulepreload"> but three.js\'s (hero/intro.js takes the first one as three\'s URL)')
    return bad


# ---- putting it together -----------------------------------------------------------------------------------------
def build(src, commit):
    text = {k: src[k].decode('utf-8') for k in FIXED}
    for k in JS_PARTS:
        if not text[k].startswith('/* ') or not text[k].endswith('})();\n'):
            die('%s no longer starts with a comment and ends with its IIFE' % k)
    for k in CSS_PARTS:
        if not text[k].startswith('/* ') or not text[k].endswith('\n'):
            die('%s no longer starts with a comment' % k)
    ports = [port_flow_core(text['flow-core.js']), port_start(text['stages/start.js']), port_build(text['stages/build.js']),
             port_test(text['stages/test.js']), port_shell(text['flow.js'])]

    # ---- flow.js -------------------------------------------------------------------------------------------------
    lead = ['Upstream: %s, %s @ %s (Kyu Kim; round 23: Start, Build and Test, desktop and phone). This file = five '
            "of its scripts, verbatim but for the edits below, concatenated in section.html's load order (its lines "
            '123-128; glass.js left out: no element is glass in R23), each under a banner naming it:'
            % (UPSTREAM, LAB, commit)]
    lead += ['  %-16s sha256 %s' % (k, sha(src[k])) for k in JS_PARTS]
    lead += ['One classic script. index.html loads it last in <body>, <script async src="flow/flow.js" '
             "data-flow-script>: async, because a parser-blocking or deferred script holds DOMContentLoaded, which the "
             "hero's entrance waits for. flow/head.js (generated too) sets html.flow-on in <head>. The assets are under "
             'flow/assets/: the %d files the stages can ask for, byte for byte. tools/flow_port.py pins every upstream '
             'file it reads or copies.' % len(COPY),
             'Edits (upstream file, line: what and why):']
    tail = ["Verbatim otherwise: every stage, timing and easing, the four categories and the four themes, the "
            "transcripts (Start's other categories and Build's themes keep their prompts and replies in the code), "
            'Replay and Copy prompt, the 600px phone layouts, reduced motion (every step final, instant switches), the '
            'knobs (behind ?lab, F1: ?final=1 ?play= ?step= ?rm=1 ?speed= ?cat=), window.FLOW and window.__flow.']
    notes = comment_block('flow/flow.js -- GENERATED by tools/flow_port.py; do not edit (change the generator and rerun it).',
                          lead, [(k, p.entries()) for k, p in zip(JS_PARTS, ports)], tail)
    body, parts, line = [notes], [], notes.count('\n') + 1
    for k, p in zip(JS_PARTS, ports):
        banner = '\n/* ==== %s @ %s (sha256 %s): edits %s ==== */\n' % (
            k, commit, sha(src[k])[:16], ', '.join(eid for eid in p.notes))
        body.append(banner)
        line += banner.count('\n')
        parts.append((k, line, line + p.text.count('\n') - 1))
        body.append(p.text)
        line += p.text.count('\n')
    flow_js = ''.join(body)
    check_js('flow/flow.js', flow_js, parts)

    # ---- flow.css ------------------------------------------------------------------------------------------------
    cports = [port_css(k, text[k]) for k in CSS_PARTS]
    lead = ['Upstream: %s, %s @ %s (Kyu Kim; round 23). This file = its four stylesheets, verbatim but for the '
            "edits below, concatenated in section.html's order (its lines 11-14; glass.css left out: no element is "
            'glass in R23), each under a banner naming it:' % (UPSTREAM, LAB, commit)]
    lead += ['  %-16s sha256 %s' % (k, sha(src[k])) for k in CSS_PARTS]
    lead += ["index.html links it in <body>, just before the flow's section (in <head> it held up the hero's "
             "entrance), <link rel=\"stylesheet\" href=\"flow/flow.css\" data-flow-css>, then the flow's own Google "
             "Fonts link. Every rule is scoped to the flow's classes except its :root tokens (--fl-*, --ease-flow, "
             '--ease-emph, and the port\'s --flow-css), the *, *::before, *::after box-sizing (the page has the same '
             'rule) and its keyframes (fl-load, fl-blink, fl-fire, fl-up, fl-rot, fl-dot, fl-shim, build-up), none of '
             'whose names the page uses. No url(): the stages build their asset URLs in JS.',
             'Edits (upstream file, line: what and why):']
    trailer = [('C5', 'the last rule of this file',
                "`:root { --flow-css: 1; }`, after the four parts: flow/flow.js (its L5) enhances nothing until it reads "
                "this, so a stylesheet that is late, failed, or arrived cut short (the rule is last) never has the "
                "stages build into unstyled markup. Not from upstream.")]
    notes = comment_block('flow/flow.css -- GENERATED by tools/flow_port.py; do not edit (change the generator and rerun it).',
                          lead, [(k, p.entries()) for k, p in zip(CSS_PARTS, cports) if p.notes] +
                          [('the port\'s own, after the four parts:', trailer)], [])
    body = [notes]
    for k, p in zip(CSS_PARTS, cports):
        body.append('\n/* ==== %s @ %s (sha256 %s)%s ==== */\n' % (
            k, commit, sha(src[k])[:16], (': edits ' + ', '.join(p.notes)) if p.notes else ', verbatim'))
        body.append(p.text)
    body.append('\n/* ==== PORT (C5): the last rule; flow/flow.js (L5) waits for it ==== */\n'
                ':root { --flow-css: 1; }\n')
    flow_css = ''.join(body)
    check_css('flow/flow.css', flow_css)
    if not flow_css.endswith(':root { --flow-css: 1; }\n') or strip_css_comments(flow_css).count('--flow-css') != 1:
        die('flow/flow.css: the --flow-css sentinel (C5) must be its last rule, and set nowhere else')

    # ---- head.js -------------------------------------------------------------------------------------------------
    head_notes = comment_block(
        'flow/head.js -- GENERATED by tools/flow_port.py; do not edit (change the generator and rerun it).',
        ["Not from upstream. It replaces %s/section.html:7 @ %s, `<script>document.documentElement.className = "
         "'js';</script>`: an inline script (refused by a CSP without 'unsafe-inline') whose `className =` would also "
         "wipe hero/intro.js's classes on <html>. Classic and parser-blocking: index.html loads it in <head>, right "
         'after hero/intro.js, so html.flow-on is there before the first paint.' % (LAB, commit)],
        [(None, [('1', 'html.flow-on (classList)',
                  "the hook of flow/flow.css's motion states (its C2) and of flow/flow.js (its L1), set "
                  'only where the flow can run: Web Animations with getAnimations(), matchMedia, and constructable '
                  "style sheets (stages/start.js's S7). Elsewhere the flow stays off: the copy and the static "
                  'transcripts (prompt, checklist, reply) with an empty visual frame, as with JavaScript off.'),
                 ('2', 'the error listener',
                  'capture phase, on window: if flow/flow.js (the <script data-flow-script>) or flow/flow.css (the '
                  '<link data-flow-css>) fails to load (404, network, CSP), or flow.js fails to parse or throws, '
                  'before the flow reports ready (data-flow="on" on the wrapper: flow/flow.js L4), flow-on comes off '
                  'and the wrapper gets data-flow="off", so the transcripts show in full again. Errors with no file '
                  'name (a ResizeObserver note) or from other files are ignored, as is everything after ready (as '
                  "hero/intro.js's edit 6 does for the field)."),
                 ('3', 'the load backstop',
                  "the same, a task after the window's load event (which waits for async scripts, so flow.js has run "
                  'or failed by then), if the flow has still not reported ready: an error the listener cannot tie to '
                  'the file (a cross-origin flow.js without crossorigin="anonymous" throws as a muted "Script error." '
                  'with no file name), or a script that ran and did nothing. A task later, so a load handler of '
                  "flow.js's own (L5, waiting for its stylesheet) runs first. A flow.js that never answers holds the "
                  'load event, and the step lines stay hidden until the browser gives up on it.')])],
        [])
    head_js = head_notes + HEAD_JS
    check_js('flow/head.js', head_js)

    files = {'flow.js': flow_js.encode('utf-8'), 'flow.css': flow_css.encode('utf-8'), 'head.js': head_js.encode('utf-8')}
    for k in COPY:
        files[k] = src[k]
    files['assets.txt'] = ''.join(k + '\n' for k in COPY).encode('utf-8')
    files['markup.html'] = flow_block(text['section.html']).encode('utf-8')
    files['MANIFEST.sha256'] = manifest(files, src, commit)
    return files


def manifest(files, src, commit):
    """flow/MANIFEST.sha256: a header, then `<sha256>  flow/<path>` for every other file the port writes, sorted (the
    format `shasum -a 256 -c` reads; it skips the # lines)"""
    pin = sha(''.join('%s  %s\n' % (sha(src[k]), k) for k in sorted(src)).encode('utf-8'))
    head = ['flow/MANIFEST.sha256 -- GENERATED by tools/flow_port.py; do not edit (change the generator and rerun it).',
            'Each file it writes under flow/, by sha256, for a consumer that takes them without the lab (the Rails',
            "landing's re-sync); `shasum -a 256 -c flow/MANIFEST.sha256`, from the repository's root, checks them.",
            '"upstream" names the lab and its commit, "pin" the upstream files the port read (PIN): how many, and the',
            'sha256 of their `<sha256>  <path>` listing.',
            'upstream: %s %s @ %s' % (UPSTREAM, LAB, commit),
            'pin: %d files, %s' % (len(src), pin)]
    return (''.join('# %s\n' % line for line in head) +
            ''.join('%s  flow/%s\n' % (sha(files[k]), k) for k in sorted(files))).encode('utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('upstream', type=Path, help='project/flow-lab of richardli-design/mock-shop-lp')
    ap.add_argument('--commit', help='the upstream commit, needed when any upstream file differs from the pinned one')
    ap.add_argument('--check', action='store_true', help='compare with flow/ (and index.html) instead of writing; exit 1 '
                                                          'on a difference')
    ap.add_argument('--print-markup', action='store_true', help="print the flow block index.html must carry, and exit")
    ap.add_argument('--list-assets', action='store_true', help='print the asset keys (data-flow-assets), and exit')
    a = ap.parse_args()
    lab = a.upstream.resolve()
    src = read_sources(lab)
    got = {k: sha(v) for k, v in src.items()}
    changed = sorted(k for k in set(got) | set(PIN) if got.get(k) != PIN.get(k))
    if changed and not a.commit:
        die('%d upstream file(s) differ from the pinned %s:\n%s\nreview the change, then rerun with --commit <its commit>'
            % (len(changed), PIN_COMMIT, '\n'.join('  %s: %s, pinned %s' % (k, got.get(k, 'not read'),
                                                                          PIN.get(k, 'not pinned')) for k in changed)))
    commit = a.commit or PIN_COMMIT
    section_html = src['section.html'].decode('utf-8')
    if a.print_markup:
        sys.stdout.write(flow_block(section_html))
        return
    if a.list_assets:
        sys.stdout.write(''.join(k + '\n' for k in COPY))
        return
    files = build(src, commit)
    if changed:
        print('upstream at %s differs from the pin in %d file(s); once the port is reviewed, set PIN_COMMIT = %r and '
              'these PIN lines:' % (commit, len(changed), commit))
        for k in [x for x in FIXED] + COPY:
            print("    '%s': '%s'," % (k, got[k]))

    present = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()) if OUT.is_dir() else []
    stale = [k for k in present if k not in files]
    differ = [k for k in files if not (OUT / k).is_file() or (OUT / k).read_bytes() != files[k]]
    bad = check_index(INDEX.read_text(encoding='utf-8'), section_html) if INDEX.is_file() else ['index.html is missing']
    if a.check:
        for k in differ:
            print('differs: flow/' + k)
        for k in stale:
            print('not generated: flow/' + k)
        for b in bad:
            print('index.html needs ' + b)
        print('%d files, %d differ, %d stale; index.html %s' % (len(files), len(differ), len(stale),
                                                                'ok' if not bad else '%d problem(s)' % len(bad)))
        sys.exit(1 if differ or stale or bad else 0)
    for k in differ:
        (OUT / k).parent.mkdir(parents=True, exist_ok=True)
        (OUT / k).write_bytes(files[k])
    for k in stale:
        (OUT / k).unlink()
    for d in sorted({p for p in OUT.rglob('*') if p.is_dir()}, key=lambda p: -len(p.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    print('flow/: %d files (%d written, %d already identical), %d stale removed; upstream %s, %d assets'
          % (len(files), len(differ), len(files) - len(differ), len(stale), commit, len(COPY)))
    if bad:
        die('index.html needs:\n' + '\n'.join('  ' + b for b in bad))


if __name__ == '__main__':
    main()
