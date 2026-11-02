"""Screenshots and GIFs of the sales example for the README (docs/images/).

    uv run --with pygments --with pandas --with pillow python examples/make_readme_images.py

Builds the example walkthrough with a scratch learning folder (your ~/learning is not touched), then drives the page
and the review hub in a headless Chromium (Playwright's chrome-headless-shell, or WT_CHROME) and saves the frames.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, "skills", "walkthrough", "engine", "run.py")
TOOLS = os.path.join(ROOT, "examples", "sales", "docs", "walkthrough_tools")
PAGE = os.path.join(ROOT, "examples", "sales", "docs", "walkthrough.html")
OUT = os.path.join(ROOT, "docs", "images")
SCRATCH = tempfile.mkdtemp(prefix="wt-images-")
LEARNING = os.path.join(SCRATCH, "learning")
CHROME = os.environ.get("WT_CHROME") or max(glob.glob(os.path.expanduser(
    "~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell")))


def build():
    env = {**os.environ, "WT_LEARNING": LEARNING}
    for cmd in ("capture", "render", "verify"):
        subprocess.run([sys.executable, RUN, cmd, TOOLS], env=env, check=True, stdout=subprocess.DEVNULL)


def shoot(html, name, size, before="", after=""):
    """Copy a page with scripts injected before and after its own, screenshot it, return the PNG path."""
    page = os.path.join(os.path.dirname(html), f"_{name}.html")
    with open(html, encoding="utf-8") as f:
        text = f.read()
    text = text.replace("<head>", f"<head><script>{before}</script>", 1).replace("</body>", f"<script>{after}</script></body>")
    with open(page, "w", encoding="utf-8") as f:
        f.write(text)
    png = os.path.join(SCRATCH, f"{name}.png")
    subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=4000",
                    f"--window-size={size[0]},{size[1]}", f"--screenshot={png}", "file://" + page],
                   check=True, capture_output=True, timeout=60)
    os.remove(page)
    return png


def step_view(step, clicks=0):
    """Show one step at the top of the page (headless screenshots do not repaint after scrolling)."""
    return (f"setTimeout(function(){{var el=document.getElementById('{step}'),nx=el.querySelector('.next');"
            f"for(var i=0;i<{clicks};i++)nx.click();var m=document.querySelector('main')||document.body;m.insertBefore(el,m.firstChild);}},300);")


def gif(pngs, name, ms):
    frames = [Image.open(p).convert("RGB") for p in pngs]
    palette = frames[0].quantize(colors=200, method=Image.Quantize.MEDIANCUT)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    path = os.path.join(OUT, name)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=True)
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    build()
    light = "localStorage.setItem('walkthrough-theme','light');"
    dark = "localStorage.setItem('walkthrough-theme','dark');"
    size = (1100, 820)
    seq = [("c1-s1", 1), ("c1-s2", 0), ("c1-s3", 0), ("c1-s4", 0), ("c1-s5", 0), ("c1-s5", 1)]
    pngs = [shoot(PAGE, f"page{i}", size, light, step_view(s, k)) for i, (s, k) in enumerate(seq)]
    made = [gif(pngs, "walkthrough.gif", [2200] * len(pngs))]
    shutil.copy(shoot(PAGE, "mobile", (390, 844), dark, step_view("c1-s3")), os.path.join(OUT, "walkthrough-mobile-dark.png"))
    made.append(os.path.join(OUT, "walkthrough-mobile-dark.png"))

    hub = os.path.join(LEARNING, "hub", "index.html")
    with open(os.path.join(LEARNING, "decks", "demo-sales.json"), encoding="utf-8") as f:
        cards = json.load(f)["cards"]
    cloze = next(c["id"] for c in cards if c["type"] == "cloze" and c["answer"] == 'how="left"')
    choice = next(c["id"] for c in cards if c["type"] == "choice" and "NaN" in c["q"])
    today = "var d=new Date(),p=function(n){return (n<10?'0':'')+n;},today=d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());"

    def store(due, progress=False):
        st = {c["id"]: {"b": 1 + i % 5, "r": 2, "l": 0, "d": "2000-01-01" if i % 3 == 0 else "2099-01-01", "s": "2026-01-01"}
              for i, c in enumerate(cards[:8])} if progress else {}
        st.update({cid: {"b": 3, "r": 2, "l": 0, "d": "2000-01-01", "s": "2026-01-01"} for cid in due})
        return today + (f"localStorage.setItem('wt-review-v1',JSON.stringify({{cards:{json.dumps(st)},"
                        f"meta:{{day:today,newToday:0}},settings:{{newPerDay:{20 if progress else 0}}}}}));")

    start = "document.getElementById('start').click();"
    typed = lambda v: start + f"document.getElementById('ans').value={json.dumps(v)};"
    hub_size = (900, 600)
    pngs = [shoot(hub, "hub0", hub_size, store([cloze]), start),
            shoot(hub, "hub1", hub_size, store([cloze]), typed('how="le')),
            shoot(hub, "hub2", hub_size, store([cloze]), typed('how="left"')),
            shoot(hub, "hub3", hub_size, store([cloze]), typed('how="left"') + "document.getElementById('check').click();"),
            shoot(hub, "hub4", hub_size, store([choice]), start),
            shoot(hub, "hub5", hub_size, store([choice]), start + "Array.from(document.querySelectorAll('.opt'))"
                  ".find(function(b){return b.textContent.indexOf('NaN')>=0;}).click();")]
    made.append(gif(pngs, "review.gif", [1800, 700, 1200, 2600, 1800, 2600]))
    shutil.copy(shoot(hub, "home", (900, 700), store([], progress=True)), os.path.join(OUT, "review-home.png"))
    made.append(os.path.join(OUT, "review-home.png"))
    for p in made:
        print(f"{os.path.relpath(p, ROOT)}  {os.path.getsize(p) / 1024:.0f} KB")
    shutil.rmtree(SCRATCH)


if __name__ == "__main__":
    main()
