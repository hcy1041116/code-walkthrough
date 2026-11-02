---
name: walkthrough
description: Build an evidence-grounded code walkthrough of code the user owns (data, backend, frontend, architecture) - line-by-line teaching pages showing the real output at every step, plus fill-in-the-blank review cards in a spaced-repetition hub. Use when the user asks to explain, teach or walk through their own code or project (逐行講解、教材、講解程式), to update a walkthrough after the code changed, or to add review / quiz cards.
---

# Walkthrough

A **walkthrough** teaches a codebase the learner owns. Each step shows real source lines, highlights one **segment** at a time, explains it in plain language, and shows the **evidence**: what the data, output, screen or response looked like when that code actually ran. Review **cards** feed a spaced-repetition hub so the understanding lasts.

Three ideas carry the whole skill:

- **Evidence**: every table, number, screenshot and response on the page comes from running the real code. Analyses added only to explain something are run too and labelled as extra.
- **Anchors**: every location is a code snippet that finds its line (`"df = pd.read_csv"`), never a typed line number. Pages, captures and cards all resolve the same anchors, so they cannot drift apart.
- **Audit first**: the walkthrough teaches correct code. Problems found while reading and running it are fixed before writing; what was wrong becomes teaching and interview material.

The engine lives in `engine/` next to this file. Run it with the **project's** Python (its virtualenv) so captures can import the project:

```bash
PY=<project>/.venv/bin/python; WT=<this skill>/engine/run.py
$PY $WT new <tools>       # scaffold <project>/docs/walkthrough_tools
$PY $WT capture <tools>   # run the capture scripts listed in project.CAPTURES
$PY $WT render <tools>    # page + review deck + refreshed hub
$PY $WT verify <tools> --list
```

Learner data lives outside every repo, in `~/learning/` (override with `WT_LEARNING`): `PROFILE.md`, `GLOSSARY.md`, `decks/`, and the hub page `hub/index.html`.

## Steps

1. **Profile and scope.** Read `~/learning/PROFILE.md` and `GLOSSARY.md` (if missing: `$PY $WT init-learning`, then fill the profile with the user). Agree on the files or flows to teach, their order, the output path, and whatever only the user can decide (data access, services to start, which version to teach).
   Done when: the chapter list, the audience and the output path are confirmed and every open question has an answer.

2. **Audit.** Read every file in scope and run it. List each bug, no-op setting, duplicated definition, stale comment, misleading claim and cross-file inconsistency, each with a reproduction (a command and its real output). Report the list, agree on fixes and methodological choices with the user, apply them, add tests that lock the fixes in, and re-run.
   Done when: the user has seen every finding, the agreed fixes are in, the tests pass, and the outputs the walkthrough will show have been regenerated.

3. **Capture evidence.** `$PY $WT new <tools>` once per project; keep `<tools>` git-ignored (it holds scratch runs and large captures). Fill `project.py`. For each chapter write `cap_<name>.py`: execute the real source by anchor in a scratch folder and save what the reader should see. Follow the playbook for the domain: [data](references/evidence-data.md), [backend](references/evidence-backend.md), [frontend](references/evidence-frontend.md), [architecture](references/evidence-architecture.md).
   Done when: every number, table, screenshot or response the text will mention exists in `data/cap_*.json` from a real run, with zero warnings, and the project's own files are untouched.

4. **Write the content** per [references/content.md](references/content.md): one `content_chN.py` per chapter; a step per logical block of code; segments that explain *why*, bridge new ideas through the strengths in PROFILE.md, use GLOSSARY.md terms, and quote only captured numbers; an interview section closing each chapter.
   Done when: every line of a file chapter belongs to a step, every hop of a flow chapter has a step, and every claim about data names the captured key it comes from.

5. **Write the cards** per [references/cards.md](references/cards.md): cloze on real lines for syntax worth recalling, choice for concepts and decisions, recall for reasoning.
   Done when: every step has at least one card, and every audit finding and every concept segment has one.

6. **Render and verify.** `$PY $WT render <tools>`, then `$PY $WT verify <tools> --list`. Fix every problem; for each flagged code reference either correct the anchor or, once you have confirmed it is deliberate (an old version, a usage pattern), list it in that segment's `ext`. Screenshot the page and the hub with a headless browser in light mode, dark mode and at about 390 px wide ([how](references/evidence-frontend.md)), and look at the screenshots.
   Done when: verify exits 0 with no warnings, the screenshots look right, and every number in the text has been re-checked against the captured data.

7. **Hand over.** Add the new terms to `~/learning/GLOSSARY.md`. Tell the user where the page is and how to open it (WSL: `explorer.exe "$(wslpath -w <page>)"`), that the hub is `~/learning/hub/index.html`, what the audit found and fixed, and what is left for them (commits, deploys, tools you could not run).

## Updating a walkthrough after the code changed

Audit the changed files (step 2), re-run the captures, render, verify. Anchors follow moved lines on their own; an anchor whose text changed fails loudly, so fix it and re-read that segment's explanation against the new code before rendering again.
