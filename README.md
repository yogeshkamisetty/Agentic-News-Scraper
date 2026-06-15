# Agentic News Engine

An automated AI market-intelligence pipeline that **collects, filters, scores, deduplicates, and repackages** high-signal AI news into decision-ready outputs — Excel datasets and trend reports.

> Turn the noisy daily flow of AI news into ranked, executive-grade intelligence — automatically.

---

## What It Does

```text
30 sources  →  collect  →  dedupe  →  score & filter  →  enrich  →  rank  →  outputs
                                                                            │
                                                       ┌────────────────────┤
                                                       ▼                    ▼
                                                   Excel                  Trend
                                                  dataset                reports
```

The engine pulls from 30 configured sources (tech press, first-party AI labs, expert newsletters, research blogs, Reddit, Hacker News), keeps only genuinely relevant items, ranks them by an importance score, and turns the top signals into publish-ready datasets.

---

## Latest Run Results (June 15, 2026)

| Metric | Value |
|--------|-------|
| Sources configured | **30** (25 RSS + Hacker News + 3 Reddit + Product Hunt) |
| RSS feeds live | **25 / 25** |
| Raw articles collected | **339** |
| After dedupe + quality filter | **59** |
| Runtime | **~38 s** |
| Score range | **30 – 128** |

**Top stories from the latest run:**

| Score | Source | Title |
|-------|--------|-------|
| 128 | MarkTechPost | Claude Code Guide 2026: 25 Features with Examples + Demo |
| 110 | Ahead of AI | Recent Developments in LLM Architectures: KV Sharing, mHC… |
| 96 | NVIDIA Blog | NVIDIA Blackwell Leads on First Agentic AI Infrastructure Benchmark |
| 95 | VentureBeat | PixelRAG beats text parsers on accuracy and cuts agent token costs 10x |
| 87 | VentureBeat | How the UK Is Turning Sovereign AI Ambition Into Action With NVIDIA... |

**Category balance:** Agentic AI 27 · Developer AI 14 · AI Update 14 · RAG/Infra 2 · Enterprise 2

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full pipeline (collect → score → export)
python main.py

# 3. (Optional) Fast config check — no network calls
python main.py --check-now
```

**Primary outputs land in `outputs/`:**
- `agentic_updates_<timestamp>.xlsx` — ranked dataset (sorted high → low score)
- `trend_report_<timestamp>.md` — markdown summary of top trends

---

## How It Works

### 1. Collection (`collectors/`)
| Collector | Source |
|-----------|--------|
| `rss_collector.py` | 25 RSS/Atom feeds — hardened with retry/backoff, multi-field summary & date extraction |
| `hackernews_collector.py` | Hacker News Firebase API (Limit expanded to 100 for broader net) |
| `reddit_collector.py` | Reddit JSON API (bot User-Agent + 429 jitter + backoff) |
| `api_collector.py` | Product Hunt GraphQL (optional, needs `PRODUCTHUNT_TOKEN`) |

Sources are collected in parallel via a bounded thread pool, so one slow feed never blocks the run.

### 2. Scoring & Filtering (`utils/scorer.py`, `utils/quality_mode.py`)
- **Keyword scoring** with word-boundary matching (so `"rag"` never matches `"dragon"`).
- **Source credibility weighting** — first-party AI labs (OpenAI, DeepMind) score highest; Reddit is penalized.
- **Category multipliers** tune emphasis per topic.
- **Quality gates:** minimum score threshold + ≥2 distinct keywords + summary ≥ 60 chars.

```text
final_score = (Σ keyword weights)  +  source weight  ×  category multiplier
```

### 3. Enrichment (`utils/`)
- `category_classifier.py` → Agentic AI · RAG/Infrastructure · Developer AI · Enterprise AI · AI Update
- `company_detector.py` → 60+ tracked companies (OpenAI, Anthropic, Mistral, Alibaba, NVIDIA…)
- `insight_generator.py` → 3 perspectives per article: **Why It Matters · SaaS Impact · PM Perspective**

### 4. Deduplication (`utils/deduplicator.py`)
Canonical URL normalization + hybrid fuzzy title/summary matching (RapidFuzz). Keeps the strongest version of near-duplicate stories across sources.

### 5. Ranking
The final dataset is **sorted by importance score (highest first)** before export — so the Excel file is delivered in ranked order.

### 6. Repackaging (`engines/`)
| Tool | Output |
|------|--------|
| `refinement_engine.py` | Merges historical runs → refined master dataset |
| `trend_analytics.py` | Markdown trend report |
| `historical_filter_engine.py` | Builds master datasets from historical runs |

---

## Project Structure

```text
agentic-news-engine/
├── main.py                       # Pipeline orchestrator (parallel collect → rank → export)
├── requirements.txt
├── README.md                     # This file
├── CONTEXT.md                    # Full development log & decision history
│
├── config/
│   ├── portals.json              # 30 source definitions
│   ├── keywords.json             # High-signal keywords
│   └── quality_modes.json        # strict / balanced / broad thresholds
│
├── collectors/                   # Source collection layer
│   ├── rss_collector.py
│   ├── hackernews_collector.py
│   ├── reddit_collector.py
│   └── api_collector.py
│
├── utils/                        # Scoring, enrichment & helpers
│   ├── scorer.py                 # Keyword importance scoring
│   ├── source_ranker.py          # Source credibility weights
│   ├── quality_mode.py           # Threshold profiles
│   ├── category_classifier.py    # Topic categorization
│   ├── company_detector.py       # Company tagging (60+ companies)
│   ├── insight_generator.py      # 3-perspective insights
│   ├── deduplicator.py           # Fuzzy + URL dedupe
│   ├── excel_writer.py           # Excel export
│   └── top_updates.py            # Top-N ranking
│
├── engines/                      # Analysis & dataset merging
│   ├── refinement_engine.py
│   ├── trend_analytics.py
│   └── historical_filter_engine.py
│
└── outputs/                      # All generated artifacts
    ├── agentic_updates_*.xlsx
    ├── refined_agentic_updates.xlsx
    └── trend_report_*.md
