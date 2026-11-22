import pytest
from ortools.sat.python import cp_model

from src.schedule.timetable_objective import coenrollment_weights, greedy_timetable, set_soft_objective
from src.schedule.timetable_report import conflict_report


def section(crn, course, start="09:00", end="10:00", penalty=0):
    return {
        "crn": crn,
        "course": course,
        "meetings": [{"days": "MWF", "start": start, "end": end}],
        "preference_penalty": penalty,
    }


def timetable(*sections):
    return {"term": "Synthetic test", "synthetic": True, "sections": list(sections)}


def test_cp_sat_and_greedy_trade_preferences_against_student_conflicts():
    first = section("1", "COMP 163")
    less_preferred_room = {**first, "room": "B", "preference_penalty": 3}
    simultaneous = section("2", "MATH 131")
    later = section("2", "MATH 131", "10:00", "11:00", penalty=1)
    weights = coenrollment_weights([
        ["comp163", "MATH-131", "COMP 163"],
        ["MATH 131", "COMP 163"],
    ])
    assert weights == {("COMP 163", "MATH 131"): 2}
    placements = {"1": [first, less_preferred_room], "2": [simultaneous, later]}
    model = cp_model.CpModel()
    choices = {
        crn: [(row, model.new_bool_var(f"{crn}_{i}")) for i, row in enumerate(rows)]
        for crn, rows in placements.items()
    }
    for options in choices.values():
        model.add_exactly_one(selected for _, selected in options)
    set_soft_objective(model, choices, weights)
    solver = cp_model.CpSolver()
    assert solver.solve(model) == cp_model.OPTIMAL
    assert solver.objective_value == 1
    proposed = [row for options in choices.values() for row, selected in options if solver.value(selected)]
    greedy, unassigned = greedy_timetable(placements, weights, lambda row, assigned: True)
    assert proposed == greedy == [first, later]
    assert not unassigned

    report = conflict_report(timetable(first, simultaneous), timetable(*proposed), weights, timetable(*greedy))
    assert report["reference"]["weighted_conflicts"] == 2
    assert report["reference_synthetic"] is True
    assert report["proposed"]["reduction_percent"] == 100
    assert report["greedy"]["weighted_conflicts"] == 0


def test_greedy_obeys_hard_rule_and_report_rejects_missing_sections():
    first = section("1", "COMP 163")
    second = section("2", "MATH 131")
    assigned, unassigned = greedy_timetable(
        {"1": [first], "2": [second]}, {}, lambda row, assigned: not assigned
    )
    assert unassigned == ["2"]
    reference = timetable(first, second)
    with pytest.raises(ValueError, match="same section IDs"):
        conflict_report(reference, reference, {}, timetable(*assigned))
    assert conflict_report(reference, reference, {})["proposed"]["reduction_percent"] is None
