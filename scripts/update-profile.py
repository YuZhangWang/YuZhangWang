#!/usr/bin/env python3
"""Refresh the GitHub profile README and its local SVG snapshots.

The profile README cannot run JavaScript and GitHub strips inline styles and
event handlers, so this script keeps the runtime dependency-free by:

1. Updating the Recent Blog table from the site RSS feed.
2. Fetching fresh GitHub stats and visitor-count SVG snapshots into images/.

The workflow commits the generated files back to the repository.
"""

import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
IMAGES_DIR = ROOT / "images"

RSS_URL = "https://yuzhang.wang/rss2.xml"
POST_COUNT = 10

BLOG_START = "<!-- BLOG-POST-LIST:START -->"
BLOG_END = "<!-- BLOG-POST-LIST:END -->"

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


def fetch(url: str) -> bytes:
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
            raise RuntimeError(f"{url} returned HTTP {status}")
        return data


def parse_blog_entries() -> List[dict]:
    raw = fetch(RSS_URL).decode("utf-8", errors="replace")
    root = ET.fromstring(raw)
    entries = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        if not title or not link or not pub_date:
            continue
        try:
            parsed_date = parsedate_to_datetime(pub_date)
        except (TypeError, ValueError):
            parsed_date = None
        entries.append(
            {
                "title": title,
                "url": link,
                "date": parsed_date,
            }
        )

    entries.sort(key=lambda entry: entry["date"] or datetime.min, reverse=True)
    return [
        {
            "title": item["title"],
            "url": item["url"],
            "date": item["date"].strftime("%Y-%m-%d") if item["date"] else "",
        }
        for item in entries[:POST_COUNT]
    ]


def update_blog_section(readme: str, entries: List[dict]) -> str:
    if BLOG_START not in readme or BLOG_END not in readme:
        raise RuntimeError("README is missing the BLOG-POST-LIST markers")

    rows = []
    for entry in entries:
        title = entry["title"].replace("|", "\\|")
        rows.append(f"| {entry['date']} | [{title}]({entry['url']}) |")

    content = "\n".join(rows)
    start_index = readme.index(BLOG_START)
    end_index = readme.index(BLOG_END)
    return (
        readme[: start_index + len(BLOG_START)]
        + "\n"
        + content
        + "\n"
        + readme[end_index:]
    )


def refresh_snapshot(url: str, filename: str) -> bool:
    destination = IMAGES_DIR / filename
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        data = fetch(url)
        temporary.write_bytes(data)
        os.replace(temporary, destination)
        print(f"Updated {filename}")
        return True
    except Exception as error:
        print(f"Skipped {filename}: {error}")
        if temporary.exists():
            temporary.unlink()
        return False


def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    readme = README_PATH.read_text(encoding="utf-8")

    try:
        entries = parse_blog_entries()
        new_readme = update_blog_section(readme, entries)
        if new_readme != readme:
            README_PATH.write_text(new_readme, encoding="utf-8")
            print(f"Updated Recent Blog with {len(entries)} posts")
        else:
            print("Recent Blog is already up to date")
    except Exception as error:
        new_readme = readme
        print(f"Recent Blog update skipped: {error}")

    refreshed = 0
    for url, filename in STAT_DOWNLOADS:
        if refresh_snapshot(url, filename):
            refreshed += 1
    print(f"Refreshed {refreshed} local SVG snapshots")


if __name__ == "__main__":
    main()
