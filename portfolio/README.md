# 通用作品集入口

這是可攜的本機首頁，用來瀏覽作品、功能、公開版本、證據與 Demo。入口只讀自己的登錄與已審查的靜態檔案，不啟動來源 repo、不執行來源命令、不代理 API，也不共享資料庫或登入憑證。

## 啟動

需要 Python 3.12 以上；核心 CLI 只用 Python 標準函式庫，瀏覽器測試另用 Playwright。

```powershell
python portfolio/hub.py doctor --json
python portfolio/hub.py validate --mode public --offline
python portfolio/hub.py build --mode public
python portfolio/hub.py serve --mode local --port 8765 --open
```

Windows 可用 `powershell -NoProfile -File .\portfolio\start.ps1`；POSIX 可用 `sh portfolio/start.sh`。首頁只綁 `127.0.0.1`。若預設 port 忙碌，入口依序嘗試 8766–8775，再讓作業系統分配空 port；不會終止占用程序。

## 登錄與狀態

- `projects.json` 是唯一公開手動登錄。九個初始作品都固定在同一筆 `project_id`，加作品／分類／功能不必改前端。
- `projects.schema.json`、`local.schema.json` 描述資料結構；CLI 另作 URL、路徑與版本語意檢查，拒絕未知欄位與錯誤 major version。
- `snapshot` 記錄可查核的公開版本；`evidence` 記錄範圍和狀態。歷史測試不會自動升成已驗證。
- `capabilities[].status` 可用 `implemented`、`partial`、`planned`；`lifecycle=archived` 保留舊識別碼與歷史入口。
- 公開 repo 連結必須固定完整 commit。入口不會自動追蹤來源 repo 最新分支。

## 新增或更新作品

複製範例並填上穩定 slug、作品說明、能力與來源證據：

```powershell
New-Item -ItemType Directory -Force .local | Out-Null
Copy-Item portfolio/examples/project.example.json .local/new-project.json
python portfolio/hub.py upsert --input .local/new-project.json --dry-run --json
python portfolio/hub.py upsert --input .local/new-project.json --json
python portfolio/hub.py validate --mode public --offline
python portfolio/hub.py build --mode public
```

dry-run 只驗資料並回報新增、更新或不變，不會改 registry。正式 upsert 會先驗證全筆資料，再以同目錄暫存檔原子替換。相同 ID 是更新；不同 ID 不會自動猜測舊 ID，明確使用 `--previous-id <舊 ID>` 時若值不同會拒絕改名。更新功能時維持 `project_id`，修改能力、revision、證據與連結即可。

## 本機 Web Demo

來源專案依自己的 README 啟動，新增 binding 到忽略追蹤的 `.local/projects.local.json`：

```powershell
New-Item -ItemType Directory -Force .local | Out-Null
Copy-Item portfolio/examples/local.example.json .local/projects.local.json
python portfolio/hub.py validate --mode local --offline
python portfolio/hub.py build --mode local
```

範例 URL 使用 loopback；請替換為本機實際 port。可加 `source_path` 作本機診斷，但 public build 不會讀 overlay，local build 也不會輸出該路徑。沒有 binding 時入口顯示未設定／尚未檢查，不推測來源服務是否運作。

## 靜態 Demo bundle

靜態頁、CSS、JS 和資產需先經人工公開內容檢查；準備明確 allowlist 與 SHA-256 後匯入。範例檔案在 `examples/demo-bundle/`，descriptor 在 `examples/bundle.example.json`：

```powershell
New-Item -ItemType Directory -Force .local/imports/synthetic-demo/1.0.0 | Out-Null
Copy-Item portfolio/examples/demo-bundle/* .local/imports/synthetic-demo/1.0.0/
python portfolio/hub.py import-bundle --input portfolio/examples/bundle.example.json --dry-run --json
python portfolio/hub.py import-bundle --input portfolio/examples/bundle.example.json --json
```

匯入程式只讀 `.local/imports/<project_id>/<revision>/` 的列舉檔，不執行 build script；最多 500 檔／50 MiB，檢查 checksum、symlink、大小寫／Unicode 路徑碰撞及 HTML／CSS 的靜態資產引用。revision 已存在而內容不同時要使用新 revision。完成範例 bundle 匯入後，可複製靜態 Demo 專用的完整 descriptor 並先 dry-run：

```powershell
Copy-Item portfolio/examples/project-with-demo.example.json .local/synthetic-demo.json
python portfolio/hub.py upsert --input .local/synthetic-demo.json --dry-run --json
```

確認這是要公開的合成範例後再正式 upsert。其他專案只需在其 descriptor 加入下列 link，並將 `<id>`／`<revision>`／`<entry>` 換成已匯入值：

```json
{"link_id":"interactive-demo","label":"開啟靜態 Demo","kind":"static_bundle","status":"available","path":"demos/<id>/<revision>/<entry>"}
```

自我載入、動態 import 等靜態無法證明的引用須人工覆核，並由 browser 測試確認無非預期網路請求。

## 外部 HTTPS Demo

