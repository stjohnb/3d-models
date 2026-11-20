#!/usr/bin/env python3
"""Fetch a terrain heightmap PNG for a lat/lon bbox from AWS Open Data Terrain Tiles.

Downloads slippy-projection terrarium PNG tiles from
``s3.amazonaws.com/elevation-tiles-prod`` (Mapzen terrarium encoding,
publicly hosted by AWS Open Data), stitches them, crops to the exact
geographic bounding box, normalizes elevation to an 8-bit grayscale
image, and writes a sidecar JSON with the min/max metres so a consumer
(e.g. an OpenSCAD ``surface()`` call) can map 0..255 back to real
elevation.

Heightmap-fetch pipeline adapted from
https://github.com/ModelRift/terrain-to-3d (public reference
implementation, ``src/lib/terrain.ts``).

Run as a one-off generator like ``scripts/fetch_openscad_wasm.py`` — not
wired into CI. Cached tiles live under ``.cache/terrain-tiles/`` (which
is ``.cache/``-gitignored).
"""

import argparse
from io import BytesIO
import json
import math
import os
import sys

import numpy as np
import requests
from PIL import Image

CACHE_DIR = os.path.join(".cache", "terrain-tiles")
TILE_URL = (
    "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
)
USER_AGENT = (
    "3d-models-terrain-fetch/1.0 "
    "(https://github.com/St-John-Software/3d-models)"
)
TILE_PX = 256
KM_PER_DEG_LAT = 111.32
SOURCE_NAME = "AWS Open Data Terrain Tiles (Mapzen terrarium)"


def lon_to_x(lon: float, n: int) -> int:
    return int((lon + 180) / 360 * n)


def lat_to_y(lat: float, n: int) -> int:
    r = math.radians(lat)
    return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n)


def x_to_lon(x: int, n: int) -> float:
    return x / n * 360 - 180


def y_to_lat(y: int, n: int) -> float:
    v = math.pi - 2 * math.pi * y / n
    return math.degrees(math.atan(0.5 * (math.exp(v) - math.exp(-v))))


def decode_terrarium(img: Image.Image) -> np.ndarray:
    """Decode an RGB terrarium tile into a float32 elevation array (metres)."""
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    return arr[:, :, 0] * 256.0 + arr[:, :, 1] + arr[:, :, 2] / 256.0 - 32768.0


def _fetch_tile_bytes(
    session: requests.Session, z: int, x: int, y: int
) -> bytes | None:
    """Return raw bytes for a tile, with on-disk caching and 404 -> None."""
    cache_path = os.path.join(CACHE_DIR, str(z), str(x), f"{y}.png")
    if os.path.isfile(cache_path):
        with open(cache_path, "rb") as f:
            return f.read()
    url = TILE_URL.format(z=z, x=x, y=y)
    resp = session.get(url, timeout=60)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.content
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "wb") as f:
        f.write(data)
    return data


