"""Review hub tests.

- Scheduling and answer checking: the pure functions between `core:begin` and `core:end` in hub.html, run with Node.
- The answering flow: the generated hub in a headless Chromium (skipped when no browser is found).
"""
import json
import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB = os.path.join(ROOT, "skills", "walkthrough", "engine", "wt", "templates", "hub.html")

pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="needs node")


def core(expr: str):
    """Evaluate a JavaScript expression against the hub's core functions; return its JSON value."""
    with open(HUB, encoding="utf-8") as f:
        page = f.read()
    start, end = page.find("/* core:begin"), page.find("/* core:end */")
    assert start != -1 and end != -1, "hub.html has no core:begin / core:end block"
    js = page[start:end] + f"\nconsole.log(JSON.stringify({expr}));"
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=False)
    assert out.returncode == 0, next((ln for ln in out.stderr.splitlines() if "Error" in ln), out.stderr)
    return json.loads(out.stdout)


def test_new_card_answered_right_goes_to_box_2_for_three_days():
    assert core("nextState(undefined, 'good', '2026-01-30')") == {"b": 2, "r": 1, "l": 0, "d": "2026-02-02", "s": "2026-01-30"}


def test_answers_differing_only_in_quotes_or_spaces_are_accepted():
    card = "{answer: 'how=\"left\"', also: []}"
    assert core(f"[isRight({card}, \"how = 'left'\"), isRight({card}, ' how=\"left\" '), isRight({card}, 'how=\"right\"')]") == [True, True, False]


def test_wrong_answer_sends_card_back_to_box_1_for_tomorrow():
    assert core("nextState({b: 4, r: 6, l: 0}, 'again', '2026-03-10')") == {"b": 1, "r": 7, "l": 1, "d": "2026-03-11", "s": "2026-03-10"}


def test_box_5_is_the_top_and_waits_35_days():
    assert core("nextState({b: 5, r: 9, l: 1}, 'good', '2026-03-10')") == {"b": 5, "r": 10, "l": 1, "d": "2026-04-14", "s": "2026-03-10"}


# ---- the answering flow, in a real (headless) browser ----

def find_chrome():
    import glob

    for c in [os.environ.get("WT_CHROME"), shutil.which("chromium"), shutil.which("chromium-browser"),
              shutil.which("google-chrome"), shutil.which("chrome-headless-shell"),
              *sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell")))]:
        if c and os.path.exists(c):
            return c
    return None


CHROME = find_chrome()
needs_chrome = pytest.mark.skipif(not CHROME, reason="needs a headless Chromium")

CARD = {"type": "cloze", "deck": "t", "file": "x.py", "link": "#c1-s1-1", "where": "1.1", "id": "t:1",
        "lines": [[1, "y = f(axis=1)"]], "blank": [0, 6, 6], "answer": "axis=1", "also": [], "hint": "", "why": "why"}


def hub_page(tmp_path, lang, before_js="", after_js="", cards=(CARD,)):
    """Build a hub with one deck, add test scripts around the page's own script, and return the rendered DOM."""
    import sys

    sys.path.insert(0, os.path.join(ROOT, "skills", "walkthrough", "engine"))
    from wt import hub

    learning = tmp_path / "learning"
    (learning / "decks").mkdir(parents=True)
    deck = {"project": "t", "title": "Test deck", "lang": lang, "walkthrough": str(tmp_path / "none.html"), "built": "2026-01-01", "cards": list(cards)}
    (learning / "decks" / "t.json").write_text(json.dumps(deck), encoding="utf-8")
    page = (learning / "hub" / "index.html") if hub.build(str(learning)) else None
    html = page.read_text(encoding="utf-8")
    html = html.replace('<script src="decks.js"></script>', f'<script src="decks.js"></script><script>{before_js}</script>')
    html = html.replace("</body>", f"<script>{after_js}</script></body>")
    test_page = page.with_name("test.html")
    test_page.write_text(html, encoding="utf-8")
    out = subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=3000", "--dump-dom",
                          test_page.as_uri()], capture_output=True, text=True, check=False, timeout=60)
    return out.stdout


def result(dom: str) -> str:
    """Text of the <pre id="result"> the test script appended (the last one: the script's own source also contains the tag)."""
    return dom.rsplit('<pre id="result">', 1)[1].split("</pre>")[0]


TODAY_JS = "var d=new Date(),p=function(n){return (n<10?'0':'')+n;},today=d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());"


@needs_chrome
def test_accepting_a_typo_moves_the_card_up_from_its_previous_box(tmp_path):
    before = TODAY_JS + ("localStorage.setItem('wt-review-v1',JSON.stringify({cards:{'t:1':{b:4,r:3,l:0,d:'2000-01-01',s:'1999-12-01'}},"
                         "meta:{day:today,newToday:0},settings:{newPerDay:20}}));")
    after = ("document.getElementById('start').click();document.getElementById('ans').value='axis=0';"
             "document.getElementById('check').click();document.getElementById('accept').click();"
             "document.body.insertAdjacentHTML('beforeend','<pre id=\"result\">'+localStorage.getItem('wt-review-v1')+'</pre>');")
    dom = hub_page(tmp_path, "zh-TW", before, after)
    state = json.loads(result(dom))["cards"]["t:1"]
    assert (state["b"], state["l"]) == (5, 0)


@needs_chrome
def test_box_labels_follow_the_deck_language(tmp_path):
    dom = hub_page(tmp_path, "zh-TW")
    assert "第 1 盒" in dom and "Box 1" not in dom


@needs_chrome
def test_due_cards_come_before_new_cards(tmp_path):
    new = {**CARD, "id": "t:new", "where": "new card"}
    due = {**CARD, "id": "t:due", "where": "due card"}
    before = TODAY_JS + ("Math.random=function(){return 0;};"  # a fixed shuffle, so the order is reproducible
                         "localStorage.setItem('wt-review-v1',JSON.stringify({cards:{'t:due':{b:3,r:2,l:0,d:'2000-01-01',s:'1999-12-01'}},"
                         "meta:{day:today,newToday:0},settings:{newPerDay:20}}));")
    after = ("document.getElementById('start').click();"
             "document.body.insertAdjacentHTML('beforeend','<pre id=\"result\">'+document.querySelector('.where').textContent+'</pre>');")
    dom = hub_page(tmp_path, "en", before, after, cards=[new, due])
    assert result(dom).endswith("due card")


@needs_chrome
def test_zero_new_cards_per_day_means_reviews_only(tmp_path):
    new = {**CARD, "id": "t:new", "where": "new card"}
    due = {**CARD, "id": "t:due", "where": "due card"}
    before = TODAY_JS + ("localStorage.setItem('wt-review-v1',JSON.stringify({cards:{'t:due':{b:3,r:2,l:0,d:'2000-01-01',s:'1999-12-01'}},"
                         "meta:{day:today,newToday:0},settings:{newPerDay:0}}));")
    after = ("var limit=document.getElementById('limit').value;document.getElementById('start').click();"
             "document.body.insertAdjacentHTML('beforeend','<pre id=\"result\">'+limit+' | '+document.querySelector('.sbar span').textContent+'</pre>');")
    dom = hub_page(tmp_path, "en", before, after, cards=[new, due])
    assert result(dom) == "0 | Card 1 / 1"
