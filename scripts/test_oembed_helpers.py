"""Unit tests for oembed_helpers.py.

Covers slugify, display_name, thumbnail_name, and parse_scad_map.
slugify must stay in sync with the JS implementations in index.html and
embed.html — these tests document the expected edge-case behaviour.
"""

import json
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

from oembed_helpers import (
    slugify,
    display_name,
    thumbnail_name,
    parse_scad_map,
    public_source_url,
    project_display_name,
    build_structured_data,
    standalone_url,
    strip_stl_ext,
    build_sitemap,
    stl_lastmods,
    og_hero_thumbnails,
    OG_HERO_MAX_TILES,
    OG_HERO_TILE_COLUMNS,
    OG_HERO_TILE_ROWS,
    BASE_URL,
    ORG_ID,
    SITE_ID,
    COLLECTION_ID,
)


class TestSlugify(unittest.TestCase):
    """slugify must match the JS: strip .stl, replace [_\\s]+ with -, lowercase."""

    def test_basic(self):
        self.assertEqual(slugify('drill-bit.stl'), 'drill-bit')

    def test_uppercase_extension(self):
        self.assertEqual(slugify('Part.STL'), 'part')

    def test_mixed_case_extension(self):
        self.assertEqual(slugify('Widget.Stl'), 'widget')

    def test_underscores(self):
        self.assertEqual(slugify('my_cool_part.stl'), 'my-cool-part')

    def test_spaces(self):
        self.assertEqual(slugify('my cool part.stl'), 'my-cool-part')

    def test_mixed_underscores_and_spaces(self):
        self.assertEqual(slugify('my_ _part.stl'), 'my-part')

    def test_consecutive_underscores(self):
        self.assertEqual(slugify('a___b.stl'), 'a-b')

    def test_no_extension(self):
        """Directory names don't have .stl — should still slugify."""
        self.assertEqual(slugify('Power_Workshop'), 'power-workshop')

    def test_already_slugified(self):
        self.assertEqual(slugify('simple-name.stl'), 'simple-name')

    def test_mixed_case(self):
        self.assertEqual(slugify('MyPart.stl'), 'mypart')

    def test_mixed_separators(self):
        """Hyphens in input are preserved; underscores become hyphens."""
        self.assertEqual(slugify('a-b_c.stl'), 'a-b-c')

    def test_dot_stl_only(self):
        """Edge case: bare '.stl' produces empty string after stripping extension."""
        self.assertEqual(slugify('.stl'), '')


