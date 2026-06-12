# End-to-End Workflow

The operational workflow of the Agentic News Engine consists of a continuous pipeline moving from raw data collection to curated, publishable content.

## 1. Source Ingestion
The process begins when `main.py` is executed.
- The `load_portals()` function reads `config/portals.json`.
- A ThreadPoolExecutor spins up concurrent workers (up to `MAX_COLLECTION_WORKERS`).
- Each worker queries its assigned platform (HackerNews, Reddit, RSS, ProductHunt) fetching recent updates.
- If an API fails (e.g., rate limits), the pipeline logs a warning and proceeds with the remaining data.

## 2. Deduplication (Phase 1)
Because multiple portals may report on the same event (e.g., a new AI model launch on both Reddit and HackerNews), the engine must deduplicate early.
- All raw articles are merged into a single array.
- `utils.deduplicator.py` uses string normalization and fuzzy matching (Token Sort & Token Set Ratios) on titles and summaries.
- Redundant articles are discarded, keeping the highest-priority source.

## 3. Analysis & Processing
Each deduplicated article undergoes individual processing (`process_article`):
1. **Categorization**: Text is analyzed using `category_classifier.py` to tag the event type (e.g., "Funding", "Product Launch").
2. **Company Detection**: `company_detector.py` scans for known entities (e.g., OpenAI, Anthropic) based on tracked keywords.
3. **Scoring**: `scorer.py` evaluates the importance of the article by looking for high-value keywords and multiplying by source weight.
4. **Insight Generation**: `insight_generator.py` extracts three key perspectives:
   - *Why It Matters*
   - *SaaS Impact*
   - *PM Perspective*

## 4. Filtering (Phase 2)
To ensure only high-quality content reaches the final output:
- **Threshold Check**: The calculated score must meet the dynamic threshold set by the current `QUALITY_MODE`.
- **Engagement Check**: Articles from platforms like Reddit must pass `passes_engagement_filter` (e.g., minimum 5 upvotes, 5 comments).
- **Substantive Content Check**: Articles with summaries under 60 characters are dropped to filter out "link stubs."

## 5. Content Draft Generation
The high-quality articles proceed to the generators:
- **Excel Report**: `excel_writer.py` dumps the fully structured data (title, URL, insights, score, category) into an `.xlsx` file for data analysts.
- **LinkedIn Drafts**: `linkedin_generator.py` converts the structured insights into formatted Markdown designed specifically for LinkedIn posts.
- **Theme Clustering & Whitepapers**: `theme_clustering.py` identifies broad trends across the accepted articles and feeds this to `engines/whitepaper_generator.py` or `carousel_pdf_generator.py`.

## 6. Review & Publishing
This stage is manual (handled by the User or Social Media Manager):
- The generated Excel spreadsheet acts as the master record.
- The `.md` and `.pdf` files located in the `outputs/` folder are reviewed, edited if necessary, and manually published to LinkedIn or other target platforms.
