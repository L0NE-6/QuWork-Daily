<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🧩 QuWork Daily

**QuWork デイリー報酬の内部 POC：状態確認、確認台帳、claim、再読み取り**

> Version: **v0.1.0**（スクリプト 2026-11-12 · Release 2026-11-24） · Status: `implemented_unverified`

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · **[日本語](README.ja.md)** · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

状態優先 · confirming 台帳 · claim 再読み取り · Token 更新 · 複数アカウント · 任意通知

<img src="https://img.shields.io/badge/Version-v0.1.0-2ea44f?style=for-the-badge&logo=github" alt="Version v0.1.0" />
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
<img src="https://img.shields.io/badge/Status-implemented__unverified-FFA500?style=for-the-badge" alt="Implemented and unverified" />

</div>

---

<a id="policy"></a>
## 利用境界

QuWork Daily は、アカウント所有者が自分のデイリー報酬を維持するための内部 POC です。リポジトリと導入説明は無料で公開し、有料再配布、作者のなりすまし、クレジット削除は受け付けません。

プロトコル状態は `implemented_unverified` です。単体テストは状態機械の整合性だけを示し、実アカウントの受取とポイント到着はサーバー側の再読み取りで確認する必要があります。

---

<a id="overview"></a>
## 30 秒概要

| 項目 | 内容 |
| :--- | :--- |
| **用途** | 報酬状態を確認し、必要なら claim し、再度読み取る。 |
| **入力** | `QUWORK_ACCOUNTS` または `QUWORK_ACCESS_TOKEN`。 |
| **保護** | 初回 claim 前に `confirming` を保存し、不明時は再送しない。 |
| **出力** | `query`、`done`、`claimed`、`inactive`、`pending`、`failed`。 |
| **実行** | Windows、Linux、Qinglong、手動 GitHub Actions。 |
| **リリース** | `v0.1.0` 内部 POC。[GitHub Release](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0) を公開済みです。 |

---

<a id="what"></a>
## これは何か

QuWork Daily は単一ファイルの報酬実行ツールです。状態確認、確認台帳の保存、claim、状態の再読み取りを順番に実行します。

`quwork_get_token.py` はローカル QuWork クライアントの SQLite を読み取り専用で開きます。既定ではマスクし、`--export` のときだけ完全な JSON を出力します。

---

<a id="protocol"></a>
## プロトコルと再読み取り

| 項目 | 現在値 |
| :--- | :--- |
| ベース URL | `https://llm.rrzu.com` |
| クライアント版 | `1.6.0` |
| 状態 | `GET /api/user/daily-reward/status` |
| 受取 | `POST /api/user/daily-reward/claim` |
| 更新 | `GET /api/user/refresh` |
| 環境ヘッダー | `X-QurWork-Env: prod` |
| バージョンヘッダー | `X-QurWork-Version: 1.6.0` |

状態には boolean の `claimed` と `can_claim`、数値 `points`、整数 `consecutive_days`、有効な `next_refresh_at` が必要です。claim 後の再読み取りで `claimed=true` かつ `next_refresh_at` が変わらない場合だけ成功です。

---

<a id="credentials"></a>
## 認証情報とアカウント

| 変数 | 必須 | 説明 |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | 二択 | `accessToken` を含む JSON 配列またはオブジェクト |
| `QUWORK_ACCESS_TOKEN` | 二択 | 単一アカウントの Bearer Token |
| `QUWORK_PROXY` | 任意 | 全体 HTTP/HTTPS プロキシ |
| `QUWORK_STATE_DIR` | 任意 | 状態ディレクトリ |
| `QUWORK_QUERY_ONLY` | 任意 | `1` で照会のみ |

`secret`、`session`、`data`、`auth`、`user` 内の token フィールドも認識します。

```powershell
python .\quwork_get_token.py
python .\quwork_get_token.py --export
```

---

<a id="quickstart"></a>
## クイックスタート

```powershell
python -m pip install -r requirements.txt
$env:QUWORK_ACCESS_TOKEN = "REPLACE_WITH_ACCESS_TOKEN"
python .\quwork_daily.py --query
python .\quwork_daily.py
```

複数アカウントの場合:

```powershell
$env:QUWORK_ACCOUNTS = '{"accounts":[{"name":"main","accessToken":"REPLACE_WITH_TOKEN"}]}'
python .\quwork_daily.py
```

最初に `--query` を実行し、状態契約を確認してから claim を有効にします。

---

<a id="qinglong"></a>
## Qinglong

| 手順 | 操作 |
| :---: | :--- |
| 1 | `quwork_daily.py` と必要なら `quwork_get_token.py` を配置。 |
| 2 | `requests>=2.25.0` をインストール。 |
| 3 | `QUWORK_ACCOUNTS` または `QUWORK_ACCESS_TOKEN` を設定。 |
| 4 | 永続化される `QUWORK_STATE_DIR` を設定。 |
| 5 | 最初は `task quwork_daily.py --query` で確認。 |

状態ディレクトリがないと、更新済み Token と `confirming` 台帳を復元できません。

---

<a id="actions"></a>
## GitHub Actions

このリポジトリには現在 `.github/workflows` がありません。プライベート Actions では次の Secrets を利用できます。

| Secret | 必須 | 説明 |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | 二択 | 複数アカウント JSON |
| `QUWORK_ACCESS_TOKEN` | 二択 | 単一アカウント Token |
| `QUWORK_PROXY` | 任意 | プロキシ URL |

