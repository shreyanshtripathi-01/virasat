"""One replaceable provider for optional AI-assisted catalog drafts."""

import json
import logging
import re

import requests
from django.conf import settings


logger = logging.getLogger(__name__)
API_URL = "https://api.anthropic.com/v1/messages"
SYSTEM_PROMPT = (
    "You write catalog entries for handmade Indian heritage crafts sold by artisans. "
    "Use ONLY the facts supplied. Do not invent history, dates, awards, GI-tag status, prices or claims. "
    "Use warm, respectful, simple English; the description is 70-110 words. "
    "Never use em dashes or en dashes. "
    "Also give a faithful simple Hindi version of the description. "
    "Write a 2-3 sentence heritage_story that stays general if details are not supplied. "
    "Write 2-3 practical lines of care_instructions suited to the materials. "
    "Provide 5-8 lowercase tags. Return STRICT JSON only with keys: title, description, "
    "hindi_description, heritage_story, care_instructions, tags (a list of strings). "
    "No markdown and no commentary."
)
TEXT_LIMITS = {
    "title": 160, "description": 1200, "hindi_description": 1600,
    "heritage_story": 600, "care_instructions": 400,
}


def clean_dashes(text):
    """Replace em and en dashes and collapse repeated spaces in display text."""
    # Syllabus extension guard: generated prose keeps a consistent punctuation style.
    if not isinstance(text, str):
        return text
    text = re.sub(r"(?<=\d)[\u2014\u2013](?=\d)", "-", text)
    text = text.replace("\u2014", ", ").replace("\u2013", ", ")
    return re.sub(r" {2,}", " ", text).strip()


def _clean_draft(draft):
    """Run every text value in a draft through the dash guard."""
    return {
        key: clean_dashes(value) if isinstance(value, str) else value
        for key, value in draft.items()
    }


def fallback_content(craft_name, state, materials, technique, notes, language_hint):
    """Build a safe, reproducible draft using only information supplied."""
    craft = craft_name.strip()[:100] or "handmade"
    origin = state.strip()[:100] or "India"
    material = materials.strip()[:150] or "carefully chosen materials"
    method = technique.strip()[:150] or "hand work"
    details = notes.strip()[:300] or "Made with care by an artisan."
    description = (
        f"This handmade {craft} piece is made using {material}. {details} "
        f"The maker uses {method} to bring each detail together. "
        f"This work is connected to the {craft} tradition associated with {origin}. "
        "It is made by hand, so small variations may appear from one piece to another. "
        "Take a closer look at its materials and details before choosing it for your home or as a gift."
    )
    hindi = (
        f"यह {craft} शिल्प से जुड़ी हस्तनिर्मित वस्तु है। इसे {material} से बनाया गया है। "
        f"कारीगर ने {method} का उपयोग किया है। {details} "
        "हर हस्तनिर्मित वस्तु में थोड़ी भिन्नता हो सकती है।"
    )
    words = [word.lower() for word in craft.replace("-", " ").split() if word.isalpha()]
    tags = list(dict.fromkeys((words + ["handmade", "artisan", "heritage", "india", "craft"])))[:8]
    if any(word in material.lower() for word in ["cotton", "silk", "fabric", "cloth"]):
        care = "Wash gently in cold water. Dry in shade. Avoid scrubbing printed or stitched parts."
    elif any(word in material.lower() for word in ["ceramic", "clay", "pottery", "metal"]):
        care = "Wipe with a soft cloth. Handle carefully to avoid knocks and scratches."
    else:
        care = "Keep dry and out of direct sunlight. Wipe lightly with a soft cloth."
    return _clean_draft({
        "title": f"Handmade {craft} piece"[:160],
        "description": description[:1200],
        "hindi_description": hindi[:1600],
        "heritage_story": (
            f"{craft} is associated with {origin}. "
            "This piece reflects an artisan's handmade approach to the craft."
        )[:600],
        "care_instructions": care,
        "tags": ", ".join(tags)[:255],
        "source": "fallback",
    })


def parse_catalog_response(response):
    """Extract strict JSON from the provider and reject missing or wrong fields."""
    if response.status_code != 200:
        raise ValueError("Provider returned a non-200 response.")
    text = response.json()["content"][0]["text"].strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    data = json.loads(text)
    result = {}
    for key, limit in TEXT_LIMITS.items():
        value = data[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Catalog text is missing or invalid.")
        result[key] = value.strip()[:limit]
    tags = data["tags"]
    if not isinstance(tags, list) or not 5 <= len(tags) <= 8:
        raise ValueError("Catalog tags are missing or invalid.")
    if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        raise ValueError("Catalog tags must be words.")
    result["tags"] = ", ".join(tag.strip().lower()[:30] for tag in tags)[:255]
    result["source"] = "ai"
    return _clean_draft(result)


def generate_catalog_content(craft_name, state, materials, technique, notes, language_hint):
    """Request one AI draft or return the same-shaped offline draft on failure."""
    fallback = fallback_content(craft_name, state, materials, technique, notes, language_hint)
    if not settings.ANTHROPIC_API_KEY:
        logger.info("Catalog AI fallback: no API key is configured.")
        return fallback
    facts = {
        "craft_name": craft_name, "state": state, "materials": materials,
        "technique": technique, "notes": notes, "language_hint": language_hint,
    }
    try:
        response = requests.post(
            API_URL,
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.AI_MODEL,
                "max_tokens": 900,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": json.dumps(facts, ensure_ascii=False)}],
            },
            timeout=20,
        )
        return parse_catalog_response(response)
    except Exception as error:
        # Never log the exception message: providers may echo request headers.
        logger.error("Catalog AI fallback after %s.", type(error).__name__)
        return fallback
