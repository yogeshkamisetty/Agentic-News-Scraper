# Exact Code Changes - May 31, 2026

## File 1: collectors/reddit_collector.py

### Change 1.1: Added imports
```python
import requests
import time  # ADDED
```

### Change 1.2: Improved headers
```python
HEADERS = {
    "User-Agent":
    (
        "Mozilla/5.0 "
        "(Windows NT 10.0; "
        "Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0.0.0 "  # UPDATED: was "Chrome/124.0"
        "Safari/537.36"
    ),
    "Accept": "application/json",  # ADDED
    "Accept-Encoding": "gzip, deflate"  # ADDED
}
```

### Change 1.3: Retry logic wrapper
```python
def collect_reddit(subreddit, limit=10):
    articles = []
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    
    max_retries = 2  # ADDED
    retry_count = 0  # ADDED
    
    while retry_count < max_retries:  # ADDED: Wrap in while loop
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=12  # CHANGED: was 8
            )
            response.raise_for_status()
            
            data = response.json()
            
            # FIXED: Moved inside try block (was outside)
            posts = data.get("data", {}).get("children", [])
            
            AI_KEYWORDS = [...]
            
            # FIXED: Moved inside try block and indented (was outside)
            for post in posts:
                # ... process posts ...
            
            return articles
        
        except Exception as e:  # ADDED: Different error handling
            retry_count += 1
            
            if retry_count < max_retries:  # ADDED: Retry logic
                time.sleep(1)  # ADDED: 1 second delay
                continue
            else:
                print(
                    f"Reddit error {subreddit}: "
                    f"{str(e)[:100]}"  # CHANGED: truncate to 100 chars
                )
    
    return articles
```

---

## File 2: collectors/hackernews_collector.py

### Change 2.1: Increased timeout
```python
item_response = session.get(
    ITEM_URL.format(story_id),
    timeout=5  # CHANGED: was 2
)
```

---

## File 3: main.py

### No changes
Product Hunt handling already in place:
```python
elif method == "producthunt":
    return collect_producthunt()
```

---

## New Files Created

### 1. TROUBLESHOOTING.md
- Complete troubleshooting guide
- 4 major issues documented
- Solutions with implementation guides
- Diagnostic procedures
- ~250 lines

### 2. FIXES_SUMMARY_2026-05-31.md
- This summary document
- Test results
- Remaining work
- Next steps

---

## Configuration Changes

**No configuration file changes required.**

All fixes are in code. To apply:
1. Update `collectors/reddit_collector.py` with retry logic
2. Update `collectors/hackernews_collector.py` with timeout increase
3. No changes to config files needed

---

## Testing the Changes

```bash
# Test the fixed pipeline
python main.py

# Expected output should NOT have syntax errors
# Reddit will still show 403 errors (requires OAuth to fix)
# Hacker News should have more time to fetch items (5s timeout)
```

---

## Validation Checklist

- [x] No syntax errors
- [x] Reddit collector has retry logic
- [x] Hacker News timeout increased
- [x] Product Hunt handled gracefully
- [x] Pipeline completes successfully
- [x] Documentation created
- [ ] Reddit OAuth implemented (future work)
- [ ] Empty RSS feeds investigated (future work)
- [ ] Hacker News results improved (future work)
