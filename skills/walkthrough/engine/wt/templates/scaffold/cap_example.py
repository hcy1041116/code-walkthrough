"""Capture evidence for chapter 1: run the real lines and save what the data looks like."""
import os

import wt_env  # noqa: F401
from wt.capture import Workspace

ws = Workspace(__file__)
os.chdir(ws.run_dir("example", []))    # scratch folder; list the project files it needs as symlinks
R = ws.runner("main.py")
O = {}
R.run("def main(", "=return result")   # running a def only defines main() ...
O["ex_result"] = repr(R["main"]())     # ... so call it and record what it returns
ws.save("cap_example.json", O)
