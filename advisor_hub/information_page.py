"""Information Assistant presentation and session history."""

from urllib.parse import urlsplit

from advisor_hub.information import ask


def information_page(st, hub):
    st.header("Information Assistant")
    st.caption("Ask about registration using the university pages indexed for this prototype. Use fictional details only.")
    history = st.session_state.setdefault("information_history", [])
    with st.form("information_question"):
        question = st.text_input("Registration question", max_chars=500)
        submitted = st.form_submit_button("Ask Information Assistant", type="primary")
    if submitted:
        try:
            with st.spinner("Searching university sources and checking local generation…"):
                result = ask(question)
        except ValueError as error:
            st.error(str(error))
        except OSError:
            st.error("The university source index is unavailable.")
        else:
            history.insert(0, (question.strip(), result))
            del history[10:]
    for index, (question, result) in enumerate(history):
        with st.expander(question, expanded=index == 0):
            if result["answer"]:
                st.subheader("Generated answer")
                st.text(result["answer"])
            else:
                st.info(f"Retrieval only. {result['reason']}")
            st.subheader("Retrieved sources")
            if not result["excerpts"]:
                st.warning("No source excerpts were found for this question.")
            for number, source in enumerate(result["excerpts"], start=1):
                title, url = source["title"], source["source_url"]
                address = urlsplit(url)
                if address.scheme in {"http", "https"} and address.netloc:
                    st.link_button(f"[{number}] {title}", url)
                else:
                    st.write(f"[{number}] {title} · source link unavailable")
                st.caption(f"{result['method']} score {source['score']:.3f}")
                st.text(source["text"])
