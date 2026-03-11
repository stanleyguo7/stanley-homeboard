#!/usr/bin/env python3
"""Render Netflix viewing dashboard page."""

from pathlib import Path
from lib import load_history, aggregate, infer_tags, pick_recommendations, REPORTS_DIR
import json

project_root = Path(__file__).resolve().parent
dashboard_path = project_root / "reports" / "dashboard.html"


def render(status, tags, recs, releases):
    sections = []
    sections.append("<section class='card stats'><h2>观影概况</h2><ul>")
    for title, entry in sorted(status.items(), key=lambda item: item[1]["count"], reverse=True)[:4]:
        sections.append(f"<li><strong>{title}</strong><span>{entry['count']} 集 · 最后看过 {entry['last']:%Y-%m-%d}</span></li>")
    sections.append("</ul></section>")
    sections.append("<section class='card tags'><h2>关键词热度</h2><div class='tag-cloud'>")
    for tag, value in tags.most_common():
        sections.append(f"<span>{tag} · {value}</span>")
    sections.append("</div></section>")
    sections.append("<section class='card recs'><h2>推荐剧集</h2><div class='recommendations'>")
    if not recs:
        sections.append("<div class='empty'>暂无推荐，等你输更多偏好。</div>")
    else:
        for rec in recs:
            cover = rec.get("cover") or "https://images.unsplash.com/photo-1515165562834-c0f1c8f75ff7?auto=format&fit=crop&w=640&q=80"
            actors = ", ".join(rec.get("actors", []))
            genres = ", ".join(rec.get("genres", []))
            link = rec.get("netflix_link", "#")
            sections.append(
                """
                <article>
                  <div class='cover' style='background-image:url(%s);'></div>
                  <div class='info'>
                    <h3><a href='%s' target='_blank'>%s</a></h3>
                    <p class='meta'>%s</p>
                    <p class='desc'>%s</p>
                    <p class='meta actors'>演员：%s</p>
                  </div>
                </article>
                """ % (cover, link, rec['title'], genres, rec.get('description') or rec.get('reason', ''), actors)
            )
    sections.append("</div></section>")
    sections.append("<section class='card releases'><h2>香港新片速递</h2><div class='releases'>")
    for release in releases[:3]:
        summary = release.get('summary','').replace('\n',' ')[:220]
        sections.append(
            """
            <article>
              <strong>%s</strong>
              <p>%s</p>
            </article>
            """ % (release['title'], summary)
        )
    sections.append("</div></section>")
    base_style = """<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'/><title>观影仪表板</title><meta name='viewport' content='width=device-width, initial-scale=1'/><style>
    :root{color-scheme: dark;}
    body{font-family:'Noto Sans SC',sans-serif;background:#060B16;color:#EFF0F7;margin:0;padding:0;}
    main{width:min(1100px,100%);margin:0 auto;padding:32px 16px 48px;}
    header{margin-bottom:32px;}
    h1{font-size:2.8rem;margin:0;}
    .subtitle{color:#9fb1c8;font-size:1rem;margin-top:6px;}
    .card{background:linear-gradient(160deg,#101827,#070B11);border:1px solid rgba(255,255,255,.08);padding:20px 22px;border-radius:22px;margin-bottom:20px;box-shadow:0 25px 50px rgba(5,11,20,.6);}
    h2{margin-top:0;margin-bottom:16px;font-size:1.5rem;color:#5FE4FF;}
    ul{list-style:none;margin:0;padding:0;}
    li{padding:10px 0;border-bottom:1px solid rgba(255,255,255,.08);display:flex;flex-direction:column;}
    li span{color:#9fb1c8;font-size:0.95rem;}
    .card.tags .tag-cloud{display:flex;flex-wrap:wrap;gap:8px;}
    .tag-cloud span{padding:6px 10px;background:rgba(255,255,255,.08);border-radius:999px;font-size:0.9rem;}
    .recommendations article{display:flex;gap:18px;border-bottom:1px solid rgba(255,255,255,.05);padding-bottom:18px;margin-bottom:18px;}
    .recommendations article:last-child{border-bottom:none;margin-bottom:0;padding-bottom:0;}
    .cover{width:140px;height:200px;background-size:cover;background-position:center;border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,.45);}
    .info{flex:1;display:flex;flex-direction:column;gap:8px;}
    .info h3{margin:0;font-size:1.2rem;}
    .info h3 a{color:#FFFFFF;text-decoration:none;}
    .info h3 a:hover{text-decoration:underline;}
    .meta{color:#9fb1c8;font-size:0.9rem;}
    .actors{font-size:0.85rem;}
    .desc{color:#f0f0f7;}
    .releases article{background:rgba(255,255,255,.02);padding:12px 14px;border-radius:12px;margin-bottom:12px;}
    @media (max-width:768px){.recommendations article{flex-direction:column;} .cover{width:100%;height:220px;} }
    </style></head><body><main><header><h1>Netflix 观影管家</h1><p class='subtitle'>结合你的观影记录+香港新片，实时生成个性推荐。</p></header>"""
    return base_style + "".join(sections) + "</main></body></html>"


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
