"""Walkthrough configuration. Paths are relative to this folder (the walkthrough tools folder)."""
import wt_env  # noqa: F401  (puts the engine on sys.path)
from content import CHAPTERS  # noqa: F401

PROJECT = "my-project"            # deck id: ~/learning/decks/<PROJECT>.json
LANG = "zh-TW"                    # UI language of the page and the review hub
REPO = "../.."                    # project root
OUT = "docs/walkthrough.html"     # output page, relative to the project root
CAPTURES = ["cap_example.py"]     # capture scripts, in run order

TITLE = "專案名稱：講解的主題"
KICKER = "程式逐行講解"
LEAD = "<p>依序講解這幾支檔案。每一步上面是程式，按「下一段」會標出正在講的那幾行，下面是白話說明，以及<strong>實際執行到那裡時</strong>資料的樣子。</p>"
FLOW = [  # optional diagram rows in the hero: how the files connect
    # {"num": "1", "label": "main.py", "href": "#c1", "in": "input.csv", "out": "result.json"},
]
CHARTS = {}  # optional, see references/content.md


def ENV(O):
    """One line about how the evidence was produced (versions, data size). O = all captured data."""
    return ""
