"""Aggies Enroll Advisor Hub. Run with Streamlit from the repository root."""
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
import sys
from uuid import uuid4

# Streamlit executes this file as a script and may omit the repository root.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from advisor_hub.management import (
    APPOINTMENT_STATUSES, CATEGORIES, REQUEST_STATUSES, URGENCIES,
    HubState, distribution, filter_requests, utc_now,
)


def request_table(st, rows):
    st.dataframe([{
        "Request ID": r.id, "Student identifier": r.student,
        "Summary": r.text[:100], "Category": r.triage.category,
        "Urgency": r.triage.urgency, "Submitted (UTC)": r.submitted_at,
        "Status": r.status, "Synthetic demo": r.demo,
    } for r in rows], hide_index=True, width="stretch")


def request_detail(st, record):
    result = record.triage
    {"High": st.error, "Medium": st.warning, "Low": st.info}[result.urgency](
        f"{result.urgency} urgency · {result.category}")
    st.write("Request ID:", record.id)
    st.write("Predicted category (rule-based):", result.category)
    st.write("Assigned urgency:", result.urgency)
    st.write("Student identifier:", record.student)
    st.write("Description:", record.text)
    st.write("Current status:", record.status)
    st.write("Submitted (UTC):", record.submitted_at.isoformat())
    st.write("Matched category rules:", ", ".join(result.matched_categories) or "None")
    st.write("Matched keywords:", ", ".join(result.matched_keywords) or "None")
    st.write("Urgency explanation:", ", ".join(result.urgency_reasons) or "No urgency rule matched; risk has not been verified.")
    st.write("Human review recommended:", "Yes" if result.needs_review else "No — advisor verification still required")
    if record.demo:
        st.caption("Fictional synthetic demonstration record")


def overview(st, hub):
    st.header("Advising at a glance")
    for column, (label, value) in zip(st.columns(5), hub.metrics().items()):
        column.metric(label, value)
    st.caption("Open counts only Open status. High-priority active includes Open and In Progress.")
    if not hub.requests:
        st.info("No requests yet. Submit a fictional request or load the optional demonstration records.")
        return
    st.subheader("Recent requests")
    request_table(st, filter_requests(hub.requests, sort="Newest first")[:5])
    left, right = st.columns(2)
    with left:
        st.subheader("Priority breakdown")
        st.bar_chart(distribution(hub.requests, "urgency"), color="#004684")
    with right:
        st.subheader("Request categories")
        st.bar_chart(distribution(hub.requests, "category"), color="#004684")


def student_requests(st, hub):
    st.header("Submit an advising request")
    st.caption("Use fictional identifiers only. Rules suggest routing and urgency; an advisor must verify them.")
    with st.form("student_request", clear_on_submit=True):
        student = st.text_input("Fictional student identifier", max_chars=100)
        description = st.text_area("Advising request description", max_chars=4000, height=150)
        submitted = st.form_submit_button("Submit request", type="primary")
    if submitted:
        try:
            record = hub.submit_request(student, description, st.session_state.request_token)
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state.last_request = record.id
            st.session_state.request_token = uuid4().hex
            st.success("Request added to the advisor queue.")
    record = next((r for r in hub.requests if r.id == st.session_state.get("last_request")), None)
    if record:
        st.subheader("Latest submission · rule-based triage")
        request_detail(st, record)


def advisor_queue(st, hub):
    st.header("Advisor Queue")
    st.caption("Prototype advisor workspace — no authentication or role-based access is implemented.")
    cols = st.columns(3)
    category = cols[0].selectbox("Category filter", ("All", *CATEGORIES))
    urgency = cols[1].selectbox("Urgency filter", ("All", *URGENCIES))
    status = cols[2].selectbox("Status filter", ("All", *REQUEST_STATUSES))
    search = st.text_input("Search request text, student identifier, or request ID")
    sort = st.selectbox("Sort requests", ("Priority, oldest first", "Newest first", "Oldest first"))
    rows = filter_requests(hub.requests, category=category, urgency=urgency, status=status, search=search, sort=sort)
    if not rows:
        st.info("No requests match these filters.")
        return
    high = sum(r.triage.urgency == "High" for r in rows)
    if high:
        st.error(f"{high} High urgency request(s) in this view. Check active deadlines first.")
    request_table(st, rows)
    selected = st.selectbox("View full request", [r.id for r in rows],
                            format_func=lambda key: next(f"{r.student} · {r.triage.urgency} · {r.id}" for r in rows if r.id == key))
    record = next(r for r in rows if r.id == selected)
    with st.container(border=True):
        request_detail(st, record)
        with st.form(f"request_status_{record.id}_{record.status}"):
            new_status = st.selectbox("Request status", REQUEST_STATUSES, index=REQUEST_STATUSES.index(record.status))
            save = st.form_submit_button("Save request status")
        if save:
            hub.update_status(record.id, new_status)
            st.rerun()


