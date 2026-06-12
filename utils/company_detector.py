"""
company_detector.py
───────────────────
Detects the primary company mentioned in an article.
Checks title first (higher confidence), then summary.
"""

# ── Company list ──────────────────────────────────────────────────────────
# Priority order: more specific names first to avoid partial matches
# (e.g. "AWS" before "Amazon" so "Amazon AWS" → "AWS")

COMPANIES = [

    # AI labs — tier 1
    "Anthropic",
    "OpenAI",
    "Google DeepMind",
    "DeepMind",
    "Google",
    "Microsoft",
    "Meta",
    "Amazon",
    "AWS",
    "NVIDIA",
    "Apple",

    # AI labs — tier 2
    "Mistral",
    "Mistral AI",
    "Cohere",
    "AI21 Labs",
    "Inflection",
    "Stability AI",
    "Runway",
    "ElevenLabs",
    "Character AI",
    "Perplexity",

    # Chinese AI labs
    "Alibaba",
    "Baidu",
    "ByteDance",
    "Tencent",
    "Zhipu AI",
    "Moonshot AI",
    "DeepSeek",
    "MiniMax",

    # Agentic / infra startups
    "LangChain",
    "LangGraph",
    "CrewAI",
    "AutoGen",
    "Cognition",
    "Devin",
    "Rippletide",
    "Kore.ai",
    "Resolve AI",
    "Mind Lab",
    "Datacurve",
    "Vertu",

    # Developer tools
    "Cursor",
    "Replit",
    "GitHub",
    "GitLab",
    "JetBrains",
    "Tabnine",
    "Codeium",

    # Vector / RAG infra
    "Pinecone",
    "Weaviate",
    "Chroma",
    "Qdrant",
    "Neo4j",
    "MongoDB",

    # Cloud / enterprise platforms
    "Salesforce",
    "ServiceNow",
    "Workday",
    "SAP",
    "Oracle",
    "IBM",
    "Cisco",

    # Investment / research
    "a16z",
    "Y Combinator",
    "Sequoia",
    "Bessemer",
    "OpenRouter",
    "Hugging Face",
    "EleutherAI",
]


def detect_company(title: str, summary: str) -> str:
    """
    Returns the first matched company name (priority: title > summary).
    Returns empty string if no match.
    """
    title_lower   = str(title or "").lower()
    summary_lower = str(summary or "").lower()

    for company in COMPANIES:
        c = company.lower()
        if c in title_lower:
            return company

    for company in COMPANIES:
        c = company.lower()
        if c in summary_lower:
            return company

    return ""
