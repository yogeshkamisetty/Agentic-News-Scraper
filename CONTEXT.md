# Agentic News Engine - Project Context

**Current snapshot:** June 15, 2026

## June 15, 2026 (Part 4) — Architecture Pruning & Performance Deep Dive

### What We Did
- **Feature Pruning:** Completely removed the peripheral content generation engines (Whitepapers, LinkedIn Carousels, Theme Clustering, LinkedIn text generators). The repository is now strictly an intelligence aggregation and refinement engine.
- **Deep Dive Fixes:** 
  - **Reddit Concurrency:** Added a randomized `time.sleep(random.uniform(0.5, 3.0))` to `reddit_collector.py`. The parallel thread pool was firing all requests simultaneously, triggering Reddit's 429 DDoS protections. This jitter stagger fixed the issue completely.
  - **Duplicate Code Removed:** Cleaned up a duplicated `clean_summary()` block in the Reddit collector.
  - **Hacker News Expansion:** The `collect_hackernews()` limit in `main.py` was artificially low (20). It was bumped to 100, which expanded raw HN collection to 60+ updates per run, finding vastly more AI-specific content.

### Result (Deep Dive Run)
- Raw collected updates surged from 287 to **339**.
- Runtime improved to ~38s.
- All 3 configured subreddits successfully returned 10 updates each without any 429 failures.

---

## June 15, 2026 (Part 3) — Project Cleanup & Reddit Rate Limit Fix

### What We Did
- Cleaned up the repository by removing obsolete documentation (`CODE_CHANGES_2026-05-31.md`, `FIXES_SUMMARY_2026-05-31.md`, `TROUBLESHOOTING.md`), and empty folders (`.claude/`, `samples/`).
- Updated the git remote repository to track: `https://github.com/yogeshkamisetty/Agentic-News-Scraper.git`.

### Issues Faced & Resolved
- **Reddit Rate Limits (429 Too Many Requests):** The engine was consistently failing to collect from Reddit (especially `r/singularity`) because Reddit rate limits anonymous and rapid API requests.
- **Resolution:** Modified `collectors/reddit_collector.py` to use a custom Python bot `User-Agent` (`python:agentic_news_engine:v1.0`). We also introduced a backoff retry loop: if the engine encounters a `429` status code, it sleeps for 3 seconds and retries up to 3 times before failing. This resolved the issue and allowed Reddit to successfully return updates.

---

## June 15, 2026 (Part 2) — Source Audit & Scrape Engine Hardening

Tested every configured source for liveness, pruned dead feeds, added verified
new sources, and hardened the RSS collector.

### Dead feeds removed
- **The Batch** (`deeplearning.ai/the-batch/feed/`) — 404, all alternate URLs
  (ghost, substack, raw) also failed. Removed.
- **AI Breakfast** (`aibreakfast.beehiiv.com/feed`) — 404, feed discontinued. Removed.

### Feed fixed
- **a16z** — old `a16z.com/feed/` was 404. Switched to the Substack feed
  `https://a16z.news/feed` (verified, 20 fresh entries).

### New verified sources added (12)
First-party AI labs: **OpenAI** (`openai.com/news/rss.xml`), **Google DeepMind**
(`deepmind.google/blog/rss.xml`), **Google AI Blog**, **Hugging Face**, **NVIDIA Blog**.
Press: **The Decoder**, **MarkTechPost**. Expert commentary: **Simon Willison**,
**TLDR AI**, **Stratechery**. Research: **BAIR Berkeley**, **MIT News AI**.
All tested live (HTTP 200, fresh entries) before adding.

> Couldn't find a working Anthropic RSS feed (all known URLs 404); skipped rather
> than add a broken source. Microsoft AI blog returned 410 Gone; skipped.

### Source weights updated
`utils/source_ranker.py` — added credibility weights for all new sources
(OpenAI/DeepMind +22 as first-party; The Decoder/MarkTechPost mid-press;
Simon Willison/Stratechery expert tier; BAIR/MIT News research tier).

### Scrape engine hardened (`collectors/rss_collector.py`)
- Retry with backoff (2 retries) on timeouts, 429, and 5xx.
- Timeout raised 8s → 15s (configurable).
- **Multi-field summary extraction**: summary → content[].value → description →
  subtitle, picking the richest body (fixes thin-summary sources).
- Multi-field date extraction (published → updated → pubDate → created).
- Never raises — always returns a list; consistent article schema.

### Result (full run, June 15)
- Portals: 20 → **30** configured.
- Raw collected: 177 → **296**. Quality articles: 24 → **59**. Runtime ~21s.
- 28 of 59 quality articles come from newly-added sources.
- Category balance healthy: Agentic 27 / Developer 14 / AI Update 14 / RAG 2 / Enterprise 2.

