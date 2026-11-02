"""Per-line syntax highlighting. Uses Pygments when installed (any language), else Python's tokenizer for
.py files, else plain escaped text. Each source line becomes one HTML string, so lines can be
highlighted and numbered independently even when a token (a docstring) spans several lines."""
import builtins
import html
import io
import keyword
import tokenize

CLASSES = ("kw", "str", "com", "num", "bi")


def highlight(src: str, filename: str = "x.py") -> list:
    lines = _pygments(src, filename)
    if lines is not None:
        return lines
    if filename.endswith(".py"):
        try:
            return _python(src)
        except (tokenize.TokenError, SyntaxError):
            pass
    return [html.escape(ln) for ln in src.split("\n")]


def _pygments(src: str, filename: str):
    """Highlighted lines, or None when Pygments is missing or has no lexer for this file type."""
    try:
        from pygments import lex
        from pygments.lexers import get_lexer_for_filename
        from pygments.token import Comment, Keyword, Name, Number, String
        from pygments.util import ClassNotFound
    except ImportError:
        return None
    try:
        lexer = get_lexer_for_filename(filename, stripnl=False, stripall=False, ensurenl=False)
    except ClassNotFound:
        return None

    def cls(tt):
        if tt in Comment:
            return "com"
        if tt in String:
            return "str"
        if tt in Number:
            return "num"
        if tt in Keyword:
            return "kw"
        if tt in Name.Builtin:
            return "bi"
        return None

    lines, cur = [], ""
    for tt, value in lex(src, lexer):
        c = cls(tt)
        parts = value.split("\n")
        for i, part in enumerate(parts):
            if i:
                lines.append(cur)
                cur = ""
            if part:
                cur += f'<em class="{c}">{html.escape(part)}</em>' if c else html.escape(part)
    lines.append(cur)
    n = len(src.split("\n"))
    return (lines + [""] * n)[:n]


_BUILTINS = set(dir(builtins)) - {"copyright", "credits", "license", "exit", "quit"}
_FS = {getattr(tokenize, n) for n in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END") if hasattr(tokenize, n)}


def _python(src: str) -> list:
    lines = src.split("\n")
    marks = {i: [] for i in range(1, len(lines) + 2)}
    depth, fstart = 0, None

    def mark(sr, sc, er, ec, c):
        if sr == er:
            marks[sr].append((sc, ec, c))
            return
        marks[sr].append((sc, len(lines[sr - 1]), c))
        for r in range(sr + 1, er):
            marks[r].append((0, len(lines[r - 1]), c))
        marks[er].append((0, ec, c))

    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        tt, s, (sr, sc), (er, ec), _ = tok
        if hasattr(tokenize, "FSTRING_START") and tt == tokenize.FSTRING_START:
            if depth == 0:
                fstart = (sr, sc)
            depth += 1
            continue
        if hasattr(tokenize, "FSTRING_END") and tt == tokenize.FSTRING_END:
            depth -= 1
            if depth == 0:
                mark(fstart[0], fstart[1], er, ec, "str")
            continue
        if depth > 0 or tt in _FS:
            continue
        c = None
        if tt == tokenize.COMMENT:
            c = "com"
        elif tt == tokenize.STRING:
            c = "str"
        elif tt == tokenize.NUMBER:
            c = "num"
        elif tt == tokenize.NAME:
            c = "kw" if keyword.iskeyword(s) else ("bi" if s in _BUILTINS else None)
        if c:
            mark(sr, sc, er, ec, c)
    out = []
    for i, ln in enumerate(lines, start=1):
        pos, h = 0, ""
        for a, b, c in sorted(marks[i]):
            if a < pos:
                continue
            h += html.escape(ln[pos:a]) + f'<em class="{c}">' + html.escape(ln[a:b]) + "</em>"
            pos = b
        out.append(h + html.escape(ln[pos:]))
    return out
