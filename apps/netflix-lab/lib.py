from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
DATA_FILE = Path.home() / "NetflixViewingHistory.csv"
RECOMMENDATIONS_FILE = PROJECT_ROOT / "recommendations.json"


def normalize_title(raw: str) -> str:
    clean = raw.strip()
    if ":" in clean:
        return clean.split(":", 1)[0].strip()
    if "第" in clean and "季" in clean:
        return clean.split("第")[0].strip()
    return clean


def load_history() -> list[tuple[str, datetime]]:
    history = []
    if not DATA_FILE.exists():
        return history
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = normalize_title(row["Title"])
            try:
                date = datetime.strptime(row["Date"], "%m/%d/%y")
            except ValueError:
                try:
                    date = datetime.fromisoformat(row["Date"])
                except ValueError:
                    continue
            history.append((title, date.replace(tzinfo=timezone.utc)))
    return history


def aggregate(history: list[tuple[str, datetime]]) -> dict:
    stats = defaultdict(lambda: {"count": 0, "first": None, "last": None})
    for title, date in history:
        entry = stats[title]
        entry["count"] += 1
        if entry["first"] is None or date < entry["first"]:
            entry["first"] = date
        if entry["last"] is None or date > entry["last"]:
            entry["last"] = date
    return stats


def infer_tags(history: list[tuple[str, datetime]]) -> Counter:
    keywords = {
        "悬疑": ["悬疑", "犯", "罪", "谋杀", "追"],
        "女性": ["女性", "莎拉", "她"],
        "美食": ["吃货", "食", "餐"],
        "旅行": ["旅", "游", "公路", "济州"],
        "心理": ["心理", "人性"],
        "犯罪": ["犯", "罪", "警"],
        "科幻": ["宇宙", "太空", "科幻", "未来"],
    }
    tags = Counter()
    for title, _ in history:
        for tag, words in keywords.items():
            if any(word in title for word in words):
                tags[tag] += 1
    return tags


def load_recommendations() -> list[dict]:
    if not RECOMMENDATIONS_FILE.exists():
        return []
    with open(RECOMMENDATIONS_FILE, encoding="utf-8") as f:
        return json.load(f)


def pick_recommendations(tags: Counter, watched: set[str], limit: int = 5) -> list[dict]:
    recs = load_recommendations()
    scored = []
    for rec in recs:
        if rec["title"] in watched:
            continue
        score = sum(tags.get(tag, 0) for tag in rec.get("tags", []))
        scored.append((score, rec))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [rec for _, rec in scored[:limit]]