---

## June 15, 2026 — Data Quality, Theme Naming & Content Repurposing

This session focused on three things: hardening the scoring/filter so noise
stops reaching the dataset, cleaning up theme names that leaked into output
titles, and building the LinkedIn carousel layer.

### Bugs found and fixed (data pipeline)
1. **Substring keyword false positives** — `utils/scorer.py` used `keyword in text`,
   so `"rag"` matched `"d**rag**on"` and a "House of the Dragon" trailer scored 32
   and entered the dataset. **Fix:** word-boundary regex matching (`\brag`). Also
   added negative keywords (`trailer`, `romance`, `lithium`, `season`, etc.).
2. **Tier-1 source threshold too low (25)** — Wired/TechCrunch/VentureBeat passed on
   source bonus alone. **Fix:** raised tier1 `25→40`, newsletters `30→45` in
   `config/quality_modes.json` default + `utils/quality_mode.py` fallback.
3. **`Developer AI` category never used** — classifier checked Agentic AI first and
   absorbed all coding articles. **Fix:** reordered `utils/category_classifier.py`
   so Developer AI / RAG / Enterprise are tested before the broad Agentic bucket,
   all with word-boundary matching.
4. **Thin newsletter summaries passing** — Import AI / Latent Space return 20–90 char
   teasers. **Fix:** `main.py` rejects `summary < 60 chars`.
5. **Single keyword could solo-pass an article** — **Fix:** `main.py` requires
   ≥2 distinct keyword hits.
6. **Empty Excel files saved** — runs with 0 results still wrote a file.
   **Fix:** `utils/excel_writer.py` returns `None` and skips writing when empty;
   `main.py` prints a warning instead.
7. **Company detector too small (14 names)** — 15/22 rows had blank "Company".
   **Fix:** `utils/company_detector.py` expanded to 60+ companies (Mistral,
   Alibaba, Mind Lab, Datacurve, DeepSeek, Cursor, Neo4j, etc.).
8. **Noisy theme names** ("Apex Qwen3", "Import 440", "Google 2026", "Reasoning Llms")
   leaked into whitepaper/carousel titles. **Fix:** `utils/theme_clustering.py` —
   drop digit-bearing tokens, newsletter names, and short fragments; fall back to the
   representative's Category when only vendor/proper-noun fragments remain; added
   acronym casing (LLM/RAG/API/MCP/SaaS). Result: clean theme names.

### Content repurposing layer built
- `engines/linkedin_carousel_bw.py` — premium black-and-white editorial carousel
  (10 slides, 600×600pt, Apple/Notion style). Standalone, zero API.
- `engines/linkedin_carousel_canva.py` — "Gray Minimal" Canva-style carousel
  (9 slides, 540×675pt 4:5, oval number badges, pill buttons, logo). Standalone.
- `engines/carousel_pdf_generator.py` — per-article 6-slide dark-theme prototype.
  **NOTE:** this is distinct from `generators/carousel_pdf_generator.py` (the
  theme-level generator wired into the documented workflow). Same filename, two
  folders, different purpose — see "Known maintainability notes" below.

### Decisions recorded (publishing strategy)
- **LinkedIn carousels** are uploaded as a PDF Document post (one PDF per article).
- **Medium auto-publishing was considered and rejected** in favor of an
  **auto-draft + manual-publish** flow: republishing scraped summaries verbatim
  risks copyright + Medium ToS + duplicate-content penalties, and unattended
  publishing has no safety gate. The engine should draft; a human hits publish.

### Verification (June 15)
- `python -m compileall` on all source: no syntax errors.
- All 27 modules import cleanly.
- All downstream engines run green: refinement, theme carousel, whitepaper,
  trend analytics, master LinkedIn, carousel JSON, BW carousel, Canva carousel.
- `python -B main.py --check-now` passes (quality mode balanced, 20 portals).

---

## June 6, 2026 Maintenance Update

- Added `python main.py --check-now` as a fast local configuration check that does not run network collection.
- Set `sys.dont_write_bytecode = True` in `main.py` so read-only or locked `__pycache__` files do not interfere with normal runs.
- Changed source collection in `main.py` from sequential collection to a bounded thread pool (`MAX_COLLECTION_WORKERS = 6`) so slow feeds do not force the whole pipeline to wait source-by-source.
- Updated Reddit RSS fallback to fetch feeds with `requests.get(..., timeout=...)` before parsing, replacing unbounded `feedparser.parse(url)` calls.
- Added a source-level timeout to Hacker News item fetching and cancelation for pending futures.
- Added optional Product Hunt GraphQL collection when `PRODUCTHUNT_TOKEN` is set; without the token, the source cleanly returns 0 updates.
- Updated LinkedIn generation to skip file creation when no articles pass the quality filter and removed mojibake from the post header.
- Added `reportlab` to `requirements.txt` because the carousel and whitepaper engines import it.
- Verification on June 6: `python -B main.py --check-now` passed, AST parsing for project source files passed, and `python -B main.py` completed in 10.24s under a proxy-refused network environment with 0 collected updates and no crash.

