# 複習中心是靜態 HTML，排程用 Leitner，進度存在瀏覽器

複習中心是一個不需要伺服器、直接用瀏覽器打開的 HTML 頁面；卡片組打包成 `decks.js`（`file://` 無法 fetch JSON）。排程用 Leitner 記憶盒（1、3、7、16、35 天），規則簡單、看得懂為什麼這張卡今天到期。進度存在 localStorage，提供匯出／匯入備份。

## Considered Options

- 在對話裡由 Claude 出題、改答案，進度存成檔案：Claude 能依結果調整教學，但使用者選了能自己隨時開來複習的 HTML。
- 發布成 claude.ai Artifact 並用它的資料庫存進度：可以跨裝置同步，但綁定特定平台，第一版不需要。
- SM-2 等更精細的排程：效果略好，但參數難解釋，卡片數量也還不多。

## Consequences

換瀏覽器或清除網站資料會看不到進度，要靠匯出備份。
