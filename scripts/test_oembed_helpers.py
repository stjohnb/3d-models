"""Unit tests for oembed_helpers.py.

Covers slugify, display_name, thumbnail_name, and parse_scad_map.
slugify must stay in sync with the JS implementations in index.html and
embed.html — these tests document the expected edge-case behaviour.
"""

import os
import tempfile
import unittest

from oembed_helpers import slugify, display_name, thumbnail_name, parse_scad_map


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


if __name__ == '__main__':
    unittest.main()
