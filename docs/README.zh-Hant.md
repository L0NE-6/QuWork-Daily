<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🧩 QuWork Daily

**QuWork 每日獎勵內部 POC：先查狀態、寫入確認台帳、領取後回讀**

> Version: **v0.1.0** (2026-11-12) · Status: `implemented_unverified`

[简体中文](../README.md) · [English](README.en.md) · **[繁體中文](README.zh-Hant.md)** · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

狀態優先 · confirming 台帳 · claim 回讀 · Token 續期 · 多帳號 · 可選推送

<img src="https://img.shields.io/badge/Version-v0.1.0-2ea44f?style=for-the-badge&logo=github" alt="Version v0.1.0" />
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
<img src="https://img.shields.io/badge/Status-implemented__unverified-FFA500?style=for-the-badge" alt="Implemented and unverified" />

</div>

---

<a id="policy"></a>
## 使用邊界

QuWork Daily 是帳號持有人維護自身每日獎勵的內部 POC。倉庫與部署說明保持免費，不接受付費包裝、冒充作者或刪除署名後二次分發。

目前協議狀態為 `implemented_unverified`。單元測試只證明狀態機自洽；真實帳號是否可領、積分是否到帳，仍須以服務端狀態回讀確認。

---

<a id="overview"></a>
## 30 秒速覽

| 維度 | 說明 |
| :--- | :--- |
| **用途** | 查詢每日獎勵狀態，必要時領取並回讀確認。 |
| **輸入** | `QUWORK_ACCOUNTS` 或 `QUWORK_ACCESS_TOKEN`。 |
| **保護** | 首次 claim 前寫入 `confirming`，結果不明時不重複提交。 |
| **輸出** | `query`、`done`、`claimed`、`inactive`、`pending`、`failed`。 |
| **執行** | Windows、Linux、青龍或手工設定的 GitHub Actions。 |
| **發布** | `v0.1.0` 內部 POC，無 Git tag、無 Release。 |

---

<a id="what"></a>
## 這是什麼

QuWork Daily 是單檔每日獎勵執行器。它先查狀態，首次領取前寫入確認台帳，提交 claim 後再次查詢狀態。

`quwork_get_token.py` 以唯讀方式讀取本機 QuWork 客戶端 SQLite，預設脫敏，只有 `--export` 才輸出完整帳號 JSON。

---

<a id="protocol"></a>
## 協議與回讀

| 項目 | 目前值 |
| :--- | :--- |
| 基址 | `https://llm.rrzu.com` |
| 客戶端版本 | `1.6.0` |
| 狀態 | `GET /api/user/daily-reward/status` |
| 領取 | `POST /api/user/daily-reward/claim` |
| 續期 | `GET /api/user/refresh` |
| 環境標頭 | `X-QurWork-Env: prod` |
| 版本標頭 | `X-QurWork-Version: 1.6.0` |

狀態物件必須包含布林 `claimed`、`can_claim`，數值 `points`，整數 `consecutive_days`，以及有效 `next_refresh_at`。第二次查詢得到 `claimed=true` 且 `next_refresh_at` 不變，才算領取成功。

---

<a id="credentials"></a>
## 憑證與帳號

| 變數 | 必需 | 說明 |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | 二選一 | JSON 陣列或含 `accessToken` 的帳號物件 |
| `QUWORK_ACCESS_TOKEN` | 二選一 | 單帳號 Bearer Token |
| `QUWORK_PROXY` | 否 | 全域 HTTP/HTTPS 代理 |
| `QUWORK_STATE_DIR` | 否 | 狀態目錄，預設腳本目錄 |
| `QUWORK_QUERY_ONLY` | 否 | 設為 `1` 時只查詢 |

帳號物件可含 `name`、`uid`、`proxy`，並支援 `secret`、`session`、`data`、`auth`、`user` 內的 token 欄位。

```powershell
python .\quwork_get_token.py
python .\quwork_get_token.py --export
```

---

<a id="quickstart"></a>
## 快速開始

```powershell
python -m pip install -r requirements.txt
$env:QUWORK_ACCESS_TOKEN = "REPLACE_WITH_ACCESS_TOKEN"
python .\quwork_daily.py --query
python .\quwork_daily.py
```

多帳號：

```powershell
$env:QUWORK_ACCOUNTS = '{"accounts":[{"name":"main","accessToken":"REPLACE_WITH_TOKEN"}]}'
python .\quwork_daily.py
```

先執行 `--query` 並核對狀態契約，再開啟領取。

---

<a id="qinglong"></a>
## 青龍面板

| 步驟 | 操作 |
| :---: | :--- |
| 1 | 上傳 `quwork_daily.py`，可選 `quwork_get_token.py`。 |
| 2 | 安裝 `requests>=2.25.0`。 |
| 3 | 設定 `QUWORK_ACCOUNTS` 或 `QUWORK_ACCESS_TOKEN`。 |
| 4 | 設定可持久化的 `QUWORK_STATE_DIR`。 |
| 5 | 先執行 `task quwork_daily.py --query`，確認後改用正常命令。 |

狀態目錄必須跨執行保留，否則續期 Token 與 `confirming` 台帳無法恢復。

---

<a id="actions"></a>
## GitHub Actions

目前倉庫沒有 `.github/workflows`。私有 Actions 可設定以下 Secrets：

| Secret | 必需 | 說明 |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | 二選一 | 多帳號 JSON |
| `QUWORK_ACCESS_TOKEN` | 二選一 | 單帳號 Token |
| `QUWORK_PROXY` | 否 | 代理 URL |

