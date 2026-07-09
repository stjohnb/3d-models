#!/usr/bin/env python3
"""Generate self-contained single-file HTML viewers for each STL model.

Reads site/.scad-map, downloads Three.js once, then writes
site/standalone/<name>.html per model with all JS and STL data inlined.
No external dependencies — works from file:// or any static host.
"""

import base64
import hashlib
import html as html_mod
import json
import os
import re
import sys
import urllib.request

from oembed_helpers import display_name, load_meta_failures, public_source_url

# Three.js version — must match index.html importmap
THREEJS_VERSION = "0.170.0"

THREEJS_ASSETS = {
    "three": {
        "url": f"https://cdn.jsdelivr.net/npm/three@{THREEJS_VERSION}/build/three.module.min.js",
        "sha256": "08fd7545d13d2c7fb65ab691530a802dafefd638596501854f267d0fb13c39e7",
    },
    "STLLoader": {
        "url": f"https://cdn.jsdelivr.net/npm/three@{THREEJS_VERSION}/examples/jsm/loaders/STLLoader.js",
        "sha256": "a0a83c88b269c94e25b690fae770d350c4728c81853195186976be7af0f8a3b3",
    },
    "OrbitControls": {
        "url": f"https://cdn.jsdelivr.net/npm/three@{THREEJS_VERSION}/examples/jsm/controls/OrbitControls.js",
        "sha256": "80efaadea4f8a636a65fb0bd08bfef62f3d93a0bb94e2e7500f23176c5c07f4e",
    },
    "TrackballControls": {
        "url": f"https://cdn.jsdelivr.net/npm/three@{THREEJS_VERSION}/examples/jsm/controls/TrackballControls.js",
        "sha256": "5ec947668c3744d7852d06519c34270acb588a4b2bf56a0bf01cedae7ce0e931",
    },
    "ArcballControls": {
        "url": f"https://cdn.jsdelivr.net/npm/three@{THREEJS_VERSION}/examples/jsm/controls/ArcballControls.js",
        "sha256": "819adb7b1f41e5fea6114a5d87e8dfd01525acb229a797f7be0b32c0af9a21d0",
    },
}

FILAMENT_COLORS_JSON = "filament-colors.json"
SCAD_MAP = "site/.scad-map"
OUTPUT_DIR = "site/standalone"
CACHE_DIR = ".cache/threejs"


def _cache_path(url: str) -> str:
    """Return a deterministic local cache path for a URL."""
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    basename = url.rsplit("/", 1)[-1]
    return os.path.join(CACHE_DIR, f"{url_hash}_{basename}")


def fetch_url(url: str, expected_sha256: str | None = None) -> bytes:
    """Download a URL with a single retry, SHA-256 verification, and local cache fallback."""
    cache_file = _cache_path(url)

    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
        except Exception as e:
            if attempt == 0:
                print(f"  Retry {url}: {e}")
                continue
            # Both attempts failed — try cache fallback
            if os.path.isfile(cache_file):
                print(f"  CDN unreachable, using cached copy: {cache_file}")
                with open(cache_file, "rb") as f:
                    data = f.read()
                # Still verify the cached data
                if expected_sha256:
                    actual = hashlib.sha256(data).hexdigest()
                    if actual != expected_sha256:
                        raise ValueError(
                            f"Cached file SHA-256 mismatch for {url}\n"
                            f"  expected: {expected_sha256}\n"
                            f"  got:      {actual}"
                        )
                return data
            raise
        if expected_sha256:
            actual = hashlib.sha256(data).hexdigest()
            if actual != expected_sha256:
                raise ValueError(
                    f"SHA-256 mismatch for {url}\n"
                    f"  expected: {expected_sha256}\n"
                    f"  got:      {actual}"
                )
        # Cache the verified data for future runs
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, "wb") as f:
            f.write(data)
        return data
    raise RuntimeError(f"Failed to fetch {url}")