## Current Status Snapshot

- **Latest Run (May 31, 2026)**:
  - Total collected: 177 raw articles
  - After scoring: 24 articles
  - After deduplication: 24 articles
  - Execution time: 35.02 seconds
  - Top story: "The AI agent bottleneck isn't model performance — it's permissions" (Score: 109)
  - Downstream outputs: refined Excel, LinkedIn content, 6-slide theme carousels, and 12 theme whitepapers

- **Known Issues Fixed in This Session**:
  1. Reddit 403 Blocked errors - switched to RSS fallback collection and added graceful diagnostics
  2. Deduplication quality - moved dedupe after scoring and replaced title-only matching with hybrid canonical matching
  3. Hacker News breadth - increased fetch depth and added richer payload capture
  4. Insight quality - replaced generic category templates with keyword-driven insight generation
  5. Refinement layer - added a content-ready merge engine for historical Excel outputs
  6. Content tone - upgraded carousel and whitepaper language to executive-grade framing
  7. Whitepaper system - converted from a single long-form report into one theme whitepaper per cluster

- **Ongoing Issues Identified**:
  - Some RSS feeds still return 0 results or appear empty (The Batch, AI Breakfast, a16z)
  - Runtime increased because the pipeline now collects more raw content before refinement
  - Product Hunt remains a placeholder until GraphQL/OAuth integration is added
  - Some theme names remain noisy in the refined dataset and may need editorial cleanup in source data

## Project Overview

The **Agentic News Engine** is an automated AI market intelligence system that collects, filters, deduplicates, scores, refines, clusters, and repackages high-signal AI updates into executive-ready outputs.

The pipeline now produces more than a news digest. It generates:
- curated Excel datasets
- LinkedIn-ready post content
- trend reports
- theme clusters with representatives
- one 6-slide LinkedIn carousel PDF per theme
- one consulting-style whitepaper PDF per theme

**Primary Purpose**: Turn noisy AI news flow into decision-grade intelligence for product leaders, operators, founders, and enterprise stakeholders.

---

## Project Goals

1. **Automated Content Collection**: Aggregate articles from 19+ news sources including tech publications, AI newsletters, and community platforms
2. **Intelligent Filtering**: Apply keyword-based and scoring mechanisms to identify relevant content
3. **Content Enrichment**: Categorize articles, detect mentioned companies, and generate contextual insights
4. **Stakeholder Intelligence**: Provide categorized updates with importance scoring for PMs, enterprises, and developers
5. **Actionable Insights**: Generate perspective-based analysis (SaaS impact, PM perspective, why it matters)
6. **Executive Publishing**: Convert clustered intelligence into consulting-grade carousels and whitepapers
7. **Narrative Quality**: Reduce repetition and increase insight density across all outputs

---

## Technical Architecture

### Core Components

#### 1. **Article Collection Layer** (`collectors/`)
- **RSS Collector** (`rss_collector.py`): Parses RSS feeds from tech publications, newsletters, and community sources
- **HackerNews Collector** (`hackernews_collector.py`): Integrates with Hacker News API
- **Reddit Collector** (`reddit_collector.py`): Pulls relevant AI-related posts from selected subreddits
- **API Collector** (`api_collector.py`): Framework for custom API integrations

**Data Sources** (configured in `config/portals.json`):
- Tech publications: TechCrunch, VentureBeat, The Verge, Wired, MIT Tech Review, Ars Technica
- AI newsletters: Import AI, The Batch, Ahead of AI, AI Breakfast, Ben's Bites, Latent Space
- VC / startup platforms: a16z, Y Combinator, Sequoia Capital
- Community: Hacker News and Reddit (r/MachineLearning, r/LocalLLaMA, r/singularity)
- Future/queued source: Product Hunt AI is present in config, but pipeline handling is still pending in `main.py`

#### 2. **Processing Pipeline** (`main.py`)
1. **Collection**: Gather articles from all portals with timing metrics and raw counts
2. **Deduplication**: Remove duplicate articles using intelligent matching
3. **Filtering**: Apply source-aware score thresholds and engagement checks
4. **Enrichment**: Add metadata including category, company mentions, keywords, and insights
5. **Ranking**: Sort by importance score and source weight
6. **Export**: Generate Excel reports and LinkedIn-ready post content

