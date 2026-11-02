# Review cards

Cards are attached to the segment that teaches them (`S(..., cards=[...])`), so every card links back to its explanation. `render` writes them to `~/learning/decks/<PROJECT>.json` and rebuilds the hub, `~/learning/hub/index.html`.

## Types

**Cloze**: fill in a blank on the **real** source.

```python
Cloze("return pd.get_dummies", "drop_first=True", why="...", also=["drop_first = True"], hint="")
```

- `at` anchors the line(s); `blank` is the text removed and must occur exactly once there. A one-line anchor gets `CLOZE_CONTEXT` lines around it, minus any line containing the answer.
- Blank the token worth recalling: the argument that changes behaviour (`axis=1`, `how="left"`, `right=False`), the method that does the work (`groupby`, `merge`, `cache_resource`), the guard (`if __name__ == "__main__"`). A blank whose answer is arbitrary (a variable name, a literal) trains nothing.
- The hub ignores whitespace differences and treats `'` and `"` alike; list other accepted spellings in `also`.
- `why` is one sentence: the reason this token is there.

**Choice**: a concept or a decision.

```python
Choice("question?", ["correct", "distractor", "distractor", "distractor"], 0, why="...")
```

- Four options of about the same length; the hub shuffles them and verify warns when lengths differ enough to give the answer away.
- Distractors are real misconceptions (what the old buggy version assumed, what a beginner would guess), each plausible on its own.
- Good targets: the statistical meaning of a metric, why a design choice beats its alternative, what goes wrong without a step, how a tool aggregates.

**Recall**: reasoning in your own words, self-graded (forgot / fuzzy / knew it).

```python
Recall("question?", "reference answer, at most three sentences")
```

- For explanations an interviewer would ask for. Interview Q&A become recall cards automatically.

## Coverage

At least one card per step, plus one for every audit finding and every concept segment. Prefer cloze for syntax, choice for concepts, recall for reasoning. A card belongs in one place only: the same fact asked twice wastes review time.

## The hub

- Leitner boxes: a correct answer moves a card up one box (a new card answered correctly starts in box 2); intervals 1, 3, 7, 16, 35 days for boxes 1–5. A wrong answer goes back to box 1 and comes back once more at the end of the session.
- New cards per day is a setting (default 20); due cards come first, decks are interleaved.
- Progress lives in the browser (localStorage); export / import it as JSON from the hub.
- Card ids are a hash of the card's content, so editing a card's question or its source line resets its progress, and reordering content does not.
