"""Frame extraction and sharpness selection for the photogrammetry pipeline.

Operator tool — not used by CI. Third-party imports (cv2) are deliberately
lazy so the stdlib-only helpers stay importable outside `nix develop .#scan`.
"""

import json
import math
import pathlib
import subprocess

HOLD_MIN_RUN = 10        # frames of stillness that count as a hold (~1/3 s at 30 fps)
HOLD_SETTLE_MAX = 5      # frames trimmed off each end of a hold before picking
HOLD_DIFF_FLOOR = 0.35   # absolute MAD floor; measured hold medians are ~0.54
DIFF_THUMB_WIDTH = 128   # diff thumbnails: 128 px wide, aspect preserved (~128x228 portrait)


def probe_video(path):
    """Return the ffprobe stream dict for a video's first video stream.

    Note `nb_frames` is commonly "N/A" for MOV containers — never rely on it;
    count the files ffmpeg actually writes instead.
    """
    argv = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,nb_frames,avg_frame_rate",
        "-of", "json",
        str(path),
    ]
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {proc.stderr.strip()}")
    streams = json.loads(proc.stdout).get("streams", [])
    if not streams:
        raise RuntimeError(f"ffprobe found no video stream in {path}")
    return streams[0]


def extract_all_frames(video, out_dir, quiet=False):
    """Decode every frame of `video` into `out_dir` as JPEG, return sorted paths.

    JPEG q2 rather than PNG: a ~1900-frame capture at 720x1280 exceeds 1 GB as
    PNG, and the quality difference is invisible to SIFT.
    """
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    argv = [
        "ffmpeg", "-nostdin", "-y",
        "-i", str(video),
        "-vsync", "0",
        "-qscale:v", "2",
        str(out_dir / "%06d.jpg"),
    ]
    proc = subprocess.run(
        argv,
        capture_output=quiet,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"ffmpeg failed for {video}: {stderr}")
    return sorted(out_dir.glob("*.jpg"))


def score_sharpness(paths):
    """Variance-of-Laplacian sharpness score for each frame path."""
    import cv2

    scores = []
    for path in paths:
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise RuntimeError(f"could not read frame {path}")
        scores.append(float(cv2.Laplacian(image, cv2.CV_64F).var()))
    return scores


def select_sharp_frames(scores, count):
    """Pick `count` frame indices: the sharpest frame from each contiguous bin.

    Binning (rather than a global top-N) keeps the selection spread evenly
    around the turntable rotation — a global top-N would happily take every
    frame from the one stretch where the object happened to be best lit.

    Pure stdlib. Ties resolve to the lowest index.
    """
    if count < 1:
        raise ValueError("count must be at least 1")
    n = len(scores)
    if n <= count:
        return list(range(n))

    selected = []
    for i in range(count):
        start = i * n // count
        end = (i + 1) * n // count
        if start >= end:
            continue
        best = start
        for j in range(start + 1, end):
            if scores[j] > scores[best]:
                best = j
        selected.append(best)
    return sorted(selected)


def percentile(values, fraction):
    """Linear-interpolation percentile, numpy-compatible. Pure stdlib."""
    if not values:
        raise ValueError("cannot take a percentile of no values")
    ordered = sorted(values)
    idx = fraction * (len(ordered) - 1)
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo)


def hold_threshold(diffs):
    """Static/motion cutoff for consecutive-frame mean-absolute-diffs.

    Holds are the low mode of the diff distribution: on real captures hold
    medians sit around 0.5 and motion peaks 8-19, so the 25th percentile
    lands inside the hold mode. `HOLD_DIFF_FLOOR` guards an all-static clip
    where that percentile would otherwise be near zero.
    """
    return max(HOLD_DIFF_FLOOR, 1.5 * percentile(diffs, 0.25))


def find_static_runs(diffs, threshold, min_run=HOLD_MIN_RUN):
    """Maximal runs of mutually-static frames, as half-open frame intervals.

    `diffs[i]` is the mean-absolute-diff between frame `i` and frame `i+1`.
    A maximal block of consecutive indices `a..b` with `diffs[i] < threshold`
    means frames `a` through `b+1` are mutually static, hence the half-open
    interval `(a, b + 2)` — a 10-frame hold needs 9 consecutive sub-threshold
    diffs. Only intervals with `stop - start >= min_run` are kept.
    """
    runs = []
    start = None
    for i, value in enumerate(diffs):
        if value < threshold:
            if start is None:
                start = i
        else:
            if start is not None:
                runs.append((start, i + 1))
                start = None
    if start is not None:
        runs.append((start, len(diffs) + 1))
    return [(a, b) for a, b in runs if b - a >= min_run]


def select_hold_frames(scores, runs, settle_max=HOLD_SETTLE_MAX):
    """One max-sharpness frame per hold, skipping a settle margin per end.

    Raises ValueError if any run's stop index exceeds len(scores).
    """
    selected = []
    for start, stop in runs:
        if stop > len(scores):
            raise ValueError(f"run {(start, stop)} exceeds {len(scores)} scores")
        run_len = stop - start
        margin = min(settle_max, run_len // 4)
        lo, hi = start + margin, stop - margin
        if hi <= lo:
            lo, hi = start, stop
        best = lo
        for j in range(lo + 1, hi):
            if scores[j] > scores[best]:
                best = j
        selected.append(best)
    return sorted(selected)


def thin_evenly(indices, count):
    """Evenly-spaced subset of `indices` of length `count`, strictly increasing.

    Keeps angular coverage rather than favouring one part of the sequence.
    """
    if count < 1:
        raise ValueError("count must be at least 1")
    n = len(indices)
    if n <= count:
        return list(indices)
    return [indices[i * n // count] for i in range(count)]


def score_sharpness_and_diffs(paths, width=DIFF_THUMB_WIDTH):
    """Sharpness scores and consecutive-frame diffs from a single decode pass.

    One decode per frame produces both signals — at 4K a second full decode
    pass costs ~5 minutes, so do not also call `score_sharpness` in hold mode.
    Sharpness matches `score_sharpness` exactly, so continuous mode's
    behaviour is unchanged. Returns `(scores, diffs)` with
    `len(diffs) == max(0, len(scores) - 1)`.
    """
    import cv2
    import numpy

    scores = []
    diffs = []
    target = None
    prev = None
    for path in paths:
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise RuntimeError(f"could not read frame {path}")
        scores.append(float(cv2.Laplacian(image, cv2.CV_64F).var()))

        if target is None:
            h, w = image.shape[:2]
            target = (width, max(1, round(width * h / w)))
        thumb = cv2.resize(image, target, interpolation=cv2.INTER_AREA).astype(numpy.int16)
        if prev is not None:
            diffs.append(float(numpy.abs(thumb - prev).mean()))
        prev = thumb
    return scores, diffs
