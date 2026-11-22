"""Exercise the unified routing and component adapters on synthetic fixtures."""

from pathlib import Path
from unittest.mock import patch

import pytest

from advisor_hub import information
from advisor_hub.academic import audit, catalog, curriculum, profiles
from advisor_hub.retrieval_comparison import evaluate_method, term_matches

APP = Path(__file__).resolve().parents[1] / "advisor_hub" / "app.py"


@pytest.fixture
def app():
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(str(APP), default_timeout=45).run()


def go(app, page):
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    assert not app.exception


def test_question_validation_and_retrieval_history(app):
    go(app, "Information Assistant")
    click(app, "Ask Information Assistant")
    assert "3 to 500" in app.error[0].value
    with patch.object(information, "semantic_search", side_effect=FileNotFoundError):
        app.text_input[0].set_value("How do I add or drop a class?")
        click(app, "Ask Information Assistant")
    assert "Retrieval only" in app.info[0].value
    assert app.get("link_button")[0].proto.url.startswith("https://")
    assert "Registration" in app.get("link_button")[0].proto.label
    go(app, "Overview")
    go(app, "Information Assistant")
    assert app.expander[0].label == "How do I add or drop a class?"


@pytest.mark.parametrize("model_present", [True, False])
def test_local_generation_availability(app, model_present):
    excerpts = information.keyword_search("closed course enrollment")
    with (patch.object(information, "semantic_search", return_value=excerpts),
          patch.object(information.requests, "get") as tags,
          patch.object(information.requests, "post") as generate):
        tags.return_value.json.return_value = {"models": [{"name": information.MODEL}] if model_present else []}
        generate.return_value.json.return_value = {"response": "See the closed enrollment policy [1]."}
        go(app, "Information Assistant")
        app.text_input[0].set_value("What happens when a course section is closed?")
        click(app, "Ask Information Assistant")
    if model_present:
        assert app.subheader[0].value == "Generated answer"
        assert any("policy [1]" in row.value for row in app.text)
        assert excerpts[0]["text"] in generate.call_args.kwargs["json"]["prompt"]
    else:
        assert "without llama3.2:3b" in app.info[0].value
        generate.assert_not_called()


def test_ollama_connection_failure_preserves_sources():
    excerpts = information.keyword_search("closed course enrollment")
    with (patch.object(information, "semantic_search", return_value=excerpts),
          patch.object(information.requests, "get", side_effect=information.requests.ConnectionError)):
        result = information.ask("What happens when a course section is closed?")
    assert result["answer"] is None
    assert result["excerpts"] == excerpts
    assert "could not complete generation" in result["reason"]


def test_audit_transfer_profile(app):
    go(app, "Degree Audit")
    app.selectbox[0].set_value("SYN-CS-03").run()
    assert {row.label: row.value for row in app.metric} == {"Credits applied": "26", "Credits remaining": "94"}
    assert any("Mapped course equivalents" in row.value for row in app.markdown)
    assert any("unverified" in row.value for row in app.warning)


def test_schedule_runs_and_independently_checks(app):
    go(app, "Schedule Builder")
    click(app, "Generate schedules")
    assert len(app.metric) == 2
    assert len(app.success) == 2
    assert any("Synthetic section data" in row.value for row in app.warning)
    assert any("CP-SAT minus greedy" in row.value for row in app.markdown)


def test_missing_ortools_preserves_greedy_and_navigation(app):
    go(app, "Schedule Builder")
    with patch("src.schedule.schedule_builder.build_schedule", side_effect=ImportError):
        click(app, "Generate schedules")
    assert len(app.metric) == 1
    assert any("OR-Tools is unavailable" in row.value for row in app.warning)
    go(app, "Advisor Queue")
    assert not app.error


def test_electives_are_from_audit_options(app):
    go(app, "Elective Recommendations")
    app.selectbox[0].set_value("SYN-CS-02").run()
    app.multiselect[0].set_value(["cybersecurity"]).run()
    # Existing dependency-free elective ranking for deterministic widget coverage.
    with patch("src.electives.recommend._Similarity._try_model", return_value=None):
        click(app, "Generate recommendations")
    assert any("COMP 320" in row.value for row in app.subheader)
    assert any("synthetic survey" in row.value for row in app.warning)
    _, rows, _ = app.session_state["elective_result"]
    courses, lists, transfer = catalog()
    degree = audit.audit(profiles()["SYN-CS-02"], curriculum("CS"), courses, transfer, lists)
    assert rows and all(row["slots"] for row in rows)
    assert all(row["code"] in degree.elective_options[slot] for row in rows for slot in row["slots"])


def test_term_diagnostic_is_repeatable_and_uses_whole_terms():
    questions = [{"question": "registration PIN", "expected_terms": ["PIN", "registration"]}]
    first = evaluate_method(information.keyword_search, questions, 3)
    assert first == evaluate_method(information.keyword_search, questions, 3)
    assert first["all_terms_at_k"] == 1
    assert first["mean_term_coverage_at_k"] == 1
    assert not term_matches("PIN", "shopping")
