"""report.py 的證據：一段一段執行真實程式，存下每一步資料的樣子。"""
import os
import platform

import pandas as pd
import wt_env  # noqa: F401
from wt.capture import Workspace, rows, tbl

ws = Workspace(__file__)
os.chdir(ws.run_dir("report", ["data/orders.csv", "data/customers.csv"]))
R = ws.runner("report.py")
O = {"py": platform.python_version(), "pd": pd.__version__}

R.run('"""每月營收', "import pandas as pd")
R.run("orders = pd.read_csv", "customers = pd.read_csv")
orders, customers = R["orders"], R["customers"]
O["orders_head"] = tbl(orders, 5, index=False)
O["orders_dtypes"] = {c: str(t) for c, t in orders.dtypes.items()}
O["customers"] = tbl(customers, index=False)

R.run("df = orders.merge(")
df = R["df"]
O["merge_shape"] = {"orders": f"{len(orders)} 列", "合併後的 df": f"{len(df)} 列"}
O["merge_rows"] = tbl(df[df["customer_id"].isin(["C01", "C09"])], index=False)
try:  # extra: what validate does when the customer table has a duplicate
    orders.merge(pd.concat([customers, customers.iloc[[0]]]), on="customer_id", how="left", validate="many_to_one")
except pd.errors.MergeError as e:
    O["merge_validate"] = f"MergeError: {str(e).splitlines()[0]}"

raw = orders.merge(customers, on="customer_id", how="left")  # extra: the same data without the fillna line
R.run('df["tier"] = df["tier"].fillna(')
O["fill_rows"] = tbl(R["df"].loc[R["df"]["customer_id"] == "C09", ["order_id", "customer_id", "amount", "tier"]], index=False)
O["dropna"] = rows([["訂單金額總和", int(orders["amount"].sum())],
                    ["沒補值就 groupby 的營收總和（另外跑的）", int(raw.groupby("tier")["amount"].sum().sum())],
                    ["補成「未建檔」後 groupby 的營收總和", int(R["df"].groupby("tier")["amount"].sum().sum())]],
                   ["", "金額"])

R.run('df["month"] = ')
O["month"] = tbl(R["df"][["date", "month"]], 3, index=False)
d = R["df"]["date"].head(1)
O["chain"] = rows([['df["date"]', repr(d.iloc[0]), str(d.dtype)],
                   ['.dt.to_period("M")', repr(d.dt.to_period("M").iloc[0]), str(d.dt.to_period("M").dtype)],
                   [".astype(str)", repr(d.dt.to_period("M").astype(str).iloc[0]), str(d.dt.to_period("M").astype(str).dtype)]],
                  ["串到哪一步", "第一筆的值", "型別"])

R.run("report = (", "=)")
O["report_agg"] = tbl(R["report"], index=False)
R.run('report["avg_order"]')
O["report"] = tbl(R["report"], index=False)
O["totals"] = {"訂單金額總和": int(orders["amount"].sum()), "報表 revenue 總和": int(R["report"]["revenue"].sum())}

O["main_out"] = R.run('report.to_csv("monthly_report.csv"', "print(report.to_string", dedent=True).rstrip()
with open("monthly_report.csv", encoding="utf-8") as f:
    O["main_csv"] = "".join(f.readlines()[:3]).rstrip()
ws.save("cap_report.json", O)
