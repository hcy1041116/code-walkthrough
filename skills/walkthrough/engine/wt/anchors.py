"""Code anchors -> line numbers. Shared by rendering and evidence capture, so both always agree.

Anchor syntax
- 'text'    : the one line containing this text (must occur exactly once in the file)
- '=text'   : the line whose stripped content equals the text exactly
- '...#n'   : the n-th occurrence instead of "exactly once"
- (a, b)    : every line from anchor a to anchor b, inclusive
- [x, y]    : the union of several anchors / ranges
"""
import re


def find(lines: list, anchor: str, where: str = "") -> int:
    nth = None
    m = re.match(r"^(.*)#(\d+)$", anchor)
    if m:
        anchor, nth = m.group(1), int(m.group(2))
    exact = anchor.startswith("=")
    pat = anchor[1:] if exact else anchor
    hits = [i + 1 for i, ln in enumerate(lines) if (ln.strip() == pat if exact else pat in ln)]
    if nth is not None:
        if len(hits) < nth:
            raise ValueError(f"{where}: anchor {anchor!r} occurs only {len(hits)} time(s); '#{nth}' at the end means "
                             f"occurrence number {nth}, so to match text that ends in '#{nth}', add '#1'")
        return hits[nth - 1]
    if len(hits) != 1:
        raise ValueError(f"{where}: anchor {anchor!r} must occur exactly once, found on lines {hits}")
    return hits[0]


def resolve(lines: list, at, where: str = "") -> list:
    if isinstance(at, str):
        return [find(lines, at, where)]
    if isinstance(at, tuple):
        a, b = find(lines, at[0], where), find(lines, at[1], where)
        if b < a:
            raise ValueError(f"{where}: range {at} ends before it starts")
        return list(range(a, b + 1))
    out = []
    for x in at:
        out += resolve(lines, x, where)
    return sorted(set(out))


def ranges(nums: list) -> list:
    """[3, 4, 5, 9] -> ["3–5", "9"]"""
    ls = sorted(set(nums))
    parts, s, p = [], ls[0], ls[0]
    for n in ls[1:] + [None]:
        if n is not None and n == p + 1:
            p = n
            continue
        parts.append(str(s) if s == p else f"{s}–{p}")
        if n is not None:
            s = p = n
    return parts
