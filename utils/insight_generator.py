def generate_insights(title, summary, category):

    text = f"{title} {summary}".lower()

    def has_any(terms):
        return any(term in text for term in terms)

    def tail(sentence, clause):
        return f"{sentence} {clause}".strip()

    if category == "Agentic AI":

        why_it_matters = "Autonomy is moving from an experimental feature to an operating model for the workflow itself."
        saas_impact = "Winning SaaS products will expose control, orchestration, and execution layers instead of only a model-facing UI."
        pm_perspective = "PMs need to decide what the system may do, what requires approval, and how failures unwind."

        if has_any(["permission", "access", "auth", "tool use", "gating"]):
            why_it_matters = tail(
                why_it_matters,
                "The bottleneck is tool access and guardrails, not model IQ."
            )
            pm_perspective = tail(
                pm_perspective,
                "This is a control-plane problem more than a model problem."
            )

        elif has_any(["memory", "state", "context", "remember"]):
            why_it_matters = tail(
                why_it_matters,
                "Persistent memory is becoming the differentiator for agents that must carry context across sessions."
            )
            saas_impact = tail(
                saas_impact,
                "Teams need durable state and retrieval layers if they want repeatable execution."
            )

        elif has_any(["benchmark", "eval", "testing"]):
            why_it_matters = tail(
                why_it_matters,
                "Benchmarks remain a weak proxy for real-world workflow reliability."
            )
            pm_perspective = tail(
                pm_perspective,
                "Success should be measured by task completion, not headline model scores."
            )

    elif category == "Enterprise AI":

        why_it_matters = "Enterprises are now judging AI through the lens of governance, reliability, and rollout cost."
        saas_impact = "Enterprise SaaS vendors can win by bundling auditability, policy controls, and safe automation into the core product."
        pm_perspective = "PMs should prioritize rollout friction, admin control, and compliance readiness over feature theatrics."

        if has_any(["governance", "policy", "audit", "compliance", "security"]):
            why_it_matters = tail(
                why_it_matters,
                "Governance is no longer optional; it is part of product value."
            )
        elif has_any(["workflow", "automation", "ops"]):
            saas_impact = tail(
                saas_impact,
                "The winner will be the product that reduces operational overhead the most."
            )

    elif category == "Developer AI":

        why_it_matters = "Developer AI is shifting from a suggestion layer into the execution loop for shipping software."
        saas_impact = "Developer tools can move from copilots to workflow accelerators if they integrate deeply into the terminal, editor, and test loop."
        pm_perspective = "PMs should focus on trust, latency, reviewability, and the handoff between human oversight and agent execution."

        if has_any(["terminal", "cli", "shell"]):
            why_it_matters = tail(
                why_it_matters,
                "Terminal-native agents are becoming a practical interface for serious coding tasks."
            )
        elif has_any(["debug", "test", "eval"]):
            pm_perspective = tail(
                pm_perspective,
                "The product moat may come from better debugging and verification loops."
            )

    elif category == "RAG / Infrastructure":

        why_it_matters = "Retrieval, memory, and context handling are becoming core infrastructure rather than back-end plumbing."
        saas_impact = "Infrastructure vendors can differentiate by improving grounding, freshness, and state management in measurable ways."
        pm_perspective = "PMs should treat reliability and context quality as first-class product requirements."

        if has_any(["memory", "state", "context"]):
            why_it_matters = tail(
                why_it_matters,
                "Memory is no longer a backend detail; it is a product feature."
            )
        elif has_any(["rag", "retrieval", "vector", "index"]):
            saas_impact = tail(
                saas_impact,
                "Better retrieval can directly improve answer quality without changing the base model."
            )

    else:

        why_it_matters = "It is a relevant AI ecosystem signal with likely consequences for product direction and market positioning."
        saas_impact = "It may shift feature priorities, pricing posture, or customer expectations."
        pm_perspective = "PMs should watch whether the update changes workflows, cost structure, or adoption barriers."

        if has_any(["agent", "agentic", "workflow"]):
            why_it_matters = tail(
                why_it_matters,
                "It still points toward the automation of multi-step work."
            )
        elif has_any(["coding", "developer"]):
            pm_perspective = tail(
                pm_perspective,
                "Developer workflow impact is likely to be the fastest-to-market angle."
            )

    return why_it_matters, saas_impact, pm_perspective
