#!/usr/bin/env python3
"""Fetch Netflix new release highlights from public listings."""

import requests
from bs4 import BeautifulSoup
from pathlib import Path

project_root = Path(__file__).resolve().parent
reports_dir = project_root / "reports"
reports_dir.mkdir(exist_ok=True)

SOURCE_URL = "https://www.whats-on-netflix.com/whats-new/"


def fetch_new_titles(limit: int = 8):
    try:
        resp = requests.get(SOURCE_URL, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("article.post")[0:limit]
    releases = []
    for card in cards:
        title_tag = card.find("h2") or card.find("h3")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        summary = "".join(p.get_text(strip=True) for p in card.select("p"))
        releases.append({"title": title, "summary": summary[:200]})
    return releases


def write(releases):
    output = reports_dir / "new-releases.json"
    output.write_text(json.dumps(releases, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main():
    releases = fetch_new_titles()
    if not releases:
        print("No releases fetched.")
        return
    path = write(releases)
    print(f"New releases stored at {path}")


if __name__ == "__main__":
    main()
