"""Command line for the walkthrough engine.

    python run.py new <tools_dir>        scaffold a walkthrough tools folder in a project
    python run.py capture <tools_dir>    run the capture scripts listed in project.CAPTURES (with this Python)
    python run.py render <tools_dir>     build the page + review deck, refresh the review hub
    python run.py verify <tools_dir>     self-check (exit code 1 on problems); add --list for the segment map
    python run.py hub                    rebuild ~/learning/hub from all decks
    python run.py init-learning          create ~/learning (profile, glossary, hub) if missing

Run it with the project's own Python (its virtualenv), so capture scripts can import the project's packages.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from wt import hub, render, verify
from wt.capture import load_project

SKILL = os.path.dirname(HERE)


def learning() -> str:
    return render.learning_dir()


def cmd_new(tools: str):
    os.makedirs(os.path.join(tools, "data"), exist_ok=True)
    src = os.path.join(HERE, "wt", "templates", "scaffold")
    for name in sorted(os.listdir(src)):
        dst = os.path.join(tools, name)
        if os.path.exists(dst):
            print("keep", dst)
            continue
        shutil.copy(os.path.join(src, name), dst)
        print("new ", dst)
    print("Next: edit project.py, write cap_*.py and content.py, then capture -> render -> verify.")


def cmd_capture(tools: str, names: list):
    P = load_project(tools)
    for name in names or P.CAPTURES:
        print(f"== {name}")
        r = subprocess.run([sys.executable, "-W", "error::FutureWarning", "-W", "error::RuntimeWarning", os.path.join(P.TOOLS, name)], cwd=P.TOOLS, check=False)
        if r.returncode:
            sys.exit(f"capture failed: {name}")


def cmd_init_learning():
    root = learning()
    os.makedirs(os.path.join(root, "decks"), exist_ok=True)
    for name in ("PROFILE.md", "GLOSSARY.md"):
        dst = os.path.join(root, name)
        if not os.path.exists(dst):
            shutil.copy(os.path.join(SKILL, "templates", "learning", name), dst)
            print("new ", dst)
    hub.build(root)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "new":
        cmd_new(rest[0])
    elif cmd == "capture":
        cmd_capture(rest[0], rest[1:])
    elif cmd == "render":
        render.render(rest[0])
    elif cmd == "verify":
        return verify.verify(rest[0], listing="--list" in rest)
    elif cmd == "hub":
        hub.build(learning())
    elif cmd == "init-learning":
        cmd_init_learning()
    else:
        print(f"unknown command {cmd!r}\n{__doc__}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
