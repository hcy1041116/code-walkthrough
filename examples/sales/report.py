"""每月營收報表：訂單併上客戶等級，算出每個月、每個等級的營收、訂單數和平均客單價。"""
import pandas as pd

orders = pd.read_csv("data/orders.csv", parse_dates=["date"])
customers = pd.read_csv("data/customers.csv")

df = orders.merge(customers, on="customer_id", how="left", validate="many_to_one")
df["tier"] = df["tier"].fillna("未建檔")  # 客戶表裡沒有的客戶：留下來，不讓 groupby 默默丟掉
df["month"] = df["date"].dt.to_period("M").astype(str)

report = (
    df.groupby(["month", "tier"], as_index=False)
    .agg(revenue=("amount", "sum"), orders=("order_id", "count"))
)
report["avg_order"] = (report["revenue"] / report["orders"]).round(1)

if __name__ == "__main__":
    report.to_csv("monthly_report.csv", index=False)
    print(report.to_string(index=False))