状態ファイルには更新済み access token が含まれるため、通常の artifact として公開しません。

---

<a id="cli"></a>
## CLI と環境変数

```powershell
python .\quwork_daily.py --help
python .\quwork_daily.py --query
python .\quwork_daily.py
```

| 変数 | 既定値 | 説明 |
| :--- | :--- | :--- |
| `QUWORK_QUERY_ONLY` | `0` | `1` で `--query` と同じ |
| `QUWORK_STATE_DIR` | スクリプト目录 | `.quwork_state.json` の保存先 |
| `QUWORK_PROXY` | 空 | アカウント内 `proxy` が優先 |
| `QYWX_TOKEN` / `WECHAT_WEBHOOK` | 空 | WeCom 通知 |
| `PLUSPLUS_TOKEN` / `PLUSHPLUS_TOKEN` / `PUSHPLUS_TOKEN` | 空 | PushPlus 通知 |

---

<a id="result-codes"></a>
## 結果コード

| 結果 | 意味 | 成功 |
| :--- | :--- | :---: |
| `query` | 照会完了 | 中立 |
| `done` | 実行前から受取済み | はい |
| `claimed` | 今回受取り、再読み取り済み | はい |
| `inactive` | 現在受取不可 | 中立 |
| `pending` | 結果未確定。次回は照会のみ | いいえ |
| `failed` | 設定、認証、業務、通信の失敗 | いいえ |

終了コード `0` は failed アカウントなし、`1` は設定エラーまたは一つ以上の失敗を示します。

---

<a id="success"></a>
## 成功条件

次のすべてを満たす場合だけ成功です。

1. 状態オブジェクトが完全で型が正しい。
2. 既に `claimed=true`、または `claimed=false` と `can_claim=true` から開始。
3. claim 後の再読み取りが `claimed=true`。
4. `next_refresh_at` が claim 前後で同じ。
5. 台帳が `confirming` から `claimed` に変わる。

単体テストの成功は実アカウントの到着を保証しません。

---

<a id="tests"></a>
## テスト

```powershell
$env:PYTHONUTF8 = "1"
python -m unittest discover -s tests -v
python -m py_compile quwork_daily.py quwork_get_token.py
```

7 件のテストが session 解析、受取済み時の POST なし、claim 再読み取り、pending 復元、401 の一回更新、明示拒否、状態型検証を確認します。

---

<a id="design"></a>
## 設計原則

- **状態優先**：不明状態では claim しない。
- **事前台帳**：最初の POST 前に `confirming` を保存。
- **サーバー再読み取り**：`claimed=true` と同一 reset が成功条件。
- **POST 重複防止**：不明結果は pending のまま。
- **厳格な契約**：型が違えば失敗。
- **原子的保存**：一時ファイル、`fsync`、`os.replace`。
- **認証情報のマスク**：メッセージから Token を除去。

---

<a id="privacy"></a>
## プライバシーと安全

`.quwork_state.json` には更新済み access token が入るため、パスワード相当のファイルです。Git の管理対象外です。

状態ファイル、`QUWORK_ACCOUNTS`、`QUWORK_ACCESS_TOKEN`、`--export` 出力、JWT、Cookie、電話番号、UID、プロキシ認証情報を公開しないでください。

---

<a id="layout"></a>
## ディレクトリ構成

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
## バージョンとリリース

| 項目 | 現在値 |
| :--- | :--- |
| スクリプト版 | `v0.1.0` |
| スクリプト日 | `2026-11-12` |
| Git tag | [`v0.1.0`](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0) |
| GitHub Release | [`v0.1.0`](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0)（2026-11-24） |
| プロトコル状態 | `implemented_unverified` |

実アカウントで `can_claim=true -> claimed=true` の再読み取り、ポイント変化、reset 不変、失敗状態の回帰証拠、`.quwork_state.json` を含まないパッケージがリリース条件です。

---

<a id="disclaimer"></a>
## 免責事項

本プロジェクトは自分のアカウント維持を目的とします。利用前にアカウント、利用規約、地域ルールを確認してください。アカウント制限、ポイント変化、API 変更、通信失敗、第三者環境での結果は保証しません。

---

<a id="donate"></a>
## 投げ銭 QR コード

支援は任意です。コード、ドキュメント、Issue 対応には影響しません。

<div align="center">
<table>
<tr>
<td align="center"><strong>WeChat</strong><br /><img src="../assets/donate-wechat.png" width="260" alt="WeChat 投げ銭 QR" /></td>
<td align="center"><strong>Alipay</strong><br /><img src="../assets/donate-alipay.jpg" width="260" alt="Alipay 投げ銭 QR" /></td>
</tr>
</table>
</div>

---

<a id="feedback"></a>
## フィードバックと Star History

- [Issue](https://github.com/L0NE-6/QuWork-Daily/issues)
- [Pull Request](https://github.com/L0NE-6/QuWork-Daily/pulls)
- [変更履歴](../CHANGELOG.md)

マスク済みログ、結果、HTTP 状態、再現手順を添えてください。Token、Cookie、アカウント DB、`.quwork_state.json` は公開しないでください。

<a href="https://star-history.com/#L0NE-6/QuWork-Daily&Date">
  <img src="https://api.star-history.com/svg?repos=L0NE-6/QuWork-Daily&type=Date" alt="QuWork Daily Star History" />
</a>
