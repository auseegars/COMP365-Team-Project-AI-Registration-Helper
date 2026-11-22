"""Streamlit widget interactions. Install requirements to run these checks."""
from pathlib import Path
from datetime import time
import unittest
from advisor_hub.management import utc_now
try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None

APP = Path(__file__).resolve().parents[1] / "app.py"


@unittest.skipIf(AppTest is None, "Streamlit not installed; install advisor_hub/requirements.txt")
class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.at = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertFalse(self.at.exception)

    def nav(self, page):
        self.at.sidebar.radio[0].set_value(page).run()
        self.assertFalse(self.at.exception)

    def button(self, label):
        return next(b for b in self.at.button if b.label == label)

    def select(self, label):
        return next(s for s in self.at.selectbox if s.label == label)

    def test_empty_pages(self):
        self.assertEqual([m.value for m in self.at.metric], ["0"] * 5)
        for page in ("Advisor Queue", "Appointments", "Student Requests", "Overview"):
            self.nav(page)

    def test_submit_process_and_rerun_without_duplicates(self):
        self.nav("Student Requests")
        self.at.text_input[0].input("SYN-VIDEO")
        self.at.text_area[0].input("I have a registration hold and registration closes tomorrow.")
        self.button("Submit request").click().run()
        self.assertFalse(self.at.exception)
        hub = self.at.session_state["hub"]
        self.assertEqual(len(hub.requests), 1)
        self.assertEqual(hub.requests[0].triage.urgency, "High")
        self.at.run()
        self.assertEqual(len(hub.requests), 1)
        self.nav("Advisor Queue")
        for status in ("In Progress", "Resolved"):
            self.select("Request status").set_value(status)
            self.button("Save request status").click().run()
            self.assertFalse(self.at.exception)
            self.assertEqual(hub.requests[0].status, status)
        self.nav("Overview")
        self.assertEqual([m.value for m in self.at.metric], ["1", "0", "0", "1", "0"])

    def test_invalid_request_shows_validation(self):
        self.nav("Student Requests")
        self.button("Submit request").click().run()
        self.assertTrue(self.at.error)
        self.assertEqual(self.at.session_state["hub"].requests, [])

    def test_demo_filters_sort_and_reset(self):
        self.button("Load synthetic demonstration requests").click().run()
        self.assertFalse(self.at.exception)
        self.button("Load synthetic demonstration requests").click().run()
        hub = self.at.session_state["hub"]
        self.assertEqual(len(hub.requests), 7)
        self.assertEqual(len(hub.appointments), 1)
        self.nav("Advisor Queue")
        self.assertEqual(self.at.dataframe[0].value.iloc[0]["Urgency"], "High")
        self.select("Category filter").set_value("Course Selection").run()
        self.assertEqual(len(self.at.dataframe[0].value), 1)
        self.select("Urgency filter").set_value("High").run()
        self.assertEqual(len(self.at.dataframe), 0)
        self.select("Urgency filter").set_value("All").run()
        self.select("Category filter").set_value("All").run()
        self.at.text_input[0].input("no such request").run()
        self.assertEqual(len(self.at.dataframe), 0)
        self.at.text_input[0].input("").run()
        self.select("Sort requests").set_value("Newest first").run()
        self.assertFalse(self.at.exception)
        self.button("Reset demonstration records").click().run()
        self.assertEqual(hub.requests, [])
        self.assertEqual(hub.appointments, [])

    def test_appointment_submit_and_update(self):
        self.nav("Appointments")
        self.at.text_input[0].input("SYN-APPT")
        self.at.text_area[0].input("Discuss academic goals")
        self.button("Request appointment review").click().run()
        self.assertFalse(self.at.exception)
        hub = self.at.session_state["hub"]
        self.assertEqual(len(hub.appointments), 1)
        self.assertEqual(hub.appointments[0].status, "Pending")
        self.at.run()
        self.assertEqual(len(hub.appointments), 1)
        self.select("Appointment request status").set_value("Reviewed")
        self.button("Save appointment status").click().run()
        self.assertFalse(self.at.exception)
        self.assertEqual(hub.appointments[0].status, "Reviewed")
        self.assertEqual(len(self.at.dataframe), 0)
        self.nav("Overview")
        self.assertEqual(self.at.metric[4].value, "0")

    def test_invalid_appointment_shows_validation(self):
        self.nav("Appointments")
        self.button("Request appointment review").click().run()
        self.assertTrue(self.at.error)
        self.assertEqual(self.at.session_state["hub"].appointments, [])

    def test_past_appointment_time_rejected_in_ui(self):
        self.nav("Appointments")
        self.at.text_input[0].input("SYN-PAST")
        self.at.text_area[0].input("Discuss goals")
        self.at.date_input[0].set_value(utc_now().date())
        self.at.time_input[0].set_value(time(0, 0))
        self.button("Request appointment review").click().run()
        self.assertFalse(self.at.exception)
        self.assertTrue(any("future" in e.value for e in self.at.error))
        self.assertEqual(self.at.session_state["hub"].appointments, [])

    def test_status_filter_refresh_after_resolving(self):
        self.button("Load synthetic demonstration requests").click().run()
        self.nav("Advisor Queue")
        self.select("Status filter").set_value("Open").run()
        self.select("Request status").set_value("Resolved")
        self.button("Save request status").click().run()
        self.assertFalse(self.at.exception)
        self.assertEqual(len(self.at.dataframe[0].value), 6)
        self.select("Status filter").set_value("Resolved").run()
        self.assertEqual(len(self.at.dataframe[0].value), 1)
        self.assertEqual(self.select("Request status").value, "Resolved")