def appointments(st, hub):
    st.header("Appointment requests")
    st.info("Submitting a preferred time requests advisor review. This does not book or confirm an appointment.")
    st.caption("All preferred dates and times are in UTC. No calendar connection or emails.")
    with st.form("appointment_request", clear_on_submit=True):
        student = st.text_input("Fictional student identifier", max_chars=100)
        reason = st.text_area("Appointment reason", max_chars=4000)
        left, right = st.columns(2)
        date = left.date_input("Preferred date (UTC)", value=utc_now().date() + timedelta(days=1), min_value=utc_now().date())
        preferred_time = right.time_input("Preferred time (UTC)", value=time(14, 0))
        submit = st.form_submit_button("Request appointment review", type="primary")
    if submit:
        try:
            record = hub.submit_appointment(student, reason, datetime.combine(date, preferred_time, tzinfo=timezone.utc), st.session_state.appointment_token)
        except (ValueError, TypeError) as error:
            st.error(str(error))
        else:
            st.session_state.appointment_token = uuid4().hex
            st.session_state.appointment_notice = f"{record.id} is Pending. An advisor has not confirmed this time."
            st.rerun()
    notice = st.session_state.pop("appointment_notice", None)
    if notice:
        st.success(notice)
    st.subheader("Pending requests")
    pending = [a for a in hub.appointments if a.status == "Pending"]
    if pending:
        st.dataframe([{"Appointment ID": a.id, "Student": a.student, "Reason": a.reason,
                       "Preferred (UTC)": a.preferred_at, "Status": a.status, "Synthetic demo": a.demo}
                      for a in pending], hide_index=True, width="stretch")
    else:
        st.info("No pending appointment requests.")
    if hub.appointments:
        st.subheader("Manage appointment requests")
        selected = st.selectbox("Appointment request", [a.id for a in hub.appointments],
                                format_func=lambda key: next(f"{a.student} · {a.status} · {a.id}" for a in hub.appointments if a.id == key))
        record = next(a for a in hub.appointments if a.id == selected)
        st.write("Reason:", record.reason)
        st.write("Preferred (UTC):", record.preferred_at.isoformat())
        st.write("Submitted (UTC):", record.submitted_at.isoformat())
        st.write("Current status:", record.status)
        with st.form(f"appointment_status_{record.id}_{record.status}"):
            status = st.selectbox("Appointment request status", APPOINTMENT_STATUSES, index=APPOINTMENT_STATUSES.index(record.status))
            save = st.form_submit_button("Save appointment status")
        if save:
            hub.update_status(record.id, status, appointment=True)
            st.rerun()


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Aggies Enroll | Advisor Hub", page_icon="🎓", layout="wide",
                       initial_sidebar_state="expanded")
    # Small accents; layout and widgets use Streamlit's native components.
    st.markdown("<style>h1,h2,h3{color:#004684}h1{border-bottom:4px solid #d4a500;padding-bottom:.5rem}"
                "@media(prefers-color-scheme:dark){h1,h2,h3{color:#8fc8ff}}</style>", unsafe_allow_html=True)
    st.session_state.setdefault("hub", HubState())
    st.session_state.setdefault("request_token", uuid4().hex)
    st.session_state.setdefault("appointment_token", uuid4().hex)
    hub = st.session_state.hub
    with st.sidebar:
        st.title("Aggies Enroll")
        st.caption("ADVISOR HUB · COMP365")
        page = st.radio("Navigation", ("Overview", "Student Requests", "Advisor Queue", "Appointments"))
        st.divider()
        st.subheader("Demonstration tools")
        st.caption("Optional fictional records. Repeated loads do not add duplicates.")
        if st.button("Load synthetic demonstration requests"):
            hub.load_demo()
        st.caption("Reset removes only synthetic demo records, preserving your submitted fictional requests.")
        if st.button("Reset demonstration records"):
            hub.reset_demo()
        if any(r.demo for r in hub.requests) or any(a.demo for a in hub.appointments):
            st.warning("Synthetic demonstration records are loaded.")
        st.divider()
        st.caption("Temporary session storage. Closing or resetting the session may remove all records. Use no real student or protected academic information.")
    st.title("Advisor Hub")
    st.caption("Aggies Enroll · Student project prototype · Not an official NC A&T university service")
    {"Overview": overview, "Student Requests": student_requests,
     "Advisor Queue": advisor_queue, "Appointments": appointments}[page](st, hub)


if __name__ == "__main__":
    main()
