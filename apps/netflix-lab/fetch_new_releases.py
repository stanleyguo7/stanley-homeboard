#!/usr/bin/env python3
"""Fetch Netflix release headlines using multiple sources (HK focus)."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

project_root = Path(__file__).resolve().parent
reports_dir = project_root / "reports"
reports_dir.mkdir(exist_ok=True)

FEED_URL = "https://www.whats-on-netflix.com/feed/"
NEXT_URL = "https://about.netflix.com/zh_cn/new-to-watch"
FLIXABLE_URL = "https://flixable.com/new-on-netflix/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"}


def parse_feed(limit: int = 4):
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
            "region": "feed",
            "source_link": link,
        })
    return releases


def parse_next(limit: int = 6):
    try:
        resp = requests.get(NEXT_URL, timeout=12, headers=HEADERS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to fetch Next data: {exc}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    script = soup.select_one("script#__NEXT_DATA__")
    if not script or not script.string:
        return []
    data = json.loads(script.string)
    entries = data.get("props", {}).get("pageProps", {}).get("data", {}).get("results", {}).get("data", [])
    releases = []
    for entry in entries[:limit]:
        title = entry.get("title1") or entry.get("title2")
        if not title:
            continue
        summary = entry.get("summary") or entry.get("description") or ""
        video_id = entry.get("videoID")
        link = f"https://www.netflix.com/title/{video_id}" if video_id else "https://www.netflix.com/"
        releases.append({
            "title": title,
            "summary": summary[:220],
            "region": entry.get("country", "HK"),
            "source_link": link,
            "cover": entry.get("image"),
        })
    return releases


def parse_flixable(limit: int = 4):
    try:
        resp = requests.get(FLIXABLE_URL, timeout=12, headers=HEADERS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to fetch Flixable: {exc}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("div.post-list article")[:limit]
    releases = []
    for card in cards:
        title_elem = card.select_one("h2.entry-title a")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        link = title_elem["href"]
        summary_tag = card.select_one("div.entry-content p")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""
        image_tag = card.select_one("img")
        image = image_tag["src"] if image_tag else None
        releases.append({
            "title": title,
            "summary": summary[:220],
            "region": "flixable",
            "source_link": link,
            "cover": image,
        })
    return releases


def fetch(limit: int = 12):
    feed = parse_feed(limit // 4)
    next_data = parse_next(limit // 2)
    flix = parse_flixable(limit // 4)
    combined = feed + next_data + flix
    seen = set()
    deduped = []
    for release in combined:
        key = release.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(release)
    return deduped[:limit]


def write(releases):
    path = reports_dir / "new-releases.json"
    path.write_text(json.dumps(releases, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main():
    releases = fetch()
    if not releases:
        print("No releases fetched.")
        return
    path = write(releases)
    print(f"Saved {len(releases)} releases to {path}")


if __name__ == "__main__":
    main()
