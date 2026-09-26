"""Unit tests for scan_frames.py.

Covers the pure, stdlib-only selectors: select_sharp_frames (binned) and the
hold-detection helpers (hold_threshold, find_static_runs, select_hold_frames,
thin_evenly). score_sharpness and score_sharpness_and_diffs need cv2, so they
are not exercised here.
Run with: python3 -m unittest scripts/test_scan_frames.py
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from scan_frames import (
    find_static_runs, hold_threshold, select_hold_frames, select_sharp_frames,
    thin_evenly,
)


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


class HoldThresholdTests(unittest.TestCase):
    def test_clamps_to_floor_above_a_mixed_distribution(self):
        diffs = [0.5] * 40 + [12.0] * 10
        self.assertEqual(hold_threshold(diffs), max(0.35, 1.5 * 0.5))

    def test_all_quiet_clamps_to_the_floor(self):
        self.assertEqual(hold_threshold([0.1] * 20), 0.35)

    def test_realistic_mix_lands_between_holds_and_motion(self):
        diffs = [0.54] * 30 + [8.0, 19.0, 11.0]
        threshold = hold_threshold(diffs)
        self.assertGreater(threshold, 0.54)
        self.assertLess(threshold, 8.0)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            hold_threshold([])


class FindStaticRunsTests(unittest.TestCase):
    def test_pins_the_frame_space_mapping(self):
        diffs = [0.1] * 11 + [9.0] * 4 + [0.1] * 11
        self.assertEqual(find_static_runs(diffs, 1.0), [(0, 12), (15, 27)])

    def test_short_lull_is_dropped_by_default_min_run(self):
        diffs = [9.0] * 5 + [0.1] * 4 + [9.0] * 5
        self.assertEqual(find_static_runs(diffs, 1.0), [])

    def test_all_low_is_one_run(self):
        self.assertEqual(find_static_runs([0.1] * 20, 1.0), [(0, 21)])

    def test_empty_diffs(self):
        self.assertEqual(find_static_runs([], 1.0), [])

    def test_min_run_is_honoured_when_passed_explicitly(self):
        diffs = [9.0] * 5 + [0.1] * 4 + [9.0] * 5
        self.assertEqual(find_static_runs(diffs, 1.0, min_run=3), [(5, 10)])


class SelectHoldFramesTests(unittest.TestCase):
    def test_settle_margin_excludes_the_lead_in(self):
        scores = [0.0] * 20
        scores[1] = 100.0   # in the trimmed lead-in margin (0..4)
        scores[10] = 50.0   # inside the trimmed window (5..14)
        self.assertEqual(select_hold_frames(scores, [(0, 20)]), [10])

    def test_run_of_ten_uses_margin_two(self):
        scores = [0.0] * 10
        scores[2] = 1.0
        scores[7] = 5.0
        self.assertEqual(select_hold_frames(scores, [(0, 10)]), [7])

    def test_two_runs_return_two_ascending_indices(self):
        scores = [0.0] * 40
        scores[10] = 5.0
        scores[30] = 5.0
        self.assertEqual(select_hold_frames(scores, [(0, 20), (20, 40)]), [10, 30])

    def test_tied_scores_return_the_windows_lowest_index(self):
        scores = [1.0] * 20
        self.assertEqual(select_hold_frames(scores, [(0, 20)]), [5])

    def test_run_len_four_still_returns_one_frame(self):
        scores = [0.0, 1.0, 2.0, 3.0]
        self.assertEqual(select_hold_frames(scores, [(0, 4)]), [2])

    def test_degenerate_run_falls_back_to_untrimmed_window(self):
        scores = [0.0, 0.0, 0.0, 5.0]
        self.assertEqual(select_hold_frames(scores, [(3, 4)]), [3])

    def test_run_stop_beyond_scores_raises(self):
        with self.assertRaises(ValueError):
            select_hold_frames([0.0, 1.0], [(0, 3)])


class ThinEvenlyTests(unittest.TestCase):
    def test_fewer_indices_than_count_returns_everything(self):
        self.assertEqual(thin_evenly(list(range(52)), 150), list(range(52)))

    def test_thins_evenly(self):
        self.assertEqual(thin_evenly([0, 1, 2, 3, 4], 3), [0, 1, 3])

    def test_output_is_strictly_increasing_and_the_requested_length(self):
        selected = thin_evenly(list(range(300)), 150)
        self.assertEqual(len(selected), 150)
        self.assertEqual(selected, sorted(set(selected)))

    def test_count_below_one_raises(self):
        with self.assertRaises(ValueError):
            thin_evenly([0, 1, 2], 0)


if __name__ == "__main__":
    unittest.main()
