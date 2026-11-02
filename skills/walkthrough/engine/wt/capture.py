"""Evidence capture: run the project's real code segment by segment and save what the data looks like.

A capture script lives in the project's tools folder and starts like this:

    import wt_env  # noqa: F401  (puts this engine on sys.path)
    from wt.capture import Workspace, fv, tbl

    ws = Workspace(__file__)
    os.chdir(ws.run_dir("train", ["train.csv"]))   # scratch folder; project files stay untouched
    R = ws.runner("train_and_save.py")
    R.run("df = pd.read_csv", "print(df.shape)")   # execute those real lines
    O = {"tr_head": tbl(R["df"], 3)}
    ws.save("cap_train.json", O)
"""
import contextlib
import importlib.util
import io
import json
import math
import os
import sys
import textwrap
import time

from . import anchors

try:  # pandas is optional: frontend / backend projects may capture plain strings and dicts
    import numpy as np
    import pandas as pd
except ImportError:  # pragma: no cover
    np = pd = None


_LOADED = set()  # modules imported by the last project.py, dropped before loading the next one


def load_project(tools_dir: str):
    """Import the tools folder's project.py (the walkthrough's configuration) and the content it imports."""
    for name in _LOADED:
        sys.modules.pop(name, None)
    before = set(sys.modules)
    path = os.path.join(tools_dir, "project.py")
    spec = importlib.util.spec_from_file_location("wt_project", path)
    mod = importlib.util.module_from_spec(spec)
    tools = os.path.abspath(tools_dir)
    if tools in sys.path:
        sys.path.remove(tools)
    sys.path.insert(0, tools)
    spec.loader.exec_module(mod)
    _LOADED.clear()
    _LOADED.update(n for n in set(sys.modules) - before
                   if os.path.abspath(getattr(sys.modules[n], "__file__", "") or "").startswith(tools + os.sep))
    mod.TOOLS = os.path.abspath(tools_dir)
    mod.REPO = os.path.abspath(os.path.join(tools_dir, getattr(mod, "REPO", "../..")))
    return mod


class Workspace:
    """Paths for one walkthrough: the repo, the tools folder, captured data and scratch run folders."""

    def __init__(self, script_file: str):
        self.tools = os.path.dirname(os.path.abspath(script_file))
        self.project = load_project(self.tools)
        self.repo = self.project.REPO
        self.data = os.path.join(self.tools, "data")
        os.makedirs(self.data, exist_ok=True)
        if self.repo not in sys.path:
            sys.path.insert(0, self.repo)  # capture scripts can import the project's own modules

    def run_dir(self, name: str, links=()) -> str:
        """Create runs/<name> and symlink the project files it needs, so outputs never overwrite the repo."""
        d = os.path.join(self.tools, "runs", name)
        os.makedirs(d, exist_ok=True)
        for f in links:
            dst = os.path.join(d, f)
            if not os.path.lexists(dst):
                os.symlink(os.path.join(self.repo, f), dst)
        return d

    def runner(self, relpath: str) -> "Runner":
        return Runner(os.path.join(self.repo, relpath))

    def save(self, name: str, data: dict) -> None:
        path = os.path.join(self.data, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("saved", path, len(data), "keys")


class Runner:
    """Executes ranges of a real source file in one shared namespace."""

    def __init__(self, path: str):
        self.path = path
        with open(path, encoding="utf-8") as f:
            self.lines = f.read().split("\n")
        self.ns = {"__name__": "walkthrough"}

    def run(self, start, end=None, dedent=False) -> str:
        """Run the source from anchor `start` to anchor `end` (or just the `start` line); return stdout.

        Use dedent=True for lines inside a function body; bind its parameters first via R.ns.update(...).
        """
        nums = anchors.resolve(self.lines, (start, end) if end is not None else start, os.path.basename(self.path))
        a, b = nums[0], nums[-1]
        code = "\n".join(self.lines[a - 1:b])
        if dedent:
            code = textwrap.dedent(code)
        buf = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            exec(compile(code, f"{self.path}:{a}-{b}", "exec"), self.ns)  # noqa: S102  (running the project's own source is the point)
        print(f"  ran {os.path.basename(self.path)}:{a}-{b} ({time.time() - t0:.1f}s)", flush=True)
        return buf.getvalue()

    def __getitem__(self, k):
        return self.ns[k]


def _is_float(v):
    return isinstance(v, float) or (np is not None and isinstance(v, np.floating))


def fv(v, nd: int = 4) -> str:
    """One value -> display string, the way pandas would print it."""
    if v is None:
        return "None"
    if pd is not None and v is pd.NA:
        return "<NA>"
    if isinstance(v, bool) or (np is not None and isinstance(v, np.bool_)):
        return str(bool(v))
    if isinstance(v, int) or (np is not None and isinstance(v, np.integer)):
        return str(int(v))
    if _is_float(v):
        v = float(v)
        if math.isnan(v):
            return "NaN"
        if v == int(v) and abs(v) < 1e12:
            return f"{v:.1f}"
        s = f"{round(v, nd):.{nd}f}".rstrip("0").rstrip(".")
        return s if s not in ("0", "-0", "") else "0.0"
    return str(v)


def col_fmt(vals: list, nd: int) -> list:
    """Floats in one column share the same number of decimals, like pandas."""
    fl = [float(v) for v in vals if _is_float(v) and not math.isnan(float(v))]
    if not fl:
        return [fv(v, nd) for v in vals]
    dec = 1
    for v in fl:
        s = f"{round(v, nd):.{nd}f}".rstrip("0")
        dec = max(dec, len(s.split(".")[1]) if "." in s else 0)
    out = []
    for v in vals:
        if _is_float(v) and not math.isnan(float(v)):
            s = f"{float(v):.{dec}f}"
            out.append(s[1:] if s.startswith("-") and float(s) == 0 else s)
        else:
            out.append(fv(v, nd))
    return out


def tbl(obj, n=None, index=True, nd=4, index_name=None) -> dict:
    """DataFrame / Series -> {'cols': [...], 'rows': [[...]]}, ready to embed."""
    if pd is None:
        raise ImportError("tbl() needs pandas; for plain lists use rows(records, cols)")
    df = obj.to_frame() if isinstance(obj, pd.Series) else obj
    if n is not None:
        df = df.head(n)
    cols = [str(c) for c in df.columns]
    data = [col_fmt(list(df.iloc[:, j]), nd) for j in range(df.shape[1])]
    if index:
        name = index_name if index_name is not None else (str(df.index.name) if df.index.name is not None else "")
        cols = [name] + cols
        data = [col_fmt(list(df.index), nd)] + data
    rows = [list(r) for r in zip(*data)] if data else []
    return {"cols": cols, "rows": rows}


def rows(records: list, cols: list) -> dict:
    """Plain list of rows -> table, for projects without pandas (API responses, DOM states, ...)."""
    return {"cols": list(cols), "rows": [[fv(v) for v in r] for r in records]}
