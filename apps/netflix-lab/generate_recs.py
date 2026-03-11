#!/usr/bin/env python3
"""Generate Markdown recommendation report."""

from datetime import datetime, timezone
from pathlib import Path

from lib import load_history, aggregate, infer_tags, pick_recommendations, REPORTS_DIR

reports_dir = REPORTS_DIR
stats_limit = 5


def build_markdown(stats, tags, recs):
    lines = ["# Netflix Viewing Report", "", f"Generated: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}"]
    lines.append("")
    lines.append("## Top watched")
    for title, entry in sorted(stats.items(), key=lambda item: item[1]["count"], reverse=True)[:stats_limit]:
        lines.append(f"- **{title}** — {entry['count']} views ({entry['first']:%Y-%m-%d} → {entry['last']:%Y-%m-%d})")
    lines.append("")
    lines.append("## Keyword heatmap")
    for tag, count in tags.most_common():
        lines.append(f"- {tag}: {count}")
    lines.append("")
    lines.append("## Recommendations")
    if not recs:
        lines.append("_No recommendations matched your current preferences._")
    else:
        for rec in recs:
            lines.append(f"- **{rec['title']}** ({', '.join(rec.get('tags', []))}) — {rec.get('reason', '')}")
    return "\n".join(lines)


def main():
    history = load_history()
    if not history:
        print("No viewing history found at ~/NetflixViewingHistory.csv")
        return
    stats = aggregate(history)
    tags = infer_tags(history)
    recs = pick_recommendations(tags, set(stats.keys()))
    report = build_markdown(stats, tags, recs)
    destination = reports_dir / "latest-recommendation.md"
    destination.write_text(report, encoding="utf-8")
    print(f"Report written to {destination}")


if __name__ == "__main__":
    main()
