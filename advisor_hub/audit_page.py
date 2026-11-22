"""Present the existing degree audit and its data gaps."""

from advisor_hub.academic import audit, catalog, select_profile


def degree_audit_page(st, hub):
    st.header("Degree Audit")
    profile, program = select_profile(st, "audit")
    courses, lists, transfer = catalog()
    result = audit.audit(profile, program, courses, transfer, lists)
    applied, remaining = st.columns(2)
    applied.metric("Credits applied", f"{result.credits_applied:g}")
    remaining.metric("Credits remaining", f"{result.credits_remaining:g}")
    st.caption("Requirements reflect the project catalog snapshot. Verify them with an advisor before registration.")
    with st.expander(f"Satisfied requirements ({len(result.satisfied)})"):
        st.write(", ".join(result.satisfied) or "None in this profile.")
    with st.expander(f"Remaining requirements ({len(result.remaining)})", expanded=True):
        if result.remaining:
            st.dataframe([
                {"Requirement": row["id"], "Type": row["type"],
                 "Courses or category": row.get("code") or ", ".join(row.get("options", [])) or row.get("category"),
                 "Elective credits missing": row.get("credits_missing")}
                for row in result.remaining
            ], hide_index=True)
        else:
            st.write("All stored requirements are satisfied.")
    with st.expander("Eligible courses"):
        options = list(dict.fromkeys([*result.eligible_now, *(
            code for codes in result.elective_options.values() for code in codes
        )]))
        if options:
            st.dataframe([
                {"Course": code, "Title": courses[code]["title"],
                 "Prerequisites": "Unverified" if courses[code].get("prereq") is None else "Stored rules satisfied"}
                for code in options
            ], hide_index=True)
        else:
            st.write("No eligible courses returned by the audit.")
    with st.expander("Transfer credit"):
        if profile.get("transfer"):
            st.dataframe(profile["transfer"], hide_index=True)
            equivalents, generic, categories, unmatched = audit.apply_transfer_credit(profile, transfer)
            st.write("Mapped course equivalents", ", ".join(sorted(equivalents)) or "None")
            st.write(f"Mapped generic elective credits: {generic:g}")
            st.write("Mapped category credits", categories or "None")
            if unmatched:
                st.warning("These entries could not be matched by the stored equivalencies.")
                st.dataframe(unmatched, hide_index=True)
        else:
            st.write("This profile has no transfer entries.")
    with st.expander("Prerequisite warnings and data limitations", expanded=True):
        st.warning("Missing prerequisite records are unverified. Stored rules may omit grades, permissions, or standing requirements.")
        if result.unverified_prereqs:
            st.write("Required courses with missing prerequisite records", ", ".join(result.unverified_prereqs))
        for warning in result.warnings:
            st.warning(warning)
