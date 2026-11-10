# Checkpoint 2 individual demonstration

Record manually with your camera on and your own voice. This is a speaking guide,
not a generated recording. Aim for 60–90 seconds (166 words at 130–150 wpm,
plus brief clicks). Rehearse once; do installation and setup before recording.

## Before recording

1. From the repository root, run:
   `advisor_hub/.venv/Scripts/python.exe -m streamlit run advisor_hub/app.py --browser.gatherUsageStats false`
2. Open the printed local URL in a fresh session. Use only fictional information.
3. Keep the synthetic load button untouched for this short demonstration. Start
   on Overview with zero counts. Keep your camera and microphone ready in your
   own recording software. Do not show private tabs or real academic records.

## Exact click sequence and timing

1. **0–15 sec:** Show Overview while introducing your responsibilities.
2. **15–25 sec:** Click Student Requests. Enter identifier `SYN-VIDEO`; paste
   `I have a registration hold and registration closes tomorrow.` into Advising
   request description. Click Submit request.
3. **25–40 sec:** Show Registration Holds / High, `hold`, `closes tomorrow`,
   the request ID, and Open status. Scroll if needed.
4. **40–55 sec:** Click Advisor Queue. Leave filters on All and sorting on
   Priority, oldest first. The submitted request is selected. Scroll to Request
   status, choose In Progress, and click Save request status. Show the updated
   status. This confirms workflow processing, not resolution of a real hold.
5. **55–65 sec:** Click Overview. Show one submitted request, zero Open, one
   High-priority active, and zero Resolved (the request is In Progress).
6. **65–90 sec:** Explain technical decisions, limitations, and remaining work.
   If time permits, open Appointments to show that it is a request system;
   appointment submission is optional and outside the required short click path.

## Natural presentation script

“My responsibilities are the Advisor Hub, student request classification, urgency
triage, and interface development for Aggies Enroll. This is our COMP365 prototype,
not an official university service.

I kept the keyword classifier and built this Streamlit dashboard around it. I'll
submit a fictional request about a registration hold that closes tomorrow. It
returns Registration Holds with High urgency and explains the matched rules.
These are rule-based suggestions, not model confidence scores.

In the Advisor Queue, the same request appears with its ID and Open status. I'll
change it to In Progress and save. The change survives the rerun, and Overview
updates from the actual records. Appointment requests also support future
preferred times and review statuses; they don't confirm a booking.

Rules gave us an explainable starting point, and Streamlit made an interactive
Python prototype practical. Records stay temporarily in this session. The rules
can miss unfamiliar wording and misunderstand context.

Next are independent labeled evaluation, classifier improvements, shared team
integration, persistent storage, and real appointment integration.”

## Optional longer rehearsal (outside the 60–90 second recording)

- Change In Progress to Resolved and save; check the Overview resolved count.
- Load synthetic demonstration requests twice; counts should not increase on the
  second load. Show category/urgency filters, search, and the ambiguous request.
- On Appointments, submit a fictional future UTC request, show Pending, choose
  Reviewed and save. Show that it leaves the Pending list without being booked.
- Try blank submissions and a past time today in UTC; show validation.
- Reset demonstration records; confirm your separately submitted request remains.
