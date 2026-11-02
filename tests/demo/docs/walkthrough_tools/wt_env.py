import os
import sys

ENGINE = os.environ["WT_ENGINE"]
if ENGINE not in sys.path:
    sys.path.insert(0, ENGINE)
