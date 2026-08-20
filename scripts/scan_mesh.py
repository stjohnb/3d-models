"""Scaling and cleanup of the reconstructed mesh for the photogrammetry pipeline.

Operator tool — not used by CI.

Structure-from-motion recovers geometry only up to an arbitrary similarity
transform: the reconstruction has no scale, and no idea which way is up. Both
come from the platter, whose diameter is known (`platter_d = 150` in
`scanning-rig/_scanning_rig.scad`) and whose surface is the dominant plane in
the reconstructed mesh. Fitting that plane gives the up axis and the origin;
fitting the platter's radius within it gives millimetres per reconstruction
unit. The fit runs on the mesh rather than OpenMVS's `scene_dense.ply`, whose
per-vertex list properties trimesh cannot parse (issue #421).

Third-party imports (numpy, trimesh) are lazy so this module stays importable
outside `nix develop .#scan`.
"""


def load_points(ply_path):
    """Load a PLY as an (N, 3) array of points, cloud or mesh.

    Not usable on an OpenMVS dense cloud — trimesh raises
    `PLY is unexpected length!` on its per-vertex list properties.
    """
    import trimesh

    loaded = trimesh.load(str(ply_path))
    points = getattr(loaded, "points", None)
    if points is None:
        points = getattr(loaded, "vertices", None)
    if points is None:
        raise ValueError(f"{ply_path} has no points or vertices")
    import numpy

    return numpy.asarray(points, dtype=float)


def fit_plane_ransac(points, iterations=2000, threshold_frac=0.004, seed=0):
    """RANSAC-fit the dominant plane. Returns (point, normal, inlier_mask).

    Seeded deliberately: an unseeded fit would make the platter radius — and
    therefore the exported scale — differ between runs over the same capture.
    The normal is oriented toward the cloud centroid, because the object sits
    above the platter.
    """
    import numpy

    points = numpy.asarray(points, dtype=float)
    if len(points) < 3:
        raise ValueError("plane fit needs at least 3 points")

    diagonal = float(numpy.linalg.norm(points.max(axis=0) - points.min(axis=0)))
    threshold = threshold_frac * diagonal
    centroid = points.mean(axis=0)
    rng = numpy.random.default_rng(seed)

    best = None
    best_count = -1
    best_mask = None
    for _ in range(iterations):
        sample = points[rng.choice(len(points), 3, replace=False)]
        normal = numpy.cross(sample[1] - sample[0], sample[2] - sample[0])
        length = float(numpy.linalg.norm(normal))
        if length < 1e-9:
            continue
        normal = normal / length
        mask = numpy.abs((points - sample[0]) @ normal) <= threshold
        count = int(mask.sum())
        if count > best_count:
            best = (sample[0], normal)
            best_count = count
            best_mask = mask

    if best is None:
        raise ValueError("plane fit failed: every sampled triple was degenerate")

    point, normal = best
    if float(numpy.dot(centroid - point, normal)) < 0:
        normal = -normal
    return point, normal, best_mask


def _plane_basis(normal):
    """Two unit vectors spanning the plane with the given normal."""
    import numpy

    normal = numpy.asarray(normal, dtype=float)
    seed = numpy.array([1.0, 0.0, 0.0])
    if abs(float(numpy.dot(seed, normal))) > 0.9:
        seed = numpy.array([0.0, 1.0, 0.0])
    u = numpy.cross(normal, seed)
    u = u / numpy.linalg.norm(u)
    v = numpy.cross(normal, u)
    return u, v


def fit_platter(points, plane):
    """Find the platter's centre and radius within the fitted plane.

    Robust statistics throughout: fingers occlude part of the rim and stray
    points sit beyond it, so the centre is a component-wise median and the
    radius the 97.5th percentile of radial distance rather than the maximum.
    """
    import numpy

    origin, normal, inlier_mask = plane
    inliers = numpy.asarray(points, dtype=float)[inlier_mask]
    if len(inliers) == 0:
        raise ValueError("platter fit failed: the plane has no inliers")

    u, v = _plane_basis(normal)
    relative = inliers - origin
    coords = numpy.stack([relative @ u, relative @ v], axis=1)
    centre_2d = numpy.median(coords, axis=0)
    radius = float(numpy.percentile(numpy.linalg.norm(coords - centre_2d, axis=1), 97.5))
    centre = origin + centre_2d[0] * u + centre_2d[1] * v
    return centre, radius


def platter_frame(points, platter_diameter=150.0):
    """Derive the platter's coordinate frame and scale from the reconstructed mesh's vertices.

    Returns `origin` (the platter centre), `rotation` (3x3, taking the plane
    normal to +Z and the platter centre to the origin), `radius_units`,
    `mm_per_unit` and the plane's boolean `plane_inliers` mask.
    """
    import numpy

    points = numpy.asarray(points, dtype=float)
    plane = fit_plane_ransac(points)
    _, normal, inlier_mask = plane
    centre, radius_units = fit_platter(points, plane)
    if radius_units < 1e-9:
        raise ValueError("platter fit failed: radius ~0")

    u, v = _plane_basis(normal)
    rotation = numpy.stack([u, v, normal])
    return {
        "origin": centre,
        "rotation": rotation,
        "radius_units": float(radius_units),
        "mm_per_unit": float((platter_diameter / 2) / radius_units),
        "plane_inliers": inlier_mask,
    }


def scale_transform(frame):
    """The 4x4 taking reconstruction coordinates to platter-centred millimetres."""
    import numpy

    scale = frame["mm_per_unit"]
    rotation = numpy.asarray(frame["rotation"], dtype=float)
    origin = numpy.asarray(frame["origin"], dtype=float)
    matrix = numpy.eye(4)
    matrix[:3, :3] = rotation * scale
    matrix[:3, 3] = -(rotation @ origin) * scale
    return matrix


def crop_to_object(mesh, z_min=1.0, z_max=200.0, r_max=72.0):
    """Drop everything that is not the object. Bounds are in millimetres.

    Applied after the transform and scale, so the platter is the z=0 plane and
    the object stands on it. `r_max = 72` is the 75 mm platter radius less
    3 mm, which drops the rim, its tick marks, and any gripping fingers.
    """
    import numpy

    centroids = mesh.triangles.mean(axis=1)
    radius = numpy.hypot(centroids[:, 0], centroids[:, 1])
    keep = (
        (centroids[:, 2] >= z_min)
        & (centroids[:, 2] <= z_max)
        & (radius <= r_max)
    )
    mesh.update_faces(keep)
    mesh.remove_unreferenced_vertices()
    return mesh


def keep_largest_components(mesh, count=1):
    """Keep the `count` largest connected components by surface area."""
    import trimesh

    components = trimesh.graph.split(mesh, only_watertight=False)
    if len(components) == 0:
        raise ValueError("nothing survived cropping — check --z-min/--r-max")
    ordered = sorted(components, key=lambda part: float(part.area), reverse=True)
    kept = ordered[:count]
    if len(kept) == 1:
        return kept[0]
    return trimesh.util.concatenate(kept)


def export_stl(mesh, path):
    """Write the STL, plus a sibling PLY (which keeps colour, for inspection)."""
    import pathlib

    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(str(path))
    mesh.export(str(path.with_suffix(".ply")))
    return path
