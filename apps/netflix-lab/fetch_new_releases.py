#!/usr/bin/env python3
"""Fetch Netflix release headlines using What's On Netflix feed."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

project_root = Path(__file__).resolve().parent
reports_dir = project_root / "reports"
reports_dir.mkdir(exist_ok=True)

FEED_URL = "https://www.whats-on-netflix.com/feed/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"}
FLIXABLE_URL = "https://flixable.com/new-on-netflix/"


def fetch_from_feed(limit: int = 6):
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
        link = item.findtext("link", default="https://www.netflix.com/").strip()
        releases.append({
            "title": title,
            "summary": summary[:220],
            "region": "HK Feed",
            "source_link": link,
        })
    return releases


def fetch_from_flixable(limit: int = 6):
    try:
        resp = requests.get(FLIXABLE_URL, timeout=12, headers=HEADERS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to fetch Flixable: {exc}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("div.post-list > article")[:limit]
    releases = []
    for card in cards:
        title_elem = card.select_one("h2.entry-title a")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        link = title_elem["href"]
        summary_tag = card.select_one("div.entry-content p")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""
        releases.append({
            "title": title,
            "summary": summary[:220],
            "region": "HK Flixable",
            "source_link": link,
        })
    return releases


def fetch(limit: int = 8):
    feed_releases = fetch_from_feed(limit=limit//2)
    flixable_releases = fetch_from_flixable(limit=limit//2)
    combined = feed_releases + flixable_releases
    seen = set()
    deduped = []
    for release in combined:
        key = release["title"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(release)
    return deduped[:limit]


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
