# Agentic News Engine - Troubleshooting Guide

## Current Issues & Solutions (June 6, 2026)

### June 6 Runtime Fixes

- `python main.py --check-now` now runs fast local configuration validation without network collection.
- Full collection now runs sources concurrently with bounded workers instead of waiting source-by-source.
- Reddit RSS fallback now uses explicit HTTP timeouts.
- Hacker News item fetching now has a source-level timeout and cancels pending slow requests.
- Product Hunt collection is implemented when `PRODUCTHUNT_TOKEN` is configured, and remains a clean 0-update source without credentials.
- LinkedIn output generation no longer writes an empty Markdown file when no articles pass filtering.
- `reportlab` is listed in `requirements.txt` for the PDF engines.

Verification on June 6, 2026:

```bash
python -B main.py --check-now
python -B main.py
```

Both commands completed successfully. In the current sandbox, outbound HTTP is refused by a local proxy, so the full run correctly returned 0 updates without crashing.

### Issue 1: Reddit API Blocking (403 Forbidden)

**Symptoms:**
```
Reddit error MachineLearning: 403 Client Error: Blocked for url: https://www.reddit.com/r/MachineLearning/hot.json?limit=10
```

**Root Cause:** Reddit has blocked unauthenticated access to the `/hot.json` endpoint. Even with proper User-Agent headers, Reddit now requires OAuth authentication or API credentials.

**Current Status:**
- Reddit collection uses RSS fallback with explicit HTTP timeouts.
- If Reddit blocks RSS or the network is unavailable, the collector returns 0 updates and the rest of the pipeline continues.
- Reliable Reddit collection still requires OAuth or an authenticated API client.

**Solutions (in priority order):**

1. **Use Reddit API with OAuth (Recommended)**
   - Register app at https://www.reddit.com/prefs/apps
   - Get client_id and client_secret
   - Implement OAuth2 flow in `collectors/reddit_collector.py`
   - Add credentials to `.env` or config file
   - Expected effort: 2-3 hours

2. **Use PRAW Library (Reddit Python API)**
   ```bash
   pip install praw
   ```
   - Handles OAuth automatically
   - Better rate limiting
   - Cleaner implementation
   - Expected effort: 1-2 hours

3. **Use Pushshift API Alternative**
   - Pushshift provides Reddit data without OAuth
   - Alternative endpoint: `https://api.pushshift.io/reddit/submission/search`
   - Less reliable but no authentication needed
   - Expected effort: 1 hour

4. **Disable Reddit Collection (Temporary)**
   - Remove Reddit entries from `config/portals.json`
   - Keeps pipeline working for other sources
   - Expected effort: 5 minutes

---

### Issue 2: Hacker News Low Collection Rate

**Symptoms:**
- Hacker News returning 0 articles in recent runs
- Timeout increased from 2s to 5s per item (May 31)
- Still producing minimal results

**Root Cause:** 
- Low signal-to-noise ratio on HN top stories relative to agentic AI keywords
- Possible timeout issues on FirebaseIO API
- Keyword filtering too strict

**Current Status:**
- Timeout increased to 5 seconds
- Still need to analyze keyword match rate

**Solutions:**

1. **Relax Keyword Filtering**
   - Lower similarity threshold in `utils/deduplicator.py` (currently 80)
   - Add more broad keywords to HN collection

2. **Increase Sample Size**
   - Currently fetching top 10 stories
   - Increase to top 20-30 in `main.py` (line ~95)

3. **Add Comment Analysis**
   - Comments sometimes more relevant than titles
   - Requires fetching comments (API call per story)

4. **Monitor Feed Quality**
   - Add logging to see which keywords match
   - Identify if content truly irrelevant or filtering too strict

---

### Issue 3: Zero Results from Some Major RSS Feeds

**Affected Sources:**
- The Verge (0 updates)
- The Batch (0 updates)
- AI Breakfast (0 updates)
- a16z (0 updates)
- Y Combinator (0 updates)

**Possible Causes:**

1. **Feed URL Broken**
   - URLs in `config/portals.json` may have changed
   - RSS feed structure may have changed
   - Feed may be deprecated

2. **No Matching Content**
   - Feed content doesn't contain agentic AI keywords
   - Feeds may have rotated content

3. **Parsing Issues**
   - Feed format not parsed correctly
   - Missing HTML entity decoding

4. **Timeout Issues**
   - Feed server slow to respond
   - Network timeout before complete fetch

**Solutions:**

1. **Validate Feed URLs**
   ```bash
   # Test each feed manually
   python -c "
   import feedparser
   feed = feedparser.parse('https://www.theverge.com/rss/index.xml')
   print(f'Entries: {len(feed.entries)}')
   for entry in feed.entries[:3]:
       print(f'- {entry.title[:80]}')
   "
   ```

2. **Add Logging to RSS Collector**
   - Print number of items fetched per feed
   - Log why items are filtered
   - Identify which feeds are problematic

3. **Increase Timeout**
   - Some feeds take longer to respond
   - Increase timeout in `collectors/rss_collector.py`

4. **Update Feed URLs**
   - Verify all feeds still work
   - Remove deprecated feeds
   - Add new relevant feeds

---

### Issue 4: Product Hunt Requires Token

**Current Status:** Implemented as an optional GraphQL collector. It returns 0 updates unless `PRODUCTHUNT_TOKEN` is set.

**To Enable:**

1. Get a Product Hunt developer token.
2. Set it before running:
   ```bash
   set PRODUCTHUNT_TOKEN=<your_product_hunt_developer_token>
   ```
3. Run `python main.py`.

---

## Performance Metrics (May 31, 2026)

| Metric | Value | Status |
|--------|-------|--------|
| Total Sources | 20 | ✅ Wired |
| RSS Sources Working | 11/15 | ⚠️ 4 returning 0 |
| Hacker News | Partial | ⚠️ Low results |
| Reddit | Failed | ❌ 403 Blocked |
| Product Hunt | Optional | Requires PRODUCTHUNT_TOKEN |
| **Total Collection Time** | 46.77s | ⚠️ Slower due to retries |
| **Raw Articles** | 70 | ✅ |
| **After Dedup** | 69 | ✅ |
| **Quality Articles** | 28 | ✅ |

---

## Recommended Next Steps

### Priority 1 (Today)
- [x] Add bounded Reddit RSS fallback
- [ ] Validate and test RSS feed URLs
- [ ] Add logging to identify exact filtering issues

### Priority 2 (This Week)
- [ ] Implement Reddit OAuth or PRAW
- [ ] Improve Hacker News keyword matching
- [ ] Document current working/broken sources

### Priority 3 (Future)
- [x] Add optional Product Hunt API integration
- [ ] Implement caching to avoid redundant API calls
- [ ] Add database for historical article tracking

---

## Quick Diagnostics

### Check a Specific Feed
```python
import feedparser
feed = feedparser.parse('https://techcrunch.com/feed/')
print(f"Entries: {len(feed.entries)}")
for entry in feed.entries[:3]:
    print(f"- {entry.title}")
```

### Test Reddit Access
```bash
curl -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
  https://www.reddit.com/r/MachineLearning/hot.json?limit=5
```

### Run Specific Collector
```bash
python -c "
from collectors.hackernews_collector import collect_hackernews
articles = collect_hackernews(limit=30)
print(f'HN returned {len(articles)} articles')
"
```

---

## Contact & References

- Reddit API Docs: https://www.reddit.com/dev/api
- Hacker News API: https://github.com/HackerNews/API
- PRAW Library: https://praw.readthedocs.io/
- Product Hunt API: https://api.producthunt.com/v2/docs
