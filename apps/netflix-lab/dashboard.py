#!/usr/bin/env python3
"""Render Netflix viewing dashboard page."""

from pathlib import Path
from lib import load_history, aggregate, infer_tags, pick_recommendations, REPORTS_DIR
import json

project_root = Path(__file__).resolve().parent
dashboard_path = project_root / "reports" / "dashboard.html"


def render(status, tags, recs, releases):
    sections = []
    sections.append("<section><h2>观影统计</h2><ul>")
    for title, entry in sorted(status.items(), key=lambda item: item[1]["count"], reverse=True)[:4]:
        sections.append(f"<li><strong>{title}</strong> · {entry['count']} 次 · {entry['last']:%Y-%m-%d}</li>")
    sections.append("</ul></section>")
    sections.append("<section><h2>关键词热度</h2><ul>")
    for tag, value in tags.most_common():
        sections.append(f"<li>{tag}: {value}</li>")
    sections.append("</ul></section>")
    sections.append("<section><h2>推荐剧集</h2><ul>")
    if not recs:
        sections.append("<li>暂无推荐，等你看完更多内容再触发一次。</li>")
    else:
        for rec in recs:
            sections.append(f"<li><strong>{rec['title']}</strong> · {', '.join(rec.get('tags', []))}<p>{rec.get('description') or rec.get('reason','')}</p></li>")
    sections.append("</ul></section>")
    sections.append("<section><h2>最新 Netflix 发布</h2><ul>")
    for release in releases[:3]:
        sections.append(f"<li><strong>{release['title']}</strong><p>{release.get('summary','')[:180]}</p></li>")
    sections.append("</ul></section>")
    return """<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'/><title>观影仪表板</title><style>body{font-family:'Noto Sans SC',sans-serif;background:#f2f2f2;padding:24px;}section{background:#fff;margin-bottom:16px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.08);padding:16px;}h2{margin-top:0;}ul{list-style:none;padding-left:0;}li{padding:8px 0;border-bottom:1px solid #eee;}li:last-child{border-bottom:none;}strong{display:block;font-size:1.1em;}</style></head><body>" + "".join(sections) + "</body></html>"""


def main():
    history = load_history()
    stats = aggregate(history)
    tags = infer_tags(history)
    recs = pick_recommendations(tags, set(stats.keys()))
    releases_path = REPORTS_DIR / "new-releases.json"
    releases = []
    if releases_path.exists():
        releases = json.loads(releases_path.read_text(encoding='utf-8'))
    html = render(stats, tags, recs, releases)
    dashboard_path.write_text(html, encoding='utf-8')
    print(f"Dashboard updated at {dashboard_path}")


if __name__ == "__main__":
    main()
