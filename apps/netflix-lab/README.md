# Netflix Insight Lab

这是 `stanley-homeboard` 的一个 app，帮助你分析 Netflix 观影记录、梳理偏好、并自动推荐符合你口味的新剧。

## 主要模块

1. **`generate_recs.py`**：归一化 `~/NetflixViewingHistory.csv`，统计你的最爱剧目和关键词热度，结合 `recommendations.json` 中的手动剧单，输出 Markdown 报告 `reports/latest-recommendation.md`。
2. **`fetch_new_releases.py`**：抓取 `https://www.whats-on-netflix.com/feed/`（包含多篇 Netflix 新剧资讯），生成 `reports/new-releases.json` 并在 dashboard 中突出“香港+全球”新片推荐。
3. **`dashboard.py`**：整合观看统计 + 推荐 + 新发布、生成 `reports/dashboard.html` 作为个人影片管理页，可直接挂到个人主页或 Vercel。

## 使用方法

```bash
cd ~/workspace/stanley-homeboard/apps/netflix-lab
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_recs.py
python fetch_new_releases.py
python dashboard.py
```

运行完成后：
- `reports/latest-recommendation.md` 是文字版观影+推荐报告。 
- `reports/new-releases.json` 记录当前抓到的新剧。 
- `reports/dashboard.html` 展示管理页面：看记录、捕捉偏好、展示新推荐。

你可以把其中任意文件 embed 到主页或 Notion。需要我把 dashboard 自动嵌入 `stanley-homeboard` 的主界面吗？