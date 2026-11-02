# Evidence: frontend

For web UIs (React, Vue, Svelte, plain JS): the evidence is what the screen, the DOM, the state and the network looked like at each step.

## Run the UI

- Build and serve the app locally (`npm run dev` / `npm run build && npm run preview`) on a scratch port, against a mock or scratch backend.
- Drive it with a headless browser. Playwright (Python or Node) is the most capable: navigate, click, type, wait, screenshot, read the DOM, record network requests. Without it, Chromium's headless shell can still screenshot a static state: `chrome-headless-shell --headless --screenshot=out.png --window-size=1280,900 --virtual-time-budget=5000 URL`; inject a small script into a copy of the page to reach a state (click, type) before the shot.

## What to capture per step

- A screenshot of the state the code produces (`IMG` block). Save PNGs under the tools folder (`data/shots/...`); keep each under ~300 KB (crop to the component, 1x scale) because they are embedded in the page.
- The DOM fragment the component rendered (`OUT`), trimmed to the part the text discusses.
- State before and after an interaction: props, store / reducer state, URL. Log it from a test harness (Vitest / Jest rendering the component, or `page.evaluate` in Playwright) and save it as `KV`.
- Network: the request the UI sent and the response it rendered (Playwright `page.on("request")`, or the dev server's proxy log).
- Pure logic (reducers, hooks, formatters, validation): run it under Node or the test runner and capture inputs and outputs, like data scripts.

## Also capture

- Loading, empty and error states, not only the happy path.
- Responsive behaviour when the code handles it: the same component at 390 px and 1280 px.
- Accessibility facts the code is responsible for (labels, focus order) when a segment explains them.
