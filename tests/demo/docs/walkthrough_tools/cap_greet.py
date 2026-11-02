import os
import platform

import wt_env  # noqa: F401
from wt.capture import Workspace

ws = Workspace(__file__)
os.chdir(ws.run_dir("greet"))
R = ws.runner("src/greet.py")
R.run("NAMES = [", 'return text + ("!"')
O = {"g_python": platform.python_version(), "g_call": {"greet('Ada')": R["greet"]("Ada")}}
R.ns.update(name="Lin", excited=True)
R.run('text = f"Hello', 'text = f"Hello', dedent=True)
O["g_text"] = {"text": R["text"]}
R.run("def main():", "print(greet")
O["g_out"] = R.run("=main()", dedent=True).strip()
ws.save("cap_greet.json", O)
