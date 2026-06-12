# API & Internal Interface Reference

The Agentic News Engine does not expose public REST APIs for external consumption. Instead, it acts as an API client to ingest data and utilizes structured internal interfaces to move data between its modules.

## External API Integrations

### ProductHunt GraphQL API
- **Endpoint:** `https://api.producthunt.com/v2/api/graphql`
- **Authentication:** Bearer token via environment variable `PRODUCTHUNT_TOKEN`.
- **Purpose:** Fetches the top daily "artificial-intelligence" posts based on vote count.
- **Collector:** `collectors/api_collector.py`

### HackerNews API (Unofficial/Scraped via RSS or JSON)
- **Purpose:** Fetches trending startup and AI-related engineering posts.
- **Collector:** `collectors/hackernews_collector.py`

### Reddit JSON API
- **Endpoint:** `https://www.reddit.com/r/{subreddit}/top/.json`
- **Purpose:** Fetches community-curated updates (e.g., from `r/LocalLLaMA`, `r/MachineLearning`).
- **Collector:** `collectors/reddit_collector.py`

---

## Internal Data Structures

The core data structure passed between modules is the **Article Dictionary**.

### Article Dictionary Format
```json
{
  "Title": "string",
  "Source": "string",
  "Published Date": "ISO 8601 string",
  "URL": "string",
  "Summary": "string",
  "Category": "string",
  "Company Mentioned": "string",
  "Keywords": "string",
  "Importance Score": "integer or float",
  "Why It Matters": "string",
  "SaaS Impact": "string",
  "PM Perspective": "string"
}
```

## Internal Module Interfaces

### `process_article(article: dict) -> dict | None`
- **Location:** `main.py`
- **Input:** Raw article dictionary from a collector.
- **Action:** Runs categorization, scoring, and insight generation.
- **Output:** Fully enriched article dictionary. Returns `None` if the article fails threshold or engagement filters.

### `calculate_score(text: string) -> tuple(int, list)`
- **Location:** `utils/scorer.py`
- **Input:** Combined title and summary string.
- **Output:** Returns a tuple containing the base `score` (int) and a list of matched `keywords` (list of strings).

### `generate_insights(title: string, summary: string, category: string) -> tuple`
- **Location:** `utils/insight_generator.py`
- **Input:** Basic article context.
- **Output:** Returns a tuple of three strings: `(why_it_matters, saas_impact, pm_perspective)`.

### `detect_company(title: string, summary: string) -> string`
- **Location:** `utils/company_detector.py`
- **Input:** Article text.
- **Output:** Comma-separated string of identified companies based on internal lists.