#### 3. **Utility Functions** (`utils/`)
- **scorer.py**: Keyword-weighted importance scoring (keywords weighted 15-25 points)
- **category_classifier.py**: Categorizes articles into RAG/Infrastructure, Enterprise, Developer, etc.
- **company_detector.py**: Identifies mentioned AI companies (OpenAI, Anthropic, Google, etc.)
- **deduplicator.py**: Removes duplicate content across sources
- **insight_generator.py**: Generates contextual analysis from articles
- **source_ranker.py**: Applies source credibility weights to scores
- **excel_writer.py**: Formats and exports data to Excel
- **top_updates.py**: Identifies and ranks top stories
- **linkedin_generator.py**: Builds LinkedIn post content from filtered updates
- **quality_mode.py**: Controls strict, balanced, and broad output modes
- **theme_clustering.py**: Clusters repeated narratives into themes and selects representatives
- **pdf_theme.py**: Shared visual theme for carousel PDFs
- **text_layout.py**: Text fitting, bullets, chips, and paragraph rendering helpers

#### 4. **Analysis / Repurposing Engines** (`engines/`)
- **trend_analytics.py**: Builds trend reports from the latest master dataset
- **carousel_generator.py**: Creates carousel JSON content from top updates
- **carousel_pdf_generator.py**: Generates one 6-slide theme carousel PDF per cluster
- **master_linkedin_generator.py**: Generates master LinkedIn posts from master datasets
- **historical_filter_engine.py**: Supports historical filtering and master dataset creation
- **refinement_engine.py**: Combines multiple Excel outputs into a refined dataset for downstream use
- **whitepaper_generator.py**: Generates one consulting-style theme whitepaper PDF per cluster

#### 5. **Configuration** (`config/`)
- **portals.json**: News source definitions with URLs and collection methods
- **keywords.json**: List of 26 high-signal keywords for filtering

---

## Data Flow

```
News Sources (RSS/APIs)
        ↓
    Collect Articles
        ↓
  Raw Dedupe
        ↓
  Score & Filter (source-aware threshold + high-signal keyword check)
        ↓
    Classify (Category, Company, Keywords)
        ↓
    Generate Insights (3 perspectives)
        ↓
  Final Dedupe
    ↓
    Rank by Importance & Source
        ↓
  Historical Merge / Refinement
    ↓
  Theme Clustering / Representative Selection
    ↓
  Excel Export + Console Output + PDF Repurposing
```

---

## Key Features Implemented

### Content Filtering Strategy
- **Scoring System**: Keyword-based scoring with weighted importance (15-25 points per keyword)
- **High-Signal Keywords**: 19 critical terms including "agent", "agentic", "rag", "mcp", "reasoning", "workflow"
- **Minimum Threshold**: Articles must score ≥30 AND contain high-signal keywords
- **Source Weighting**: Different credibility weights for various news sources

### Content Enrichment
- **Category Detection**: Automatically categorizes into 5+ categories (RAG/Infrastructure, Enterprise, Developer, Research, News)
- **Company Tagging**: Identifies 13+ tracked companies (OpenAI, Anthropic, Google, Microsoft, NVIDIA, etc.)
- **Keyword Extraction**: Extracts relevant keywords from article text
- **Importance Scoring**: Calculates numerical importance score
- **Insight Generation**: Creates 3 perspectives on each article:
  - **Why It Matters**: Relevance to agentic AI trends
  - **SaaS Impact**: Business/product implications
  - **PM Perspective**: Product management considerations

### Executive Content Layer
- **Quality Modes**: strict, balanced, and broad profiles tune thresholds and output breadth
- **Theme Clustering**: Repeated narratives are collapsed into themes before repurposing
- **Representative Selection**: The strongest article becomes the anchor for downstream content
- **Carousel PDFs**: One LinkedIn-native 6-slide PDF is generated per theme
- **Whitepaper PDFs**: One consulting-style whitepaper PDF is generated per theme

### Output Format
- **Excel Export**: timestamped `outputs/agentic_updates_*.xlsx` plus the standard latest file
- **LinkedIn Post Export**: timestamped `outputs/linkedin_posts_*.md`
- **Master Dataset**: timestamped `outputs/master_agentic_updates_*.xlsx`
- **Refined Dataset**: timestamped `outputs/refined_agentic_updates_*.xlsx`
- **Trend Reports**: timestamped `outputs/trend_report_*.md`
- **Carousel Data**: timestamped `outputs/carousel_data_*.json`
- **Carousel PDFs**: `outputs/carousels/carousel_<theme>.pdf`
- **Whitepaper PDFs**: `outputs/whitepapers/whitepaper_<theme>.pdf`
- **Whitepaper Manifest**: `outputs/whitepapers/whitepaper_manifest.json`
- **Console Summary**: Prints collection metrics, dedupe counts, and top stories
- **Performance Metrics**: Tracks collection time per source and total pipeline duration

