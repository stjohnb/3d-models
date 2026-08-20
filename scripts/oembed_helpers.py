"""Shared helpers for OEmbed generation and link-tag injection in build.yml."""

import os
import re
import sys
from urllib.parse import quote

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