狀態檔含續期後的 access token，不可作為一般 artifact 上傳。

---

<a id="cli"></a>
## CLI 與環境變數

```powershell
python .\quwork_daily.py --help
python .\quwork_daily.py --query
python .\quwork_daily.py
```

| 變數 | 預設 | 說明 |
| :--- | :--- | :--- |
| `QUWORK_QUERY_ONLY` | `0` | 設為 `1` 等同 `--query` |
| `QUWORK_STATE_DIR` | 腳本目錄 | 儲存 `.quwork_state.json` |
| `QUWORK_PROXY` | 空 | 帳號內 `proxy` 優先 |
| `QYWX_TOKEN` / `WECHAT_WEBHOOK` | 空 | 企業微信推送 |
| `PLUSPLUS_TOKEN` / `PLUSHPLUS_TOKEN` / `PUSHPLUS_TOKEN` | 空 | PushPlus 推送 |

---

<a id="result-codes"></a>
## 結果碼

| 結果 | 含義 | 成功 |
| :--- | :--- | :---: |
| `query` | 查詢完成 | 中性 |
| `done` | 本輪前已領取 | 是 |
| `claimed` | 本次領取並完成回讀 | 是 |
| `inactive` | 當前不可領取 | 中性 |
| `pending` | 結果未定，下一輪只查詢 | 否 |
| `failed` | 設定、鑑權、業務或網路失敗 | 否 |

退出碼 `0` 表示沒有 failed 帳號；`1` 表示設定錯誤或至少一個帳號失敗。

---

<a id="success"></a>
## 成功判據

只有同時滿足以下條件才算成功：

1. 狀態物件完整且型別正確。
2. 原本已 `claimed=true`，或起始為 `claimed=false`、`can_claim=true`。
3. claim 後再次查到 `claimed=true`。
4. `next_refresh_at` 與提交前一致。
5. 台帳由 `confirming` 轉為 `claimed`。

單元測試通過不代表真實帳號已到帳。

---

<a id="tests"></a>
## 測試

```powershell
$env:PYTHONUTF8 = "1"
python -m unittest discover -s tests -v
python -m py_compile quwork_daily.py quwork_get_token.py
```

7 個測試覆蓋 session 解析、已領取不 POST、claim 回讀、pending 恢復、401 單次續期、明確拒絕與狀態型別驗證。

---

<a id="design"></a>
## 設計原則

- **狀態優先**：未知狀態不直接提交。
- **提交前落帳**：首次 POST 前寫入 `confirming`。
- **服務端回讀**：`claimed=true` 且 reset 不變才算成功。
- **不重複 POST**：結果不明保留 pending。
- **嚴格契約**：布林、數值與時間型別錯誤直接失敗。
- **原子狀態**：暫存檔、`fsync`、`os.replace`。
- **憑證脫敏**：訊息替換 Token，帳號名稱使用遮罩。

---

<a id="privacy"></a>
## 隱私與安全

`.quwork_state.json` 含續期後的 access token，屬密碼級資料，已由 Git 忽略。

不得公開狀態檔、`QUWORK_ACCOUNTS`、`QUWORK_ACCESS_TOKEN`、`--export` 輸出、完整 JWT、Cookie、手機號、UID 或代理憑證。Issue 只提供脫敏結果、HTTP 狀態、錯誤類別與重現步驟。

---

<a id="layout"></a>
## 目錄結構

```text
QuWork-Daily/
├── assets/
├── docs/
├── tests/test_quwork_daily.py
├── CHANGELOG.md
├── README.md
├── quwork_daily.py
├── quwork_get_token.py
└── requirements.txt
```

---

<a id="release"></a>
## 版本與發布

| 項目 | 目前值 |
| :--- | :--- |
| 腳本版本 | `v0.1.0` |
| 更新日期 | `2026-11-12` |
| Git tag | 無 |
| GitHub Release | 無 |
| 協議狀態 | `implemented_unverified` |

發布門檻為真實帳號完成 `can_claim=true -> claimed=true` 回讀、積分變化可核對、reset 時間不變、失敗狀態有回歸證據，且發布包不含 `.quwork_state.json`。

---

<a id="disclaimer"></a>
## 免責聲明

本專案僅供帳號持有人維護自身權益。使用前請確認帳號、服務條款與所在地規則。作者不對帳號限制、積分變化、介面調整、網路失敗或第三方部署結果作保證。

---

<a id="donate"></a>
## 讚賞碼

讚賞完全自願，不影響程式、文件與 Issue 處理。

<div align="center">
<table>
<tr>
<td align="center"><strong>微信</strong><br /><img src="../assets/donate-wechat.png" width="260" alt="微信讚賞碼" /></td>
<td align="center"><strong>支付寶</strong><br /><img src="../assets/donate-alipay.jpg" width="260" alt="支付寶讚賞碼" /></td>
</tr>
</table>
</div>

---

<a id="feedback"></a>
## 回饋與 Star History

- [提交 Issue](https://github.com/L0NE-6/QuWork-Daily/issues)
- [提交 Pull Request](https://github.com/L0NE-6/QuWork-Daily/pulls)
- [更新日誌](../CHANGELOG.md)

請附脫敏日誌、結果狀態、HTTP 狀態與重現步驟，不要貼 Token、Cookie、帳號資料庫或 `.quwork_state.json`。

<a href="https://star-history.com/#L0NE-6/QuWork-Daily&Date">
  <img src="https://api.star-history.com/svg?repos=L0NE-6/QuWork-Daily&type=Date" alt="QuWork Daily Star History" />
</a>
