"""UI smoke tests: every page renders, and 'Try this example' works end to end."""
from streamlit.testing.v1 import AppTest

from ui.config import PAGES


def _app() -> AppTest:
    return AppTest.from_file("../app.py", default_timeout=90).run()  # path is relative to this file


def test_every_page_renders_without_errors():
    at = _app()
    for label in PAGES.values():
        at.radio(key="page").set_value(label).run()
        assert not at.exception, label


def test_try_example_opens_check_page_and_reaches_escalation_note():
    at = _app()
    next(b for b in at.button if b.label.startswith("▶️")).click().run()
    assert at.session_state["page"] == PAGES["check"]  # button switched page
    for cb in at.checkbox:
        cb.check()
    for ti in at.text_input:
        if "|inf|" in (ti.key or ""):
            ti.input("x")
    at.run()
    assert not at.exception
    assert any("Engineering history" in c.value for c in at.code)  # escalation note shown