```

---

## Sources (30)

**First-party AI labs:** OpenAI · Google DeepMind · Google AI Blog · Hugging Face · NVIDIA Blog
**Tech press:** TechCrunch · VentureBeat · MIT Technology Review · The Verge · Wired · Ars Technica · The Decoder · MarkTechPost
**Expert newsletters:** Import AI · Ahead of AI · Latent Space · Ben's Bites · TLDR AI · Simon Willison · Stratechery
**Research:** BAIR Berkeley · MIT News AI
**VC / startup:** a16z · Y Combinator · Sequoia Capital
**Community:** Hacker News · r/MachineLearning · r/LocalLLaMA · r/singularity
**Optional:** Product Hunt AI (needs API token)

> All RSS feeds are verified live (25/25 returning HTTP 200 with fresh entries). Dead feeds (The Batch, AI Breakfast) were removed; a16z was migrated to its working Substack feed.

---

## Configuration

| To change… | Edit… |
|------------|-------|
| News sources | `config/portals.json` |
| Filter keywords | `config/keywords.json` |
| Score thresholds / quality mode | `config/quality_modes.json` |
| Keyword weights | `utils/scorer.py` |
| Source credibility | `utils/source_ranker.py` |
| Category rules | `utils/category_classifier.py` |

**Quality modes:** set `QUALITY_MODE=strict|balanced|broad` (default: `balanced`).

---

## Dependencies

```text
feedparser       # RSS/Atom parsing
requests         # HTTP
beautifulsoup4   # HTML cleaning
pandas           # Data handling
openpyxl         # Excel export
rapidfuzz        # Dedupe similarity
```

---

## Verified Health (June 15, 2026)

- All source code compiles with no syntax errors.
- All modules import cleanly.
- All 25 RSS feeds return live data.
- Reddit collector is stable and 429-proof with random jitter threading.
- Hacker News fetches 60+ signals reliably per run.
- Ranking is correct — output sorted by score (128 → 30), formula traced and verified.

---

## Known Notes & Roadmap

- **Product Hunt** returns 0 without `PRODUCTHUNT_TOKEN` (cleanly skipped).
- **Anthropic** has no working public RSS feed — omitted rather than adding a broken source.
- A few research/strategy feeds (Hugging Face, Stratechery) may contribute 0 on days without agentic-AI content — expected, not a fault.

See [CONTEXT.md](CONTEXT.md) for the full development log, bug-fix history, and design decisions.

---

**Status:** Active development · **Last updated:** June 15, 2026
