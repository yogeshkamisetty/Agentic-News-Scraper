import json
import os


QUALITY_MODE_CONFIG_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ),
    "config",
    "quality_modes.json"
)

DEFAULT_QUALITY_MODE = "balanced"

_QUALITY_MODES = None


def load_quality_modes():

    global _QUALITY_MODES

    if _QUALITY_MODES is not None:
        return _QUALITY_MODES

    try:
        with open(
            QUALITY_MODE_CONFIG_PATH,
            "r",
            encoding="utf-8"
        ) as file:
            _QUALITY_MODES = json.load(file)
    except Exception:
        _QUALITY_MODES = {
            DEFAULT_QUALITY_MODE: {
                "score_floor": 35,
                "source_scale": 1.0,
                "category_multipliers": {
                    "Agentic AI": 1.1,
                    "RAG / Infrastructure": 1.1,
                    "Developer AI": 1.05,
                    "Enterprise AI": 1.1,
                    "AI Update": 1.0,
                },
                "source_thresholds": {
                    # Raised from 25 → 40 for tier1 to prevent low-signal
                    # articles from sneaking through on source bonus alone.
                    "tier1": 40,
                    "newsletters": 45,
                    "reddit": 40,
                    "hackernews": 38,
                    "default": 38,
                },
                "refine_min_score": 35,
                "content_top_n": {
                    "trend": 10,
                    "carousel": 8,
                    "linkedin": 8,
                    "whitepaper": 15,
                    "default": 5,
                },
                "category_caps": {
                    "Agentic AI": 3,
                    "RAG / Infrastructure": 3,
                    "Developer AI": 2,
                    "Enterprise AI": 2,
                    "AI Update": 2,
                },
            }
        }

    return _QUALITY_MODES


def get_quality_mode(value=None):

    if value:
        candidate = str(value).strip().lower()
    else:
        candidate = str(os.environ.get("QUALITY_MODE", DEFAULT_QUALITY_MODE)).strip().lower()

    modes = load_quality_modes()

    if candidate not in modes:
        return DEFAULT_QUALITY_MODE

    return candidate


def get_quality_profile(mode=None):

    modes = load_quality_modes()
    active_mode = get_quality_mode(mode)
    return modes.get(active_mode, modes[DEFAULT_QUALITY_MODE])


def get_source_threshold(source, mode=None):

    profile = get_quality_profile(mode)
    source = str(source or "").lower()

    tier1 = {
        "techcrunch",
        "venturebeat",
        "mit technology review",
        "wired",
        "the verge",
        "ars technica",
    }

    newsletters = {
        "import ai",
        "ben's bites",
        "latent space",
        "ahead of ai",
    }

    reddit_sources = {
        "r/machinelearning",
        "r/localllama",
        "r/singularity",
    }

    source_thresholds = profile.get("source_thresholds", {})

    if source in tier1:
        return source_thresholds.get("tier1", profile.get("score_floor", 30))

    if source in newsletters:
        return source_thresholds.get("newsletters", profile.get("score_floor", 30))

    if source in reddit_sources:
        return source_thresholds.get("reddit", profile.get("score_floor", 30))

    if source == "hacker news":
        return source_thresholds.get("hackernews", profile.get("score_floor", 30))

    return source_thresholds.get("default", profile.get("score_floor", 30))


def get_refine_min_score(mode=None):

    profile = get_quality_profile(mode)
    return profile.get("refine_min_score", profile.get("score_floor", 30))


def get_content_top_n(mode=None, content_type="default"):

    profile = get_quality_profile(mode)
    top_n_map = profile.get("content_top_n", {})
    return top_n_map.get(content_type, top_n_map.get("default", 5))


def get_category_multiplier(category, mode=None):

    profile = get_quality_profile(mode)
    multipliers = profile.get("category_multipliers", {})
    return multipliers.get(category, 1.0)


def get_source_scale(mode=None):

    profile = get_quality_profile(mode)
    return profile.get("source_scale", 1.0)


def get_category_caps(mode=None):

    profile = get_quality_profile(mode)
    return profile.get("category_caps", {})
