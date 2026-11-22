"""Show the team's elective rankings and degree-audit eligibility."""

from advisor_hub.academic import catalog, select_profile


def elective_page(st, hub):
    from src.electives.recommend import recommend
    from src.electives.survey import TAG_LABELS, load_responses

    st.header("Elective Recommendations")
    st.warning("Peer ratings come from a synthetic survey. Confirm elective applicability and prerequisites with an advisor.")
    profile, _ = select_profile(st, "elective")
    selections = st.multiselect("Academic interests", list(TAG_LABELS),
                                format_func=TAG_LABELS.__getitem__)
    signature = profile["student_id"], tuple(selections)
    courses, lists, transfer = catalog()
    if st.button("Generate recommendations", type="primary"):
        if not selections:
            st.error("Select at least one academic interest.")
        else:
            with st.spinner("Checking degree eligibility and ranking electives…"):
                results, degree = recommend(profile, selections, courses, lists, load_responses(), transfer)
                st.session_state["elective_result"] = signature, results, degree.warnings
    saved = st.session_state.get("elective_result")
    if not saved or signature != saved[0]:
        return
    _, results, warnings = saved
    for warning in warnings:
        st.warning(warning)
    if not results:
        st.info("The degree audit found no eligible electives for this profile.")
    for rank, row in enumerate(results, start=1):
        st.subheader(f"{rank}. {row['code']} · {row['title']}")
        rating = "No ratings" if row["peer_rating"] is None else f"{row['peer_rating']:.2f}/5 ({row['n_ratings']} ratings)"
        st.write(f"Ranking score {row['score']:.3f} · Interest similarity {row['interest_similarity']:.3f} · Synthetic peer rating {rating}")
        st.write(row["why"])
        st.caption("Eligible for stored degree slots: " + ", ".join(row["slots"]))
        if courses[row["code"]].get("prereq") is None:
            st.warning("Prerequisites are missing from the catalog data and need advisor verification.")
