"""Deterministic keyword triage baseline, not a trained machine learning model."""

from dataclasses import dataclass
import re
from typing import Tuple
import unicodedata


OTHER = "Other/Needs Review"

# Match complete words/phrases. Rule order only controls explanation ordering;
# requests matching more than one category are referred for human review.
CATEGORY_KEYWORDS = {
    "Registration Holds": (
        "hold", "holds", "cannot register", "can t register",
        "unable to register", "blocked from registering", "registration block",
    ),
    "Degree Planning": (
        "degree plan", "degree planning", "plan my degree", "degree audit",
        "degree requirements", "academic plan", "four year plan",
        "major requirements", "credits remaining",
    ),
    "Course Selection": (
        "course selection", "choose courses", "choose classes", "which course",
        "which courses", "which classes", "course recommendation",
        "course recommendations", "recommend courses", "elective", "electives",
        "prerequisite", "prerequisites",
    ),
    "Graduation": (
        "graduation", "graduate", "graduating", "commencement", "diploma",
    ),
    "Appointments": (
        "appointment", "appointments", "advising meeting", "advising session",
        "meet with my advisor", "meet with an advisor", "meet with my adviser",
        "meet with an adviser",
    ),
}

HIGH_KEYWORDS = ("urgent", "urgently", "asap", "immediately", "emergency")
MEDIUM_KEYWORDS = (
    "deadline", "deadlines", "soon", "this week", "next week", "hold", "holds",
    "cannot register", "can t register", "unable to register",
    "blocked from registering", "registration block",
)

# A deadline must be linked to a near-term expression. A bare mention of
# "today" (for example, "I read the catalog today") does not imply urgency.
HIGH_PATTERNS = (
    r"\b(?:due|deadline|deadlines|closes?|ends?|expires?)\b"
    r"(?: \w+){0,4} (?:today|tonight|tomorrow)\b",
    r"\b(?:today|tonight|tomorrow)(?: \w+){0,4} "
    r"(?:deadline|deadlines)\b",
    r"\b(?:within|in|next) (?:24|48|twenty four|forty eight) hours?\b",
    r"\b(?:missed (?:the |my )?deadline|past due|overdue)\b",
)
NEGATED_URGENCY = re.compile(
    r"\b(?:not|isn t|is not|is not an|not an|no) "
    r"(?:urgent|urgently|an emergency|emergency)\b"
)


@dataclass(frozen=True)
class TriageResult:
    """Explainable routing suggestion; matched phrases are not confidence scores."""

    category: str
    urgency: str
    matched_categories: Tuple[str, ...]
    matched_keywords: Tuple[str, ...]
    urgency_reasons: Tuple[str, ...]

    @property
    def needs_review(self) -> bool:
        return self.category == OTHER


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", normalized).split())


def _contains(text: str, phrase: str) -> bool:
    return f" {phrase} " in f" {text} "


def _detect_urgency(text: str) -> Tuple[str, Tuple[str, ...]]:
    # Suppress simple negated urgency cues without hiding an actual due date.
    explicit_text = NEGATED_URGENCY.sub(" ", text)
    high_reasons = [word for word in HIGH_KEYWORDS if _contains(explicit_text, word)]
    high_reasons.extend(
        match.group(0)
        for pattern in HIGH_PATTERNS
        for match in re.finditer(pattern, text)
    )
    if high_reasons:
        return "High", tuple(dict.fromkeys(high_reasons))
    medium_reasons = tuple(word for word in MEDIUM_KEYWORDS if _contains(text, word))
    if medium_reasons:
        return "Medium", medium_reasons
    return "Low", ()


def classify_request(text: str) -> TriageResult:
    """Suggest a category and urgency from English keyword rules.

    Blank or unmatched input and multiple matching categories need human review.
    Non-string input raises TypeError. Urgency is evaluated independently from
    category; even an unmatched request can be urgent. No records are persisted.
    """
    if not isinstance(text, str):
        raise TypeError("Advising request must be a string.")
    normalized = _normalize(text)
    categories = []
    keywords = []
    for category, phrases in CATEGORY_KEYWORDS.items():
        matches = [phrase for phrase in phrases if _contains(normalized, phrase)]
        if matches:
            categories.append(category)
            keywords.extend(matches)
    urgency, reasons = _detect_urgency(normalized)
    return TriageResult(
        category=categories[0] if len(categories) == 1 else OTHER,
        urgency=urgency,
        matched_categories=tuple(categories),
        matched_keywords=tuple(keywords),
        urgency_reasons=reasons,
    )