class TestDisplayName(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(display_name('drill-bit.stl'), 'drill bit')

    def test_underscores(self):
        self.assertEqual(display_name('my_cool_part.stl'), 'my cool part')

    def test_uppercase_extension(self):
        self.assertEqual(display_name('Widget.STL'), 'Widget')

    def test_preserves_original_case(self):
        self.assertEqual(display_name('drill-BIT.stl'), 'drill BIT')

    def test_no_extension(self):
        self.assertEqual(display_name('some-name'), 'some name')


class TestProjectDisplayName(unittest.TestCase):
    """Canonical directory → display-name transform (issue #399)."""

    CASES = [
        ("hex-connector", "Hex Connector"),
        ("toothbrush_holder", "Toothbrush Holder"),
        ("nz-ski-fields", "Nz Ski Fields"),
        ("esp32-display-case", "Esp32 Display Case"),
        ("2x4-jig", "2X4 Jig"),
        ("d20-tray", "D20 Tray"),
        ("ESP32-case", "Esp32 Case"),
        ("mixed-CASE_dir name", "Mixed Case Dir Name"),
        ("", ""),
    ]

    def test_cases(self):
        for raw, expected in self.CASES:
            with self.subTest(raw=raw):
                self.assertEqual(project_display_name(raw), expected)


class TestThumbnailName(unittest.TestCase):

    def test_lowercase(self):
        self.assertEqual(thumbnail_name('part.stl'), 'part.png')

    def test_uppercase(self):
        self.assertEqual(thumbnail_name('Part.STL'), 'Part.png')

    def test_mixed_case(self):
        self.assertEqual(thumbnail_name('Widget.Stl'), 'Widget.png')


class TestParseScadMap(unittest.TestCase):

    def _write_map(self, content):
        """Write content to a temp file and return its path."""
        fd, path = tempfile.mkstemp(suffix='.scad-map')
        os.write(fd, content.encode())
        os.close(fd)
        self.addCleanup(os.unlink, path)
        return path

    def test_basic(self):
        path = self._write_map('part.stl\tmy-project\tmy-project/part.scad\n')
        result = parse_scad_map(path)
        self.assertIn('part.stl', result)
        self.assertEqual(result['part.stl']['dir'], 'my-project')
        self.assertEqual(result['part.stl']['project'], 'My Project')
        self.assertEqual(result['part.stl']['source'], 'my-project/part.scad')

    def test_multiple_entries(self):
        content = (
            'a.stl\tproject-one\tproject-one/a.scad\n'
            'b.stl\tproject-two\tproject-two/b.scad\n'
        )
        path = self._write_map(content)
        result = parse_scad_map(path)
        self.assertEqual(len(result), 2)
        self.assertIn('a.stl', result)
        self.assertIn('b.stl', result)

    def test_skips_empty_lines(self):
        content = '\npart.stl\tproj\tproj/part.scad\n\n'
        path = self._write_map(content)
        result = parse_scad_map(path)
        self.assertEqual(len(result), 1)

    def test_skips_malformed_lines(self):
        content = 'bad-line-no-tabs\npart.stl\tproj\tproj/part.scad\n'
        path = self._write_map(content)
        result = parse_scad_map(path)
        self.assertEqual(len(result), 1)
        self.assertIn('part.stl', result)

    def test_empty_file(self):
        path = self._write_map('')
        result = parse_scad_map(path)
        self.assertEqual(result, {})

    def test_underscore_project_dir(self):
        path = self._write_map('x.stl\tpower_workshop\tpower_workshop/x.scad\n')
        result = parse_scad_map(path)
        self.assertEqual(result['x.stl']['project'], 'Power Workshop')

    def test_skips_empty_slug(self):
        """Entries like '.stl' that slugify to '' are skipped with a warning."""
        content = '.stl\tproj\tproj/.scad\npart.stl\tproj\tproj/part.scad\n'
        path = self._write_map(content)
        result = parse_scad_map(path)
        self.assertEqual(len(result), 1)
        self.assertIn('part.stl', result)

    def test_duplicate_stl_keys(self):
        """Last entry wins when the same STL filename appears twice."""
        content = (
            'part.stl\tproject-a\tproject-a/part.scad\n'
            'part.stl\tproject-b\tproject-b/part.scad\n'
        )
        path = self._write_map(content)
        result = parse_scad_map(path)
        self.assertEqual(len(result), 1)
        self.assertEqual(result['part.stl']['dir'], 'project-b')


class TestPublicSourceUrl(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(
            public_source_url('power-workshop/drill_bit.scad'),
            'https://github.com/stjohnb/3d-models/blob/main/power-workshop/drill_bit.scad',
        )

    def test_space_in_path_segment(self):
        url = public_source_url('toothbrush/Toothbrush assembly.scad')
        self.assertTrue(url.endswith('/toothbrush/Toothbrush%20assembly.scad'))

    def test_empty_source(self):
        self.assertEqual(public_source_url(''), '')

    def test_points_at_public_mirror_not_private_repo(self):
        url = public_source_url('power-workshop/drill_bit.scad')
        self.assertIn('stjohnb/3d-models', url)
        self.assertNotIn('St-John-Software', url)


class TestStripStlExt(unittest.TestCase):

    def test_lowercase(self):
        self.assertEqual(strip_stl_ext('a.stl'), 'a')

    def test_uppercase(self):
        self.assertEqual(strip_stl_ext('A.STL'), 'A')

    def test_mixed_case(self):
        self.assertEqual(strip_stl_ext('w.Stl'), 'w')

    def test_no_extension(self):
        self.assertEqual(strip_stl_ext('no-ext'), 'no-ext')

    def test_double_extension(self):
        self.assertEqual(strip_stl_ext('a.stl.stl'), 'a.stl')

    def test_bare_stl_word(self):
        self.assertEqual(strip_stl_ext('stl'), 'stl')


class TestStandaloneUrl(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(
            standalone_url('drill-bit.stl'),
            'https://www.bstjohn.net/3d-models/standalone/drill-bit.html',
        )

    def test_space_in_name(self):
        self.assertIn('%20', standalone_url('my part.stl'))

    def test_uppercase_extension_stripped(self):
        self.assertEqual(
            standalone_url('Widget.STL'),
            'https://www.bstjohn.net/3d-models/standalone/Widget.html',
        )


class TestBuildStructuredData(unittest.TestCase):

    def _scad_map(self):
        return {
            'a.stl': {'project': 'Power Workshop', 'dir': 'power-workshop', 'source': 'power-workshop/a.scad'},
            'b part.stl': {'project': 'Toothbrush', 'dir': 'toothbrush', 'source': 'toothbrush/b part.scad'},
        }

    def test_top_level_shape(self):
        data = build_structured_data(self._scad_map(), {})
        self.assertEqual(data['@context'], 'https://schema.org')
        types = [node['@type'] for node in data['@graph']]
        self.assertEqual(types, ['Organization', 'WebSite', 'CollectionPage'])

    def test_organization_node(self):
        data = build_structured_data(self._scad_map(), {})
        org = data['@graph'][0]
        self.assertEqual(org['@id'], ORG_ID)
        self.assertEqual(
            org['sameAs'],
            ['https://github.com/St-John-Software', 'https://github.com/stjohnb'],
        )

    def test_website_and_collection_references(self):
        data = build_structured_data(self._scad_map(), {})
        website = data['@graph'][1]
        collection = data['@graph'][2]
        self.assertEqual(website['@id'], SITE_ID)
        self.assertEqual(website['publisher'], {'@id': ORG_ID})
        self.assertEqual(collection['@id'], COLLECTION_ID)
        self.assertEqual(collection['isPartOf'], {'@id': SITE_ID})
        self.assertEqual(collection['creator'], {'@id': ORG_ID})

    def test_items_reference_org_not_inline(self):
        data = build_structured_data(self._scad_map(), {})
        collection = data['@graph'][2]
        items = collection['mainEntity']['itemListElement']
        for entry in items:
            self.assertEqual(entry['item']['creator'], {'@id': ORG_ID})
        # Only the @id reference to the org should appear below mainEntity,
        # never an inline {'@type': 'Organization', ...} object.
        self.assertNotIn('"@type": "Organization"', json.dumps(collection))

    def test_item_ids_unique_and_match_standalone_url(self):
        scad_map = self._scad_map()
        data = build_structured_data(scad_map, {})
        items = data['@graph'][2]['mainEntity']['itemListElement']
        ids = [entry['item']['@id'] for entry in items]
        self.assertEqual(len(ids), len(set(ids)))
        for stl, entry in zip(sorted(scad_map), items):
            self.assertEqual(entry['item']['@id'], f'{standalone_url(stl)}#model')
            self.assertTrue(entry['item']['@id'].endswith('#model'))

    def test_positions_in_sorted_order(self):
        data = build_structured_data(self._scad_map(), {})
        items = data['@graph'][2]['mainEntity']['itemListElement']
        self.assertEqual([entry['position'] for entry in items], [1, 2])

    def test_content_size_present_only_when_given(self):
        scad_map = self._scad_map()
        data = build_structured_data(scad_map, {}, stl_sizes={'a.stl': 123})
        items = {entry['item']['@id']: entry['item'] for entry in data['@graph'][2]['mainEntity']['itemListElement']}
        a_item = items[f'{standalone_url("a.stl")}#model']
        b_item = items[f'{standalone_url("b part.stl")}#model']
        self.assertEqual(a_item['contentSize'], '123 B')
        self.assertNotIn('contentSize', b_item)

    def test_description_fallback(self):
        data = build_structured_data(self._scad_map(), {})
        item = data['@graph'][2]['mainEntity']['itemListElement'][0]['item']
        self.assertEqual(item['description'], '3D printable part from the Power Workshop collection')

    def test_description_from_project_descriptions(self):
        data = build_structured_data(self._scad_map(), {'power-workshop': 'Custom description'})
        item = data['@graph'][2]['mainEntity']['itemListElement'][0]['item']
        self.assertEqual(item['description'], 'Custom description')


class TestStlLastmods(unittest.TestCase):

    def _write_models(self, data):
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f)
        self.addCleanup(os.unlink, path)
        return path

    def test_maps_every_file_to_project_updated(self):
        path = self._write_models({
            'Dated Project': {
                'dir': 'dated-project',
                'updated': '2026-08-12T14:03:22+01:00',
                'files': [{'stl': 'a.stl'}, {'stl': 'b.stl'}],
            },
            'Undated Project': {
                'dir': 'undated-project',
                'files': [{'stl': 'c.stl'}],
            },
        })
        result = stl_lastmods(path)
        self.assertEqual(result['a.stl'], '2026-08-12T14:03:22+01:00')
        self.assertEqual(result['b.stl'], '2026-08-12T14:03:22+01:00')
        self.assertNotIn('c.stl', result)

    def test_missing_file_returns_empty(self):
        self.assertEqual(stl_lastmods('/nonexistent/models.json'), {})

    def test_malformed_json_returns_empty(self):
        fd, path = tempfile.mkstemp(suffix='.json')
        os.write(fd, b'not json')
        os.close(fd)
        self.addCleanup(os.unlink, path)
        self.assertEqual(stl_lastmods(path), {})

    def test_entry_without_files_is_skipped(self):
        path = self._write_models({
            'Dated Project': {
                'dir': 'dated-project',
                'updated': '2026-08-12T14:03:22+01:00',
            },
        })
        self.assertEqual(stl_lastmods(path), {})


class TestBuildSitemap(unittest.TestCase):

    def test_root_and_each_stl_present(self):
        xml = build_sitemap(['a.stl', 'b part.stl'])
        self.assertIn(f'<loc>{BASE_URL}/</loc>', xml)
        self.assertIn(standalone_url('a.stl'), xml)
        self.assertIn(standalone_url('b part.stl'), xml)
        self.assertEqual(xml.count('<url>'), 3)

    def test_no_lastmod_when_dates_absent(self):
        self.assertNotIn('<lastmod>', build_sitemap(['a.stl']))

    def test_lastmod_emitted_per_stl(self):
        xml = build_sitemap(['a.stl'], {'a.stl': '2026-08-12T14:03:22+01:00'})
        for line in xml.splitlines():
            if standalone_url('a.stl') in line:
                self.assertIn('<lastmod>2026-08-12T14:03:22+01:00</lastmod>', line)
                return
        self.fail('a.stl <url> line not found')

    def test_partial_lastmods(self):
        xml = build_sitemap(
            ['a.stl', 'b.stl'], {'a.stl': '2026-08-12T14:03:22+01:00'}
        )
        for line in xml.splitlines():
            if standalone_url('b.stl') in line:
                self.assertNotIn('<lastmod>', line)
                return
        self.fail('b.stl <url> line not found')

    def test_root_uses_newest_date_across_offsets(self):
        # a.stl: 2026-08-12T00:30:00+01:00 == 2026-08-11T23:30:00 UTC
        # b.stl: 2026-08-11T23:45:00+00:00 == 2026-08-11T23:45:00 UTC (later)
        lastmods = {
            'a.stl': '2026-08-12T00:30:00+01:00',
            'b.stl': '2026-08-11T23:45:00+00:00',
        }
        xml = build_sitemap(['a.stl', 'b.stl'], lastmods)
        for line in xml.splitlines():
            if f'<loc>{BASE_URL}/</loc>' in line:
                self.assertIn('<lastmod>2026-08-11T23:45:00+00:00</lastmod>', line)
                return
        self.fail('root <url> line not found')

    def test_unparsable_date_ignored_for_root_but_kept_on_entry(self):
        xml = build_sitemap(['a.stl'], {'a.stl': 'not-a-date'})
        for line in xml.splitlines():
            if f'<loc>{BASE_URL}/</loc>' in line:
                self.assertNotIn('<lastmod>', line)
            if standalone_url('a.stl') in line:
                self.assertIn('<lastmod>not-a-date</lastmod>', line)

    def test_empty_stl_list(self):
        xml = build_sitemap([])
        self.assertEqual(xml.count('<url>'), 1)
        self.assertIn(f'<loc>{BASE_URL}/</loc>', xml)

    def test_output_is_well_formed_xml(self):
        xml = build_sitemap(['a.stl', 'b.stl'], {'a.stl': '2026-08-12T14:03:22+01:00'})
        root = ET.fromstring(xml)
        self.assertEqual(len(root), 3)


class TestOgHeroThumbnails(unittest.TestCase):

    def _scad_map(self, entries):
        """entries: {project_dir: [stl, ...]} -> parse_scad_map-shaped dict."""
        scad_map = {}
        for project_dir, stls in entries.items():
            for stl in stls:
                scad_map[stl] = {
                    'project': project_display_name(project_dir),
                    'dir': project_dir,
                    'source': f'{project_dir}/{stl}',
                }
        return scad_map

    def test_hero_honoured(self):
        """limit=1 isolates the one-per-project pass from the grid-fill pass."""
        scad_map = self._scad_map({
            'blast-gate': ['gate_assembly.stl', 'gate_body.stl'],
        })
        existing = {'gate_assembly.png', 'gate_body.png'}
        result = og_hero_thumbnails(scad_map, {'blast-gate': 'gate_assembly.stl'}, existing, limit=1)
        self.assertEqual(result, ['gate_assembly.png'])

    def test_no_hero_declared_falls_back_to_alphabetical(self):
        scad_map = self._scad_map({
            'blast-gate': ['gate_body.stl', 'gate_assembly.stl'],
        })
        existing = {'gate_assembly.png', 'gate_body.png'}
        result = og_hero_thumbnails(scad_map, {}, existing, limit=1)
        self.assertEqual(result, ['gate_assembly.png'])

    def test_hero_thumbnail_missing_falls_back(self):
        scad_map = self._scad_map({
            'blast-gate': ['gate_assembly.stl', 'gate_body.stl'],
        })
        existing = {'gate_body.png'}
        result = og_hero_thumbnails(scad_map, {'blast-gate': 'gate_assembly.stl'}, existing)
        self.assertEqual(result, ['gate_body.png'])

    def test_project_with_zero_surviving_thumbnails_contributes_nothing(self):
        scad_map = self._scad_map({
            'blast-gate': ['gate_assembly.stl'],
            'hex-connector': ['hex.stl'],
        })
        existing = {'hex.png'}
        result = og_hero_thumbnails(scad_map, {}, existing)
        self.assertEqual(result, ['hex.png'])

    def test_one_tile_per_project_in_dir_order(self):
        """limit=3 isolates the one-per-project pass from the grid-fill pass."""
        scad_map = self._scad_map({
            'proj-a': ['a1.stl', 'a2.stl', 'a3.stl'],
            'proj-b': ['b1.stl', 'b2.stl', 'b3.stl'],
            'proj-c': ['c1.stl', 'c2.stl', 'c3.stl'],
        })
        existing = {f'{p}{n}.png' for p in 'abc' for n in '123'}
        result = og_hero_thumbnails(scad_map, {}, existing, limit=3)
        self.assertEqual(result, ['a1.png', 'b1.png', 'c1.png'])

    def test_grid_fill_no_duplicates(self):
        scad_map = self._scad_map({
            'proj-a': [f'a{n}.stl' for n in range(5)],
            'proj-b': [f'b{n}.stl' for n in range(5)],
        })
        existing = {f'{p}{n}.png' for p in 'ab' for n in range(5)}
        result = og_hero_thumbnails(scad_map, {}, existing)
        self.assertEqual(len(result), 10)
        self.assertEqual(len(set(result)), 10)

    def test_hard_cap_at_max_tiles(self):
        scad_map = self._scad_map({
            f'proj-{i:02d}': [f'p{i:02d}-a.stl', f'p{i:02d}-b.stl']
            for i in range(20)
        })
        existing = {thumbnail_name(stl) for stl in scad_map}
        result = og_hero_thumbnails(scad_map, {}, existing)
        self.assertEqual(len(result), OG_HERO_MAX_TILES)
        self.assertEqual(len(set(result)), OG_HERO_MAX_TILES)
        self.assertEqual(OG_HERO_MAX_TILES, OG_HERO_TILE_COLUMNS * OG_HERO_TILE_ROWS)

    def test_orthographic_views_never_selected(self):
        scad_map = self._scad_map({
            'drawer-organiser': ['drawer_bin_5x5.stl'],
        })
        existing = {'drawer_bin_5x5.png', 'drawer_bin_5x5_top.png'}
        result = og_hero_thumbnails(scad_map, {}, existing)
        self.assertNotIn('drawer_bin_5x5_top.png', result)
        self.assertEqual(result, ['drawer_bin_5x5.png'])

    def test_space_in_filename(self):
        scad_map = self._scad_map({
            'toothbrush': ['Toothbrush assembly.stl'],
        })
        existing = {'Toothbrush assembly.png'}
        result = og_hero_thumbnails(
            scad_map, {'toothbrush': 'Toothbrush assembly.stl'}, existing,
        )
        self.assertEqual(result, ['Toothbrush assembly.png'])


if __name__ == '__main__':
    unittest.main()
