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


def test_ticket_already_with_engineering_is_not_sent_back_to_checklist():
    at = _app()
    at.radio(key="page").set_value(PAGES["check"]).run()
    at.radio(key="src").set_value("A real open ticket").run()
    from rideops.data import load_tickets
    tid = load_tickets().query("status == 'Open - with Engineering'")["ticket_id"].iloc[0]
    at.selectbox[0].set_value(tid).run()
    assert not at.exception
    assert any("Already with engineering" in i.value for i in at.info)
