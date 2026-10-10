"""Shared helpers for OEmbed generation and link-tag injection in build.yml."""

import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import quote
from xml.sax.saxutils import escape

BASE_URL = 'https://www.bstjohn.net/3d-models'

PUBLIC_REPO_URL = 'https://github.com/stjohnb/3d-models'
PUBLIC_REPO_BLOB = f'{PUBLIC_REPO_URL}/blob/main'

SITE_URL = 'https://www.bstjohn.net'
ORG_ID = f'{SITE_URL}/#organization'
SITE_ID = f'{SITE_URL}/#website'
COLLECTION_ID = f'{BASE_URL}/#collection'
ORG_NAME = 'St. John Software'
ORG_SAME_AS = [
    'https://github.com/St-John-Software',
    'https://github.com/stjohnb',
]


def public_source_url(source):
    """Return the public-mirror URL for a repo-relative source path.

    Encodes each path segment (source paths may contain spaces) but leaves
    the '/' separators intact. Returns '' for a falsy path.
    """
    if not source:
        return ''
    encoded = '/'.join(quote(part, safe='') for part in source.split('/'))
    return f'{PUBLIC_REPO_BLOB}/{encoded}'


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


def strip_stl_ext(filename):
    """Remove a trailing .stl extension case-insensitively."""
    return re.sub(r'\.stl$', '', filename, flags=re.I)


def standalone_url(stl):
    """Canonical public URL of the standalone viewer page for an STL."""
    return f'{BASE_URL}/standalone/{quote(strip_stl_ext(stl))}.html'


def project_display_name(project_dir):
    """Convert a project directory name to its canonical display name.

    Hyphens/underscores become spaces, then Python title-casing. This name is
    the models.json group key and the changed.json project name (issue #399);
    build.yml's PR-comment step reads it back out of models.json rather than
    re-deriving it, so this is the only implementation.
    """
    return project_dir.replace('-', ' ').replace('_', ' ').title()


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
            project_name = project_display_name(project_dir)
            scad_map[stl] = {'project': project_name, 'dir': project_dir, 'source': source}
    return scad_map


OG_HERO_TILE_COLUMNS = 5
OG_HERO_TILE_ROWS = 3
OG_HERO_MAX_TILES = OG_HERO_TILE_COLUMNS * OG_HERO_TILE_ROWS


def og_hero_thumbnails(scad_map, heroes, existing, limit=OG_HERO_MAX_TILES):
    """Pick the ordered thumbnails for the OG hero montage (issue #458).

    scad_map: {stl: {'project','dir','source'}} from parse_scad_map.
    heroes:   {project_dir: hero_stl} from each project's meta.json.
    existing: set of PNG basenames actually present in site/.

    Returns at most `limit` thumbnail basenames: one per project (the
    declared hero when it rendered, else the first STL alphabetically),
    in project-directory order, then further models in (dir, stl) order
    to fill the grid. Never returns a name absent from `existing` and
    never returns duplicates. Excludes the _top/_bottom/_front
    orthographic views by construction: every name is derived from an
    STL in .scad-map.
    """
    by_dir = {}
    for stl, info in scad_map.items():
        by_dir.setdefault(info['dir'], []).append(stl)

    picked = []
    seen = set()
    for project_dir in sorted(by_dir):
        if len(picked) >= limit:
            break
        stls = sorted(by_dir[project_dir])
        hero = heroes.get(project_dir)
        order = ([hero] if hero in stls else []) + [s for s in stls if s != hero]
        for stl in order:
            png = thumbnail_name(stl)
            if png in existing:
                picked.append(png)
                seen.add(png)
                break

    for project_dir in sorted(by_dir):
        for stl in sorted(by_dir[project_dir]):
            if len(picked) >= limit:
                return picked[:limit]
            png = thumbnail_name(stl)
            if png in existing and png not in seen:
                picked.append(png)
                seen.add(png)
    return picked[:limit]


