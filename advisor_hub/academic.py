"""Read the shared academic datasets using the degree audit's loaders."""

from functools import lru_cache
from pathlib import Path

from src.audit import degree_audit as audit

DATA = Path(__file__).resolve().parents[1] / "data"


@lru_cache(maxsize=1)
def profiles():
    rows = audit.load_json(DATA / "profiles" / "schedule_demo_profiles.json")["profiles"]
    return {row["student_id"]: row for row in rows}


@lru_cache(maxsize=1)
def catalog():
    return (
        audit.load_courses(DATA / "courses.json"),
        audit.load_lists(DATA / "lists.json"),
        audit.load_transfer_map(DATA / "transfer" / "transfer_map.json"),
    )


@lru_cache(maxsize=None)
def curriculum(major):
    return audit.load_curriculum(DATA / "curricula" / f"{major}.json")


def select_profile(st, page):
    records = profiles()
    st.caption("Fictional student profiles from the team's synthetic demonstration dataset.")
    student = st.selectbox("Synthetic student profile", list(records), key=f"{page}_profile")
    profile = records[student]
    program = curriculum(profile["major"])
    st.write(f"Major · {program['program_name']} ({program['catalog_year']})")
    return profile, program
