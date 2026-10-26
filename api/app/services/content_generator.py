"""Deterministic, offline content generator used for the local demo."""

from __future__ import annotations

import hashlib
import re

from app.models import ContentGenerationRequest, GeneratedContent

_PLATFORM_OPENERS = {
    "x": ("Quick thought:", "Worth a moment:", "A small reminder:"),
    "linkedin": ("For the conversation:", "A perspective to consider:", "On money goals:"),
    "instagram": ("Save this reminder:", "Small steps matter:", "A little encouragement:"),
    "facebook": ("Let’s talk about it:", "A thought for today:", "What do you think?"),
}

_OBJECTIVE_LINES = {
    "brand_awareness": (
        "{topic} deserves a place in everyday money conversations.",
        "Let’s make room to talk about {topic} with curiosity and care.",
    ),
    "engagement": (
        "What does {topic} mean to you? Share one thoughtful step you’re considering.",
        "Everyone’s path is different. What is one thing you want to learn about {topic}?",
    ),
    "education": (
        "Learn about {topic}, compare your options, and consider what fits your circumstances.",
        "A useful conversation about {topic} starts with clear questions and reliable information.",
    ),
    "product_promotion": (
        "Explore whether {topic} fits your goals, priorities, and budget.",
        "Take a closer look at {topic} and decide whether it suits your needs.",
    ),
}

_TONE_CLOSERS = {
    "professional": ("Take time to review what works for you.", "Consider your options at your own pace."),
    "inspiring": ("Your next step can be a thoughtful one.", "Small, considered steps can move a goal forward."),
    "friendly": ("Start with what feels manageable for you.", "Here’s to making room for your next small step."),
    "persuasive": ("Explore a next step that fits your priorities.", "Make time to see what could work for you."),
}

_STOP_WORDS = {
    "about", "after", "and", "are", "for", "from", "into", "its", "make", "more",
    "money", "next", "that", "the", "their", "this", "with", "your", "you",
}


def generate_content(request: ContentGenerationRequest) -> GeneratedContent:
    """Create a reproducible draft from local templates; no model is called."""
    seed_material = "|".join(
        (request.topic, request.platform, request.objective, request.tone, request.keywords or "")
    )
    digest = hashlib.sha256(seed_material.encode("utf-8")).digest()
    variant = digest[0] % 2
    topic = _caption_topic(request.topic, request.platform)

    opener = _PLATFORM_OPENERS[request.platform][digest[1] % len(_PLATFORM_OPENERS[request.platform])]
    message = _OBJECTIVE_LINES[request.objective][variant].format(topic=topic)
    closer = _TONE_CLOSERS[request.tone][digest[2] % len(_TONE_CLOSERS[request.tone])]
    caption = f"{opener} {message} {closer}"

    # X posts get a concise topic and the generated caption stays within 280 chars.
    if request.platform == "x" and len(caption) > 280:
        caption = f"{opener} {message[: 280 - len(opener) - 2].rstrip(' .')}…"

    return GeneratedContent(
        topic=request.topic,
        caption=caption,
        hashtags=_suggest_hashtags(request.topic, request.keywords),
        platform=request.platform,
        objective=request.objective,
        tone=request.tone,
        character_count=len(caption),
        is_demo_generated=True,
    )


def _caption_topic(topic: str, platform: str) -> str:
    limit = 72 if platform == "x" else 120
    compact = " ".join(topic.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 1].rstrip()}…"


def _suggest_hashtags(topic: str, keywords: str | None) -> list[str]:
    candidates = re.findall(r"[A-Za-z0-9]+", f"{topic} {keywords or ''}")
    tags: list[str] = []
    seen: set[str] = set()
    for word in candidates:
        normalized = word.lower()
        if normalized in _STOP_WORDS or len(word) < 3 or normalized in seen:
            continue
        seen.add(normalized)
        safe_word = word[:31]
        tags.append(f"#{safe_word[0].upper()}{safe_word[1:]}")
        if len(tags) == 2:
            break
    if "fundly" not in seen:
        tags.append("#Fundly")
    elif not tags:
        tags.append("#Fundly")
    return tags
