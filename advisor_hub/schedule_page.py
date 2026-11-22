"""Schedule Builder controls and independent validation results."""

from advisor_hub.academic import DATA, audit, catalog, select_profile


def schedule_results(profile, program, section_file):
    from src.schedule import schedule_builder as builder
    from src.schedule.sections import load_sections

    courses, lists, transfer = catalog()
    term, sections = load_sections(section_file)
    crns = {row["crn"]: row for rows in sections.values() for row in rows}
    args = (profile, program, courses, sections, transfer, lists)
    greedy = builder.greedy_schedule(*args, term=term["term"])
    results = [greedy]
    dependency_warning = ""
    try:
        results.append(builder.build_schedule(*args, term=term["term"]))
    except (ImportError, OSError):
        dependency_warning = "OR-Tools is unavailable. The greedy schedule is still shown."
    checked = [(result, builder.check_schedule(result, profile, program, courses, crns, transfer, lists))
               for result in results]
    return checked, dependency_warning


def show_schedule(st, name, result, check):
    st.subheader(name)
    st.metric("Scheduled credits", f"{result.total_credits:g}")
    st.caption(f"Solver status {result.status} · Priority score {result.score}")
    if result.items:
        st.dataframe([
            {"Course": row["course"], "Title": row["title"], "Section CRN": row["crn"],
             "Credits": row["credits"], "Requirement": row["fills"],
             "Meetings": ", ".join(f"{m['days']} {m['start']}–{m['end']}" for m in row["meetings"])}
            for row in result.items
        ], hide_index=True)
        if check["valid"]:
            st.success("Independent checker passed the stored conflict and prerequisite rules.")
    else:
        st.warning("No courses fit the current degree, section, and preference constraints.")
    for problem in check["problems"]:
        st.error(problem)
    for warning in dict.fromkeys([*check["warnings"], *result.notes]):
        st.warning(warning)


def schedule_page(st, hub):
    from src.schedule.schedule_builder import normalize_profile

    st.header("Schedule Builder")
    st.warning("Synthetic section data for planning practice. Seat counts and meeting times are fictional.")
    profile, program = select_profile(st, "schedule")
    profile = normalize_profile(profile)
    files = {}
    for path in sorted((DATA / "sections").glob("*.json")):
        metadata = audit.load_json(path)
        if metadata.get("synthetic"):
            files[metadata["term"]] = path
    if not files:
        st.warning("No synthetic term datasets are available.")
        return
    term = st.selectbox("Synthetic term dataset", list(files))
    limit = st.number_input("Maximum scheduled credits", min_value=1.0, max_value=30.0,
                            value=profile["max_credits"], step=1.0, key=f"credits_{profile['student_id']}")
    blocks = profile["avoid_times"]
    keep_blocks = st.checkbox("Honor the profile's blocked meeting times", value=True, disabled=not blocks)
    if blocks:
        st.write("Profile time blocks", blocks)
    signature = (profile["student_id"], term, limit, keep_blocks)
    if st.button("Generate schedules", type="primary"):
        with st.spinner("Generating and independently validating schedules…"):
            selected = {**profile, "preferences": {"max_credits": limit, "avoid_times": blocks if keep_blocks else []}}
            st.session_state["schedule_result"] = signature, schedule_results(selected, program, files[term])
    saved = st.session_state.get("schedule_result")
    if not saved or signature != saved[0]:
        return
    results, warning = saved[1]
    if warning:
        st.warning(warning)
    if len(results) == 2:
        greedy, optimized = (pair[0] for pair in results)
        first = {(row["course"], row["crn"]) for row in greedy.items}
        second = {(row["course"], row["crn"]) for row in optimized.items}
        st.write(f"CP-SAT minus greedy: {optimized.total_credits - greedy.total_credits:+g} credits, "
                 f"{optimized.score - greedy.score:+d} priority points.")
        for name, difference in (("Greedy only", first - second), ("CP-SAT only", second - first)):
            st.write(name, ", ".join(f"{code} ({crn})" for code, crn in sorted(difference)) or "None")
    for name, (result, check) in zip(("Greedy baseline", "CP-SAT optimization"), results):
        show_schedule(st, name, result, check)
