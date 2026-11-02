import wt_env  # noqa: F401
from content import CHAPTERS  # noqa: F401

PROJECT = "demo"
LANG = "en"
REPO = "../.."
OUT = "docs/walkthrough.html"
CAPTURES = ["cap_greet.py"]
TITLE = "Demo walkthrough"
KICKER = "Test"
LEAD = "<p>Engine test.</p>"
FLOW = [{"num": "1", "label": "src/greet.py", "href": "#c1", "out": "greetings"}]


def ENV(O):
    return f"Captured with {O['g_python']}."
