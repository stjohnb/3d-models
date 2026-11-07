// openscad-wasm render worker.
//
// Runs every customizer render off the main thread so slider clicks and
// page interactions stay responsive while CGAL is grinding. Receives a
// {sources, entry, params, projectDir} message, writes the project files
// into the wasm FS, calls openscad with -D overrides, and posts the STL
// bytes back as a transferable Uint8Array.
//
// A fresh wasm instance is built per render (the factory is cached). This
// mirrors the in-page strategy that predated the worker: emscripten's
// non-threaded build calls exit() at the end of callMain, which can leave
// the module's internal FS state invalid — reusing one instance produced
// silent "empty STL" failures on the second render.

// Cache-busting hash injected at build time (matches index.html).
const BUILD_HASH = '__BUILD_HASH__';
const cacheBust = BUILD_HASH.startsWith('__') ? '' : `?v=${BUILD_HASH}`;

let _factory = null;
async function getFactory() {
  if (!_factory) {
    _factory = (async () => {
      const mod = await import(`./openscad/openscad.js${cacheBust}`);
      const factory = mod.default;
      if (typeof factory !== 'function') {
        throw new Error('openscad.js did not expose a factory');
      }
      return factory;
    })();
    _factory.catch(() => { _factory = null; });
  }
  return _factory;
}

// Manifest names are project-relative and may climb into another project
// (`../drawer-organiser/_drawer_organiser.scad`) when a renderable includes a
// shared library across projects. Resolve `.`/`..` segments lexically against
// workDir and refuse anything that leaves /customizer/.
function resolveSourcePath(workDir, name) {
  const parts = [];
  for (const seg of `${workDir}/${name}`.split('/')) {
    if (seg === '' || seg === '.') continue;
    if (seg === '..') parts.pop();
    else parts.push(seg);
  }
  if (parts[0] !== 'customizer' || parts.length < 2) {
    throw new Error(`source path escapes /customizer/: ${name}`);
  }
  return `/${parts.join('/')}`;
}

// FS.writeFile does not create parent directories.
function writeNested(FS, filePath, data) {
  let dir = '';
  for (const seg of filePath.split('/').slice(1, -1)) {
    dir += `/${seg}`;
    if (!FS.analyzePath(dir).exists) FS.mkdir(dir);
  }
  FS.writeFile(filePath, data);
}

async function render({ sources, entry, params, projectDir }) {
  const factory = await getFactory();
  const instance = await factory();

  instance.FS.mkdir('/customizer');
  const workDir = `/customizer/${projectDir}`;
  instance.FS.mkdir(workDir);
  for (const [name, text] of sources) {
    writeNested(instance.FS, resolveSourcePath(workDir, name), text);
  }

  const outPath = `${workDir}/out.stl`;
  const args = [];
  for (const [k, v] of Object.entries(params)) {
    args.push('-D', `${k}=${typeof v === 'boolean' ? (v ? 'true' : 'false') : String(v)}`);
  }
  args.push('-o', outPath, `${workDir}/${entry}`);

  try {
    instance.callMain(args);
  } catch (ex) {
    if (ex?.name !== 'ExitStatus') throw ex;
    // emscripten exits via ExitStatus throw — fall through and check output
  }

  let raw;
  try {
    raw = instance.FS.readFile(outPath);
  } catch (_) {
    throw new Error('OpenSCAD render failed (no output file)');
  }
  if (!raw || raw.length === 0) {
    throw new Error('OpenSCAD render failed (empty output)');
  }

  // Copy into a fresh Uint8Array so the transfer can detach the buffer
  // without touching memory the wasm instance may still reference.
  const stl = new Uint8Array(raw.length);
  stl.set(raw);
  return stl;
}

self.addEventListener('message', async (event) => {
  const { id } = event.data;
  try {
    const stl = await render(event.data);
    self.postMessage({ id, stl }, [stl.buffer]);
  } catch (err) {
    self.postMessage({ id, error: String(err?.message || err) });
  }
});
