"""Self-check a rendered walkthrough: shown code == source, line labels agree between Python and the page's
own JavaScript, no hand-written line numbers, code references sit on the highlighted lines, cards are sound."""
import html
import json
import os
import re
import shutil
import subprocess

from .capture import load_project

HANDWRITTEN = [re.compile(r"第 ?\d+[\d–\-、 ]*行"), re.compile(r"\b[Ll]ines? \d+")]
TEMPLATE_TOKEN = re.compile(r"[一-鿿]|\.\.\.")


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s).replace('"', "'")


def verify(tools_dir: str, listing: bool = False) -> int:
    P = load_project(tools_dir)
    with open(os.path.join(P.REPO, P.OUT), encoding="utf-8") as f:
        page = f.read()
    with open(os.path.join(P.TOOLS, "data", "built_debug.json"), encoding="utf-8") as f:
        dbg = json.load(f)
    subs, steps, cards = dbg["subs"], dbg["steps"], dbg["cards"]
    problems, warnings, templ = [], [], []
    sources = {}

    def src(fname):
        if fname not in sources:
            with open(os.path.join(P.REPO, fname), encoding="utf-8") as fh:
                sources[fname] = fh.read().split("\n")
        return sources[fname]

    # 1. code embedded in the page == source, line by line
    n_lines = 0
    for s in steps:
        shown = [x[0] for x in s["code"] if x]
        for x in s["code"]:
            if x is None:
                continue
            n_lines += 1
            text = html.unescape(re.sub(r"<[^>]+>", "", x[1]))
            if text != src(s["file"])[x[0] - 1]:
                problems.append(f"{s['key']} line {x[0]}: shown code differs from {s['file']}: {text!r}")
        for k, sub in enumerate(s["subs"], 1):
            if not sub["l"]:
                problems.append(f"{s['key']}-{k}: highlights no lines")
            elif not set(sub["l"]) <= set(shown):
                problems.append(f"{s['key']}-{k}: highlighted lines are not in the shown code")

    # 2. the page's own JavaScript produces the same line labels as Python
    if shutil.which("node"):
        js = "\n".join([
            "var S=" + re.search(r"\nvar S=(\{.*?\});\n", page, re.DOTALL).group(1) + ";",
            re.search(r"\n(var fmt=function.*?;)\n", page).group(1),
            re.search(r"(function ranges\(l\)\{.*?\nfunction lineLabel\(l\)\{[^\n]*)", page, re.DOTALL).group(1),
            "const L=JSON.parse(require('fs').readFileSync(0,'utf8'));console.log(JSON.stringify(L.map(lineLabel)));",
        ])
        out = subprocess.run(["node", "-e", js], input=json.dumps([d["l"] for d in subs]), capture_output=True, text=True, check=True)
        for d, jl in zip(subs, json.loads(out.stdout)):
            d["js"] = jl
            if jl != d["label"]:
                problems.append(f"{d['key']}: page shows {jl!r} but Python computed {d['label']!r}")
    else:
        warnings.append("node not found: skipped the JavaScript line-label check")
        for d in subs:
            d["js"] = d["label"]

    # 3. no hand-written line numbers in explanations (they must come from {{anchors}})
    for d in subs:
        raw = re.sub(r"\{\{.+?\}\}", "", d["raw"])
        if any(p.search(raw) for p in HANDWRITTEN):
            problems.append(f"{d['key']}: hand-written line number in the text; use {{{{anchor}}}} instead")

    # 4. `code` references in the text appear on the highlighted lines (ext lists deliberate exceptions)
    misses = []
    for d in subs:
        hl = norm("\n".join(d["hl_text"]))
        for tok in re.findall(r"`([^`]+)`", d["raw"]):
            if tok in d["ext"] or norm(tok) in hl:
                continue
            if TEMPLATE_TOKEN.search(tok):  # pattern like `os.environ.get(名字, 預設值)` or `f(...)`
                pat = re.sub(r"(?:[一-鿿]+|\\\.\\\.\\\.)", ".*?", re.escape(norm(tok)))
                if re.search(pat, hl):
                    templ.append(f"{d['key']} `{tok}`")
                    continue
            misses.append(f"{d['key']} [{d['js']}] `{tok}` not on: {' | '.join(x.strip() for x in d['hl_text'])[:90]}")

    # 5. review cards
    for c in cards:
        if c["type"] == "cloze":
            i, col, n = c["blank"]
            ln, text = c["lines"][i]
            if text != src(c["file"])[ln - 1] or text[col:col + n] != c["answer"]:
                problems.append(f"card {c['id']}: cloze does not match {c['file']} line {ln}")
        if c["type"] == "choice":
            lens = [len(o) for o in c["options"]]
            if max(lens) > 1.8 * max(1, min(lens)):
                warnings.append(f"card {c['id']} ({c['where']}): option lengths {lens} differ a lot; length can give the answer away")

    print(f"checked {len(steps)} steps, {len(subs)} segments, {n_lines} code lines, {len(cards)} cards")
    print(f"problems: {len(problems)}")
    for p in problems:
        print("  ✗", p)
    print(f"code references not on the highlighted lines: {len(misses)}")
    for m in misses:
        print("  ?", m)
    print(f"template-style references (wildcard match): {len(templ)}")
    for w in warnings:
        print("  !", w)
    if listing:
        print("\nsegment map (label ← first highlighted line | text)")
        for d in subs:
            txt = re.sub(r"\{\{.+?\}\}", "§", d["raw"]).replace("\n", " ")
            print(f"{d['key']:<9} {d['js']:<16} {d['hl_text'][0].strip()[:50]:<50} | {txt[:44]}")
    return 1 if problems or misses else 0
