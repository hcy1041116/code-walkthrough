import wt_env  # noqa: F401
from wt.content import CH, IV, KV, OUT, ST, Choice, Cloze, Recall, S

C1 = CH(
    "c1", "src/greet.py", "Greeting",
    intro=["Builds greetings."],
    steps=[
        ST("s1", "greet", "One greeting.", ("def greet(", 'return text + ("!"'), [
            S("def greet(", "`excited` defaults to `False`, see {{def main():..print(greet}}.",
              [KV("g_call")], tags=["Syntax: default argument"],
              cards=[Cloze("def greet(", "excited: bool = False")]),
            S(('text = f"Hello', 'return text + ("!"'), "An f-string builds the text; `return` adds the ending.",
              [KV("g_text")], cards=[Choice("What does greet('Ada') return?", ["Hello, Ada.", "Hello, Ada!", "Hello Ada.", "Hello Ada!"], 0)]),
        ]),
        ST("s2", "main", "Prints both names.", ("def main():", "=main()"), [
            S(("for n in NAMES:", "print(greet"), "Loops over `NAMES`.", [OUT("g_out")], ext=["NAMES"]),
            S(("if __name__", "=main()"), "Runs only when executed directly.", cards=[Recall("Why guard with __name__?", "So importing the module does not run main().")]),
        ]),
    ],
    interview=IV("Small.", ["One point"], [("Any question?", "An answer.")]),
)
CHAPTERS = [C1]
