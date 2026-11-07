/**
 * Regression tests for the viewer's URL hash grammar.
 *
 *   node scripts/test_hash_routing.mjs
 *
 * The multi-pane redesign (issue #300) extended the hash from
 * `#project/model` to a `+`/`,` separated grammar. Every link already in the
 * wild — QR codes (`#project/model`), README gallery rows (`#project`), and
 * shared deep links — must keep parsing to exactly one pane with one model
 * and must round-trip byte-identically, otherwise arriving at a legacy URL
 * would rewrite the address bar and double-count Plausible hash pageviews.
 *
 * parseHash/formatHash are extracted straight out of index.html between the
 * __HASH_ROUTING_START__ / __HASH_ROUTING_END__ marker comments, so this
 * tests the shipped implementation rather than a copy of it.
 */

import { fileURLToPath } from 'url';
import path from 'path';
import { readFileSync } from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const indexHtml = path.join(__dirname, '..', 'index.html');

const START = '// __HASH_ROUTING_START__';
const END = '// __HASH_ROUTING_END__';

function extractRouting() {
  const html = readFileSync(indexHtml, 'utf8');
  const start = html.indexOf(START);
  const end = html.indexOf(END);
  if (start === -1 || end === -1 || end < start) {
    throw new Error(`Could not find ${START} / ${END} markers in index.html`);
  }
  return html.slice(start + START.length, end);
}

const { parseHash, formatHash } = new Function(
  extractRouting() + '; return { parseHash, formatHash };'
)();

let failures = 0;

function check(name, actual, expected) {
  const a = JSON.stringify(actual);
  const b = JSON.stringify(expected);
  if (a === b) {
    console.log(`  ok   ${name}`);
  } else {
    failures++;
    console.error(`  FAIL ${name}\n       expected: ${b}\n       actual:   ${a}`);
  }
}

console.log('Legacy link compatibility');

// QR codes and shared deep links: #<project-slug>/<model-slug>
check(
  "parseHash('vacuum-hose/adapter')",
  parseHash('vacuum-hose/adapter'),
  [[{ p: 'vacuum-hose', m: 'adapter' }]]
);
check(
  'single-model round-trip is byte-identical',
  formatHash(parseHash('vacuum-hose/adapter')),
  'vacuum-hose/adapter'
);

// Every README gallery row links to the project-only form.
check(
  "parseHash('toothbrush')",
  parseHash('toothbrush'),
  [[{ p: 'toothbrush', m: null }]]
);
check(
  'project-only round-trip is byte-identical',
  formatHash(parseHash('toothbrush')),
  'toothbrush'
);

// A model slug can itself contain hyphens and dots; only the FIRST slash
// separates project from model.
check(
  "parseHash('power-workshop/drill-bit')",
  parseHash('power-workshop/drill-bit'),
  [[{ p: 'power-workshop', m: 'drill-bit' }]]
);

console.log('Multi-pane grammar');

check(
  "parseHash('a/b+c/d') splits panes on '+'",
  parseHash('a/b+c/d'),
  [[{ p: 'a', m: 'b' }], [{ p: 'c', m: 'd' }]]
);
check(
  "parseHash('a/b,c/d') splits models on ','",
  parseHash('a/b,c/d'),
  [[{ p: 'a', m: 'b' }, { p: 'c', m: 'd' }]]
);
check(
  "parseHash('a/b,c/d+e/f') combines both",
  parseHash('a/b,c/d+e/f'),
  [[{ p: 'a', m: 'b' }, { p: 'c', m: 'd' }], [{ p: 'e', m: 'f' }]]
);
check(
  'multi-pane round-trip',
  formatHash(parseHash('a/b,c/d+e/f')),
  'a/b,c/d+e/f'
);
check(
  'formatHash drops empty panes',
  formatHash([[{ p: 'a', m: 'b' }], [], [{ p: 'c', m: 'd' }]]),
  'a/b+c/d'
);

console.log('Edge cases');

check("parseHash('') is null", parseHash(''), null);
check('parseHash(undefined) is null', parseHash(undefined), null);
check("parseHash('+') is null", parseHash('+'), null);

// Segments are decoded individually, after splitting — decoding the whole
// string first would let an encoded separator forge extra panes.
check(
  'percent-encoded segments decode',
  parseHash('my%20project/my%20part'),
  [[{ p: 'my project', m: 'my part' }]]
);
// URLSearchParams-style decoding would turn '+' into a space here.
check(
  "'+' is a separator, never a space",
  parseHash('a/b+c/d'),
  [[{ p: 'a', m: 'b' }], [{ p: 'c', m: 'd' }]]
);
check(
  "encoded '+' inside a segment stays literal",
  parseHash('a%2Bb/c'),
  [[{ p: 'a+b', m: 'c' }]]
);

if (failures) {
  console.error(`\n${failures} hash-routing assertion(s) failed`);
  process.exit(1);
}
console.log('\nAll hash-routing tests passed');
