from utils.quality_mode import (
    get_category_multiplier,
    get_source_scale,
)


SOURCE_WEIGHTS = {

    # Tier 1 — primary AI labs (highest authority, first-party announcements)
    "OpenAI": 22,
    "Google DeepMind": 22,
    "Anthropic": 22,
    "Google AI Blog": 18,
    "Hugging Face": 18,
    "NVIDIA Blog": 14,

    # Tier 1 — premium tech press
    "VentureBeat": 20,
    "MIT Technology Review": 20,
    "TechCrunch": 15,
    "The Decoder": 14,
    "MarkTechPost": 12,
    "The Verge": 10,
    "Wired": 10,
    "Ars Technica": 10,

    # Tier 2 — expert newsletters / commentary
    "Import AI": 15,
    "Simon Willison": 15,
    "Ahead of AI": 12,
    "Latent Space": 12,
    "TLDR AI": 10,
    "Ben's Bites": 10,
    "Stratechery": 12,

    # Tier 2 — research labs
    "BAIR Berkeley": 14,
    "MIT News AI": 12,

    # Tier 3 — VC / startup
    "a16z": 10,
    "Y Combinator": 10,
    "Sequoia Capital": 10,

    # Reddit penalty (community noise)
    "r/MachineLearning": -10,
    "r/LocalLLaMA": -10,
    "r/singularity": -15
}


def apply_source_weight(
    score,
    source,
    category=None,
    mode=None
):

    bonus = SOURCE_WEIGHTS.get(
        source,
        0
    )

    source_scale = get_source_scale(
        mode
    )

    category_multiplier = get_category_multiplier(
        category,
        mode
    )

    adjusted = (
        score
        + round(bonus * source_scale)
    )

    adjusted = round(
        adjusted * category_multiplier
    )

    return max(
        adjusted,
        0
    )