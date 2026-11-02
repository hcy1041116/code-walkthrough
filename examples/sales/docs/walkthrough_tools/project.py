"""示範教材的設定（examples/sales）。路徑相對於這個資料夾。"""
import wt_env  # noqa: F401  (puts the engine on sys.path)
from content import CHAPTERS  # noqa: F401

PROJECT = "demo-sales"
LANG = "zh-TW"
REPO = "../.."
OUT = "docs/walkthrough.html"
CAPTURES = ["cap_report.py"]

TITLE = "示範：每月營收報表"
KICKER = "程式逐行講解（示範）"
LEAD = ("<p>用 code-walkthrough skill 產生的示範教材：一支 18 行的 pandas 報表程式，資料是虛構的 12 筆訂單。"
        "每一步上面是程式，按「下一段」會標出正在講的那幾行，下面是白話說明，以及<strong>實際執行到那裡時</strong>資料的樣子。</p>")
FLOW = [{"num": "1", "label": "report.py", "href": "#c1", "in": "orders.csv + customers.csv", "out": "monthly_report.csv"}]


def ENV(O):
    return (f"表格都是實際執行 report.py 取得的（Python {O['py']}、pandas {O['pd']}；訂單 12 筆、客戶 5 位，都是虛構資料）。"
            "程式在暫存資料夾執行，不會覆蓋專案檔。標「另外跑的」是為了說明而額外做的檢查。說明開頭的「第 X–Y 行」由標示的行號自動產生。")