def build_structured_data(scad_map, project_descriptions, stl_sizes=None):
    """Build the root page's Schema.org @graph payload.

    scad_map: {stl: {'project': str, 'dir': str, 'source': str}} from parse_scad_map.
    project_descriptions: {project_dir: description} from valid meta.json files.
    stl_sizes: optional {stl: int bytes}; entries present get a contentSize.
    """
    stl_sizes = stl_sizes or {}
    items = []
    for i, (stl, info) in enumerate(sorted(scad_map.items()), start=1):
        desc = project_descriptions.get(
            info['dir'],
            f"3D printable part from the {info['project']} collection",
        )
        item = {
            '@type': '3DModel',
            '@id': f'{standalone_url(stl)}#model',
            'name': display_name(stl).title(),
            'description': desc,
            'contentUrl': f'{BASE_URL}/{quote(stl)}',
            'encodingFormat': 'model/stl',
            'thumbnailUrl': f'{BASE_URL}/{quote(thumbnail_name(stl))}',
            'isPartOf': {'@type': 'CreativeWork', 'name': info['project']},
            'creator': {'@id': ORG_ID},
        }
        if stl in stl_sizes:
            item['contentSize'] = f'{stl_sizes[stl]} B'
        items.append({'@type': 'ListItem', 'position': i, 'item': item})

    return {
        '@context': 'https://schema.org',
        '@graph': [
            {
                '@type': 'Organization',
                '@id': ORG_ID,
                'name': ORG_NAME,
                'url': SITE_URL,
                'sameAs': list(ORG_SAME_AS),
            },
            {
                '@type': 'WebSite',
                '@id': SITE_ID,
                'url': SITE_URL,
                'name': 'bstjohn.net',
                'publisher': {'@id': ORG_ID},
            },
            {
                '@type': 'CollectionPage',
                '@id': COLLECTION_ID,
                'name': '3D Printable Models',
                'description': 'Interactive 3D viewer for printable OpenSCAD models — browse, rotate, and download STL files.',
                'url': f'{BASE_URL}/',
                'isPartOf': {'@id': SITE_ID},
                'creator': {'@id': ORG_ID},
                'mainEntity': {'@type': 'ItemList', 'itemListElement': items},
            },
        ],
    }


def stl_lastmods(models_path='site/models.json'):
    """Return {stl filename: ISO-8601 'updated' string} from a models.json.

    Each models.json project entry carries an optional 'updated' field (the
    project directory's last commit date, from scripts/project_dates.py) and a
    'files' list of {'stl': ...} entries. Projects without 'updated' — every
    project on a shallow clone — contribute nothing. A missing or malformed
    models.json returns {}; a missing date must degrade silently, never fail
    the build (same contract as project_updated()).
    """
    try:
        with open(models_path) as f:
            models = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(models, dict):
        return {}
    lastmods = {}
    for entry in models.values():
        if not isinstance(entry, dict):
            continue
        updated = entry.get('updated')
        if not updated:
            continue
        for file_entry in entry.get('files') or []:
            stl = (file_entry or {}).get('stl')
            if stl:
                lastmods[stl] = updated
    return lastmods


def _parse_iso(value):
    """Parse an ISO-8601 timestamp to an aware datetime, or None if unparsable."""
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def build_sitemap(stls, lastmods=None):
    """Return the sitemap.xml document text.

    stls: iterable of STL filenames (from parse_scad_map). Emitted in the
      order given — build.yml passes them sorted.
    lastmods: optional {stl: ISO-8601 string} from stl_lastmods(). An STL with
      no entry (or an empty value) gets no <lastmod> element. The gallery root
      URL gets the newest parsable date across the emitted STLs, and no
      <lastmod> at all when none are available.
    """
    lastmods = lastmods or {}
    stls = list(stls)
    rows = []
    newest = None
    newest_raw = None
    for stl in stls:
        rows.append((standalone_url(stl), lastmods.get(stl)))
    for _, raw in rows:
        parsed = _parse_iso(raw) if raw else None
        if parsed is not None and (newest is None or parsed > newest):
            newest, newest_raw = parsed, raw
    entries = [(f'{BASE_URL}/', newest_raw)] + rows

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, raw in entries:
        lastmod = f'<lastmod>{escape(raw)}</lastmod>' if raw else ''
        lines.append(f'  <url><loc>{escape(loc)}</loc>{lastmod}</url>')
    lines.append('</urlset>')
    return '\n'.join(lines) + '\n'
