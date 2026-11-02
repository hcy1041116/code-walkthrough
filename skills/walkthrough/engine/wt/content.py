"""Authoring helpers for walkthrough content. See references/content.md for the full spec.

A chapter is CH(id, file, title, intro=[...], steps=[ST(...)], interview=IV(...) or None).
Line numbers never appear in content: every location is a code anchor (see anchors.py), and
`{{anchor}}` / `{{a..b}}` / `{{file.py:a..b}}` inside text becomes "Line N–M" at render time.
"""


def S(at, t, p=(), tags=(), ext=(), cards=()):
    """One segment: highlight the lines at `at`, explain them in `t`, show evidence `p`, add review `cards`."""
    return {"at": at, "t": t, "p": list(p), "tags": list(tags), "ext": list(ext), "cards": list(cards)}


def ST(sid, title, why, span, subs, file=None):
    """One step: a logical block of code (`span`) explained segment by segment.

    `file` overrides the chapter's file, so a chapter can follow one flow across several files
    (a request through router -> service -> database, for architecture walkthroughs)."""
    return {"id": sid, "title": title, "why": why, "span": span, "subs": subs, "file": file}


def CH(cid, file, title, intro, steps, interview=None, label=None):
    """One chapter. `file` is its source file, or None for a flow chapter whose steps name their own files
    (then `label` names the chapter in the contents)."""
    return {"id": cid, "file": file, "title": title, "intro": list(intro), "steps": steps, "interview": interview, "label": label}


def IV(pitch, points, qa):
    """The interview section closing a chapter: a 30-second pitch, points with numbers, (question, answer) pairs."""
    return {"pitch": pitch, "points": list(points), "qa": list(qa)}


# ---- evidence blocks (keys refer to captured data in data/cap_*.json) ----
def T(key, title=None, note=None):
    return ("table", key, title, note)


def OUT(key, title=None):
    return ("out", key, title)


def KV(key, title=None):
    return ("kv", key, title)


def LST(key, title=None):
    return ("list", key, title)


def IMG(key, title=None, note=None):
    """A captured screenshot: data value is a path relative to the tools folder (frontend projects)."""
    return ("img", key, title, note)


def CODE(code, title):
    """Illustrative code that is NOT in the file (an equivalent rewrite, the old buggy version...)."""
    return ("code", code, title)


def CHART(name, title, note=None):
    """A chart defined in project.CHARTS."""
    return ("chart", name, title, note)


# ---- review cards (see references/cards.md) ----
def Cloze(at, blank, why="", also=(), hint="", id=None):
    """Fill-in-the-blank on the REAL source: the lines at `at` are shown with `blank` removed.

    `blank` must occur exactly once in those lines. `also` lists other accepted answers.
    """
    return {"type": "cloze", "at": at, "blank": blank, "why": why, "also": list(also), "hint": hint, "id": id}


def Choice(q, options, answer=0, why="", at=None, id=None):
    """Multiple choice. Options are shuffled in the hub; keep them about the same length."""
    return {"type": "choice", "q": q, "options": list(options), "answer": answer, "why": why, "at": at, "id": id}


def Recall(q, a, at=None, id=None):
    """Free recall, self-graded: for concepts, reasoning and interview answers."""
    return {"type": "recall", "q": q, "a": a, "at": at, "id": id}
