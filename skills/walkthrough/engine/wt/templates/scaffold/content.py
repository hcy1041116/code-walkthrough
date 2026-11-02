"""Walkthrough content. Spec: references/content.md and references/cards.md in the walkthrough skill."""
import wt_env  # noqa: F401
from wt.content import CH, IV, KV, OUT, ST, Choice, Cloze, Recall, S, T  # noqa: F401

C1 = CH(
    "c1", "main.py", "這支檔案在做什麼",
    intro=["兩三句話：這個檔案的目的，以及它在整個專案裡的位置。"],
    steps=[
        ST("s1", "第一個邏輯段落", "這一步為什麼存在。",
           ("def main(", "=return result"),
           [
               S("def main(", "白話說明：這幾行在做什麼、為什麼這樣寫。",
                 [OUT("ex_print", "輸出")],
                 cards=[Cloze("def main(", "main")]),
           ]),
    ],
    interview=IV("30 秒版本。", ["可以主動提的重點"], [("可能被追問的問題？", "參考答案。")]),
)

CHAPTERS = [C1]
