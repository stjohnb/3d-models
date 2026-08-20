"""Frame extraction and sharpness selection for the photogrammetry pipeline.

Operator tool — not used by CI. Third-party imports (cv2) are deliberately
lazy so the stdlib-only helpers stay importable outside `nix develop .#scan`.
"""

import json
import pathlib
import subprocess


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
