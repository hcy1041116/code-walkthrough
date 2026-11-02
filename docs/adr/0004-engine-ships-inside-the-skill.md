# 引擎放在 skill 資料夾裡，不發成 pip 套件

產生頁面、擷取、自我檢查的 Python 程式放在 `skills/walkthrough/engine/`，用專案自己的 Python 執行 `run.py`；專案的工具資料夾用 `wt_env.py` 把引擎加進 `sys.path`。這樣安裝 skill 就等於裝好引擎，`git pull` 一次更新兩者，也不需要在每個專案的依賴裡加套件。代價是引擎只能依賴標準函式庫（pandas、Pygments 都是選用），而且舊教材會用新版引擎重新產生。

## Considered Options

- pip 套件：版本可以鎖定，但每個專案都要多一個依賴，skill 和引擎版本也可能不一致。
- 每個專案複製一份引擎：最穩定，但修一個 bug 要改 N 份。
