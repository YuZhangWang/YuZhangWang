#!/usr/bin/env python3
"""Refresh the GitHub profile's local SVG snapshots.

The profile README cannot run JavaScript, and GitHub strips inline styles and
event handlers. Keeping the stats and visitor badge as committed SVG files
means the profile itself does not depend on a third-party image service at
render time. This workflow refreshes those snapshots on a schedule.
"""

import os
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGES_DIR = ROOT / "images"

STAT_DOWNLOADS = [
    (
        "https://github-readme-stats.shion.dev/api?username=YuZhangWang"
        "&show_icons=true&line_height=28&hide_border=true&card_width=347"
        "&include_all_commits=true&role=owner,collaborator"
        "&show=reviews,discussions_answered&rank_icon=percentile"
        "&exclude_repo=github-readme-stats&theme=default",
        "github-stats-light.svg",
    ),
    (
        "https://github-readme-stats.shion.dev/api?username=YuZhangWang"
        "&show_icons=true&line_height=28&hide_border=true&card_width=347"
        "&include_all_commits=true&role=owner,collaborator"
        "&show=reviews,discussions_answered&rank_icon=percentile"
        "&exclude_repo=github-readme-stats&theme=dark&bg_color=000000",
        "github-stats-dark.svg",
    ),
    (
        "https://github-readme-stats.shion.dev/api/top-langs/?username=YuZhangWang"
        "&layout=compact&langs_count=12&hide_border=true"
        "&role=owner,collaborator&theme=default",
        "github-langs-light.svg",
    ),
    (
        "https://github-readme-stats.shion.dev/api/top-langs/?username=YuZhangWang"
        "&layout=compact&langs_count=12&hide_border=true"
        "&role=owner,collaborator&theme=dark&bg_color=000000",
        "github-langs-dark.svg",
    ),
    (
        "https://komarev.com/ghpvc/?username=YuZhangWang&color=blue&style=for-the-badge",
        "visitor-badge.svg",
    ),
]


def fetch(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "YuZhangWang-profile-updater/1.0",
            "Accept": "image/svg+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
        status = getattr(response, "status", 200)
        if status != 200:
            raise RuntimeError(url + " returned HTTP " + str(status))
        return data


def refresh_snapshot(url, filename):
    destination = IMAGES_DIR / filename
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        data = fetch(url)
        temporary.write_bytes(data)
        os.replace(temporary, destination)
        print("Updated " + filename)
        return True
    except Exception as error:
        print("Skipped " + filename + ": " + str(error))
        if temporary.exists():
            temporary.unlink()
        return False


def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    refreshed = 0
    for url, filename in STAT_DOWNLOADS:
        if refresh_snapshot(url, filename):
            refreshed += 1
    print("Refreshed " + str(refreshed) + " local SVG snapshots")


if __name__ == "__main__":
    main()
