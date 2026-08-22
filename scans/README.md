# Scan reference meshes

Each subdirectory here holds one scanned real-world object, as design input for
models that have to fit around it:

```
scans/<object>/<object>-reference.stl   the reference mesh
scans/<object>/scan-report.json         provenance from the capture that made it
```

## Why these are committed when every other STL is not

`.gitignore` ignores `*.stl` and carves these back out with `!scans/**/*.stl`.
That is not a loophole around the rejected "committed revision snapshots"
pattern (#198): those were *derived outputs* of committed `.scad` sources, so
CI can always reproduce them. A scan mesh is *captured input data* — nothing in
this repo can regenerate it from anything else, the capture video is a one-off
on the operator's machine, and reconstruction takes hours of COLMAP/OpenMVS.
It is the same category as `nz-ski-fields/heightmap.png`, which is tracked for
exactly the same reason.

## What a reference mesh guarantees

- **Watertight.** `scripts/scan_reference.py` closes the open shell the scan
  pipeline produces, so the mesh is a manifold OpenSCAD's CSG will accept as a
  `difference()` operand. The raw `clean` export is not — a single low camera
  ring never sees the underside of the object.
- **Small.** Under 500 KB (`--reference-max-bytes`, default 512000). The stage
  deletes an over-budget file rather than committing it.
- **Millimetres, platter-centred, Z-up.** The mesh inherits the `clean` stage's
  frame: the platter centre is the origin and its surface is z=0. Leave it
  Z-up — never add a top-level `rotate([-90, 0, 0])`, the viewers apply that
  conversion themselves.
- **Named within `[A-Za-z0-9._ -]`**, the same charset CI enforces on `.scad`
  basenames.

## Producing one

Run the pipeline's last stage on a capture that has already been through
`clean` (see `playbooks/scan_a_capture.md`):

```bash
python3 scripts/scan_pipeline.py ~/captures/IMG_3826.MOV \
    --only reference --reference-mode slabs --install-as pliers
```

`--reference-mode hull` (the default) takes the convex hull: always available,
tiny, and the right answer for a convex-ish object like a toothpaste tube.
`--reference-mode slabs` unions per-slab hulls instead, which keeps concavity
that varies with Z at the cost of a larger file.

`--install-as <name>` is what writes into this directory. The report it commits
is sanitised — the raw one holds the absolute capture path under the operator's
home directory, and `scans/` mirrors to the public repo.

## Using one from a model

A renderable may `import()` a reference mesh by relative path:

```openscad
difference() {
    holder_body();
    translate([0, 0, 2]) import("../scans/tube/tube-reference.stl");
}
```

CI renders this correctly — the mesh is committed, and `scripts/render_cache.py`
already hashes `import()` targets into the cache key, so editing the mesh
invalidates the render.

**Such a model must not ship a `<basename>.parameters.json`.** The in-browser
customizer writes a project's files flat into the wasm filesystem, where a
`../scans/…` path cannot resolve; the parameter-manifest validation step in
`build.yml` fails the build on that combination.