用 `external_https` link 設定公開 HTTPS URL；`expires_at` 使用 UTC ISO-8601。可選擇執行：

```json
{"link_id":"public-demo","label":"查看線上 Demo","kind":"external_https","status":"unverified","url":"https://example.com/demo","expires_at":"2027-12-31T00:00:00Z"}
```

```powershell
python portfolio/hub.py verify-links --remote --json
```

只有這個明確命令會作遠端讀取；每個 hostname 的解析結果與 redirect 都重新檢查公開 IP，連線保留 TLS 主機驗證。逾時／外站故障會回報 `UNVERIFIED`，不影響離線 build。Demo 網址是新分頁連結；本單不建立雲端網站、tunnel、DNS 或帳單。

## 輸出、去名與安全

- `build --mode public` 只讀公開 registry；即使 `.local/projects.local.json` 遺失、破損或含本機資料，public digest 仍相同。
- `build --mode local` 才讀 overlay，顯示 loopback Demo 與 local-only 作品。兩種結果分別寫到 `.local/dist/public/` 與 `.local/dist/local/`。
- 只掃描經 registry 與 allowlist 指定的作品輸出；文字以 DOM `textContent` 呈現，不把 registry 文字當 HTML。沒有 CDN、外部字型、分析碼或 service worker。
- `.local/company-rules.json` 是本機私有去名規則，請勿提交。公開測試只使用 `tests/fixtures/company-rules.synthetic.json`。

```powershell
python portfolio/hub.py audit --mode public --scope artifact --rules portfolio/tests/fixtures/company-rules.synthetic.json --json
python portfolio/hub.py audit --mode public --scope all --rules .local/company-rules.json --asset-ledger 308063538eaec8df533416b3972039551f04677d --json
```

artifact audit 只掃已生成的公開輸出；all 會掃 Git 追蹤／未追蹤公開文字與檔名，排除 `.git`、`.local`、venv、cache；binary image/PDF 另列資產帳本，未改 byte 且已有目視／抽取證據才可沿用。匹配報告只含路徑、rule ID 與計數，不輸出私有詞彙。零命中仍須人工檢查。

## 開發測試

```powershell
python -m unittest discover -s portfolio/tests -p "test_*.py" -q
python portfolio/hub.py validate --mode public --offline
python portfolio/hub.py validate --mode local --offline
python portfolio/hub.py build --mode public
python portfolio/hub.py build --mode local
python portfolio/tests/test_browser.py --browser auto --json
```

測試專用依賴見 `requirements-dev.txt`（Playwright 1.64.1）；Windows 建議安裝到隔離環境：

```powershell
python -m venv .local/venv
.\.local\venv\Scripts\python.exe -m pip install -r portfolio/requirements-dev.txt
.\.local\venv\Scripts\python.exe -m playwright install chromium
.\.local\venv\Scripts\python.exe portfolio/tests/test_browser.py --browser auto --json
```

POSIX 對應 `.local/venv/bin/python`。browser runner 會先選已安裝的 Playwright Chromium，之後嘗試系統 Edge／Chrome；不會外連網站內容。首頁另可用 JavaScript 關閉模式閱讀靜態 fallback。受限主機若不能啟動瀏覽器，請記錄為 `BLOCKED_E2E`，不可將靜態檢查寫成瀏覽器通過。

本入口核心沒有第三方 runtime dependency。Playwright 1.64.1 為開發／驗收依賴，採 Apache-2.0 授權；安裝後的套件中包含 LICENSE。現有作品各自沿用來源 repo 的 LICENSE／NOTICE，不在此入口重新授權或改寫來源授權。

## 常見輸入錯誤

| 錯誤 | CLI 回報 | 修正 |
|---|---|---|
| JSON 缺欄位、拼錯欄位、重複 ID | `ValidationError`，exit 2 | 對照 `projects.schema.json`；維持既有 `project_id`，讓每筆 feature/link ID 唯一 |
| repo URL 用 `main`／短 SHA | 拒絕固定版本連結 | 改成可讀取的 40 字元 commit URL，同步更新 `snapshot.public_ref` |
| 外部 link 含 credential、敏感 query 或非 HTTPS | URL 驗證拒絕 | 移除憑證並改用公開 HTTPS 網址；本機服務請改 `local_http` binding |
| local URL 是 LAN／0.0.0.0 或沒宣告 binding | overlay validation 失敗 | 使用 `127.0.0.1`、`localhost` 或 `[::1]`，且 matching link 要先登錄 binding_id |
| bundle checksum／靜態路徑不符 | import exit 2，舊 revision 保留 | 重算 SHA-256、修正 allowlist 或改用新 revision；不放寬安全路徑限制 |
| bundle 超過 500 檔或 50 MiB | import 拒絕 | 只匯出真正需要且已審查的頁面資產 |
| build 發現未知檔或舊輸出沒有 manifest | build exit 4，舊輸出保留 | 將使用者檔案移出受管輸出資料夾；不要手動刪除不明輸出 |
| 預設 port 被占用 | CLI 回報實際 fallback URL | 使用實際印出的 URL；入口不終止其他程序 |
