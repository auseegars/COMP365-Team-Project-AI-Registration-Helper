"""Request lifecycle tests, using only fictional records."""
from datetime import datetime, timedelta, timezone
import unittest
from advisor_hub.classifier import classify_request
from advisor_hub.management import HubState, distribution, filter_requests

NOW = datetime(2026, 11, 10, 16, tzinfo=timezone.utc)


class ManagementTests(unittest.TestCase):
    def setUp(self):
        self.hub = HubState()

    def request(self, text="Which courses should I take?", token="one", **kwargs):
        return self.hub.submit_request("SYN-TEST", text, token, now=NOW, **kwargs)

    def appointment(self, token="appt", **kwargs):
        return self.hub.submit_appointment("SYN-TEST", "Discuss goals", NOW + timedelta(days=1), token, now=NOW, **kwargs)

    def test_empty_state(self):
        self.assertEqual(list(self.hub.metrics().values()), [0] * 5)
        self.assertEqual(filter_requests([]), [])
        self.assertFalse(any(distribution([], "category").values()))

    def test_classification_integration_and_unique_ids(self):
        text = "I have a hold and registration closes tomorrow."
        first = self.request(text)
        second = self.request(text, token="two")
        self.assertEqual(first.triage, classify_request(text))
        self.assertEqual(first.status, "Open")
        self.assertEqual(first.submitted_at, NOW)
        self.assertNotEqual(first.id, second.id)
        self.assertTrue(first.id.startswith("REQ-"))

    def test_request_replay_and_conflicting_token(self):
        first = self.request()
        self.assertIs(first, self.request())
        with self.assertRaises(ValueError):
            self.request("graduation")
        self.assertEqual(len(self.hub.requests), 1)

    def test_request_invalid_inputs_are_atomic(self):
        for student, text, token in [("", "help", "a"), (None, "help", "a"), ("SYN", " \n", "a"),
                                     ("SYN", 42, "a"), ("SYN", "help", ""), ("S" * 101, "help", "a"),
                                     ("SYN", "a" * 4001, "a")]:
            with self.subTest(student=student):
                with self.assertRaises(ValueError):
                    self.hub.submit_request(student, text, token)
        self.assertEqual(self.hub.requests, [])

    def test_status_transitions_and_metrics(self):
        r = self.request("Urgent hold")
        for status in ("In Progress", "Resolved", "Open"):
            self.hub.update_status(r.id, status)
            self.assertEqual(r.status, status)
            self.assertEqual(self.hub.metrics()["High-priority active"], int(status != "Resolved"))
            self.assertEqual(self.hub.metrics()["Resolved"], int(status == "Resolved"))
        self.assertEqual(len(self.hub.requests), 1)

    def test_invalid_status_and_id(self):
        r = self.request()
        for key, status in [(r.id, "Deleted"), ("missing", "Open")]:
            with self.assertRaises(ValueError):
                self.hub.update_status(key, status)
        self.assertEqual(r.status, "Open")

    def test_combined_filters_and_search(self):
        r = self.request("Urgent hold")
        self.request(token="two")
        self.assertEqual(filter_requests(self.hub.requests, category="Registration Holds", urgency="High", status="Open", search="SYN-test"), [r])
        self.assertEqual(filter_requests(self.hub.requests, search="URGENT"), [r])
        self.assertEqual(filter_requests(self.hub.requests, search=r.id), [r])
        self.assertEqual(filter_requests(self.hub.requests, status="Resolved"), [])

    def test_sort_priority_and_time_without_mutation(self):
        low = self.request()
        high_new = self.hub.submit_request("SYN", "Urgent hold", "highnew", now=NOW + timedelta(minutes=1))
        high_old = self.request("Urgent graduation", "highold")
        medium = self.request("hold", "medium")
        self.assertEqual(filter_requests(self.hub.requests), [high_old, high_new, medium, low])
        self.assertEqual(filter_requests(self.hub.requests, sort="Newest first")[0], high_new)
        self.assertEqual(filter_requests(self.hub.requests, sort="Oldest first")[-1], high_new)
        self.assertEqual(self.hub.requests, [low, high_new, high_old, medium])
        with self.assertRaises(ValueError):
            filter_requests([], sort="unknown")

    def test_demo_idempotence_status_and_reset_preserve_submissions(self):
        own = self.request()
        own_appt = self.appointment()
        self.hub.load_demo(now=NOW)
        demo = next(r for r in self.hub.requests if r.demo)
        self.hub.update_status(demo.id, "Resolved")
        ids = [r.id for r in self.hub.requests]
        self.hub.load_demo(now=NOW + timedelta(days=3))
        self.assertEqual([r.id for r in self.hub.requests], ids)
        self.assertEqual(demo.status, "Resolved")
        self.assertEqual(len(self.hub.appointments), 2)
        self.hub.reset_demo()
        self.assertEqual(self.hub.requests, [own])
        self.assertEqual(self.hub.appointments, [own_appt])
        self.hub.load_demo(now=NOW)
        self.assertEqual(len(self.hub.requests), 8)

    def test_appointment_replay_unique_and_separate(self):
        a = self.appointment()
        self.assertIs(a, self.appointment())
        b = self.appointment("two")
        self.assertNotEqual(a.id, b.id)
        self.assertEqual(a.status, "Pending")
        self.assertEqual(self.hub.requests, [])
        with self.assertRaises(ValueError):
            self.hub.submit_appointment("SYN", "Different", a.preferred_at, a.token, now=NOW)

    def test_appointment_validation(self):
        for preferred in (NOW, NOW - timedelta(seconds=1), NOW.replace(tzinfo=None), "tomorrow", None):
            with self.subTest(preferred=preferred):
                with self.assertRaises(ValueError):
                    self.hub.submit_appointment("SYN", "Goals", preferred, "bad", now=NOW)
        for student, reason in [("", "goals"), ("SYN", " "), ("SYN", "x" * 4001)]:
            with self.assertRaises(ValueError):
                self.hub.submit_appointment(student, reason, NOW + timedelta(days=1), "bad", now=NOW)
        self.assertEqual(self.hub.appointments, [])

    def test_appointment_status_and_pending_metric(self):
        a = self.appointment()
        self.assertEqual(self.hub.metrics()["Pending appointments"], 1)
        for status in ("Reviewed", "Cancelled", "Pending"):
            self.hub.update_status(a.id, status, appointment=True)
            self.assertEqual(a.status, status)
            self.assertEqual(self.hub.metrics()["Pending appointments"], int(status == "Pending"))
        with self.assertRaises(ValueError):
            self.hub.update_status(a.id, "Confirmed", appointment=True)

    def test_distributions(self):
        self.request("hold")
        self.request("Urgent hold", "two")
        self.assertEqual(distribution(self.hub.requests, "category")["Registration Holds"], 2)
        self.assertEqual(distribution(self.hub.requests, "urgency")["High"], 1)
        with self.assertRaises(ValueError):
            distribution([], "status")
