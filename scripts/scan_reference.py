"""Watertight reference meshes from a cleaned scan (operator tool, not used by CI).

The `clean` stage exports the OpenMVS mesh as-is: an open shell, because a
single low camera ring never sees the underside of the object. OpenSCAD's CSG
needs manifold operands, so that mesh cannot be `difference()`d out of a holder
body no matter how it is stored. This module closes it.

Two modes:

- `hull` — the convex hull of the cleaned mesh. Always available, always
  watertight, tiny (~1k faces on a real scan), and the right operand for a
  convex-ish object like a toothpaste tube. Loses every concavity.
- `slabs` — slice the mesh into overlapping horizontal slabs, hull each slab,
  and boolean-union the results. Every operand is a closed convex solid, so
  the union is watertight by construction, and concavity that varies with Z (a
  taper, a waist) survives. Needs trimesh's `manifold` boolean engine.

Quadric decimation is deliberately not offered: it lowers the face count but
preserves the open boundary, so the result is still not watertight and would
not satisfy the only requirement that matters here (#439).

Third-party imports (numpy, trimesh) are lazy so this module stays importable
outside `nix develop .#scan`.
"""

import json
import pathlib
import re
import shutil

REFERENCE_MODES = ("hull", "slabs")

# Reference meshes are committed under scans/, so they carry a size budget the
# raw 2-4 MB scan export cannot meet.
DEFAULT_MAX_BYTES = 512_000

# The same charset build.yml enforces on .scad basenames before rendering.
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._ -]+$")


def safe_name(name):
    """Validate an object name for use as a path component under scans/."""
    if not name:
        raise ValueError("object name is empty")
    if name in (".", ".."):
        raise ValueError(f"object name {name!r} is not a directory name")
    if "/" in name or "\\" in name:
        raise ValueError(f"object name {name!r} must not contain a path separator")
    if not SAFE_NAME_RE.match(name):
        raise ValueError(
            f"object name {name!r} contains characters outside [A-Za-z0-9._ -]"
        )
    return name


def convex_hull_reference(mesh):
    """The convex hull of the mesh — watertight whatever the input shell."""
    return mesh.convex_hull


def slab_hull_reference(mesh, slabs=12, overlap=0.15):
    """Union of per-slab convex hulls: watertight, but keeps Z-varying concavity.

    Adjacent slabs overlap by `overlap` of a slab height so the union has real
    volume to work with — abutting solids can leave trimesh with a Scene of
    disjoint bodies rather than one solid.
    """
    import trimesh

    vertices = mesh.vertices
    z0, z1 = float(mesh.bounds[0][2]), float(mesh.bounds[1][2])
    if z1 - z0 <= 1e-9:
        raise ValueError("slab-hull needs a positive Z extent")

    step = (z1 - z0) / slabs
    pad = overlap * step

    parts = []
    for i in range(slabs):
        low = z0 + i * step - pad
        high = z0 + (i + 1) * step + pad
        z = vertices[:, 2]
        points = vertices[(z >= low) & (z <= high)]
        if len(points) < 4:
            continue
        try:
            # Qhull raises on coplanar or otherwise degenerate slabs; a slab
            # that cannot be hulled simply contributes nothing.
            hull = trimesh.PointCloud(points).convex_hull
        except Exception:
            continue
        if abs(float(hull.volume)) < 1e-9:
            continue
        parts.append(hull)

    if not parts:
        raise ValueError("no slab produced a solid hull — try --reference-mode hull")
    if len(parts) == 1:
        return parts[0]

    solid = trimesh.boolean.union(parts, engine="manifold")
    solid = _largest_body(solid)
    solid.merge_vertices()
    if hasattr(solid, "remove_degenerate_faces"):
        solid.remove_degenerate_faces()
    trimesh.repair.fix_normals(solid)
    return solid


def _largest_body(solid):
    """Reduce a boolean result to a single body, the largest by volume."""
    import trimesh

    if isinstance(solid, trimesh.Scene):
        bodies = list(solid.geometry.values())
    else:
        bodies = trimesh.graph.split(solid, only_watertight=False)
    if len(bodies) <= 1:
        return solid if not isinstance(solid, trimesh.Scene) else bodies[0]
    return max(bodies, key=lambda part: abs(float(part.volume)))


def build_reference(mesh, mode="hull", slabs=12):
    """Dispatch to the requested reference-mesh mode."""
    if mode == "hull":
        return convex_hull_reference(mesh)
    if mode == "slabs":
        return slab_hull_reference(mesh, slabs=slabs)
    raise ValueError(f"unknown reference mode {mode!r}")


def assert_watertight(mesh):
    """Refuse a reference mesh OpenSCAD's CSG could not use."""
    if not (mesh.is_watertight and mesh.is_volume):
        raise ValueError(
            f"reference mesh is not watertight ({len(mesh.faces)} faces) — "
            f"OpenSCAD difference() needs a manifold operand"
        )
    return mesh


def write_reference(mesh, path, max_bytes=DEFAULT_MAX_BYTES):
    """Export a binary STL, refusing anything over the size budget.

    Unlike scan_mesh.export_stl there is no sibling PLY: these are committed,
    and staying small is the point.
    """
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(str(path))
    size = path.stat().st_size
    if size > max_bytes:
        path.unlink()
        raise ValueError(
            f"reference mesh is {size} bytes, over the {max_bytes}-byte budget — "
            f"lower --reference-slabs or use --reference-mode hull"
        )
    return path


def sanitised_report(report, extra):
    """The scan report as it may be committed, plus the reference metadata.

    `video` is an absolute path under the operator's home directory in the raw
    report, and scans/ is mirrored to the public repo — so only the basename
    survives.
    """
    sanitised = dict(report)
    if sanitised.get("video"):
        sanitised["video"] = pathlib.Path(sanitised["video"]).name
    sanitised["reference"] = extra
    return sanitised


def install_reference(stl_path, report, object_name, repo_root, force=False):
    """Copy the reference mesh and its report into scans/<object>/."""
    object_name = safe_name(object_name)
    dest_dir = pathlib.Path(repo_root) / "scans" / object_name
    stl_dest = dest_dir / f"{object_name}-reference.stl"
    report_dest = dest_dir / "scan-report.json"

    for dest in (stl_dest, report_dest):
        if dest.exists() and not force:
            raise ValueError(f"{dest} exists — pass --force to overwrite")

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(str(stl_path), str(stl_dest))
    report_dest.write_text(json.dumps(report, indent=2) + "\n")
    return stl_dest, report_dest
