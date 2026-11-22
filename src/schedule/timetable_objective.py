"""Student conflict scoring shared by the department timetabler and its baseline.

Each overlapping section pair contributes the number of simulated students
requesting both courses. Parallel sections can contribute multiple times, so
the score measures timetable pressure rather than unique affected students.
"""

from collections import Counter, defaultdict
from itertools import combinations

from src.audit.degree_audit import norm
from src.schedule.sections import meeting_blocks, sections_overlap


def coenrollment_weights(student_course_loads):
    """Count students requesting each unordered pair of distinct courses."""
    return Counter(
        pair
        for load in student_course_loads
        for pair in combinations(sorted({norm(code) for code in load}), 2)
    )


def course_pair(left, right):
    return tuple(sorted((norm(left["course"]), norm(right["course"]))))


def conflict_cost(left, right, weights):
    """Charge the course-pair weight once if any meetings overlap."""
    pair = course_pair(left, right)
    weight = weights.get(pair, 0)
    return weight if weight and sections_overlap(left, right) else 0


def set_soft_objective(model, choices_by_section, weights):
    """Minimize weighted conflicts plus instructor preference penalties.

    Each section maps to (placement, selected BoolVar) pairs. A placement
    uses the section meeting schema and may have a nonnegative integer
    preference_penalty. The hard-constraint model owns selection, room
    and instructor feasibility, and enforces one placement per section.
    This function sets the model's objective.
    """
    choices = [list(options) for options in choices_by_section.values()]
    terms = [
        option["preference_penalty"] * selected
        for options in choices
        for option, selected in options
        if option.get("preference_penalty", 0)
    ]
    # Room and instructor variants at the same time share one conflict indicator.
    by_time = []
    for options in choices:
        groups = defaultdict(list)
        for option, selected in options:
            groups[tuple(sorted(meeting_blocks(option)))].append((option, selected))
        times = []
        for group in groups.values():
            option, selected = group[0]
            if len(group) > 1:
                selected = model.new_bool_var("meeting_time_selected")
                model.add(selected == sum(var for _, var in group))
            times.append((option, selected))
        by_time.append(times)
    for left, right in combinations(by_time, 2):
        if not left or not right or not weights.get(course_pair(left[0][0], right[0][0])):
            continue
        for first, first_selected in left:
            for second, second_selected in right:
                cost = conflict_cost(first, second, weights)
                if cost:
                    overlap = model.new_bool_var("conflicting_times_selected")
                    model.add_multiplication_equality(overlap, [first_selected, second_selected])
                    terms.append(cost * overlap)
    model.minimize(sum(terms))


def greedy_timetable(placements_by_section, weights, can_place):
    """Place the most constrained sections first, minimizing added soft cost.

    can_place(candidate, assigned) checks the hard rules against the
    current partial timetable. Candidate order breaks ties. Return any
    unassigned section IDs so an incomplete result cannot be scored as
    an improvement over a complete timetable.
    """
    options = {crn: list(rows) for crn, rows in placements_by_section.items()}
    assigned = []
    unassigned = []
    for crn in sorted(options, key=lambda key: (len(options[key]), key)):
        selected = min(
            (row for row in options[crn] if can_place(row, assigned)),
            key=lambda row: row.get("preference_penalty", 0) + sum(
                conflict_cost(row, earlier, weights) for earlier in assigned
            ),
            default=None,
        )
        if selected is None:
            unassigned.append(crn)
        else:
            assigned.append(selected)
    return assigned, unassigned


def conflict_breakdown(sections, weights):
    """Report overlapping section pairs, weighted by simulated student demand."""
    counts = Counter()
    for left, right in combinations(sections, 2):
        cost = conflict_cost(left, right, weights)
        if cost:
            counts[course_pair(left, right)] += cost
    return {
        "weighted_conflicts": sum(counts.values()),
        "by_course_pair": [
            {"courses": list(pair), "weighted_conflicts": cost}
            for pair, cost in sorted(counts.items(), key=lambda row: (-row[1], row[0]))
        ],
    }