---

## Progress Made

### ✅ Completed Features
- [x] Multi-source RSS feed aggregation
- [x] Hacker News integration
- [x] Reddit post collection for AI-relevant discussions
- [x] Article deduplication logic
- [x] Keyword-based scoring system with weighted keywords
- [x] Source-aware thresholding
- [x] Engagement filter for Reddit-derived items
- [x] Category classification system
- [x] Company detection and tagging
- [x] Insight generation (3-perspective analysis)
- [x] Source credibility weighting
- [x] Excel export functionality with formatting
- [x] LinkedIn post generation from filtered updates
- [x] Trend report generation from master datasets
- [x] Carousel JSON generation from top updates
- [x] Theme clustering and representative selection
- [x] Quality mode system (strict / balanced / broad)
- [x] Theme-level LinkedIn carousel PDF generation
- [x] Theme-level consulting whitepaper PDF generation
- [x] Performance monitoring and timing metrics
- [x] Top stories ranking and display
- [x] Configuration-driven source management
- [x] Command-line executable (`python main.py`)

### Recent Work
- Added source-specific thresholds for RSS, newsletters, Reddit, and Hacker News
- Added LinkedIn output generation directly from the main pipeline
- Added a master dataset workflow for trend analytics and repurposing tools
- Added carousel and master LinkedIn generators for downstream content creation
- Added richer output artifacts in `outputs/` for reporting and social reuse
- Updated collection logging to show raw counts, deduped counts, and final quality updates
- Added production-grade theme clustering for repeated narratives
- Added one PDF carousel per theme with a 6-slide editorial structure
- Added one consulting-style whitepaper PDF per theme
- Refined content copy to be more executive, strategic, and less template-driven

---

## Challenges Encountered

### 1. **Feed Consistency Issues**
- **Challenge**: Different RSS feeds have varying formats, encoding, and content structure
- **Solution**: Implemented HTML cleaning and entity decoding; fallback error handling

### 2. **Duplicate Detection**
- **Challenge**: Same article published across multiple sources with slight variations
- **Solution**: Implemented deduplication logic based on title/summary similarity

### 3. **Relevance Filtering**
- **Challenge**: Balancing sensitivity to avoid false positives while capturing all relevant content
- **Solution**: Two-layer filtering (score + high-signal keyword requirement)

### 4. **Insight Generation Quality**
- **Challenge**: Creating meaningful, consistent insights without sophisticated NLP
- **Solution**: Template-based insight generation with pattern matching

### 4b. **Executive Tone & Narrative Quality**
- **Challenge**: Outputs were technically correct but still read like AI-generated summaries
- **Solution**: Reworked insight phrasing, carousel hooks, and whitepaper section copy to be more concise, strategic, and decision-oriented

### 5. **Performance Optimization**
- **Challenge**: Slower collection from certain sources impacting pipeline time
- **Solution**: Added timing metrics per source for identification; potential parallelization

### 6. **Configuration Management**
- **Challenge**: Managing 19+ news sources and 26 keywords efficiently
- **Solution**: JSON-based configuration for easy updates without code changes

### 7. **Source Coverage Gaps**
- **Challenge**: `config/portals.json` includes a Product Hunt AI source, but `main.py` does not yet route `producthunt` through a collector
- **Solution**: Kept the config entry as a placeholder for the next collector implementation and documented it as pending

### 8. **Reddit API Blocking (May 31, 2026)**
- **Challenge**: Reddit returns 403 Forbidden errors for all subreddit collections despite valid User-Agent
- **Status**: Partially addressed with improved User-Agent headers and retry logic with 1-second delay
- **Remaining**: May require API token authentication or IP rotation for reliable access
- **Impact**: Currently 0 articles collected from Reddit sources

### 9. **Hacker News Limited Results**
- **Challenge**: Very few articles passing keyword filters from Hacker News (0 in latest run)
- **Solution**: Increased per-item timeout from 2s to 5s to allow more complete fetches
- **Remaining**: May need to relax keyword filtering for HN or expand keyword list

### 10. **Empty RSS Feeds**
- **Challenge**: Some major sources returning 0 results (The Verge, The Batch, AI Breakfast, a16z, Y Combinator)
- **Possible Causes**: 
  - Feed URL broken or changed
  - No matching content on current feed
  - Feed structure changed unexpectedly
  - Timeout issues