def b64_data_uri(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def _js_escape(s: str) -> str:
    """Escape <, >, & so a JSON literal can't break out of a <script> block."""
    return s.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def _composite_parts_js(parts) -> str:
    """Serialise composite parts (list of {"stl_b64", "color"}) to a safe JS literal."""
    return _js_escape(json.dumps(parts))


def _source_link_html(source):
    """Return an <a> tag linking to the public source, or '' when unknown.

    The URL is percent-encoded per path segment by public_source_url(); the
    result is additionally HTML-escaped (quote=True) before interpolation.
    """
    url = public_source_url(source)
    if not url:
        return ""
    return (
        f'<a href="{html_mod.escape(url, quote=True)}" target="_blank" '
        f'rel="noopener noreferrer">View OpenSCAD source on GitHub</a>'
    )


def strip_stl_ext(filename: str) -> str:
    """Remove .stl extension case-insensitively."""
    if filename.lower().endswith(".stl"):
        return filename[:-4]
    return filename


def _load_filament_colors_js() -> str:
    """Read filament-colors.json and return a JS array literal for the template."""
    with open(FILAMENT_COLORS_JSON) as f:
        colors = json.load(f)
    entries = []
    for c in colors:
        hex_val = c['hex']
        if not re.fullmatch(r'[0-9a-fA-F]{6}', hex_val):
            raise ValueError(
                f"Invalid hex value {hex_val!r} in {FILAMENT_COLORS_JSON} "
                f"(color: {c['name']!r}). Must be exactly 6 hex characters."
            )
        name = c['name']
        if any(ord(ch) < 0x20 for ch in name):
            raise ValueError(
                f"Invalid name {name!r} in {FILAMENT_COLORS_JSON}: "
                "names must not contain control characters."
            )
        safe_name = (
            json.dumps(name)
            .replace('<', '\\u003c')
            .replace('>', '\\u003e')
            .replace('&', '\\u0026')
        )
        entries.append(f"      {{ name: {safe_name}, hex: 0x{hex_val} }}")
    return "[\n" + ",\n".join(entries) + ",\n    ]"


HTML_TEMPLATE = """\
<!DOCTYPE html>
<!-- Generated by github.com/stjohnb/3d-models CI -->
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #1a1a2e;
      color: #e0e0e0;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    header {{
      text-align: center;
      padding: 1rem;
      flex-shrink: 0;
    }}
    header h1 {{
      font-size: 1.5rem;
      font-weight: 600;
    }}
    #viewer {{
      flex: 1;
      min-height: 0;
    }}
    canvas {{
      display: block;
      width: 100%;
      height: 100%;
      cursor: grab;
    }}
    canvas:active {{ cursor: grabbing; }}
    .controls {{
      display: flex;
      gap: 0.5rem;
      padding: 0.5rem 1rem;
      flex-wrap: wrap;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .color-swatch {{
      width: 24px;
      height: 24px;
      border-radius: 50%;
      border: 2px solid rgba(255,255,255,0.15);
      cursor: pointer;
      padding: 0;
      flex-shrink: 0;
    }}
    .color-swatch[aria-pressed="true"] {{ border-color: #fff; }}
    .color-swatch:hover {{ border-color: rgba(255,255,255,0.6); }}
    .fullscreen-btn {{
      position: fixed;
      top: 0.5rem;
      right: 0.5rem;
      background: rgba(0,0,0,0.4);
      border: none;
      color: #e0e0e0;
      font-size: 1.2rem;
      width: 2rem;
      height: 2rem;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1;
    }}
    .fullscreen-btn:hover {{ background: rgba(0,0,0,0.6); }}
    footer {{
      text-align: center;
      padding: 0.5rem;
      font-size: 0.8rem;
      flex-shrink: 0;
    }}
    footer a {{ color: #64b5f6; text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}
    footer a + a {{ margin-left: 1rem; }}
    .noscript {{
      text-align: center;
      padding: 4rem 2rem;
      font-size: 1.2rem;
      color: #888;
    }}
    .cross-section-row {{
      display: flex;
      align-items: center;
      gap: 6px;
      justify-content: center;
      margin-top: 4px;
      flex-wrap: nowrap;
    }}
    .cross-btn {{
      background: rgba(255,255,255,0.1);
      border: none;
      border-radius: 4px;
      color: #e0e0e0;
      cursor: pointer;
      padding: 4px 8px;
      font-size: 13px;
      white-space: nowrap;
      font-family: inherit;
    }}
    .cross-btn:hover {{ background: rgba(255,255,255,0.2); }}
    .cross-btn:focus-visible {{ outline: 2px solid #64b5f6; outline-offset: 2px; }}
    .cross-btn[aria-pressed="true"] {{
      background: rgba(100, 181, 246, 0.3);
      color: #64b5f6;
    }}
    .clip-slider {{
      flex: 1;
      max-width: 200px;
      accent-color: #64b5f6;
    }}
    .view-controls-row {{
      display: flex;
      align-items: center;
      gap: 6px;
      justify-content: center;
      margin-top: 4px;
      flex-wrap: wrap;
    }}
    .view-btn {{
      background: rgba(255,255,255,0.1);
      border: none;
      border-radius: 4px;
      color: #e0e0e0;
      cursor: pointer;
      padding: 4px 8px;
      font-size: 13px;
      white-space: nowrap;
      font-family: inherit;
    }}
    .view-btn:hover {{ background: rgba(255,255,255,0.2); }}
    .view-btn:disabled {{ opacity: 0.4; cursor: default; }}
    .view-btn:focus-visible {{ outline: 2px solid #64b5f6; outline-offset: 2px; }}
    .view-btn[aria-pressed="true"] {{ background: rgba(100,181,246,0.3); color: #64b5f6; }}
  </style>
</head>
<body>
  <header><h1>{title}</h1></header>
  <div id="viewer">
    <noscript>
      <div class="noscript">This viewer requires a modern browser with JavaScript module support.</div>
    </noscript>
  </div>
  <div class="controls" id="colors"></div>
  <div class="cross-section-row">
    <button class="cross-btn" id="cross-btn" aria-label="Toggle cross section" aria-pressed="false">&#x2702; Cross Section</button>
    <input type="range" class="clip-slider" id="clip-slider" min="0" max="100" value="50" style="display:none;" aria-label="Cross section depth">
  </div>
  <div class="view-controls-row">
    <button class="view-btn" id="rot-x" aria-label="Rotate model 90 degrees about the X axis">Rotate X</button>
    <button class="view-btn" id="rot-y" aria-label="Rotate model 90 degrees about the Y axis">Rotate Y</button>
    <button class="view-btn" id="rot-z" aria-label="Rotate model 90 degrees about the Z axis">Rotate Z</button>
    <button class="view-btn" id="reset-view" aria-label="Reset view orientation and camera">Reset</button>
    <button class="view-btn mode-btn" id="mode-orbit" aria-label="Use Orbit controls" aria-pressed="true">Orbit</button>
    <button class="view-btn mode-btn" id="mode-trackball" aria-label="Use Trackball controls" aria-pressed="false">Trackball</button>
    <button class="view-btn mode-btn" id="mode-arcball" aria-label="Use Arcball controls" aria-pressed="false">Arcball</button>
  </div>
  <button class="fullscreen-btn" id="fs-btn" aria-label="Toggle fullscreen">&#x26F6;</button>
  <footer>
    <a href="https://www.bstjohn.net/3d-models/">View all models at bstjohn.net</a>
    {source_link_html}
  </footer>

  <script type="importmap">
  {{
    "imports": {{
      "three": "{three_uri}",
      "three/addons/loaders/STLLoader.js": "{stlloader_uri}",
      "three/addons/controls/OrbitControls.js": "{orbitcontrols_uri}",
      "three/addons/controls/TrackballControls.js": "{trackballcontrols_uri}",
      "three/addons/controls/ArcballControls.js": "{arcballcontrols_uri}"
    }}
  }}
  </script>
  <script type="module">
    import * as THREE from 'three';
    import {{ STLLoader }} from 'three/addons/loaders/STLLoader.js';
    import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
    import {{ TrackballControls }} from 'three/addons/controls/TrackballControls.js';
    import {{ ArcballControls }} from 'three/addons/controls/ArcballControls.js';

    const STL_BASE64 = "{stl_base64}";

    // Non-empty only for a coloured multi-part composite (issue #275): each
    // entry is {{ stl_b64, color }}. When empty, the single STL_BASE64 loads.
    const COMPOSITE_PARTS = {composite_parts_js};

    const FILAMENT_COLORS = {filament_colors_js};

    const container = document.getElementById('viewer');
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);

    const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true }});
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.localClippingEnabled = true;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f3460);

    const camera = new THREE.PerspectiveCamera(45, canvas.clientWidth / canvas.clientHeight, 0.1, 10000);

    // Reassignable so the user can switch between Orbit / Trackball /
    // Arcball at runtime (issue #230). Preserve target across switches.
    let controls = null;
    let controlMode = 'orbit';
    function makeControls(mode) {{
      const saved = controls ? controls.target.clone() : new THREE.Vector3();
      if (controls) controls.dispose();
      if (mode === 'trackball') {{
        controls = new TrackballControls(camera, canvas);
        controls.handleResize();
      }} else if (mode === 'arcball') {{
        controls = new ArcballControls(camera, canvas, scene);
        controls.setGizmosVisible(false);
      }} else {{
        controls = new OrbitControls(camera, canvas);
        controls.enableDamping = true;
      }}
      controls.target.copy(saved);
      controls.update();
      controlMode = mode;
    }}
    makeControls('orbit');

    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(1, 2, 3);
    scene.add(dirLight);
    const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
    dirLight2.position.set(-2, -1, -1);
    scene.add(dirLight2);

    const material = new THREE.MeshPhongMaterial({{
      color: 0x64b5f6,
      specular: 0x222222,
      shininess: 40,
      clippingPlanes: [],
      clipShadows: false,
    }});

    // displayObject is the Mesh (single model) or Group (composite) the view
    // controls rotate/reset. clipMaterials are the materials the cross-section
    // toggles. clipBounds is mutable: rotating changes the world-space Y extent.
    let displayObject;
    let defaultCamPos;
    let clipBounds;
    const clipMaterials = [];

    function b64ToGeometry(b64) {{
      const binary = atob(b64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      return new STLLoader().parse(bytes.buffer);
    }}

    if (COMPOSITE_PARTS.length) {{
      // Coloured multi-part composite: each already-co-registered part STL as
      // its own mesh/material in one Group (issue #275).
      const geometries = COMPOSITE_PARTS.map(p => b64ToGeometry(p.stl_b64));
      const union = new THREE.Box3();
      for (const g of geometries) {{
        g.computeBoundingBox();
        union.union(g.boundingBox);
      }}
      const center = new THREE.Vector3();
      union.getCenter(center);

      const group = new THREE.Group();
      geometries.forEach((geometry, i) => {{
        geometry.translate(-center.x, -center.y, -center.z);
        const mat = new THREE.MeshPhongMaterial({{
          color: COMPOSITE_PARTS[i].color,
          specular: 0x222222,
          shininess: 40,
          clippingPlanes: [],
          clipShadows: false,
        }});
        group.add(new THREE.Mesh(geometry, mat));
        clipMaterials.push(mat);
      }});
      scene.add(group);
      displayObject = group;

      const size = new THREE.Vector3();
      union.getSize(size);
      clipBounds = {{ minY: -size.y / 2, maxY: size.y / 2 }};
      const maxDim = Math.max(size.x, size.y, size.z);
      const dist = maxDim * 1.8;
      camera.position.set(dist * 0.6, dist * 0.5, dist * 0.8);
      defaultCamPos = camera.position.clone();
      controls.update();
    }} else {{
      // Decode STL from base64
      const geometry = b64ToGeometry(STL_BASE64);
      geometry.computeBoundingBox();
      const clipHalfSizeY = (geometry.boundingBox.max.y - geometry.boundingBox.min.y) / 2;
      clipBounds = {{ minY: -clipHalfSizeY, maxY: clipHalfSizeY }};
      geometry.center();

      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);
      displayObject = mesh;
      clipMaterials.push(material);

      const size = new THREE.Vector3();
      geometry.boundingBox.getSize(size);
      const maxDim = Math.max(size.x, size.y, size.z);
      const dist = maxDim * 1.8;
      camera.position.set(dist * 0.6, dist * 0.5, dist * 0.8);
      defaultCamPos = camera.position.clone();
      controls.update();
    }}

    function resize() {{
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (canvas.width !== w || canvas.height !== h) {{
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        controls.handleResize?.();
      }}
    }}

    let animating = true;
    function animate() {{
      if (!animating) return;
      requestAnimationFrame(animate);
      resize();
      controls.update();
      renderer.render(scene, camera);
    }}
    animate();

    document.addEventListener('visibilitychange', () => {{
      if (document.hidden) {{
        animating = false;
      }} else {{
        animating = true;
        animate();
      }}
    }});

    // Color picker — a composite has fixed per-part colours, so no swatches.
    if (!COMPOSITE_PARTS.length) {{
      const colorContainer = document.getElementById('colors');
      for (const color of FILAMENT_COLORS) {{
        const swatch = document.createElement('button');
        swatch.className = 'color-swatch';
        swatch.style.backgroundColor = '#' + color.hex.toString(16).padStart(6, '0');
        swatch.title = color.name;
        swatch.setAttribute('aria-label', color.name);
        if (color.hex === 0x64b5f6) swatch.setAttribute('aria-pressed', 'true');
        swatch.addEventListener('click', () => {{
          colorContainer.querySelectorAll('.color-swatch').forEach(s => s.removeAttribute('aria-pressed'));
          swatch.setAttribute('aria-pressed', 'true');
          material.color.setHex(color.hex);
        }});
        colorContainer.appendChild(swatch);
      }}
    }}

    // Fullscreen
    document.getElementById('fs-btn').addEventListener('click', () => {{
      if (document.fullscreenElement) {{
        document.exitFullscreen();
      }} else {{
        document.documentElement.requestFullscreen();
      }}
    }});

    // Cross-section
    let clipPlane = null;
    const crossBtn = document.getElementById('cross-btn');
    const clipSlider = document.getElementById('clip-slider');

    crossBtn.addEventListener('click', () => {{
      const active = crossBtn.getAttribute('aria-pressed') === 'true';
      if (active) {{
        for (const m of clipMaterials) m.clippingPlanes = [];
        clipPlane = null;
        clipSlider.style.display = 'none';
        crossBtn.setAttribute('aria-pressed', 'false');
      }} else {{
        clipPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 0);
        clipPlane.constant = clipBounds.minY + 0.5 * (clipBounds.maxY - clipBounds.minY);
        for (const m of clipMaterials) m.clippingPlanes = [clipPlane];
        clipSlider.value = '50';
        clipSlider.style.display = '';
        crossBtn.setAttribute('aria-pressed', 'true');
      }}
    }});

    clipSlider.addEventListener('input', () => {{
      if (!clipPlane) return;
      const pct = clipSlider.value / 100;
      clipPlane.constant = clipBounds.minY + pct * (clipBounds.maxY - clipBounds.minY);
    }});

    // View controls — rotate 90° per world axis, reset, and switch controls.
    // displayObject is the Mesh (single) or Group (composite) built above.
    function recomputeClip() {{
      const box = new THREE.Box3().setFromObject(displayObject);
      clipBounds = {{ minY: box.min.y, maxY: box.max.y }};
      if (clipPlane) {{
        const pct = Number(clipSlider.value) / 100;
        clipPlane.constant = clipBounds.minY + pct * (clipBounds.maxY - clipBounds.minY);
      }}
    }}

    function rotateMesh(axis) {{
      const v = axis === 'x' ? new THREE.Vector3(1, 0, 0)
        : axis === 'y' ? new THREE.Vector3(0, 1, 0)
        : new THREE.Vector3(0, 0, 1);
      displayObject.rotateOnWorldAxis(v, Math.PI / 2);
      recomputeClip();
    }}

    document.getElementById('rot-x').addEventListener('click', () => rotateMesh('x'));
    document.getElementById('rot-y').addEventListener('click', () => rotateMesh('y'));
    document.getElementById('rot-z').addEventListener('click', () => rotateMesh('z'));
    document.getElementById('reset-view').addEventListener('click', () => {{
      displayObject.rotation.set(0, 0, 0);
      camera.position.copy(defaultCamPos);
      controls.target.set(0, 0, 0);
      camera.up.set(0, 1, 0);
      makeControls(controlMode);
      recomputeClip();
    }});

    const modeBtns = {{
      orbit: document.getElementById('mode-orbit'),
      trackball: document.getElementById('mode-trackball'),
      arcball: document.getElementById('mode-arcball'),
    }};
    Object.entries(modeBtns).forEach(([mode, btn]) => {{
      btn.addEventListener('click', () => {{
        makeControls(mode);
        Object.entries(modeBtns).forEach(([m, b]) =>
          b.setAttribute('aria-pressed', String(m === mode)));
      }});
    }});
  </script>
</body>
</html>
"""


def _check_threejs_version():
    """Verify THREEJS_VERSION matches the version in index.html's and embed.html's importmaps."""
    for html_file in ("index.html", "embed.html"):
        if not os.path.isfile(html_file):
            continue  # Skip check if file not available (e.g. running standalone)
        with open(html_file) as f:
            content = f.read()
        versions = re.findall(r"cdn\.jsdelivr\.net/npm/three@([\d.]+)/", content)
        if not versions:
            print(f"Warning: could not extract Three.js version from {html_file}")
            continue
        file_version = versions[0]
        if file_version != THREEJS_VERSION:
            width = max(len("generate-standalone.py"), len(html_file))
            print(
                f"Error: Three.js version mismatch\n"
                f"  {'generate-standalone.py':<{width}}: {THREEJS_VERSION}\n"
                f"  {html_file:<{width}}: {file_version}\n"
                f"Update THREEJS_VERSION in this script to match {html_file}."
            )
            sys.exit(1)
        print(f"Three.js version {THREEJS_VERSION} matches {html_file}")


def main():
    if not os.path.isfile(SCAD_MAP):
        print(f"Error: {SCAD_MAP} not found. Run the STL render step first.")
        sys.exit(1)

    _check_threejs_version()

    filament_colors_js = _load_filament_colors_js()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Download and base64-encode Three.js assets (once for all models)
    print("Downloading Three.js assets...")
    js_uris = {}
    for key, asset in THREEJS_ASSETS.items():
        print(f"  Fetching {key}...")
        data = fetch_url(asset["url"], expected_sha256=asset["sha256"])
        js_uris[key] = b64_data_uri(data, "text/javascript")
        print(f"  {key}: {len(data)} bytes -> {len(js_uris[key])} chars base64 URI")

    # Parse .scad-map and generate one HTML per STL
    models = []
    stl_to_dir = {}  # stl basename -> project dir (for meta.json lookup)
    stl_to_source = {}  # stl basename -> source .scad path (for public source link)
    with open(SCAD_MAP) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 2)
            if len(parts) >= 3:
                models.append(parts[0])  # stl filename
                stl_to_dir[parts[0]] = parts[1]  # project dir
                stl_to_source[parts[0]] = parts[2]  # source .scad path
            else:
                print(f"  Warning: malformed .scad-map line: {line!r}")

    # Cache parsed meta.json per project dir so composite lookups are cheap.
    meta_cache = {}
    failed_meta = load_meta_failures()

    def load_meta(project_dir):
        if project_dir in meta_cache:
            return meta_cache[project_dir]
        meta = {}
        meta_path = os.path.join(project_dir, "meta.json")
        # Same deferred-enforcement gate models.json uses (build.yml): a
        # meta.json that failed schema validation is treated as absent here
        # rather than blocking every other project's standalone viewer.
        if os.path.isfile(meta_path) and meta_path not in failed_meta:
            try:
                with open(meta_path) as mf:
                    meta = json.load(mf)
            except (OSError, json.JSONDecodeError):
                meta = {}
        meta_cache[project_dir] = meta
        return meta

    def build_composite_js(stl):
        """Return a safe JS literal of composite parts, or "[]" if not a composite."""
        project_dir = stl_to_dir.get(stl)
        if not project_dir:
            return "[]"
        assembly = load_meta(project_dir).get("assembly")
        if not isinstance(assembly, dict) or assembly.get("stl") != stl:
            return "[]"
        parts_list = []
        for part in assembly.get("parts", []):
            if not isinstance(part, dict):
                print(f"  Warning: malformed composite part entry for {stl}, skipping part")
                continue
            color = part.get("color", "")
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                print(f"  Warning: invalid composite color {color!r} for {stl}, skipping part")
                continue
            part_stl = part.get("stl")
            if not isinstance(part_stl, str) or not part_stl:
                print(f"  Warning: composite part missing stl filename for {stl}, skipping part")
                continue
            part_path = os.path.join("site", part_stl)
            if not os.path.isfile(part_path):
                print(f"  Warning: composite part {part_path} not found, skipping")
                continue
            with open(part_path, "rb") as pf:
                part_b64 = base64.b64encode(pf.read()).decode()
            parts_list.append({"stl_b64": part_b64, "color": color})
        return _composite_parts_js(parts_list)

    print(f"\nGenerating standalone viewers for {len(models)} models...")
    generated = 0
    for stl in sorted(models):
        stl_path = os.path.join("site", stl)
        if not os.path.isfile(stl_path):
            print(f"  Warning: {stl_path} not found, skipping")
            continue

        name = display_name(stl)
        html_name = strip_stl_ext(stl) + ".html"
        out_path = os.path.join(OUTPUT_DIR, html_name)

        with open(stl_path, "rb") as f:
            stl_data = f.read()
        stl_b64 = base64.b64encode(stl_data).decode()

        composite_js = build_composite_js(stl)

        html = HTML_TEMPLATE.format(
            title=html_mod.escape(name),
            three_uri=js_uris["three"],
            stlloader_uri=js_uris["STLLoader"],
            orbitcontrols_uri=js_uris["OrbitControls"],
            trackballcontrols_uri=js_uris["TrackballControls"],
            arcballcontrols_uri=js_uris["ArcballControls"],
            stl_base64=stl_b64,
            filament_colors_js=filament_colors_js,
            composite_parts_js=composite_js,
            source_link_html=_source_link_html(stl_to_source.get(stl, "")),
        )

        with open(out_path, "w") as f:
            f.write(html)

        stl_kb = len(stl_data) / 1024
        html_kb = len(html.encode()) / 1024
        print(f"  {html_name}: STL {stl_kb:.0f}KB -> HTML {html_kb:.0f}KB")
        generated += 1

    print(f"\nDone. Generated {generated}/{len(models)} standalone viewers in {OUTPUT_DIR}/")

    if generated == 0 and models:
        print("Error: no standalone viewers were generated despite models in .scad-map")
        sys.exit(1)


if __name__ == "__main__":
    main()
