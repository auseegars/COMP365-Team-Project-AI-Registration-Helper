"""Temporary Advisor Hub records; independent of Streamlit and external services."""
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from advisor_hub.classifier import CATEGORY_KEYWORDS, OTHER, TriageResult, classify_request

CATEGORIES = (*CATEGORY_KEYWORDS, OTHER)
URGENCIES = ("High", "Medium", "Low")
REQUEST_STATUSES = ("Open", "In Progress", "Resolved")
APPOINTMENT_STATUSES = ("Pending", "Reviewed", "Cancelled")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def required_text(value: str, label: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"{label} must be {limit} characters or fewer.")
    return value


@dataclass
class AdvisingRequest:
    id: str
    student: str
    text: str
    triage: TriageResult
    submitted_at: datetime
    token: str
    status: str = "Open"
    demo: bool = False


@dataclass
class AppointmentRequest:
    id: str
    student: str
    reason: str
    preferred_at: datetime
    submitted_at: datetime
    token: str
    status: str = "Pending"
    demo: bool = False


@dataclass
class HubState:
    requests: list[AdvisingRequest] = field(default_factory=list)
    appointments: list[AppointmentRequest] = field(default_factory=list)

    def submit_request(self, student: str, text: str, token: str, *,
                       now: datetime | None = None, demo: bool = False) -> AdvisingRequest:
        student = required_text(student, "Fictional student identifier", 100)
        text = required_text(text, "Request description", 4000)
        token = required_text(token, "Submission token", 100)
        existing = next((r for r in self.requests if r.token == token), None)
        if existing:
            if (existing.student, existing.text) != (student, text):
                raise ValueError("Submission token already belongs to another request.")
            return existing
        record = AdvisingRequest("REQ-" + uuid4().hex, student, text,
                                 classify_request(text), now or utc_now(), token, demo=demo)
        self.requests.append(record)
        return record

    def submit_appointment(self, student: str, reason: str, preferred_at: datetime,
                           token: str, *, now: datetime | None = None,
                           demo: bool = False) -> AppointmentRequest:
        student = required_text(student, "Fictional student identifier", 100)
        reason = required_text(reason, "Appointment reason", 4000)
        token = required_text(token, "Submission token", 100)
        if not isinstance(preferred_at, datetime) or preferred_at.utcoffset() is None:
            raise ValueError("Preferred date and time must include a timezone.")
        existing = next((a for a in self.appointments if a.token == token), None)
        if existing:
            if (existing.student, existing.reason, existing.preferred_at) != (student, reason, preferred_at):
                raise ValueError("Submission token already belongs to another appointment.")
            return existing
        now = now or utc_now()
        if preferred_at <= now:
            raise ValueError("Preferred date and time must be in the future (UTC).")
        record = AppointmentRequest("APT-" + uuid4().hex, student, reason,
                                    preferred_at, now, token, demo=demo)
        self.appointments.append(record)
        return record

    def update_status(self, record_id: str, status: str, *, appointment: bool = False) -> None:
        allowed = APPOINTMENT_STATUSES if appointment else REQUEST_STATUSES
        if status not in allowed:
            raise ValueError("Unsupported status.")
        records = self.appointments if appointment else self.requests
        record = next((r for r in records if r.id == record_id), None)
        if record is None:
            raise ValueError("Record not found.")
        record.status = status

    def metrics(self) -> dict[str, int]:
        return {
            "Total submitted": len(self.requests),
            "Open requests": sum(r.status == "Open" for r in self.requests),
            "High-priority active": sum(r.triage.urgency == "High" and r.status != "Resolved" for r in self.requests),
            "Resolved": sum(r.status == "Resolved" for r in self.requests),
            "Pending appointments": sum(a.status == "Pending" for a in self.appointments),
        }

    def load_demo(self, *, now: datetime | None = None) -> None:
        now = now or utc_now()
        for index, text in enumerate(DEMO_REQUESTS):
            self.submit_request(f"SYN-DEMO-{index + 1:03}", text, f"demo-request-{index}", now=now, demo=True)
        if not any(a.token == "demo-appointment" for a in self.appointments):
            self.submit_appointment("SYN-DEMO-007", "Discuss next semester's academic goals.",
                                    now + timedelta(days=2), "demo-appointment", now=now, demo=True)

    def reset_demo(self) -> None:
        """Explicitly remove demo records only; preserve user-submitted records."""
        self.requests[:] = [r for r in self.requests if not r.demo]
        self.appointments[:] = [a for a in self.appointments if not a.demo]


DEMO_REQUESTS = (
    "I have a registration hold and registration closes tomorrow.",
    "Which courses should I take next semester?",
    "My graduation application is due today.",
    "Can you help me build a four-year plan?",
    "I would like an appointment soon.",
    "I need an appointment to discuss my graduation.",
    "This is urgent. My registration deadline is today.",
)


def filter_requests(records: list[AdvisingRequest], *, category: str = "All",
                    urgency: str = "All", status: str = "All", search: str = "",
                    sort: str = "Priority, oldest first") -> list[AdvisingRequest]:
    query = search.strip().casefold()
    rows = [r for r in records
            if (category == "All" or r.triage.category == category)
            and (urgency == "All" or r.triage.urgency == urgency)
            and (status == "All" or r.status == status)
            and (not query or query in f"{r.id} {r.student} {r.text}".casefold())]
    if sort == "Priority, oldest first":
        return sorted(rows, key=lambda r: (URGENCIES.index(r.triage.urgency), r.submitted_at, r.id))
    if sort == "Newest first":
        return sorted(rows, key=lambda r: (r.submitted_at, r.id), reverse=True)
    if sort == "Oldest first":
        return sorted(rows, key=lambda r: (r.submitted_at, r.id))
    raise ValueError("Unsupported sort order.")


def distribution(records: list[AdvisingRequest], attribute: str) -> dict[str, int]:
    if attribute not in ("category", "urgency"):
        raise ValueError("Unsupported distribution.")
    labels = CATEGORIES if attribute == "category" else URGENCIES
    counts = Counter(getattr(r.triage, attribute) for r in records)
    return {label: counts[label] for label in labels}
