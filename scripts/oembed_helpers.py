"""Shared helpers for OEmbed generation and link-tag injection in build.yml."""

import os
import re
import sys

BASE_URL = 'https://www.bstjohn.net/3d-models'


def load_meta_failures():
    """Return the set of meta.json paths that failed schema validation."""
    failed = set()
    if os.path.isfile(".meta-failures"):
        with open(".meta-failures") as f:
            failed = {p.strip() for p in f if p.strip()}
    return failed


def slugify(name):
    """Convert a filename or directory name to a URL-safe slug."""
    return re.sub(r'[_\s]+', '-', re.sub(r'\.stl$', '', name, flags=re.I)).lower()


def display_name(filename):
    """Convert a filename like 'my-part.stl' to a human-readable name."""
    return re.sub(r'\.stl$', '', filename, flags=re.I).replace('-', ' ').replace('_', ' ')


def thumbnail_name(stl):
    """Derive PNG thumbnail filename from an STL filename (case-insensitive)."""
    return re.sub(r'\.stl$', '.png', stl, flags=re.I)


def parse_scad_map(path):
    """Parse a .scad-map file and return {stl: {'project': ..., 'dir': ...}}."""
    scad_map = {}
    with open(path) as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t', 2)
            if len(parts) < 3:
                print(f'WARNING: {path}:{lineno}: skipping malformed line (expected 3 tab-separated fields): {line!r}', file=sys.stderr)
                continue
            stl, project_dir, source = parts
            if not slugify(stl):
                print(f'WARNING: {path}:{lineno}: empty slug for {stl!r}, skipping', file=sys.stderr)
                continue
            if stl in scad_map:
                print(f'WARNING: {path}:{lineno}: duplicate key {stl!r}, overwriting', file=sys.stderr)
            project_name = project_dir.replace('-', ' ').replace('_', ' ').title()
            scad_map[stl] = {'project': project_name, 'dir': project_dir, 'source': source}
    return scad_map
