"""Puts the walkthrough skill's engine on sys.path. Override the location with WT_ENGINE=/path/to/engine."""
import os
import sys

ENGINE = os.environ.get("WT_ENGINE", os.path.expanduser("~/.claude/skills/walkthrough/engine"))
if ENGINE not in sys.path:
    sys.path.insert(0, ENGINE)