- **Next Steps**: Validate feed URLs and RSS structure

### 11. **Generic Executive Copy**
- **Challenge**: Carousel and whitepaper outputs used repetitive, summary-heavy phrasing
- **Solution**: Tightened hooks, transitions, PM framing, SaaS framing, recommendations, and conclusions so the prose reads like executive intelligence rather than a report dump

---

## Solutions Implemented

### Intelligent Scoring System
```
Score Calculation:
- Base: Sum of weighted keyword matches
- Weight Range: 15-25 points per keyword
- Threshold: Source-aware minimum score plus engagement checks where applicable
- Source Weighting: Apply credibility multiplier based on source
```

### Category Classification
Priority-based detection:
1. **RAG/Infrastructure**: Keywords like "rag", "retrieval", "memory", "mcp"
2. **Enterprise**: Keywords like "enterprise", "governance", "saas"
3. **Developer**: Keywords like "developer", "coding", "programming"
4. **Research**: Academic/paper indicators
5. **News**: Default category

### Deduplication Logic
- Canonical URL normalization
- Title and summary similarity matching
- Source-aware replacement of weaker duplicates
- Removes near-duplicates and rewritten duplicates across portals

### Multi-Perspective Insights
Each article receives analysis from three angles:
- **Why It Matters**: Trend relevance
- **SaaS Impact**: Market/business implications
- **PM Perspective**: Product opportunity/consideration

---

## Dependencies

```
feedparser         - RSS feed parsing
pandas             - Data manipulation
openpyxl           - Excel export
requests           - HTTP requests
beautifulsoup4     - HTML parsing and cleaning
rapidfuzz          - Similarity scoring for dedupe and clustering
reportlab          - Carousel and whitepaper PDF generation
```

---

## Current File Structure

```
agentic-news-engine/
├── main.py                          # Main execution script & pipeline orchestrator
├── README.txt                       # Basic setup instructions
├── requirements.txt                 # Python dependencies
├── CONTEXT.md                       # This file - Project documentation
├── engines/                         # Trend analysis and dataset merging
│   ├── historical_filter_engine.py  # Builds master datasets from historical runs
│   ├── refinement_engine.py         # Builds refined datasets
│   └── trend_analytics.py           # Creates trend report markdown
│
├── collectors/                      # Article collection modules
│   ├── __init__.py
│   ├── api_collector.py             # Generic API collection framework
│   ├── hackernews_collector.py      # Hacker News API integration
│   ├── reddit_collector.py          # Reddit AI discussion collection (⚠️ 403 issues)
│   └── rss_collector.py             # RSS feed aggregation
│
├── config/                          # Configuration files
│   ├── keywords.json                # High-signal keywords list
│   └── portals.json                 # News source definitions and collection methods
│
├── utils/                           # Processing & enrichment utilities
│   ├── __init__.py
│   ├── category_classifier.py      # Category detection logic
│   ├── company_detector.py         # Company mention detection
│   ├── deduplicator.py             # Duplicate removal
│   ├── excel_writer.py             # Excel export formatting
│   ├── insight_generator.py        # Insight generation (3 perspectives)
│   ├── scorer.py                   # Importance scoring engine
│   ├── quality_mode.py             # Quality mode profiles and thresholds
│   ├── source_ranker.py            # Source credibility weighting
│   └── top_updates.py              # Top stories ranking
│   └── __pycache__/
│
└── outputs/                         # Generated output directory
    ├── agentic_updates.xlsx        # Latest Excel output
    ├── refined_agentic_updates.xlsx # Canonical refined dataset (overwritten each run)
    ├── master_agentic_updates_*.xlsx
    ├── refined_agentic_updates_*.xlsx
    ├── trend_report_*.md
    └── other timestamped artifacts
```

---

## Known Maintainability Notes

1. **Duplicate filename `carousel_pdf_generator.py`** exists in two folders:
   - `generators/carousel_pdf_generator.py` — **canonical**, theme-level, reads
     `outputs/refined_agentic_updates.xlsx`, writes `outputs/carousels/`. This is
     the one the documented workflow uses.
   - `engines/carousel_pdf_generator.py` — earlier per-article prototype, reads the
     master dataset, writes `outputs/carousel/` (singular). Kept for reference but
     superseded by the style-specific generators (`linkedin_carousel_bw.py`,
     `linkedin_carousel_canva.py`). Neither file is imported by other modules, so
     they don't collide — but the shared name is confusing. Consider renaming the
     engines/ prototype (e.g. `carousel_per_article_prototype.py`) or removing it.

