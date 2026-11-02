# Content spec

The tools folder (`<project>/docs/walkthrough_tools/`) holds everything project-specific:

```
project.py         configuration (below)
content.py         CHAPTERS = [C1, C2, ...]   (imports content_ch1.py ...)
content_chN.py     one chapter each
cap_<name>.py      evidence capture scripts
wt_env.py          puts the engine on sys.path (scaffolded)
data/              captured evidence (cap_*.json) and build output used by verify
runs/              scratch folders the captures run in
```

## project.py

| name | meaning |
|---|---|
| `PROJECT` | deck id; the deck is written to `~/learning/decks/<PROJECT>.json` |
| `LANG` | UI language (`zh-TW`, `en`); take it from PROFILE.md |
| `REPO`, `OUT` | project root relative to the tools folder; output page relative to the root |
| `CAPTURES` | capture scripts in run order |
| `TITLE`, `KICKER`, `LEAD` | page heading; `LEAD` is HTML |
| `FLOW` | optional rows showing how the files connect: `{"num", "label", "href", "in", "out"}` |
| `ENV(O)` | one paragraph on how the evidence was produced (versions, data size, scratch folders, what "extra" means); `O` is all captured data |
| `CHARTS` | named chart specs used by `CHART(name, ...)` (below) |
| `TAG_GROUPS` | optional `[[group title, [tag prefixes], css class]]`; css classes: `syn`, `stat`, `model`, `warn` |
| `CLOZE_CONTEXT` | lines shown around a one-line cloze, default `(2, 1)` |
| `CARDS_FROM_INTERVIEW` | turn interview Q&A into recall cards, default `True` |
| `UNUSED_OK` | suffixes of captured keys that may stay unused (timings: `("_sec",)`) |

## Anchors

Every location in content and captures is an anchor resolved against the real file:

- `"text"`: the one line containing `text` (must be unique in the file)
- `"=text"`: the line whose stripped content equals `text` (for `)`, `"""`, `return d`)
- `"text#n"`: the n-th occurrence
- `("a", "b")`: lines from anchor a to anchor b inclusive; `["a", ("b", "c")]`: union

Inside explanation text, `{{anchor}}`, `{{a..b}}` and `{{other.py:a..b}}` become "Line N–M" when rendering. Typed line numbers fail verification.

## Chapters, steps, segments

```python
from wt.content import CH, IV, ST, S, T, OUT, KV, Cloze, Choice, Recall

C1 = CH("c1", "features.py", "title", intro=["2–3 sentences: the file's purpose and place"],
        steps=[ST("s1", "title", "why this step exists", span, [S(...), S(...)])],
        interview=IV("30-second version", ["<strong>...</strong>: ..."], [(question, answer)]))
```

`CH`, `IV`, `ST` and `S` return plain dicts, so hand-written dicts with the same keys work too.

- A **step** covers one logical block (`span`). A flow chapter sets `file=None` and gives each step `file=`.
- A **segment** `S(at, text, evidence, tags=[], ext=[], cards=[])` highlights `at` (inside the span) and explains it. Several segments may highlight the same lines to explain different ideas.
- Text supports `` `code` ``, `**bold**`, blank-line paragraphs, and `- ` / `1. ` lists.
- `tags` are `"<prefix>：<name>"` (zh-TW) or `"<prefix>: <name>"` (en); the prefix picks the group in the page index. Default prefixes: 語法 / 新手卡關, 統計 / 概念, 模型選擇 / 設計選擇, 注意.
- `ext` lists code references in the text that deliberately point elsewhere (the old version, a usage pattern); verify checks every other `` `code` `` reference sits on the highlighted lines.

## Evidence blocks

| block | shows |
|---|---|
| `T(key, title, note)` | a table (`tbl(df)` / `rows(...)` in captures) |
| `OUT(key, title)` | terminal output or text |
| `KV(key, title)` | a dict as chips, or one scalar |
| `LST(key, title)` | a list as chips |
| `IMG(key, title, note)` | an image file (path relative to the tools folder): screenshots, diagrams |
| `CHART(name, title, note)` | a chart from `project.CHARTS` |
| `CODE(code, title)` | illustrative code that is not in the file (an equivalent rewrite, the old buggy version); title it as such |

Chart kinds: `hist2` (two-series histogram: `data` key holding `edges` + one list per series, `series=[[key, label], ...]`, `x`, `y`, `ymax`, `unit`, `clip`, `tip_title`, `legend`, optional `table` header) and `calib` (calibration plot: `data` key of `[x, y]` points, `rows_key` table for tooltips, `tip_title` / `tip_label` with `{0}`, `{1}` ... row fields, `legend`).

## Writing

- Explain what the lines do **and why they are written this way**; a translation of the code into words teaches nothing.
- Bridge every new idea through what PROFILE.md says the learner already knows (for a statistician: AUC as Mann-Whitney U, cross-validation as repeated resampling, one-hot `drop_first` as dummy coding with a reference category).
- Give beginner syntax its own segment the first time it appears: method chaining across lines, `groupby`, `merge`, `lambda`, comprehensions, `axis`, index alignment, `with`, decorators, `if __name__ == "__main__"`, saving / loading models, async / await, hooks, whatever the language needs. Tag it so the index finds it.
- Every number in the text appears in the captured data shown in that segment or one before it. Re-check after every recapture.
- Name design choices honestly: the alternatives, how much better the choice really is, and judgement calls stated as judgement calls.
- Audit findings: a `注意：...` (or `Note: ...`) tagged segment saying what the old version did, how it failed with real evidence, and why the fix is right.
- Label analyses that are not in the file as extra (另外跑的), in the block title.
- Keep the learner's language (PROFILE.md) everywhere, including evidence titles and chart labels.

## Interview section

`pitch`: what the file does and the one or two decisions worth defending, in 30 seconds. `points`: 3–5 bullets with real numbers. `qa`: likely follow-ups with honest answers, including what was fixed and what you would do next. Each Q&A becomes a recall card.
