import re


HIGH_SIGNAL_KEYWORDS = {

    # strongest signals — agentic & orchestration
    "agent":          15,
    "agentic":        20,
    "mcp":            20,
    "orchestration":  20,
    "multi-agent":    18,

    # memory & retrieval
    "rag":            18,   # word-boundary matched — won't hit "dragon"
    "memory":         18,
    "reasoning":      18,
    "retrieval":      15,
    "vector database":15,
    "embedding":       8,

    # access & safety
    "permissions":    12,
    "permission":     12,
    "authorization":  10,
    "sandbox":        12,
    "policy":          8,
    "governance":     12,

    # developer & tooling
    "coding":         15,
    "developer":      15,
    "copilot":        15,
    "terminal":       12,
    "langchain":      15,
    "crewai":         15,

    # AI product signals
    "workflow":       15,
    "automation":     15,
    "enterprise":     15,
    "llm":            12,
    "benchmark":       8,
    "evaluation":      8,
    "eval":            8,

    # model names
    "gemini":         10,
    "claude":         10,
    "anthropic":      10,
    "openai":         10,
    "mistral":        10,
    "gpt":            10,

    # misc
    "browser":        10,
}


LOW_SIGNAL_KEYWORDS = {

    "funding":       -10,
    "acquisition":   -10,
    "celebrity":     -20,
    "lawsuit":       -20,
    "gossip":        -30,
    "viral":         -15,
    "opinion":       -10,
    "rumor":         -15,
    "marketing":     -10,
    "design":        -10,
    "trailer":       -25,   # movie/TV trailers
    "romance":       -25,
    "scam":          -20,
    "season":        -15,   # TV seasons
    "lithium":       -20,   # non-AI tech
    "battery":       -15,
}


# ── Single-word boundary matching ──────────────────────────────────────────
#
# Bug fix: plain `if keyword in text` causes false positives:
#   "rag" matches "d-rag-on"   →  Dragon articles score +18
#   "mcp" could match "compact" etc.
#
# Rule: use \b<keyword> so the keyword must start at a word boundary.
# This means "rag" matches "rag-based / RAG architecture" but NOT "dragon".
# Multi-word keywords (e.g. "vector database") are matched as a phrase.

_KEYWORD_PATTERNS = {
    kw: re.compile(r"\b" + re.escape(kw), re.IGNORECASE)
    for kw in list(HIGH_SIGNAL_KEYWORDS) + list(LOW_SIGNAL_KEYWORDS)
}


def _match(keyword: str, text: str) -> bool:
    """True if keyword appears at a word boundary in text."""
    pat = _KEYWORD_PATTERNS.get(keyword)
    if pat is None:
        pat = re.compile(r"\b" + re.escape(keyword), re.IGNORECASE)
    return bool(pat.search(text))


def calculate_score(text):

    score = 0
    matched_keywords = []

    for keyword, weight in HIGH_SIGNAL_KEYWORDS.items():
        if _match(keyword, text):
            score += weight
            matched_keywords.append(keyword)

    for keyword, penalty in LOW_SIGNAL_KEYWORDS.items():
        if _match(keyword, text):
            score += penalty

    return (
        max(score, 0),
        matched_keywords
    )