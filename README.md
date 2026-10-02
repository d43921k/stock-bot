# stock-bot

自動抓取台股大盤指數、焦點族群與財經新聞，透過 Google Gemini API 產生盤勢摘要，
並輸出成一份適合手機閱讀的 HTML 晨報（`docs/index.html`），方便之後部署到 GitHub Pages。

## 專案架構

```
stock_bot/
├── config.py              # 讀取 .env 設定
├── fetchers/
│   ├── twse.py             # 台灣證交所 OpenAPI：加權指數、各類股指數
│   └── news.py             # Google 新聞 RSS：財經新聞
├── analysis/
│   └── gemini_client.py    # 串接 Gemini API，產生盤勢摘要
├── report/
│   ├── generator.py        # 組合資料並輸出 HTML
│   └── templates/
│       └── report.html.j2  # 手機版現代化排版樣板
└── main.py                 # 主流程：抓資料 -> AI 摘要 -> 產生 HTML

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

所有測試皆以 mock 模擬外部 API（TWSE、Google 新聞 RSS、Gemini），不需要網路連線或 API Key。

## 資料來源

- 大盤與類股指數：[TWSE OpenAPI](https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX)（公開資料，無需金鑰）
- 財經新聞：Google 新聞 RSS（關鍵字可在 `.env` 的 `NEWS_QUERY` 調整）
- 盤勢摘要：Google Gemini API（需自備 `GEMINI_API_KEY`）

## 部署到 GitHub Pages（未來）

`docs/index.html` 已經是最終輸出頁面，之後可以在 GitHub repo 設定：
Settings → Pages → Source 選擇 `main` branch 的 `/docs` 目錄即可上線，
之後可搭配排程（如 GitHub Actions cron）每天自動重新執行 `python -m stock_bot.main` 並 commit 新的 `docs/index.html`。