2. **Input-file freshness**: `refinement_engine.py` overwrites the static
   `outputs/refined_agentic_updates.xlsx` on every run AND writes a timestamped
   copy. Downstream generators read the static file first, so they always get the
   freshest refined data. Do not delete the static file or downstream tools fall
   back to the newest timestamped/master file.

3. **Carousel themes/colors**: a proposed `config/carousel_themes.json` (single
   source of truth for palettes) is the recommended next step so all carousel
   templates read colors from one place rather than hardcoding hex values.

---

## Proposed Future Structure & Enhancements

### Recommended Folder Structure for Scaling

```
agentic-news-engine/
│
├── src/                             # Refactored source code
│   ├── __init__.py
│   ├── main.py                     # Entry point
│   │
│   ├── collectors/                 # Existing collector modules
│   ├── config/                     # Existing configuration
│   ├── utils/                      # Existing utility modules
│   ├── engines/                    # Existing analysis and repurposing engines
│   ├── generators/                 # PDF / document rendering layer
│   │
│   ├── models/                     # NEW: Data models & schemas
│   │   ├── __init__.py
│   │   ├── article.py              # Article dataclass
│   │   └── portal.py               # Portal/source definitions
│   │
│   ├── services/                   # NEW: Business logic layer
│   │   ├── __init__.py
│   │   ├── collection_service.py   # Unified collection orchestration
│   │   ├── filtering_service.py    # Filtering & scoring
│   │   ├── enrichment_service.py   # Metadata enrichment
│   │   └── export_service.py       # Output generation
│   │
│   └── common/                     # NEW: Shared utilities
│       ├── __init__.py
│       ├── logger.py               # Logging configuration
│       ├── constants.py            # App constants
│       └── exceptions.py           # Custom exceptions
│
├── tests/                          # NEW: Test suite
│   ├── __init__.py
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── fixtures/                   # Test data
│
├── config/                         # Configuration management
│   ├── base.json                   # Base configuration
│   ├── portals.json                # Existing: News sources
│   ├── keywords.json               # Existing: Keywords
│   ├── categories.json             # NEW: Category rules
│   ├── companies.json              # NEW: Company database
│   └── scoring_weights.json        # NEW: Separate scoring config
│
├── outputs/                        # Generated outputs
│   ├── logs/                       # NEW: Application logs
│   ├── reports/                    # Excel/PDF exports
│   └── cache/                      # NEW: Intermediate caches
│
├── docs/                           # NEW: Documentation
│   ├── CONTEXT.md                  # This file
│   ├── ARCHITECTURE.md             # Technical architecture
│   ├── API_GUIDE.md                # API documentation
│   └── DEVELOPMENT.md              # Developer guide
│
├── requirements.txt                # Dependencies
├── setup.py                        # NEW: Package setup
├── .env.example                    # NEW: Environment variables template
├── .gitignore                      # NEW: Git ignore
└── README.md                       # NEW: Enhanced documentation
```

### Recommended Enhancements

#### 1. **Architecture Improvements**
- [ ] Extract data models (`src/models/`) for type safety
- [ ] Create service layer for business logic separation
- [ ] Implement dependency injection for testability
- [ ] Add configuration management system
- [ ] Create custom exception classes

#### 2. **New Features**
- [ ] **Real-time Monitoring**: WebSocket updates for live aggregation
- [ ] **Advanced Filtering**: ML-based relevance classification
- [ ] **Trend Detection**: Identify emerging topics and trending keywords
- [ ] **Sentiment Analysis**: Analyze tone of articles
- [ ] **Historical Analytics**: Track keyword trends over time
- [ ] **Email Delivery**: Automated report distribution
- [ ] **Web Dashboard**: Interactive news browsing interface
- [ ] **API Endpoint**: REST API for programmatic access

#### 3. **Quality Improvements**
- [ ] Comprehensive test coverage (unit + integration)
- [ ] Type hints throughout codebase
- [ ] Enhanced logging system
- [ ] Configuration validation
- [ ] Error recovery mechanisms
- [ ] Performance profiling and optimization

#### 4. **Operational Features**
- [ ] Database integration (PostgreSQL/MongoDB) for historical data
- [ ] Scheduled execution (Airflow/APScheduler)
- [ ] Alerts for critical news items
- [ ] User preferences and filters
- [ ] Multi-user support
- [ ] Rate limiting for API sources
- [ ] Caching layer (Redis)

#### 5. **Documentation & DevOps**
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Architecture diagrams
- [ ] Contributing guidelines
- [ ] Deployment guide

---

## Performance Characteristics

