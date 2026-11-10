"""Reproduce real classifier outputs and verification evidence from the repo root."""
from contextlib import redirect_stderr
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
import io
import json
from pathlib import Path
import platform
import socket
import subprocess
import sys
import time
import unittest
from urllib.error import URLError
from urllib.request import urlopen

from advisor_hub.classifier import classify_request
from advisor_hub.evaluation import evaluate_requests

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "advisor_hub"
OUTPUT = PACKAGE / "checkpoint_evidence"
EXAMPLES = (
    ("A", "I have a registration hold and registration closes tomorrow."),
    ("B", "Which courses should I take next semester?"),
    ("C", "I need an appointment to discuss my graduation."),
    ("D", "This is urgent. My registration deadline is today."),
)
EDGE_CASES = (
    ("Ambiguous wording", "Can someone help me?", "No specific intent keywords; review is needed."),
    ("Multiple categories", "I have a registration hold and need help choosing electives.", "The baseline refers multiple categories for review rather than breaking ties."),
    ("Unrecognized question", "Where is the campus library?", "Out-of-scope questions have no category rule."),
    ("Urgent without category", "Urgent: my student portal is broken!", "Urgency is detected independently from routing."),
    ("Incidental date", "I read the catalog today.", "A time mention alone should not establish a deadline."),
    ("Simple negation", "This is not urgent; I need an appointment.", "Supported simple negation suppresses the explicit cue."),
    ("Empty input", "", "The classifier accepts blank strings for review; the submission form rejects blanks."),
    ("Punctuation and capitalization", "  WHICH---COURSES should I take???  ", "Normalization collapses punctuation and case."),
    ("Resolved hold context", "I no longer have a hold.", "The broad hold rule ignores resolved context and can over-triage."),
    ("Complex urgency negation", "I do not need help urgently.", "Negation outside the simple patterns can cause a false High suggestion."),
    ("Absolute deadline", "My graduation application is due November 11, 2026.", "Absolute calendar dates are not interpreted; a real imminent deadline can be missed."),
    ("Unseen synonym", "The system won't let me enroll.", "Missing synonyms can hide a registration problem and its urgency."),
    ("Negation plus real deadline", "Not urgent, but my graduation application is due today.", "A supported near deadline remains High despite negated explicit urgency."),
)


def prediction(case_id: str, text: str) -> dict:
    result = classify_request(text)
    return {"id": case_id, "input": text, **asdict(result), "needs_review": result.needs_review}


def build_reports() -> dict[str, dict]:
    fixture_path = PACKAGE / "sample_data" / "synthetic_requests.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8-sig"))
    if fixture.get("synthetic") is not True or len(fixture["requests"]) != 18:
        raise ValueError("Expected the preserved 18 synthetic regression fixtures.")
    return {
        "examples.json": {"synthetic": True, "method": "Executed classify_request; no manual result overrides",
                          "examples": [prediction(key, text) for key, text in EXAMPLES]},
        "error_analysis.json": {"synthetic": True, "cases": [
            {**prediction(f"EDGE-{i:02}", text), "case": label, "interpretation": note}
            for i, (label, text, note) in enumerate(EDGE_CASES, 1)]},
        "fixture_report.json": {
            "dataset": "18 synthetic regression fixtures used during baseline development",
            "synthetic": True, "held_out": False,
            "interpretation": "Fixture agreement only; not held-out accuracy or evidence that targets are met.",
            "fixture_sha256": sha256(fixture_path.read_bytes()).hexdigest(),
            **evaluate_requests(fixture["requests"])},
    }


