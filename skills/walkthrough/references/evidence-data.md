# Evidence: data and Python scripts

For pandas / scikit-learn / ETL / notebook-style scripts: the evidence is what the DataFrame, the variables and the printed output look like right after each segment runs.

## Capture script shape

```python
import os
import wt_env  # noqa: F401
from wt.capture import Workspace, fv, tbl

ws = Workspace(__file__)
os.chdir(ws.run_dir("train", ["train.csv", "model.joblib"]))   # scratch folder, project files symlinked
R = ws.runner("train_and_save.py")
O = {}
R.run('"""Train', 'DATA_PATH = ')                 # module header: imports and constants
R.run("def make_model()", "=return labels")      # define functions (a def only defines)
out = R.run("df = pd.read_csv(DATA_PATH)", 'print("raw", df.shape)', dedent=True)   # lines of main()
O["tr_raw_print"] = out.strip()
O["tr_head"] = tbl(R["df"], 3)
ws.save("cap_train.json", O)
```

- `R.run(start, end)` executes those real lines in one shared namespace and returns stdout. Lines inside a function body need `dedent=True`, with the function's parameters bound first: `R.ns.update(d=df)`.
- To show the state *inside* a function, run its body line ranges one after another instead of calling it.
- Calling the real function (`R["engineer"](df)`) is also real evidence when the intermediate states are not needed.
- Prefix keys per chapter (`fe_`, `tr_`, `pg_`...) so chapters never collide.

## What to capture

- `df.head(3)` after each transformation that changes it; `.shape` and `.dtypes` when they change.
- Values the text interprets: rates, medians, AUC, fold scores, counts per group.
- Small demonstrations on toy inputs for behaviour the full data cannot show (a coerce on a blank string, an unknown category raising), titled as small examples.
- Before/after pairs for every audit finding: the old code extracted from git (`git show HEAD:file.py`, then `ast` to pull out one function) next to the fixed version on the same input.
- Statistical framing the learner knows: AUC checked against Mann-Whitney U, calibration by deciles plus Brier score, cross-validation fold scores, in-sample vs out-of-sample comparisons. These are extra analyses: label them.
- Reproducibility: compare regenerated artifacts with the repo's (model predictions, CSV bytes) and show the result.

## Formatting

`tbl(df, n, nd=4)` gives each float column one number of decimals, like pandas; `fv(value)` formats one value; `rows(records, cols)` builds a table without pandas.

## Databases and services

Run them in throwaway containers on a non-default port, point the script at them through its own configuration (environment variables), write, read back with SQL, and remove the container afterwards:

```bash
docker run -d --rm --name wt-pg -e POSTGRES_PASSWORD=wt -e POSTGRES_DB=wt -p 55432:5432 postgres:16-alpine
until pg_isready -h localhost -p 55432; do sleep 1; done
# ... capture ...
docker stop wt-pg     # --rm removes it
```

Mask passwords in anything you save.

## Hygiene

Run captures with warnings as errors (`-W error::FutureWarning -W error::RuntimeWarning`, which `run.py capture` does for FutureWarning) and fix the code, not the warning filter. Outputs go to `runs/`; compare them with the project's files rather than overwriting them.
