# stock-bot

自動抓取美股／台股大盤指數、焦點族群與財經新聞，透過 Google Gemini API 產生新聞摘要並
挑選短中長線潛力股，輸出成一份適合手機閱讀的 HTML 晨報（`docs/index.html`），方便部署到 GitHub Pages。

晨報內容依序為：美股＋台股指數看板（收盤價/漲跌幅）→ 焦點族群 Top 5 → 財經新聞＋AI 摘要與總結
→ 短線／中線／長線潛力股推薦（各 5 檔，含建議進場區間與防守價格）。

## 專案架構

```
stock_bot/
├── config.py              # 讀取 .env 設定
├── fetchers/
│   ├── twse.py             # 台灣證交所 OpenAPI：各項台股指數、各類股指數
│   ├── us_indices.py       # Yahoo Finance：道瓊、S&P 500、那斯達克
│   └── news.py             # Google 新聞 RSS：財經新聞
├── analysis/
│   └── gemini_client.py    # 串接 Gemini API，結構化 JSON 輸出新聞摘要/總結與潛力股推薦
├── report/
│   ├── generator.py        # 組合資料並輸出 HTML
│   └── templates/
│       └── report.html.j2  # 手機版現代化排版樣板
└── main.py                 # 主流程：抓資料 -> AI 分析/選股 -> 產生 HTML

docs/
└── index.html               # 產生的晨報（GitHub Pages 可直接用 /docs 當來源）

tests/                        # pytest 單元測試（皆使用 mock，不需要 API Key 或網路）
```

## 環境設定

1. 建立並啟用虛擬環境：

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. 安裝套件：

   ```bash
   pip install -r requirements.txt
   ```

3. 複製環境變數範例檔並填入你的 Gemini API Key：

   ```bash
   cp .env.example .env
   ```

   到 [Google AI Studio](https://aistudio.google.com/apikey) 免費申請 `GEMINI_API_KEY`，
   填入 `.env` 中。

## 執行

```bash
source .venv/bin/activate
python -m stock_bot.main
```

執行成功後，會在 `docs/index.html` 產生最新一份晨報，用手機瀏覽器打開即可預覽。

## 測試

```bash
source .venv/bin/activate
python -m pytest -q
```

所有測試皆以 mock 模擬外部 API（TWSE、Yahoo Finance、Google 新聞 RSS、Gemini），不需要網路連線或 API Key。

## 資料來源

- 台股指數與類股指數：[TWSE OpenAPI](https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX)（公開資料，無需金鑰）
- 美股指數：Yahoo Finance Chart API（公開資料，無需金鑰）
- 財經新聞：Google 新聞 RSS（關鍵字可在 `.env` 的 `NEWS_QUERY` 調整）
- 新聞摘要/總結與潛力股推薦：Google Gemini API（需自備 `GEMINI_API_KEY`），皆由 AI 自動生成，僅供參考，不構成投資建議。

## 部署到 GitHub Pages（未來）

`docs/index.html` 已經是最終輸出頁面，之後可以在 GitHub repo 設定：
Settings → Pages → Source 選擇 `main` branch 的 `/docs` 目錄即可上線，
之後可搭配排程（如 GitHub Actions cron）每天自動重新執行 `python -m stock_bot.main` 並 commit 新的 `docs/index.html`。
