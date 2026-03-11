#!/usr/bin/env python3
"""Render Netflix viewing dashboard page."""

from pathlib import Path
from lib import load_history, aggregate, infer_tags, pick_recommendations, REPORTS_DIR
import json

project_root = Path(__file__).resolve().parent
dashboard_path = project_root / "reports" / "dashboard.html"


def render(status, tags, recs, releases):
    sections = []
    sections.append("<section class='card'><h2>观影统计</h2><ul>")
    for title, entry in sorted(status.items(), key=lambda item: item[1]["count"], reverse=True)[:4]:
        sections.append(f"<li><strong>{title}</strong> · {entry['count']} 次 · {entry['last']:%Y-%m-%d}</li>")
    sections.append("</ul></section>")
    sections.append("<section class='card'><h2>关键词热度</h2><ul>")
    for tag, value in tags.most_common():
        sections.append(f"<li>{tag}: {value}</li>")
    sections.append("</ul></section>")
    sections.append("<section class='card'><h2>推荐剧集</h2><ul class='recommendations'>")
    if not recs:
        sections.append("<li>暂无推荐，等你看完更多内容再触发一次。</li>")
    else:
        for rec in recs:
            sections.append(f"<li><strong>{rec['title']}</strong> · {', '.join(rec.get('tags', []))}<p>{rec.get('description') or rec.get('reason','')}</p></li>")
    sections.append("</ul></section>")
    sections.append("<section class='card'><h2>香港新片速递</h2><ul class='releases'>")
    for release in releases[:3]:
        sections.append(f"<li><strong>{release['title']}</strong><p>{release.get('summary','')[:200]}</p></li>")
    sections.append("</ul></section>")
    base_style = """<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'/><title>观影仪表板</title><style>body{font-family:'Noto Sans SC',sans-serif;background:#0c0f1c;color:#f5f5f7;margin:0;padding:0;}main{max-width:1100px;margin:0 auto;padding:32px 24px 48px;}header{margin-bottom:28px;}h1{font-size:2.6rem;margin:0;}h2{margin:0 0 12px;font-size:1.4rem;color:#1ef3e3;}section.card{background:linear-gradient(145deg,#111524,#0b0d17);border:1px solid rgba(255,255,255,.08);padding:24px;border-radius:20px;margin-bottom:20px;box-shadow:0 20px 45px rgba(0,0,0,.45);}ul{list-style:none;margin:0;padding:0;}li{border-bottom:1px dashed rgba(255,255,255,.12);padding:10px 0;}li:last-child{border-bottom:none;}strong{font-size:1.15rem;display:block;margin-bottom:6px;}p{margin:0;color:#d4d4de;line-height:1.6;} .recommendations li{display:flex;flex-direction:column;} .releases li{background:rgba(255,255,255,.03);border-radius:12px;padding:12px 14px;margin-bottom:10px;} .footer-note{margin-top:16px;font-size:0.9rem;color:#888;}@media (max-width:768px){section.card{padding:18px;border-radius:16px;}main{padding:24px 16px 40px;}} </style></head><body><main><header><h1>Netflix 观影管家</h1><p class='footer-note'>结合你的历史记录与最新香港新片，帮你快速选剧。</p></header>"""
    return base_style + "".join(sections) + "</main></body></html>"""


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
