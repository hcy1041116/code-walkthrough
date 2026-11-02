"""Engine tests on a tiny demo project: anchors, capture, render, verify, cards and the hub.

Run from the repo root:  uv run --with pytest python -m pytest -q
They use whatever Python runs pytest; pandas and Pygments are optional for the engine.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, "skills", "walkthrough", "engine")
sys.path.insert(0, ENGINE)

from wt import anchors, render, verify
from wt.strings import line_label

LINES = ["import os", "def f():", "    return 1", ")", "x = f()", ")"]


def test_anchor_forms():
    assert anchors.find(LINES, "def f") == 2
    assert anchors.find(LINES, "=)#2") == 6
    assert anchors.resolve(LINES, ("def f", "return 1")) == [2, 3]
    assert anchors.resolve(LINES, ["import os", ("x = f", "=)#2")]) == [1, 5, 6]
    with pytest.raises(ValueError, match="exactly once"):
        anchors.find(LINES, "f()")
    with pytest.raises(ValueError, match="ends before"):
        anchors.resolve(LINES, ("x = f", "def f"))


def test_line_labels():
    assert line_label([3, 4, 5, 9], "zh-TW") == "第 3–5、9 行"
    assert line_label([7], "en") == "Line 7"
    assert line_label([3, 4, 5], "en") == "Lines 3–5"


@pytest.fixture()
def demo(tmp_path, monkeypatch):
    """A fresh copy of the demo project and an empty learning folder."""
    proj = tmp_path / "demo"
    shutil.copytree(os.path.join(ROOT, "tests", "demo"), proj)
    monkeypatch.setenv("WT_ENGINE", ENGINE)
    monkeypatch.setenv("WT_LEARNING", str(tmp_path / "learning"))
    tools = proj / "docs" / "walkthrough_tools"
    r = subprocess.run([sys.executable, os.path.join(ENGINE, "run.py"), "capture", str(tools)],
                       capture_output=True, text=True, env={**os.environ}, check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    return proj, tools, tmp_path / "learning"


def test_render_verify_and_hub(demo):
    proj, tools, learning = demo
    render.render(str(tools))
    page = (proj / "docs" / "walkthrough.html").read_text(encoding="utf-8")
    assert "Hello, Ada" in page and "Line" in page
    assert verify.verify(str(tools)) == 0
    deck = json.loads((learning / "decks" / "demo.json").read_text(encoding="utf-8"))
    kinds = sorted(c["type"] for c in deck["cards"])
    assert kinds == ["choice", "cloze", "recall", "recall"]  # one recall comes from the interview Q&A
    cloze = next(c for c in deck["cards"] if c["type"] == "cloze")
    i, col, n = cloze["blank"]
    assert cloze["lines"][i][1][col:col + n] == "excited: bool = False"
    assert "window.WT_DECKS" in (learning / "hub" / "decks.js").read_text(encoding="utf-8")
    assert (learning / "hub" / "index.html").exists()


def test_cloze_blank_must_be_unique(demo):
    _, tools, _ = demo
    content = tools / "content.py"
    content.write_text(content.read_text(encoding="utf-8").replace('Cloze("def greet(", "excited: bool = False")',
                                                                     'Cloze("def greet(", "e")'), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly once"):
        render.render(str(tools))


def test_verify_flags_typed_line_numbers(demo):
    _, tools, _ = demo
    content = tools / "content.py"
    content.write_text(content.read_text(encoding="utf-8").replace("Loops over `NAMES`.", "Loops over `NAMES` on line 12."),
                       encoding="utf-8")
    render.render(str(tools))
    assert verify.verify(str(tools)) == 1


def test_tbl_without_pandas_points_to_rows(monkeypatch):
    from wt import capture

    monkeypatch.setattr(capture, "pd", None)
    with pytest.raises(ImportError, match="rows"):
        capture.tbl([[1, 2]])


def test_scaffold_example_capture_records_a_real_value(tmp_path, monkeypatch):
    (tmp_path / "main.py").write_text("def main():\n    result = 6 * 7\n    return result\n", encoding="utf-8")
    tools = tmp_path / "docs" / "walkthrough_tools"
    monkeypatch.setenv("WT_ENGINE", ENGINE)
    run = [sys.executable, os.path.join(ENGINE, "run.py")]
    subprocess.run([*run, "new", str(tools)], capture_output=True, text=True, check=True)
    r = subprocess.run([*run, "capture", str(tools)], capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    captured = json.loads((tools / "data" / "cap_example.json").read_text(encoding="utf-8"))
    assert captured == {"ex_result": "42"}
