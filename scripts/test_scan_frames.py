"""Unit tests for scan_frames.py.

Covers select_sharp_frames only — the pure, stdlib-only part. ffmpeg/ffprobe
invocation and cv2 sharpness scoring are not exercised here.
Run with: python3 -m unittest scripts/test_scan_frames.py
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from scan_frames import select_sharp_frames


class SelectSharpFramesTests(unittest.TestCase):
    def test_picks_the_max_score_in_each_bin(self):
        # Six scores, three bins of two: (0,1), (2,3), (4,5).
        scores = [1.0, 9.0, 8.0, 2.0, 3.0, 7.0]
        self.assertEqual(select_sharp_frames(scores, 3), [1, 2, 5])

    def test_1900_frames_to_150_spreads_evenly(self):
        n, count = 1900, 150
        scores = [float(i % 7) for i in range(n)]
        selected = select_sharp_frames(scores, count)

        self.assertEqual(len(selected), count)
        self.assertEqual(selected, sorted(set(selected)))
        for i, index in enumerate(selected):
            start = i * n // count
            end = (i + 1) * n // count
            self.assertGreaterEqual(index, start)
            self.assertLess(index, end)

    def test_fewer_scores_than_count_returns_everything(self):
        self.assertEqual(select_sharp_frames([3.0, 1.0, 2.0], 10), [0, 1, 2])
        self.assertEqual(select_sharp_frames([3.0, 1.0, 2.0], 3), [0, 1, 2])
        self.assertEqual(select_sharp_frames([], 5), [])

    def test_count_below_one_raises(self):
        with self.assertRaises(ValueError):
            select_sharp_frames([1.0, 2.0], 0)
        with self.assertRaises(ValueError):
            select_sharp_frames([1.0, 2.0], -1)

    def test_tie_goes_to_the_lower_index(self):
        self.assertEqual(select_sharp_frames([5.0, 5.0, 5.0, 5.0], 2), [0, 2])


if __name__ == "__main__":
    unittest.main()
