# Agentic News Engine

## Product Overview
Agentic News Engine is an automated AI-driven pipeline that collects, deduplicates, scores, filters, and formats news and market updates about the Agentic AI space. It runs across multiple portals including RSS feeds, HackerNews, Reddit, and ProductHunt, ingesting data to create structured datasets, insights, and various output formats (such as LinkedIn posts and PDF carousels).

## Features
- **Multi-Source Ingestion**: Pulls updates from RSS, HackerNews, Reddit, and ProductHunt APIs.
- **Deduplication Engine**: Uses fuzzy matching and token set ratios to prevent duplicate news processing.
- **Intelligent Filtering & Scoring**: Assigns importance scores and categorizes articles based on tracked keywords and companies.
- **Generative Outputs**: Creates summaries, whitepapers, formatted LinkedIn drafts, and PDF carousels.
- **Configurable Quality Modes**: Allows dynamic threshold adjustment to control output volume and quality.
- **Theme Clustering**: Groups similar articles into high-level themes.

## Architecture Summary
The system operates as a sequential data pipeline:
1. **Collectors** (`collectors/`): Fetch raw articles from various external APIs and feeds.
2. **Utils/Filters** (`utils/`): A suite of tools that process raw articles, filtering out low-engagement links, assigning categories, scoring importance, extracting company mentions, and generating contextual insights.
3. **Engines/Generators** (`engines/`, `generators/`): Consume the processed articles to generate final outputs (Markdown, Excel, PDF, JSON).

## Installation
1. Clone the repository.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your environment variables (e.g., `PRODUCTHUNT_TOKEN`).

## Usage
Run the main engine:
```bash
python main.py
```
To run a configuration check without hitting external APIs:
```bash
python main.py --check-now
```

## Outputs
Outputs are saved in the `outputs/` directory and can include:
- Extracted and enriched articles in `.xlsx` format.
- Markdown drafts for LinkedIn posts.
- Topic-specific whitepapers and PDF carousels.
