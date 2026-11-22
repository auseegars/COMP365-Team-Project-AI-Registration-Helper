"""Student-survey loading and peer-rating aggregation for the elective recommender.

Owner: Ryan Kevena.

Holds the interest taxonomy shared by the survey instrument and the recommender, loads the survey
instrument and responses, derives interest tags for a course from its title, and aggregates the
survey's 1-5 elective ratings into peer ratings (overall and restricted to peers who share a
student's interests).  No real student data is used; see data/electives/survey_responses.json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "electives"
INSTRUMENT_FILE = DATA / "survey_instrument.json"
RESPONSES_FILE = DATA / "survey_responses.json"

# Interest taxonomy (tag -> human label).  Kept in step with data/electives/survey_instrument.json.
TAG_LABELS = {
    "ai_ml": "AI & Machine Learning",
    "cybersecurity": "Cybersecurity",
    "data_analytics": "Data Analytics & Data Science",
    "software_engineering": "Software Engineering",
    "systems_programming": "Systems & Low-level Programming",
    "networks": "Networking",
    "computer_graphics": "Computer Graphics",
    "game_design": "Game Design",
    "theory_algorithms": "Theory & Algorithms",
    "hci_ar_vr": "HCI, AR & VR",
    "hardware_embedded": "Hardware & Embedded",
    "simulation_modeling": "Simulation & Modeling",
    "bioinformatics_health": "Health & Bioinformatics",
    "management_business": "Tech Management & Business",
}

# Keywords used to tag a course from its title (and so to expand an interest into search text).
TAG_KEYWORDS = {
    "ai_ml": ["intelligence", "learning", "mining", "analytics", "neural"],
    "cybersecurity": ["security", "privacy", "cyber", "cryptography"],
    "data_analytics": ["data", "analytics", "mining", "statistics"],
    "software_engineering": ["software", "object-oriented", "object oriented", "testing", "development", "design"],
    "systems_programming": ["system", "parallel", "compiler", "operating", "architecture"],
    "networks": ["network", "networking"],
    "computer_graphics": ["graphics", "visual", "rendering"],
    "game_design": ["game"],
    "theory_algorithms": ["algorithm", "compiler", "theory", "science"],
    "hci_ar_vr": ["virtual", "augmented", "reality", "interaction"],
    "hardware_embedded": ["embedded", "hardware", "circuit", "fpga"],
    "simulation_modeling": ["simulation", "modeling", "discrete event", "event"],
    "bioinformatics_health": ["health", "care", "bio", "medical"],
    "management_business": ["management", "business", "information systems", "privacy"],
}


def load_instrument(path=INSTRUMENT_FILE):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_responses(path=RESPONSES_FILE):
    """Return the list of survey responses: {student_id, major, interests[], ratings{code:1-5}, goal}."""
    return json.loads(Path(path).read_text(encoding="utf-8"))["responses"]


def _words(text):
    return [w for w in re.split(r"[^a-z]+", text.lower()) if w]


def course_tags(title):
    """Interest tags implied by a course title (keyword match).  Empty set if none match."""
    t = (title or "").lower()
    tags = set()
    for tag, kws in TAG_KEYWORDS.items():
        if any(kw in t for kw in kws):
            tags.add(tag)
    return tags


def interest_text(interests):
    """Expand a set of interest tags into a bag of search words (label words + keywords)."""
    words = []
    for tag in interests:
        words += _words(TAG_LABELS.get(tag, tag))
        words += [w for kw in TAG_KEYWORDS.get(tag, []) for w in _words(kw)]
    return words


def aggregate(responses, interests=None):
    """Average 1-5 rating per course.

    Returns {code: {"mean": float, "n": int}}.  If `interests` is given, only responses that share at
    least one of those interests are counted (peer ratings for a like-minded student); callers fall
    back to the overall aggregate when a course has no in-interest ratings.
    """
    want = set(interests or [])
    buckets = {}
    for r in responses:
        if want and not (want & set(r.get("interests", []))):
            continue
        for code, score in r.get("ratings", {}).items():
            buckets.setdefault(code, []).append(float(score))
    return {c: {"mean": sum(v) / len(v), "n": len(v)} for c, v in buckets.items()}


def popularity(responses):
    """How many respondents rated each course (used by the most-popular baseline in evaluation)."""
    counts = {}
    for r in responses:
        for code in r.get("ratings", {}):
            counts[code] = counts.get(code, 0) + 1
    return counts
