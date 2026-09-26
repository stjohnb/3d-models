/**
 * Regression tests for the viewer's history-write decision.
 *
 *   node scripts/test_hash_history.mjs
 *
 * Every JS-driven route change (tree click, add-to-scene, remove chip, layout
 * change, "All models") used to call `history.replaceState()`, which never
 * creates a new session-history entry — Back left the site entirely and
 * Forward was dead (issue #383). `hashWriteMode()` decides whether a freshly
 * computed hash should push a new entry, replace the current one, or be
 * skipped entirely, and is what `updateHash()` now defers to.
 *
 * hashWriteMode is extracted straight out of index.html between the
 * __HASH_WRITE_START__ / __HASH_WRITE_END__ marker comments, so this tests
 * the shipped implementation rather than a copy of it.
 */

import { fileURLToPath } from 'url';
import path from 'path';
import { readFileSync } from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const indexHtml = path.join(__dirname, '..', 'index.html');

const START = '// __HASH_WRITE_START__';
const END = '// __HASH_WRITE_END__';

function extractHashWrite() {
  const html = readFileSync(indexHtml, 'utf8');
  const start = html.indexOf(START);
  const end = html.indexOf(END);
  if (start === -1 || end === -1 || end < start) {
    throw new Error(`Could not find ${START} / ${END} markers in index.html`);
  }
  return html.slice(start + START.length, end);
}

const { hashWriteMode } = new Function(
  extractHashWrite() + '; return { hashWriteMode };'
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

console.log('Route changes push a history entry');

// First tree click from the gallery creates an entry.
check(
  "hashWriteMode('toothbrush/backplate', '', false)",
  hashWriteMode('toothbrush/backplate', '', false),
  'push'
);

// "All models" is Back-able.
check(
  "hashWriteMode('', 'toothbrush/backplate', false)",
  hashWriteMode('', 'toothbrush/backplate', false),
  'push'
);

// Add-to-scene creates an entry.
check(
  "hashWriteMode('a+b', 'a', false)",
  hashWriteMode('a+b', 'a', false),
  'push'
);

console.log('No-op route changes add no entry');

// A layout change that doesn't alter the route adds no entry.
check(
  "hashWriteMode('a', 'a', false)",
  hashWriteMode('a', 'a', false),
  'skip'
);

// Clearing an already-empty stage adds no entry.
check(
  "hashWriteMode('', '', false)",
  hashWriteMode('', '', false),
  'skip'
);

// Skip wins over replace.
check(
  "hashWriteMode('a', 'a', true)",
  hashWriteMode('a', 'a', true),
  'skip'
);

console.log('PR-preview autoload replaces, never pushes');

check(
  "hashWriteMode('vacuum-hose/adapter', '', true)",
  hashWriteMode('vacuum-hose/adapter', '', true),
  'replace'
);

if (failures) {
  console.error(`\n${failures} hash-history assertion(s) failed`);
  process.exit(1);
}
console.log('\nAll hash-history tests passed');