### Typical Execution Metrics
- **Collection Time**: ~5-15 seconds per source (depends on network)
- **Total Pipeline Duration**: ~60-120 seconds for full run
- **Articles Collected**: 50-200 per run (varies by day)
- **Filtered Output**: 10-40 relevant articles per run
- **Processing Efficiency**: ~80% of collected articles filtered out
- **Theme Clustering Output**: typically 8-18 themes in refined runs
- **Carousel Generation**: one PDF per theme in `outputs/carousels/`
- **Whitepaper Generation**: one PDF per theme in `outputs/whitepapers/`

### Optimization Opportunities
1. Parallel source collection (currently sequential)
2. Caching of parsed feeds
3. Incremental updates instead of full refresh
4. Database integration for faster deduplication

---

## Usage

### Setup & Execution
```bash
# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python main.py

# Build theme carousel PDFs
python generators/carousel_pdf_generator.py

# Build theme whitepaper PDFs
python engines/whitepaper_generator.py

# Primary outputs
outputs/agentic_updates.xlsx
outputs/linkedin_posts_*.md
outputs/trend_report_*.md
```

### Configuration
- **News Sources**: Edit `config/portals.json` to add/remove RSS feeds
- **Keywords**: Modify `config/keywords.json` to change filtering keywords
- **Scoring**: Adjust keyword weights in `utils/scorer.py`
- **Categories**: Update patterns in `utils/category_classifier.py`

---

## Key Metrics & KPIs

- **Collection Coverage**: 19 sources aggregated daily
- **Keyword Tracking**: 26 high-signal keywords monitored
- **Company Watch List**: 13 tracked AI/tech companies
- **Category Diversity**: 5+ article categories
- **Relevance Rate**: Avg 20-30% of collected articles meet threshold
- **Processing Speed**: Sub-2-minute full pipeline execution
- **Output Quality**: 3-perspective analysis per article
- **Theme-Level Outputs**: clustered narratives converted into per-theme PDFs rather than article dumps

---

## Known Limitations

1. **No Advanced NLP**: Insight generation uses pattern matching, not ML
2. **Manual Configuration**: Keywords, companies, and weights are manually set
3. **No Persistence**: Historical data not stored (each run is independent)
4. **Sequential Processing**: Sources collected one at a time (not parallel)
5. **Limited Deduplication**: May miss subtle duplicates
6. **Config / pipeline mismatch**: Some sources can be listed in config before their collector is wired into `main.py`
7. **RSS-dependent for many sources**: No general web scraping layer yet
8. **Reddit API Blocked**: 403/429 errors mitigated via custom User-Agents and retry loops, but true reliability requires OAuth implementation.
9. **Hacker News Low Results**: Keyword filtering too strict, producing 0 results in many runs
10. **Intermittent Feed Failures**: 5 RSS feeds consistently returning 0 results
11. **Editorial Polishing Still Ongoing**: The content layer is now stronger, but theme-specific copy can still be tightened further when new topics appear

---

## Troubleshooting & Known Issues

*(Note: The old TROUBLESHOOTING.md has been deleted; issues are now tracked here).*

- **Reddit Rate Limiting**: Largely mitigated via retry loops and custom User-Agent in the collector.
- **Hacker News Low Collection**: Timeouts have been increased to allow more comprehensive fetching.
- **Product Hunt Integration**: Currently returns 0 updates until `PRODUCTHUNT_TOKEN` is configured.
- **Performance Metrics**: Added source-specific execution times to the console output to track slow endpoints.

---

## Next Steps for Development

### Immediate (Priority 1)
1. Add database storage for historical data
2. Implement basic web dashboard
3. Set up automated scheduling (daily runs)
4. Add email notification system

### Short-term (Priority 2)
1. Enhance deduplication with similarity scoring
2. Add trend detection capabilities
3. Implement user preferences/filtering
4. Create REST API for integration

### Long-term (Priority 3)
1. ML-based relevance classification
2. Real-time processing pipeline
3. Multi-user platform with personalization
4. Advanced analytics and reporting

### Current Editorial Focus
1. Keep refining executive copy so whitepapers and carousels stay strategic rather than descriptive
2. Maintain theme-level synthesis so repeated stories collapse into one market thesis
3. Preserve concise, executive-friendly phrasing across all downstream outputs

---

## Maintenance Notes

- **Feed URLs**: Verify quarterly that all RSS feeds are still active
- **Keywords**: Review and update keyword list monthly based on trends
- **Company List**: Add new AI companies as market evolves
- **Scoring Weights**: Adjust based on output quality feedback
- **Dependencies**: Keep feedparser and openpyxl updated
- **Editorial Tone**: Review carousel/whitepaper copy periodically for repetition, generic phrasing, and weak transitions

---

**Last Updated**: June 15, 2026  
**Project Status**: Active Development  
**Maintained By**: Agentic News Engine Team
