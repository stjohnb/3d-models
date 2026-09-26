/**
 * Smoke tests for the in-browser openscad-wasm customizer rendering path.
 *
 * Run after fetch_openscad_wasm.py has populated site/openscad/:
 *   node scripts/test_wasm_customizer.mjs
 *
 * Tests:
 *   1. A fresh WASM instance can render a simple model to STL.
 *   2. A second fresh instance (from the same factory) also renders — regression
 *      test for the dead-instance bug where emscripten's exit() corrupts the
 *      module FS state, causing subsequent renders to silently fail.
 *   3. -D parameter injection produces the correct output geometry.
 */

import { fileURLToPath } from 'url';
import path from 'path';
import { existsSync, readFileSync } from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.join(__dirname, '..');
const openscadJs = path.join(repoRoot, 'site', 'openscad', 'openscad.js');

/**
 * Redirect local fetch() calls to fs.readFileSync.
 * Node's built-in fetch only handles http(s) URLs; openscad.js constructs
 * file:// URLs via import.meta.url for openscad.wasm.js and openscad.wasm,
 * which native Node fetch rejects. We also handle bare relative filenames.
 */
function installNodeFetchPolyfill(baseDir) {
  const original = globalThis.fetch;
  globalThis.fetch = async function nodeFileFetch(resource, init) {
    const url = typeof resource === 'string' ? resource : resource?.url ?? String(resource);

    let filePath = null;
    if (url.startsWith('file://')) {
      try {
        filePath = fileURLToPath(url);
      } catch {
        // malformed file URL — fall through to original fetch
      }
    } else if (!url.startsWith('http://') && !url.startsWith('https://') && !url.startsWith('//')) {
      filePath = path.resolve(baseDir, url);
    }

    if (filePath !== null) {
      let data;
      try {
        data = readFileSync(filePath);
      } catch {
        if (original) return original(resource, init);
        throw new Error(`File not found: ${filePath}`);
      }
      const buf = data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength);
      const contentType = filePath.endsWith('.wasm') ? 'application/wasm' : 'application/octet-stream';
      return new Response(buf, {
        status: 200,
        statusText: 'OK',
        headers: { 'Content-Type': contentType },
      });
    }
    if (original) return original(resource, init);
    throw new TypeError(`fetch is not defined — cannot fetch ${url}`);
  };
}

// A minimal SCAD model parameterised by `size`.
const SCAD_CUBE = 'cube([size, size, size]);\n';

let passed = 0;
let failed = 0;

function ok(label) {
  console.log(`  PASS: ${label}`);
  passed++;
}

function fail(label, err) {
  console.error(`  FAIL: ${label} — ${err.message || err}`);
  failed++;
}

/**
 * Run one render on a fresh WASM instance and return the STL bytes.
 * Mirrors the runRender() logic in index.html.
 */
async function render(factory, scadSource, defines = {}) {
  const instance = await factory();

  instance.FS.mkdir('/work');
  instance.FS.writeFile('/work/model.scad', scadSource);

  const args = [];
  for (const [k, v] of Object.entries(defines)) {
    args.push('-D', `${k}=${typeof v === 'boolean' ? (v ? 'true' : 'false') : String(v)}`);
  }
  args.push('-o', '/work/out.stl', '/work/model.scad');

  try {
    instance.callMain(args);
  } catch (ex) {
    if (ex?.name !== 'ExitStatus') throw ex;
    // emscripten exits via ExitStatus throw — fall through and check output
  }

  let stlBytes;
  try {
    stlBytes = instance.FS.readFile('/work/out.stl');
  } catch (_) {
    throw new Error('Output file not found in WASM FS after render');
  }

  if (!stlBytes || stlBytes.length === 0) {
    throw new Error('Output STL is empty');
  }

  return stlBytes;
}

async function main() {
  console.log('openscad-wasm customizer smoke tests');
  console.log(`  openscad.js: ${openscadJs}`);

  if (!existsSync(openscadJs)) {
    console.log('  SKIP: site/openscad/openscad.js not found — run fetch_openscad_wasm.py first');
    process.exit(0);
  }

  // Redirect bare-filename fetch() calls (e.g. 'openscad.wasm') to the
  // filesystem so tests run without a browser or HTTP server.
  installNodeFetchPolyfill(path.dirname(openscadJs));

  let factory;
  try {
    const mod = await import(openscadJs);
    factory = mod.default;
    if (typeof factory !== 'function') throw new Error('default export is not a function');
  } catch (err) {
    // openscad.js may use browser-only APIs not available in this Node version.
    console.log(`  SKIP: could not load openscad.js in Node.js — ${err.message}`);
    process.exit(0);
  }

  // Test 1: basic render
  try {
    const stl = await render(factory, `size = 10;\n${SCAD_CUBE}`);
    ok(`basic render (${stl.length} bytes)`);
  } catch (err) {
    fail('basic render', err);
  }

  // Test 2: second render from same factory (regression for dead-instance bug)
  try {
    const stl = await render(factory, `size = 20;\n${SCAD_CUBE}`);
    ok(`second render — fresh instance reuse (${stl.length} bytes)`);
  } catch (err) {
    fail('second render — fresh instance reuse', err);
  }

  // Test 3: -D parameter injection overrides in-file default
  try {
    // File says size=5 but -D overrides to 30; resulting mesh must differ from
    // a size-5 cube (we just check the bytes differ, not exact geometry).
    const stlSmall = await render(factory, `size = 5;\n${SCAD_CUBE}`);
    const stlLarge = await render(factory, `size = 5;\n${SCAD_CUBE}`, { size: 30 });
    if (stlSmall.length === stlLarge.length) {
      throw new Error('-D size=30 produced same byte count as size=5 — injection may have failed');
    }
    ok(`-D parameter injection (${stlSmall.length}B vs ${stlLarge.length}B)`);
  } catch (err) {
    fail('-D parameter injection', err);
  }

  // Test 4: boolean -D formatting (true/false not True/False)
  try {
    // OpenSCAD rejects Python-style True/False — if serialisation is wrong the
    // render will fail. Use a parameter that controls wall thickness so the
    // model is always non-empty regardless of the boolean value.
    const stl = await render(
      factory,
      'tall = true;\nwall = tall ? 10 : 3;\ncube([5, 5, wall]);\n',
      { tall: false },
    );
    ok(`boolean -D serialisation (${stl.length} bytes)`);
  } catch (err) {
    fail('boolean -D serialisation', err);
  }

  console.log('');
  if (failed > 0) {
    console.error(`${failed} test(s) failed, ${passed} passed`);
    process.exit(1);
  }
  console.log(`${passed} test(s) passed`);
}

main().catch(err => {
  console.error('Unexpected error:', err);
  process.exit(1);
});
