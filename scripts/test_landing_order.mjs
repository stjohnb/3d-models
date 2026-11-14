/**
 * Regression tests for the landing gallery's project ordering.
 *
 *   node scripts/test_landing_order.mjs
 *
 * The landing page (issue #345) puts "interesting & recent" projects above
 * "simple & old" ones. The ranking is pure arithmetic over models.json fields,
 * so it is worth pinning: a scoring change that silently flattened the order
 * would leave the grid looking fine while burying the newest work.
 *
 * interestScore/recencyScore/landingOrder are extracted straight out of
 * index.html between the __LANDING_ORDER_START__ / __LANDING_ORDER_END__
 * marker comments, so this tests the shipped implementation rather than a
 * copy of it.
 */

import { fileURLToPath } from 'url';
import path from 'path';
import { readFileSync } from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const indexHtml = path.join(__dirname, '..', 'index.html');

const START = '// __LANDING_ORDER_START__';
const END = '// __LANDING_ORDER_END__';

function extractOrdering() {
  const html = readFileSync(indexHtml, 'utf8');
  const start = html.indexOf(START);
  const end = html.indexOf(END);
  if (start === -1 || end === -1 || end < start) {
    throw new Error(`Could not find ${START} / ${END} markers in index.html`);
  }
  return html.slice(start + START.length, end);
}

const { interestScore, recencyScore, landingOrder } = new Function(
  extractOrdering() + '; return { interestScore, recencyScore, landingOrder };'
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

// A fixed "now" so the recency buckets are deterministic.
const NOW = Date.parse('2026-07-30T00:00:00Z');
const daysAgo = (n) => new Date(NOW - n * 86400000).toISOString();

const BIG = {
  files: Array.from({ length: 14 }, (_, i) => ({ stl: `p${i}.stl` })).map(
    (f, i) => (i === 0 ? { ...f, parameters: { parameters: [] } } : f)
  ),
  difficulty: 'intermediate',
};
const SMALL = { files: [{ stl: 'only.stl' }], difficulty: 'beginner' };

console.log('interestScore');

check('14 files + intermediate + a parameter manifest', interestScore(BIG), 4);
check('single beginner model with no extras', interestScore(SMALL), 0);
check('empty project', interestScore({}), 0);
check(
  'advanced assembly with hardware maxes out',
  interestScore({
    files: [
      { stl: 'a.stl', parameters: {} }, { stl: 'b.stl' },
      { stl: 'c.stl' }, { stl: 'd.stl' },
    ],
    difficulty: 'advanced',
    assembly: { stl: 'a.stl', parts: [] },
    hardware: [{ item: 'M5 bolt', quantity: 1 }],
  }),
  7
);

console.log('recencyScore');

check('30 days old', recencyScore({ updated: daysAgo(30) }, NOW), 2);
check('200 days old', recencyScore({ updated: daysAgo(200) }, NOW), 1);
check('900 days old', recencyScore({ updated: daysAgo(900) }, NOW), 0);
check('missing updated', recencyScore({}, NOW), 0);
check('unparseable updated', recencyScore({ updated: 'whenever' }, NOW), 0);

console.log('landingOrder');

check(
  'high-score project sorts first',
  landingOrder({ Small: SMALL, Big: BIG }, NOW).map(e => e.name),
  ['Big', 'Small']
);

// Two identically-scored projects: the more recently touched one wins.
const tieA = { files: [{ stl: 'a.stl' }], updated: daysAgo(10) };
const tieB = { files: [{ stl: 'b.stl' }], updated: daysAgo(60) };
check(
  'equal scores break on updated, newest first',
  landingOrder({ Older: tieB, Newer: tieA }, NOW).map(e => e.name),
  ['Newer', 'Older']
);

// Equal score AND equal date: fall back to a stable alphabetical order.
check(
  'equal scores and dates break on name',
  landingOrder(
    {
      Zeta: { files: [{ stl: 'z.stl' }], updated: daysAgo(10) },
      Alpha: { files: [{ stl: 'a.stl' }], updated: daysAgo(10) },
    },
    NOW
  ).map(e => e.name),
  ['Alpha', 'Zeta']
);

check(
  'every project is present exactly once',
  landingOrder({ A: SMALL, B: BIG, C: {} }, NOW).length,
  3
);

if (failures) {
  console.error(`\n${failures} landing-order assertion(s) failed`);
  process.exit(1);
}
console.log('\nAll landing-order tests passed');
