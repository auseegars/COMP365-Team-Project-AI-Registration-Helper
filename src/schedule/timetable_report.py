"""Compare department timetables on identical sections and student demand."""

import argparse
import json

from src.audit.degree_audit import load_json, norm
from src.schedule.timetable_objective import coenrollment_weights, conflict_breakdown


def _section_ids(timetable):
    sections = timetable["sections"]
    ids = {section["crn"]: norm(section["course"]) for section in sections}
    if len(ids) != len(sections):
        raise ValueError("A timetable contains duplicate section IDs.")
    return ids


def conflict_report(reference, proposed, weights, greedy=None):
    """Score the same section inventory against the same student cohort."""
    ids = _section_ids(reference)
    baseline = conflict_breakdown(reference["sections"], weights)
    report = {
        "reference_term": reference["term"],
        "reference_synthetic": reference.get("synthetic"),
        "section_count": len(ids),
        "reference": baseline,
    }
    for label, timetable in (("proposed", proposed), ("greedy", greedy)):
        if timetable is None:
            continue
        if _section_ids(timetable) != ids:
            raise ValueError(f"The {label} timetable must contain the same section IDs and courses as the reference.")
        score = conflict_breakdown(timetable["sections"], weights)
        original = baseline["weighted_conflicts"]
        score["reduction_percent"] = (
            100 * (original - score["weighted_conflicts"]) / original if original else None
        )
        report[label] = score
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", help="Published or synthetic reference timetable JSON")
    parser.add_argument("proposed", help="Proposed timetable JSON")
    parser.add_argument("student_loads", help="JSON array of course-code arrays, one array per simulated student")
    parser.add_argument("--greedy", help="Completed greedy timetable JSON")
    args = parser.parse_args()
    try:
        report = conflict_report(
            load_json(args.reference),
            load_json(args.proposed),
            coenrollment_weights(load_json(args.student_loads)),
            load_json(args.greedy) if args.greedy else None,
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
