#!/usr/bin/env python3
"""Generate a Model Gallery section in README.md from models.json and meta.json files."""

import html
import json
import os
import sys
from urllib.parse import quote

from oembed_helpers import slugify

MODELS_JSON = "site/models.json"
README_PATH = "README.md"
BASE_URL = "https://www.bstjohn.net/3d-models"

START_MARKER = "<!-- gallery:start -->"
END_MARKER = "<!-- gallery:end -->"


def get_project_dir(files):
    """Derive project directory from the first file's source path."""
    if not files:
        return None
    source = files[0].get("source", "")
    return source.split("/")[0] if "/" in source else None


def load_description(project_dir):
    """Load description from meta.json, falling back to a dash."""
    meta_path = os.path.join(project_dir, "meta.json")
    try:
        with open(meta_path) as f:
            meta = json.load(f)
        return meta.get("description", "\u2014")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return "\u2014"


def pick_thumbnail(files):
    """Pick a representative thumbnail: first STL alphabetically, derive PNG name."""
    stls = sorted(f["stl"] for f in files if f.get("stl"))
    if not stls:
        return None
    return stls[0].rsplit(".", 1)[0] + ".png"


def generate_gallery_table(models):
    """Generate the markdown gallery table from models.json data."""
    lines = []
    lines.append("| | Project | Models | Description |")
    lines.append("|:-:|---------|:------:|-------------|")

    for project_name in sorted(models.keys(), key=str.casefold):
        entry = models[project_name]
        files = entry.get("files", [])
        project_dir = entry.get("dir") or get_project_dir(files)

        if not project_dir:
            continue

        description = entry.get("description") or load_description(project_dir)
        thumbnail = pick_thumbnail(files)
        model_count = len(files)
        viewer_url = f"{BASE_URL}/#{slugify(project_name)}"

        if thumbnail:
            img_tag = (
                f'<a href="{html.escape(viewer_url)}">'
                f'<img src="{html.escape(f"{BASE_URL}/{quote(thumbnail)}")}" width="160" alt="{html.escape(project_name)}"'
                f" onerror=\"this.style.display='none'\">"
                f"</a>"
            )
        else:
            img_tag = ""

        safe_name = project_name.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        safe_desc = description.replace("|", "\\|")
        lines.append(f"| {img_tag} | [**{safe_name}**]({viewer_url}) | {model_count} | {safe_desc} |")

    return "\n".join(lines)


def update_readme(gallery_content):
    """Replace content between gallery markers in README.md."""
    with open(README_PATH) as f:
        readme = f.read()

    start_idx = readme.find(START_MARKER)
    end_idx = readme.find(END_MARKER)

    if start_idx == -1 or end_idx == -1:
        print(f"WARNING: Gallery markers not found in {README_PATH}, skipping update")
        return False

    if end_idx <= start_idx:
        print(f"WARNING: Gallery markers are out of order in {README_PATH}, skipping update")
        return False

    new_readme = (
        readme[: start_idx + len(START_MARKER)]
        + "\n"
        + gallery_content
        + "\n"
        + readme[end_idx:]
    )

    with open(README_PATH, "w") as f:
        f.write(new_readme)

    return True


def main():
    if not os.path.exists(MODELS_JSON):
        print(f"WARNING: {MODELS_JSON} not found, skipping gallery generation")
        sys.exit(0)

    with open(MODELS_JSON) as f:
        models = json.load(f)

    if not models:
        print("WARNING: models.json is empty, skipping gallery generation")
        sys.exit(0)

    gallery_table = generate_gallery_table(models)
    if update_readme(gallery_table):
        print(f"Updated {README_PATH} with gallery for {len(models)} projects")
    else:
        print("Gallery update skipped")


if __name__ == "__main__":
    main()