def command(args: list[str]) -> dict:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return {"command": args, "exit_code": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def write_json(name: str, content: dict) -> None:
    (OUTPUT / name).write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def probe_server() -> dict:
    """Probe a separate local server, then stop only that child process."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    args = [sys.executable, "-m", "streamlit", "run", "advisor_hub/app.py",
            "--server.headless", "true", "--server.address", "127.0.0.1",
            "--server.port", str(port), "--browser.gatherUsageStats", "false"]
    process = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    status, body = None, ""
    try:
        deadline = time.monotonic() + 20
        while process.poll() is None and time.monotonic() < deadline:
            try:
                with urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
                    status, body = response.status, response.read().decode("utf-8")
                break
            except (URLError, TimeoutError, OSError):
                time.sleep(0.2)
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            output, _ = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate(timeout=5)
    return {"command": args, "health_status": status, "health_body": body,
            "server_output": output, "passed": status == 200 and body.strip() == "ok",
            "scope": "Startup and health only; widget behavior is covered separately by AppTest."}


def main() -> int:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Use Python 3.12 to reproduce checkpoint verification.")
    OUTPUT.mkdir(exist_ok=True)
    reports = build_reports()
    for name, report in reports.items():
        write_json(name, report)
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(PACKAGE / "tests"))
    with redirect_stderr(log):
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    (OUTPUT / "test_results.txt").write_text(log.getvalue(), encoding="utf-8")
    checks = [command([sys.executable, "-m", "pip", "check"]),
              command([sys.executable, "-m", "compileall", "-q", "advisor_hub/app.py",
                       "advisor_hub/management.py", "advisor_hub/classifier.py", "advisor_hub/evaluation.py",
                       "advisor_hub/generate_evidence.py", "advisor_hub/tests"]),
              command(["git", "diff", "--check"])]
    startup = probe_server()
    write_json("startup_probe.json", startup)
    environment = command([sys.executable, "-m", "pip", "freeze"])
    (OUTPUT / "environment.txt").write_text(
        f"Python {platform.python_version()}\n\n" + environment["stdout"] + "\n", encoding="utf-8")
    stage3 = command(["git", "log", "-1", "--format=%H", "--fixed-strings", "--grep=Build functional Streamlit advisor dashboard"])
    branch = command(["git", "branch", "--show-current"])
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "streamlit": version("streamlit"),
        "branch": branch["stdout"], "stage3_commit": stage3["stdout"],
        "stage4_commit": "The commit containing this evidence; resolve with git log -1 -- advisor_hub/checkpoint_evidence/verification.json",
        "tests": {"run": result.testsRun, "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped) - len(result.expectedFailures),
                  "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
                  "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses)},
        "checks": checks,
        "startup_probe_passed": startup["passed"],
        "preserved_sources_sha256": {str(path.relative_to(ROOT)).replace('\\', '/'): sha256(path.read_bytes()).hexdigest()
                                     for path in (PACKAGE / "classifier.py", PACKAGE / "sample_data" / "synthetic_requests.json")},
        "verification_scope": "Unit tests and eight Streamlit AppTest widget workflows. Startup/HTTP health independently checked during Stage 3.",
        "manual_verification": "Browser visual/responsive/keyboard checks and screenshots remain manual. Computer Use stopped because it could not verify Chrome's URL. No screenshots or video fabricated.",
    }
    write_json("verification.json", summary)
    # Human-readable table is rendered from exactly the same executed results.
    lines = ["# Executed synthetic classifier cases", "", "Generated by `python -m advisor_hub.generate_evidence`.", "",
             "These are observed rule outputs, not independent evaluation labels.", "",
             "| Case | Input | Category | Urgency | Keywords | Urgency reasons | Review |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    rows = reports["examples.json"]["examples"] + reports["error_analysis.json"]["cases"]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in (
            row.get("case", row["id"]), row["input"] or "(empty)", row["category"], row["urgency"],
            ", ".join(row["matched_keywords"]) or "None", ", ".join(row["urgency_reasons"]) or "None", row["needs_review"])) + " |")
    lines += ["", "## Error interpretation", ""]
    lines += [f"- **{row['case']}:** {row['interpretation']}" for row in reports["error_analysis.json"]["cases"]]
    (OUTPUT / "executed_cases.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"tests": summary["tests"], "checks_passed": all(c["exit_code"] == 0 for c in checks),
                      "evidence_directory": str(OUTPUT)}, indent=2))
    return 0 if (result.wasSuccessful() and not result.skipped and startup["passed"]
                 and environment["exit_code"] == 0 and all(c["exit_code"] == 0 for c in checks)
                 and branch["stdout"] == "feature/advisor-hub" and stage3["stdout"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