def fetch_heightmap(
    lat: float,
    lon: float,
    area_km: float,
    zoom: int,
    px: int,
    session: requests.Session | None = None,
) -> tuple[Image.Image, dict]:
    """Return ``(png_image, metadata)`` for the bbox centred on ``(lat, lon)``."""
    if session is None:
        session = requests.Session()
        session.headers["User-Agent"] = USER_AGENT

    km_per_deg_lon = KM_PER_DEG_LAT * math.cos(math.radians(lat))
    dlat = (area_km / 2.0) / KM_PER_DEG_LAT
    dlon = (area_km / 2.0) / km_per_deg_lon
    bbox_north = lat + dlat
    bbox_south = lat - dlat
    bbox_west = lon - dlon
    bbox_east = lon + dlon

    n = 1 << zoom
    tx_min = lon_to_x(bbox_west, n)
    tx_max = lon_to_x(bbox_east, n)
    ty_min = lat_to_y(bbox_north, n)
    ty_max = lat_to_y(bbox_south, n)

    tiles_x = tx_max - tx_min + 1
    tiles_y = ty_max - ty_min + 1
    full_w = tiles_x * TILE_PX
    full_h = tiles_y * TILE_PX
    full = np.zeros((full_h, full_w), dtype=np.float32)

    missing_tiles: list[tuple[int, int, int]] = []
    for ty in range(ty_min, ty_max + 1):
        for tx in range(tx_min, tx_max + 1):
            data = _fetch_tile_bytes(session, zoom, tx, ty)
            row = (ty - ty_min) * TILE_PX
            col = (tx - tx_min) * TILE_PX
            if data is None:
                missing_tiles.append((zoom, tx, ty))
                print(
                    f"warning: missing tile {zoom}/{tx}/{ty}, "
                    "filling with sea-level (0)",
                    file=sys.stderr,
                )
                continue
            tile_img = Image.open(BytesIO(data))
            full[row : row + TILE_PX, col : col + TILE_PX] = decode_terrarium(
                tile_img
            )

    grid_w = x_to_lon(tx_min, n)
    grid_e = x_to_lon(tx_max + 1, n)
    grid_n = y_to_lat(ty_min, n)
    grid_s = y_to_lat(ty_max + 1, n)
    crop_l = max(0, round((bbox_west - grid_w) / (grid_e - grid_w) * full_w))
    crop_r = min(full_w, round((bbox_east - grid_w) / (grid_e - grid_w) * full_w))
    crop_t = max(0, round((grid_n - bbox_north) / (grid_n - grid_s) * full_h))
    crop_b = min(full_h, round((grid_n - bbox_south) / (grid_n - grid_s) * full_h))
    cropped = full[crop_t:crop_b, crop_l:crop_r]
    if cropped.size == 0:
        raise ValueError(
            f"empty crop {crop_l}:{crop_r}, {crop_t}:{crop_b} "
            f"in {full_w}x{full_h} grid"
        )

    elev_min = float(cropped.min())
    elev_max = float(cropped.max())
    elev_range = (elev_max - elev_min) or 1.0
    u8 = np.round((cropped - elev_min) / elev_range * 255).astype(np.uint8)
    img = Image.fromarray(u8, mode="L").resize((px, px), Image.LANCZOS)

    metadata = {
        "elev_min_m": elev_min,
        "elev_max_m": elev_max,
        "elev_range_m": round(elev_max - elev_min),
        "area_km": area_km,
        "lat": lat,
        "lon": lon,
        "px": px,
        "zoom": zoom,
        "tile_count_x": tiles_x,
        "tile_count_y": tiles_y,
        "missing_tiles": [
            {"z": z, "x": x, "y": y} for (z, x, y) in missing_tiles
        ],
        "source": SOURCE_NAME,
    }
    return img, metadata


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Fetch a terrain heightmap PNG (and elevation metadata JSON) "
            "for a lat/lon bbox from AWS Open Data Terrain Tiles."
        )
    )
    p.add_argument("--lat", type=float, required=True, help="centre latitude (deg)")
    p.add_argument("--lon", type=float, required=True, help="centre longitude (deg)")
    p.add_argument("--area-km", type=float, required=True, help="bbox edge length (km)")
    p.add_argument("--zoom", type=int, default=14, help="slippy zoom level (default 14)")
    p.add_argument("--px", type=int, default=512, help="output image edge length (default 512)")
    p.add_argument("--output", required=True, help="output PNG path")
    p.add_argument("--metadata-output", required=True, help="output JSON sidecar path")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    img, metadata = fetch_heightmap(
        lat=args.lat,
        lon=args.lon,
        area_km=args.area_km,
        zoom=args.zoom,
        px=args.px,
    )
    img.save(args.output, format="PNG")
    with open(args.metadata_output, "w") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)
        f.write("\n")
    print(
        f"  heightmap: {args.px}x{args.px} -> {args.output}; "
        f"elev {metadata['elev_min_m']:.1f}..{metadata['elev_max_m']:.1f} m "
        f"(range {metadata['elev_range_m']} m) -> {args.metadata_output}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
