"""示範教材的內容：report.py 一章。寫法見 skill 的 references/content.md。"""
import wt_env  # noqa: F401
from wt.content import CH, IV, KV, OUT, ST, Choice, Cloze, Recall, S, T

C1 = CH(
    "c1", "report.py", "每月營收報表",
    intro=[
        "這支程式把訂單和客戶資料合併，算出每個月、每個客戶等級的營收、訂單數和平均客單價，存成 monthly_report.csv。",
        "資料是虛構的：12 筆訂單、5 位客戶。其中訂單 1009 的客戶 C09 不在客戶表裡，這是報表程式最常見的陷阱之一，第 3 步會看到它差點讓 400 元從報表消失。",
    ],
    steps=[
        ST("s1", "讀進資料", "報表的原料：訂單和客戶兩張表。", ('"""每月營收', "customers = pd.read_csv"), [
            S(('"""每月營收', "import pandas as pd"),
              "第一行是 docstring，說明這支程式做什麼。`import pandas as pd` 是慣例的簡寫，之後都用 `pd.` 開頭呼叫 pandas。",
              tags=["語法：import 別名"], ext=["pd."]),
            S(("orders = pd.read_csv", "customers = pd.read_csv"),
              "`read_csv` 讀進 CSV 變成 DataFrame。`parse_dates=[\"date\"]` 讓 date 欄直接變成日期型別（`datetime64`），"
              "不然它只是一串文字，後面就不能取月份。下面是實際讀進來的樣子和每欄的型別。",
              [T("orders_head", "orders 的前 5 筆"), KV("orders_dtypes", "orders 每欄的型別"), T("customers", "customers")],
              tags=["語法：parse_dates"], ext=["datetime64"],
              cards=[Cloze("orders = pd.read_csv", 'parse_dates=["date"]', why="讀檔時就把 date 欄轉成日期型別，後面才能用 .dt 取月份。",
                           also=["parse_dates=['date']"])]),
        ]),
        ST("s2", "合併客戶資料", "訂單只有客戶編號，等級在客戶表裡，要合併才能按等級彙總。", "df = orders.merge(", [
            S("df = orders.merge(",
              "`merge` 像 SQL 的 JOIN：用 `on=\"customer_id\"` 對齊兩張表。`how=\"left\"` 是 left join，**每一筆訂單都保留**，"
              "客戶表裡找不到的客戶，等級和城市就是 NaN（下表訂單 1009）。如果用預設的 inner join，這筆訂單會直接消失。",
              [KV("merge_shape", "合併前後的列數"), T("merge_rows", "客戶 C01 和 C09 的訂單")],
              tags=["語法：merge", "概念：left join"],
              cards=[Cloze("df = orders.merge(", 'how="left"', why="left join：每筆訂單都保留，找不到客戶的欄位是 NaN。", also=["how='left'"]),
                     Choice("訂單併客戶表時，為什麼用 how=\"left\" 而不是預設的 inner？",
                            ["客戶表裡沒有的訂單也要留在報表裡", "left join 的速度比 inner join 快", "inner join 會讓訂單重複出現", "pandas 規定 merge 一定要寫 how"], 0,
                            why="營收報表不能漏掉訂單；inner join 會把找不到客戶的訂單丟掉。")]),
            S("df = orders.merge(",
              "`validate=\"many_to_one\"` 是一道保險：宣告「很多訂單對到一位客戶」。如果客戶表裡同一個編號出現兩次，合併後訂單會被複製、營收會算兩次；"
              "加了 validate，pandas 會直接報錯，而不是默默算錯。下面是故意把一位客戶重複一次的結果。",
              [OUT("merge_validate", "客戶表有重複時（另外跑的）")],
              tags=["設計選擇：validate 讓錯誤大聲出現"],
              cards=[Recall("merge 的 validate=\"many_to_one\" 防的是什麼？",
                            "防右邊那張表（客戶表）的鍵重複。重複的話每筆訂單會被複製、營收被重算；加了 validate，pandas 直接報錯，不會默默算錯。")]),
        ]),
        ST("s3", "補上沒建檔的客戶", "上一步留下的 NaN，如果不處理，會在彙總時默默消失。", 'df["tier"] = df["tier"].fillna(', [
            S('df["tier"] = df["tier"].fillna(',
              "**注意：** `groupby` 預設會丟掉分組欄是 NaN 的列。如果不補值，訂單 1009 的 400 元雖然在 left join 時保住了，彙總時還是會從報表消失，"
              "而且不會有任何警告（下表第二列）。`fillna(\"未建檔\")` 把空的等級補成一個看得見的類別，報表總和才和訂單總和一致。",
              [T("fill_rows", "補值之後的訂單 1009"), T("dropna", "三種總和")],
              tags=["注意：groupby 預設丟掉 NaN"], ext=["groupby"],
              cards=[Choice("left join 後 tier 是 NaN 的訂單，直接 groupby(\"tier\") 會怎樣？",
                            ["整筆被丟掉，營收總和變少", "自成一組，標成 NaN", "pandas 報錯，要求先補值", "被併到第一個等級的營收裡"], 0,
                            why="groupby 預設 dropna=True：分組欄是 NaN 的列不會出現在結果裡。")]),
        ]),
        ST("s4", "取出月份", "報表按月彙總，需要一個「年-月」欄。", 'df["month"] = ', [
            S('df["month"] = ',
              "這一行是**方法串接**：每個點接著處理前一步的結果。`.dt` 是日期欄專用的工具箱，`.to_period(\"M\")` 把日期變成「哪一個月」，"
              "`.astype(str)` 再轉成 2026-01 這種文字，存檔和排序都方便。下表是串到每一步時，第一筆的值和型別。",
              [T("chain", "一步一步串（另外跑的）"), T("month", "新增的 month 欄")],
              tags=["語法：方法串接", "語法：.dt 存取日期"],
              cards=[Cloze('df["month"] = ', 'to_period("M")', why="把日期變成「哪一個月」（Period），再轉文字。", also=["to_period('M')"])]),
        ]),
        ST("s5", "每月、每個等級彙總", "報表的核心：分組、加總、算平均。", ("report = (", 'report["avg_order"]'), [
            S(("report = (", "=)"),
              "整段用括號包起來，方法串接就可以分行寫，一行一個動作。`groupby([\"month\", \"tier\"], as_index=False)` 按月份和等級分組；"
              "`as_index=False` 讓分組欄留在一般的欄位，而不是變成 index，存 CSV 時才會有 month 和 tier 兩欄。\n\n"
              "`.agg(revenue=(\"amount\", \"sum\"), ...)` 是**具名彙總**：新欄名 = (哪一欄, 怎麼算)。一次算出營收和訂單數，欄名也直接取好。",
              [T("report_agg", "彙總結果")],
              tags=["語法：groupby", "語法：具名彙總"],
              cards=[Cloze("df.groupby([", "as_index=False", why="分組欄留在一般欄位，不變成 index。"),
                     Cloze(".agg(revenue=", '("amount", "sum")', why="具名彙總：新欄名 = (來源欄, 彙總方式)。", also=["('amount', 'sum')"])]),
            S('report["avg_order"]',
              "平均客單價 = 營收 ÷ 訂單數，兩欄直接相除，pandas 會一列一列對齊計算；`round(1)` 取到小數一位。最後核對：報表的營收總和等於所有訂單金額的總和。",
              [T("report", "最後的報表"), KV("totals", "核對總和")],
              cards=[Recall("怎麼確認這份報表沒有漏掉或重複算訂單？",
                            "把報表的 revenue 加總，和原始訂單的 amount 總和比較；一樣才代表合併和分組沒有丟掉或複製任何一筆。")]),
        ]),
        ST("s6", "直接執行時才輸出", "被別的程式 import 時，不該自動寫檔。", ('if __name__ == "__main__":', "print(report.to_string"), [
            S(('if __name__ == "__main__":', "print(report.to_string"),
              "`if __name__ == \"__main__\":` 底下的程式只有「直接執行這個檔案」時才會跑；被別的程式 import 時不會寫檔、不會印東西。"
              "`to_csv(..., index=False)` 不把 0、1、2 這種列編號寫進檔案。",
              [OUT("main_out", "python report.py 印出的內容"), OUT("main_csv", "monthly_report.csv 的前三行")],
              tags=["語法：__name__ 守衛"],
              cards=[Recall("if __name__ == \"__main__\" 有什麼用？",
                            "只有直接執行這個檔案時才跑底下的程式；被 import 時（例如測試或別的程式要用 report）不會寫檔或印東西。")]),
        ]),
    ],
    interview=IV(
        "這支程式把訂單併上客戶等級，產出每月、每個等級的營收報表。兩個重點：用 left join 加 validate 確保訂單不漏也不重複，"
        "以及把找不到客戶的訂單補成「未建檔」，避免 groupby 默默丟掉 NaN；最後用總和核對報表和原始訂單一致。",
        ["<strong>left join</strong>：每筆訂單都保留",
         "<strong>validate=\"many_to_one\"</strong>：客戶表重複時直接報錯，不會重複計算",
         "<strong>fillna(\"未建檔\")</strong>：沒補值的話，400 元會從報表消失",
         "<strong>總和核對</strong>：報表營收 11,500 = 訂單金額 11,500"],
        [("為什麼不在 groupby 加 dropna=False 就好？",
          "也可以，但分組會出現 NaN 這個看不懂的類別；補成「未建檔」更清楚，讀報表的人也知道要去補客戶資料。"),
         ("資料量變大時要注意什麼？",
          "邏輯不變；要注意的是讀檔時指定欄位型別、只讀需要的欄，以及客戶表的重複檢查（validate 會變慢，但能擋下最貴的錯誤）。")],
    ),
)

CHAPTERS = [C1]
