"""Render a walkthrough: project.py + content + captured data + real source -> one HTML page and a review deck."""
import base64
import hashlib
import html
import json
import mimetypes
import os
import re
from datetime import date

from . import anchors, hub
from .capture import load_project
from .highlight import highlight
from .strings import line_label, strings

ENGINE = os.path.dirname(os.path.abspath(__file__))
NUM = re.compile(r"^-?[\d,]+(\.\d+)?%?$|^NaN$|^<NA>$")
DATA_KINDS = {"table", "out", "kv", "list", "chart", "img"}


def esc(x) -> str:
    return html.escape(str(x), quote=False)


def learning_dir() -> str:
    return os.path.expanduser(os.environ.get("WT_LEARNING", "~/learning"))


class Renderer:
    def __init__(self, tools_dir: str):
        self.P = load_project(tools_dir)
        self.lang = getattr(self.P, "LANG", "zh-TW")
        self.S = strings(self.lang)
        self.O = {}
        data = os.path.join(self.P.TOOLS, "data")
        for f in sorted(os.listdir(data)) if os.path.isdir(data) else []:
            if f.startswith("cap_") and f.endswith(".json"):
                with open(os.path.join(data, f), encoding="utf-8") as fh:
                    self.O.update(json.load(fh))
        self.files, self.hl_cache = {}, {}
        groups = getattr(self.P, "TAG_GROUPS", None) or self.S["tag_groups"]
        self.groups = groups
        self.tag_class = {pre: cls for _, pres, cls in groups for pre in pres}
        self.used = set()

    # ------------------------------------------------------------ source & anchors
    def lines(self, fname: str) -> list:
        if fname not in self.files:
            with open(os.path.join(self.P.REPO, fname), encoding="utf-8") as f:
                self.files[fname] = f.read().split("\n")
        return self.files[fname]

    def highlighted(self, fname: str) -> list:
        if fname not in self.hl_cache:
            self.hl_cache[fname] = highlight("\n".join(self.lines(fname)), fname)
        return self.hl_cache[fname]

    def resolve(self, fname, at):
        return anchors.resolve(self.lines(fname), at, fname)

    def ref(self, fname: str, spec: str) -> str:
        other = None
        m = re.match(r"^([\w./-]+\.\w+):(.*)$", spec)
        if m:
            other, spec = m.group(1), m.group(2)
        at = tuple(spec.split("..")) if ".." in spec else spec
        lab = line_label(self.resolve(other or fname, at), self.lang)
        return f"{other} {lab}" if other else lab

    # ------------------------------------------------------------ text
    def md(self, text: str, fname: str) -> str:
        text = re.sub(r"\{\{(.+?)\}\}", lambda m: self.ref(fname, m.group(1)), text)
        text = esc(text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        out = []
        for para in text.split("\n\n"):
            rows = para.split("\n")
            if len(rows) > 1 and all(re.match(r"^(- |\d+\. )", r) for r in rows[1:]):
                tag = "ol" if re.match(r"^\d+\. ", rows[1]) else "ul"
                lis = "".join(f"<li>{re.sub(r'^(- |\d+\. )', '', r)}</li>" for r in rows[1:])
                out.append((f"<p>{rows[0]}</p>" if rows[0] else "") + f"<{tag}>{lis}</{tag}>")
            else:
                out.append("<p>" + "<br>".join(rows) + "</p>")
        return "".join(out)

    def tagcls(self, tag: str) -> str:
        pre = tag.split(self.S["tag_sep"], 1)[0]
        if pre not in self.tag_class:
            raise ValueError(f"tag {tag!r}: prefix {pre!r} is not in any tag group {list(self.tag_class)}")
        return self.tag_class[pre]

    # ------------------------------------------------------------ evidence blocks
    def table_html(self, t: dict) -> str:
        numcol = [all(NUM.match(str(r[j])) for r in t["rows"]) for j in range(len(t["cols"]))]
        head = "".join(f'<th{" class=n" if numcol[j] else ""}>{esc(c)}</th>' for j, c in enumerate(t["cols"]))
        body = "".join("<tr>" + "".join(f'<td{"" if NUM.match(str(v)) else " class=t"}>{esc(v)}</td>' for v in r) + "</tr>"
                       for r in t["rows"])
        return f'<div class="tw"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

    def data(self, key):
        if key not in self.O:
            raise KeyError(f"no captured data named {key!r} (run the capture scripts?)")
        self.used.add(key)
        return self.O[key]

    def probe(self, p, fname: str) -> str:
        kind = p[0]
        h4 = lambda t: f"<h4>{esc(t)}</h4>" if t else ""
        note = lambda t: f'<p class="pnote">{esc(t)}</p>' if t else ""
        if kind == "table":
            _, key, title, n = p
            return h4(title) + self.table_html(self.data(key)) + note(n)
        if kind == "out":
            _, key, title = p
            return h4(title or self.S["evidence"]) + f'<pre class="out">{esc(self.data(key))}</pre>'
        if kind == "kv":
            _, key, title = p
            v = self.data(key)
            val = lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else str(x)
            if isinstance(v, dict):
                chips = "".join(f"<span><b>{esc(k)}</b> = {esc(val(x))}</span>" for k, x in v.items())
                return h4(title) + f'<div class="kv">{chips}</div>'
            return f'<div class="kv"><span><b>{esc(title or key)}</b> = {esc(val(v))}</span></div>'
        if kind == "list":
            _, key, title = p
            v = self.data(key)
            return h4(f"{title or key}（{len(v)}）") + '<div class="kv list">' + "".join(f"<span>{esc(x)}</span>" for x in v) + "</div>"
        if kind == "img":
            _, key, title, n = p
            path = os.path.join(self.P.TOOLS, self.data(key))
            mime = mimetypes.guess_type(path)[0] or "image/png"
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return h4(title) + f'<img class="shot" alt="{esc(title or key)}" src="data:{mime};base64,{b64}">' + note(n)
        if kind == "code":
            _, code, title = p
            return h4(title) + '<pre class="snippet">' + "\n".join(highlight(code, fname)) + "</pre>"
        if kind == "chart":
            _, name, title, n = p
            spec = self.P.CHARTS[name]
            leg = "".join(f'<span><i class="sw {c}"></i>{esc(lab)}</span>' for c, lab in spec.get("legend", []))
            extra = ""
            if spec.get("table"):
                extra = f'<details class="tview"><summary>{esc(self.S["show_table"])}</summary>' + self.table_html(self.chart_table(spec)) + "</details>"
            return (h4(title) + f'<div class="legend">{leg}</div><div class="chart" data-chart="{esc(name)}">'
                    f'<canvas role="img" aria-label="{esc(title)}"></canvas></div>' + note(n) + extra)
        raise ValueError(f"unknown evidence kind {kind!r}")

    def chart_data(self, spec: dict) -> dict:
        out = {k: v for k, v in spec.items() if k not in ("data", "rows_key", "table")}
        if spec["kind"] == "hist2":
            out["data"] = self.data(spec["data"])
        elif spec["kind"] == "calib":
            out["xy"] = self.data(spec["data"])
            out["rows"] = self.data(spec["rows_key"])["rows"]
        else:
            raise ValueError(f"unknown chart kind {spec['kind']!r}")
        return out

    def chart_table(self, spec: dict) -> dict:
        d = self.data(spec["data"])
        e = d["edges"]
        keys = [k for k, _ in spec["series"]]
        return {"cols": spec["table"], "rows": [[f"{e[i]:.2f}–{e[i + 1]:.2f}"] + [f"{d[k][i]:.2f}" for k in keys] for i in range(len(e) - 1)]}

    # ------------------------------------------------------------ review cards
    def card(self, c: dict, ctx: dict) -> dict:
        base = {"type": c["type"], "deck": self.P.PROJECT, "file": ctx["file"], "link": ctx["link"], "where": ctx["where"]}
        if c["type"] == "cloze":
            nums = self.resolve(ctx["file"], c["at"])
            text = [self.lines(ctx["file"])[n - 1] for n in nums]
            hits = [(i, t.find(c["blank"])) for i, t in enumerate(text) if c["blank"] in t]
            if len(hits) != 1 or text[hits[0][0]].count(c["blank"]) != 1:
                raise ValueError(f"{ctx['where']}: cloze blank {c['blank']!r} must occur exactly once in {line_label(nums, self.lang)}")
            i, col = hits[0]
            target = nums[i]
            if len(nums) == 1:  # one anchored line: show a little context, minus any line that would give the answer away
                before, after = getattr(self.P, "CLOZE_CONTEXT", (2, 1))
                src = self.lines(ctx["file"])
                ctx_nums = [n for n in range(max(1, target - before), min(len(src), target + after) + 1)
                            if n == target or (src[n - 1].strip() and c["blank"] not in src[n - 1])]
                nums, text, i = ctx_nums, [src[n - 1] for n in ctx_nums], ctx_nums.index(target)
            card = {**base, "lines": [[n, t] for n, t in zip(nums, text)], "blank": [i, col, len(c["blank"])],
                    "answer": c["blank"], "also": c["also"], "hint": c["hint"], "why": c["why"]}
            key = f"{ctx['file']}|{text[i]}|{c['blank']}"
        elif c["type"] == "choice":
            if not 0 <= c["answer"] < len(c["options"]):
                raise ValueError(f"{ctx['where']}: choice answer index {c['answer']} out of range")
            card = {**base, "q": c["q"], "options": c["options"], "answer": c["answer"], "why": c["why"]}
            key = c["q"]
        else:
            card = {**base, "q": c["q"], "a": c["a"]}
            key = c["q"]
        if c.get("at") and c["type"] != "cloze":
            nums = self.resolve(ctx["file"], c["at"])
            card["lines"] = [[n, self.lines(ctx["file"])[n - 1]] for n in nums]
        if card.get("lines"):
            card["hl"] = highlight("\n".join(t for _, t in card["lines"]), ctx["file"])
        card["id"] = c.get("id") or f"{self.P.PROJECT}:{c['type']}:" + hashlib.sha1(key.encode()).hexdigest()[:10]
        return card

    # ------------------------------------------------------------ page
    def build(self):
        P, S = self.P, self.S
        js_steps, debug, index, cards = [], [], {}, []
        nav, body = [], []
        for ci, ch in enumerate(P.CHAPTERS, start=1):
            nav_items, sec = [], []
            for si, st in enumerate(ch["steps"], start=1):
                fname = st.get("file") or ch["file"]
                src = self.lines(fname)
                hl = self.highlighted(fname)
                key = f"{ch['id']}-{st['id']}"
                span = self.resolve(fname, st["span"])
                code, prev = [], None
                for n in span:
                    if prev is not None and n != prev + 1:
                        code.append(None)
                    code.append([n, hl[n - 1]])
                    prev = n
                subs = []
                for k, sb in enumerate(st["subs"], start=1):
                    ls = self.resolve(fname, sb["at"])
                    outside = [n for n in ls if n not in span]
                    if outside:
                        raise ValueError(f"{key}-{k}: lines {outside} are outside this step's code")
                    blocks = [self.probe(p, fname) for p in sb["p"]]
                    r = ""
                    if blocks:
                        head = S["evidence"] if any(p[0] in DATA_KINDS for p in sb["p"]) else S["aside"]
                        r = f'<p class="res-h">{esc(head)}</p>' + "".join(f'<div class="blk">{x}</div>' for x in blocks)
                    subs.append({"l": ls, "tags": [[self.tagcls(t), t] for t in sb["tags"]], "t": self.md(sb["t"], fname),
                                 "r": r, "charts": [p[1] for p in sb["p"] if p[0] == "chart"]})
                    for t in sb["tags"]:
                        index.setdefault(t, []).append((f"{key}-{k}", f"{ci}.{si}"))
                    where = f"{key}-{k}"
                    for c in sb.get("cards", []):
                        cards.append(self.card(c, {"file": fname, "link": f"#{where}", "where": f"{ci}.{si} {st['title']}"}))
                    debug.append({"key": where, "file": fname, "l": ls, "label": line_label(ls, self.lang), "raw": sb["t"],
                                  "ext": sb["ext"], "hl_text": [src[n - 1] for n in ls]})
                last = si == len(ch["steps"])
                has_iv = bool(ch.get("interview"))
                nxt = f"{ch['id']}-iv" if last and has_iv else (f"{ch['id']}-{ch['steps'][si]['id']}" if not last else "")
                nxt_title = S["interview_short"] if last and has_iv else (ch["steps"][si]["title"] if not last else "")
                js_steps.append({"key": key, "file": fname, "code": code, "subs": subs, "next": nxt, "nextTitle": nxt_title})
                nav_items.append(f'<li><a href="#{key}"><span class="no">{ci}.{si}</span>{esc(st["title"])}</a></li>')
                sec.append(f'''
<article class="step" id="{key}">
  <h3><span class="no">{ci}.{si}</span>{esc(st["title"])}</h3>
  <p class="why">{esc(st["why"])}</p>
  <div class="panel" data-key="{key}">
    <div class="code-head"><span class="fname">{esc(fname)}</span><span class="span-lab"></span></div>
    <pre class="code" tabindex="0" aria-label="{esc(S["code_of"].format(file=fname))}"></pre>
    <div class="ctrl">
      <button type="button" class="btn prev">{esc(S["prev"])}</button>
      <div class="dots" role="group" aria-label="{esc(S["segments"])}"></div>
      <span class="count" aria-live="polite"></span>
      <button type="button" class="btn next primary">{esc(S["next"])}</button>
    </div>
    <div class="cap"></div>
    <div class="res"></div>
  </div>
</article>''')
            iv = ch.get("interview")
            if iv:
                pts = "".join(f"<li>{p}</li>" for p in iv["points"])
                qa = "".join(f'<details class="qa"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in iv["qa"])
                n_iv = len(ch["steps"]) + 1
                sec.append(f'''
<article class="iv" id="{ch['id']}-iv">
  <h3><span class="no">{ci}.{n_iv}</span>{esc(S["interview"])}</h3>
  <div class="iv-card">
    <p class="iv-h">{esc(S["pitch"])}</p>
    <blockquote>{esc(iv["pitch"])}</blockquote>
    <p class="iv-h">{esc(S["points"])}</p>
    <ul class="pts">{pts}</ul>
    <p class="iv-h">{esc(S["qa"])}</p>
    {qa}
  </div>
</article>''')
                nav_items.append(f'<li><a href="#{ch["id"]}-iv"><span class="no">{ci}.{n_iv}</span>{esc(S["interview_short"])}</a></li>')
                if getattr(P, "CARDS_FROM_INTERVIEW", True):
                    for q, a in iv["qa"]:
                        cards.append(self.card({"type": "recall", "q": q, "a": a},
                                               {"file": fname, "link": f"#{ch['id']}-iv", "where": f"{ci}.{n_iv} {S['interview_short']}"}))
            label = ch.get("file") or ch.get("label") or ch["title"]
            nav.append(f'<li class="ch"><a href="#{ch["id"]}" class="ch-a"><span class="chno">{esc(S["chapter"].format(n=ci))}</span>'
                       f'<span class="mono">{esc(label)}</span></a><ol>{"".join(nav_items)}</ol></li>')
            if ch.get("file"):
                src = self.lines(ch["file"])
                meta = S["chapter_meta"].format(n=ci, lines=len(src) if src[-1] else len(src) - 1, steps=len(ch["steps"]))
            else:
                meta = S["chapter"].format(n=ci)
            intro = "".join(f"<p>{esc(p)}</p>" for p in ch["intro"])
            body.append(f'''
<section class="chapter" id="{ch['id']}">
  <header class="ch-head">
    <p class="ch-kicker">{esc(meta)}</p>
    <h2><span class="mono">{esc(label)}</span><span class="ch-title">{esc(ch["title"])}</span></h2>
    <div class="ch-intro">{intro}</div>
  </header>
  {"".join(sec)}
</section>''')

        ids = [c["id"] for c in cards]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            raise ValueError(f"duplicate card ids {sorted(dup)}: give one of them an explicit id=")

        idx = ""
        for gname, pres, cls in self.groups:
            items = []
            for t, locs in index.items():
                if t.split(S["tag_sep"], 1)[0] in pres:
                    name = t.split(S["tag_sep"], 1)[1]
                    links = " ".join(f'<a href="#{h}">{lab}</a>' for h, lab in locs)
                    items.append(f'<li><span class="tag {cls}">{esc(name)}</span>{links}</li>')
            if items:
                idx += f'<div class="idx-g"><p class="idx-h">{esc(gname)}</p><ul>{"".join(items)}</ul></div>'

        out_html = os.path.join(P.REPO, P.OUT)
        hub_dir = os.path.join(learning_dir(), "hub")
        flow = "".join(
            '<div class="frow">' + (f'<span class="fin">{esc(r["in"])}</span><span class="arr">→</span>' if r.get("in") else "")
            + f'<a href="{esc(r["href"])}"><b>{esc(r["num"])}</b>{esc(r["label"])}</a>'
            + ('<span class="arr">→</span>' if r.get("in") and r.get("out") else "")
            + (f'<span class="fout">{esc(r["out"])}</span>' if r.get("out") else "") + "</div>"
            for r in getattr(P, "FLOW", []))
        review = ""
        if cards:
            href = os.path.relpath(os.path.join(hub_dir, "index.html"), os.path.dirname(out_html)) + f"#deck={P.PROJECT}"
            review = f'<p class="review-link"><a href="{esc(href)}">{esc(S["review_link"].format(n=len(cards)))}</a></p>'
        env = P.ENV(self.O) if hasattr(P, "ENV") else ""
        charts = {name: self.chart_data(spec) for name, spec in getattr(P, "CHARTS", {}).items()}
        with open(os.path.join(ENGINE, "templates", "walkthrough.html"), encoding="utf-8") as f:
            page = f.read()
        js = lambda v: json.dumps(v, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        for k, val in {
            "__LANG__": self.lang, "__TITLE__": esc(P.TITLE), "__KICKER__": esc(getattr(P, "KICKER", "")), "__LEAD__": P.LEAD,
            "__FLOW__": f'<div class="flow">{flow}</div>' if flow else "",
            "__HOWTO__": "".join(f"<li>{esc(h)}</li>" for h in S["howto"]),
            "__ENVNOTE__": f'<p class="envnote">{env}</p>' if env else "", "__REVIEW__": review,
            "__INDEX__": idx, "__NAV__": "".join(nav), "__BODY__": "".join(body), "__FOOTER__": esc(S["footer"]),
            "__TOC__": esc(S["toc"]), "__TOCBTN__": esc(S["toc_button"]), "__THEME__": esc(S["theme"]["auto"]),
            "__STEPS__": js(js_steps), "__CHARTS__": js(charts), "__S__": js(S),
        }.items():
            page = page.replace(k, val)
        os.makedirs(os.path.dirname(out_html), exist_ok=True)
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(page)
        with open(os.path.join(P.TOOLS, "data", "built_debug.json"), "w", encoding="utf-8") as f:
            json.dump({"subs": debug, "steps": js_steps, "cards": cards, "lang": self.lang}, f, ensure_ascii=False)

        deck = {"project": P.PROJECT, "title": P.TITLE, "lang": self.lang, "walkthrough": out_html,
                "built": date.today().isoformat(), "cards": cards}
        os.makedirs(os.path.join(learning_dir(), "decks"), exist_ok=True)
        with open(os.path.join(learning_dir(), "decks", f"{P.PROJECT}.json"), "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=1)
        hub.build(learning_dir())
        unused = sorted(k for k in self.O if k not in self.used and not k.endswith(tuple(getattr(P, "UNUSED_OK", ("_sec",)))))
        print(f"wrote {out_html} ({len(page) / 1024:.0f} KB) | {len(debug)} segments | {len(cards)} cards"
              + (f" | unused data: {unused}" if unused else ""))


def render(tools_dir: str):
    Renderer(tools_dir).build()
