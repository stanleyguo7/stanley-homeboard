#!/usr/bin/env python3
"""Fetch Netflix release headlines using What's On Netflix feed."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

project_root = Path(__file__).resolve().parent
reports_dir = project_root / "reports"
reports_dir.mkdir(exist_ok=True)

FEED_URL = "https://www.whats-on-netflix.com/feed/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"}


def fetch(limit: int = 10):
    try:
        resp = requests.get(FEED_URL, timeout=12, headers=HEADERS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to fetch feed: {exc}")
        return []
    root = ET.fromstring(resp.text)
    releases = []
    for item in root.findall("channel/item")[:limit]:
        title = item.findtext("title", default="").strip()
        summary = item.findtext("description", default="").strip()
        releases.append({"title": title, "summary": summary[:220], "region": "HK Feed"})
    return releases


def write(releases):
    dest = reports_dir / "new-releases.json"
    dest.write_text(json.dumps(releases, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def main():
    releases = fetch()
    if not releases:
        print("No releases fetched.")
        return
    path = write(releases)
    print(f"Saved {len(releases)} releases to {path}")


if __name__ == "__main__":
    main()
