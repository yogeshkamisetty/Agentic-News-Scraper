import re


# ── Word-boundary helper ───────────────────────────────────────────────────
# Prevents "developer" from matching "underdeveloped",
# "agent" from matching partial substrings, etc.

def _has(text: str, *terms) -> bool:
    """Return True if ANY term appears at a word boundary in text."""
    for term in terms:
        if re.search(r"\b" + re.escape(term), text, re.IGNORECASE):
            return True
    return False


def detect_category(text: str) -> str:
    """
    Classify an article into one of five categories.

    Priority order (most specific → most general):
      1. Developer AI     — coding, terminal, copilot work
      2. RAG/Infra        — retrieval, vector, context plumbing
      3. Enterprise AI    — governance, compliance, rollout
      4. Agentic AI       — autonomous agents, orchestration, workflows
      5. AI Update        — catch-all

    Changed from original:
    - Word-boundary matching (was plain substring → "dragon" triggered RAG)
    - Developer AI checked BEFORE Agentic AI so coding articles
      are no longer absorbed into the Agentic AI bucket
    - Enterprise AI checked before Agentic AI for governance articles
    """

    t = text.lower()

    # ── 1. Developer AI ──────────────────────────────────────────────────
    # Must mention coding/developer tooling explicitly.
    if _has(t, "coding agent", "code generation", "codegen",
               "copilot", "terminal", "cli agent", "developer tool",
               "ai coding", "programming assistant"):
        return "Developer AI"

    # Generic developer/coding — but only if NOT primarily about agents
    if _has(t, "coding", "developer") and not _has(t, "agentic", "multi-agent", "orchestration"):
        return "Developer AI"

    # ── 2. RAG / Infrastructure ──────────────────────────────────────────
    # Retrieval, vector, context infrastructure — explicit terms only.
    if _has(t, "rag", "retrieval augmented", "vector database",
               "vector store", "embedding model", "knowledge graph",
               "context window", "long context", "grounding"):
        return "RAG / Infrastructure"

    # Memory architecture (non-agent context)
    if _has(t, "memory model", "working memory", "episodic memory",
               "delta-mem", "osam matrix"):
        return "RAG / Infrastructure"

    # ── 3. Enterprise AI ─────────────────────────────────────────────────
    if _has(t, "governance", "compliance", "audit", "policy enforcement",
               "enterprise deployment", "rollout", "procurement",
               "organizational design", "enterprise ai", "saas ai"):
        return "Enterprise AI"

    # ── 4. Agentic AI ────────────────────────────────────────────────────
    if _has(t, "ai agent", "agentic", "autonomous agent", "multi-agent",
               "agent workflow", "orchestration", "tool use", "tool call",
               "agent memory", "planning agent", "mcp", "function calling",
               "agent framework", "langchain", "crewai"):
        return "Agentic AI"

    # Broader agent/workflow signal — only if no stronger category matched
    if _has(t, "agent", "workflow", "automation", "memory", "reasoning"):
        return "Agentic AI"

    # ── 5. Catch-all ─────────────────────────────────────────────────────
    return "AI Update"
