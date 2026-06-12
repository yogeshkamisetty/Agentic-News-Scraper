from utils.quality_mode import (
    get_category_multiplier,
    get_source_scale,
)


SOURCE_WEIGHTS = {

    # Tier 1
    "TechCrunch": 15,
    "VentureBeat": 20,
    "MIT Technology Review": 20,
    "The Verge": 10,
    "Wired": 10,
    "Ars Technica": 10,

    # Tier 2
    "Import AI": 15,
    "The Batch": 15,
    "Ahead of AI": 12,
    "AI Breakfast": 10,
    "Ben's Bites": 10,
    "Latent Space": 10,

    # Tier 3
    "a16z": 10,
    "Y Combinator": 10,
    "Sequoia Capital": 10,

    # Reddit penalty
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