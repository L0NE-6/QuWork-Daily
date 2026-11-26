<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🧩 QuWork Daily

**Internal QuWork daily-reward POC: inspect status, persist intent, claim, then read back**

> Version: **v0.1.0** (script 2026-11-12 · release 2026-11-24) · Status: `implemented_unverified`

[简体中文](../README.md) · **[English](README.en.md)** · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

Status first · confirming ledger · claim readback · token refresh · multi-account · optional notifications

<img src="https://img.shields.io/badge/Version-v0.1.0-2ea44f?style=for-the-badge&logo=github" alt="Version v0.1.0" />
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
<img src="https://img.shields.io/badge/Status-implemented__unverified-FFA500?style=for-the-badge" alt="Implemented and unverified" />

</div>

---

<a id="policy"></a>
## Usage policy

QuWork Daily is an internal POC for account owners maintaining their own daily rewards. The repository and deployment notes remain free. Do not repackage them as a paid product, impersonate the author, or remove attribution.

The protocol state is `implemented_unverified`. Unit tests prove that the state machine is internally consistent; a real account still needs a server-side status readback before delivery can be called successful.

---

<a id="overview"></a>
## 30-second overview

| Item | Description |
| :--- | :--- |
| **Purpose** | Read daily-reward status, claim when available, and verify the result. |
| **Input** | `QUWORK_ACCOUNTS` or `QUWORK_ACCESS_TOKEN`. |
| **Safety** | Persist `confirming` before the first claim; never resubmit after an uncertain result. |
| **Outputs** | `query`, `done`, `claimed`, `inactive`, `pending`, `failed`. |
| **Runtime** | Windows, Linux, Qinglong, or a manually configured GitHub Actions workflow. |
| **Release** | `v0.1.0` internal POC, published as a [GitHub Release](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0). |

---

<a id="what"></a>
## What it is

QuWork Daily is a single-file reward runner with a strict state machine. It reads the current reward status, writes a confirmation ledger before a claim, submits once, then reads the status again.

The companion `quwork_get_token.py` reads the local QuWork client SQLite database in read-only mode. It masks credentials by default and prints the full account JSON only with `--export`.

---

<a id="protocol"></a>
## Protocol and readback

| Item | Current value |
| :--- | :--- |
| Base URL | `https://llm.rrzu.com` |
| Client version | `1.6.0` |
| Status | `GET /api/user/daily-reward/status` |
| Claim | `POST /api/user/daily-reward/claim` |
| Refresh | `GET /api/user/refresh` |
| Environment header | `X-QurWork-Env: prod` |
| Version header | `X-QurWork-Version: 1.6.0` |

The status object must contain boolean `claimed` and `can_claim`, numeric `points`, integer `consecutive_days`, and a valid `next_refresh_at`. A claim is confirmed only when a second status read returns `claimed=true` with the same `next_refresh_at`.

---

<a id="credentials"></a>
## Credentials and accounts

| Variable | Required | Description |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | one of two | JSON array or account object with `accessToken` |
| `QUWORK_ACCESS_TOKEN` | one of two | Single-account bearer token |
| `QUWORK_PROXY` | No | Global HTTP/HTTPS proxy |
| `QUWORK_STATE_DIR` | No | State directory; defaults to the script directory |
| `QUWORK_QUERY_ONLY` | No | Set to `1` for query-only mode |

Account objects may include `name`, `uid`, and `proxy`. Nested `accessToken`, `access_token`, or `token` fields under `secret`, `session`, `data`, `auth`, and `user` are also recognized.

```powershell
python .\quwork_get_token.py
python .\quwork_get_token.py --export
```

---

<a id="quickstart"></a>
## Quick start

```powershell
python -m pip install -r requirements.txt
$env:QUWORK_ACCESS_TOKEN = "REPLACE_WITH_ACCESS_TOKEN"
python .\quwork_daily.py --query
python .\quwork_daily.py
```

For multiple accounts:

```powershell
$env:QUWORK_ACCOUNTS = '{"accounts":[{"name":"main","accessToken":"REPLACE_WITH_TOKEN"}]}'
python .\quwork_daily.py
```

Run `--query` first and verify the status contract before enabling claims.

---

<a id="qinglong"></a>
## Qinglong

| Step | Action |
| :---: | :--- |
| 1 | Upload `quwork_daily.py` and optionally `quwork_get_token.py`. |
| 2 | Install `requests>=2.25.0`. |
| 3 | Add `QUWORK_ACCOUNTS` or `QUWORK_ACCESS_TOKEN`. |
| 4 | Configure a persistent `QUWORK_STATE_DIR`. |
| 5 | Start with `task quwork_daily.py --query`, then switch to the normal command. |

The state directory must survive between runs so that refresh tokens and `confirming` claims can be recovered.

---

<a id="actions"></a>
## GitHub Actions

This repository does not currently include `.github/workflows`. A private GitHub Actions workflow can use these Secrets:

| Secret | Required | Description |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | one of two | Multi-account JSON |
| `QUWORK_ACCESS_TOKEN` | one of two | Single-account token |
| `QUWORK_PROXY` | No | Proxy URL |

The state file contains a refreshed access token. Do not upload it as a normal artifact; use an encrypted cache or private persistent volume.

---

<a id="cli"></a>
## CLI and environment variables

```powershell
python .\quwork_daily.py --help
python .\quwork_daily.py --query
python .\quwork_daily.py
```

| Variable | Default | Description |
| :--- | :--- | :--- |
| `QUWORK_QUERY_ONLY` | `0` | Equivalent to `--query` when set to `1` |
| `QUWORK_STATE_DIR` | Script directory | Stores `.quwork_state.json` |
| `QUWORK_PROXY` | Empty | Account-level `proxy` takes precedence |
| `QYWX_TOKEN` / `WECHAT_WEBHOOK` | Empty | WeCom notification |
| `PLUSPLUS_TOKEN` / `PLUSHPLUS_TOKEN` / `PUSHPLUS_TOKEN` | Empty | PushPlus notification |

---

<a id="result-codes"></a>
## Result codes

| Outcome | Meaning | Success |
| :--- | :--- | :---: |
| `query` | Query completed | Neutral |
| `done` | Already claimed before this run | Yes |
| `claimed` | Claimed and verified by readback | Yes |
| `inactive` | Not claimable in the current period | Neutral |
| `pending` | Submitted or uncertain; next run only reads status | No |
| `failed` | Configuration, authentication, business, or network failure | No |

Exit code `0` means no account failed. Exit code `1` means a configuration error or at least one failed account.

---

<a id="success"></a>
## Success criteria

An account is successful only when:

1. The status object is complete and has the correct types.
2. The account is either already `claimed=true`, or starts with `claimed=false` and `can_claim=true`.
3. A claim is followed by a second status read with `claimed=true`.
4. `next_refresh_at` stays unchanged across the claim.
5. The ledger changes from `confirming` to `claimed`.

Passing unit tests is not proof that a real account can claim or that points changed.

---

<a id="tests"></a>
## Tests

```powershell
$env:PYTHONUTF8 = "1"
python -m unittest discover -s tests -v
python -m py_compile quwork_daily.py quwork_get_token.py
```

The seven tests cover session parsing, no-POST completion, claim readback, pending recovery, one-time 401 refresh, explicit rejection, and strict status validation.

---

<a id="design"></a>
## Design principles

- **Status first:** never claim from an unknown state.
- **Persist intent:** write `confirming` before the first POST.
- **Server readback:** success requires `claimed=true` with the same reset timestamp.
- **No duplicate POST:** uncertain results remain pending.
- **Strict contract:** reject wrong boolean, number, or timestamp types.
- **Atomic state:** temporary file, `fsync`, and `os.replace`.
- **Credential masking:** tokens are removed from messages and account labels are masked.

---

<a id="privacy"></a>
## Privacy and security

`.quwork_state.json` contains refreshed access tokens and is a password-level file. It is ignored by Git.

Do not publish the state file, `QUWORK_ACCOUNTS`, `QUWORK_ACCESS_TOKEN`, `--export` output, full JWTs, cookies, phone numbers, UIDs, or proxy credentials. Issue reports should contain only masked results, HTTP status, error category, and reproduction steps.

---

<a id="layout"></a>
## Directory layout

```text
QuWork-Daily/
├── assets/
│   ├── donate-alipay.jpg
│   └── donate-wechat.png
├── docs/
│   ├── README.en.md
│   ├── README.ja.md
│   ├── README.ko.md
│   ├── README.pt-BR.md
│   └── README.zh-Hant.md
├── tests/test_quwork_daily.py
├── CHANGELOG.md
├── README.md
├── quwork_daily.py
├── quwork_get_token.py
└── requirements.txt
```

---

<a id="release"></a>
## Version and releases

| Item | Current value |
| :--- | :--- |
| Script version | `v0.1.0` |
| Script date | `2026-11-12` |
| Git tag | [`v0.1.0`](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0) |
| GitHub Release | [`v0.1.0`](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0) (2026-11-24) |
| Protocol state | `implemented_unverified` |

Release requires a real account readback from `can_claim=true` to `claimed=true`, a verifiable points change, unchanged `next_refresh_at`, regression evidence for failure states, and a package that excludes `.quwork_state.json`.

---

<a id="disclaimer"></a>
## Disclaimer

Use this project only to maintain your own account. Confirm the account, service terms, and applicable rules before use. The author does not guarantee account status, point changes, API stability, network availability, or results from third-party deployments.

---

<a id="donate"></a>
## Donation QR codes

Donations are optional and do not affect code, documentation, or Issue handling.

<div align="center">
<table>
<tr>
<td align="center"><strong>WeChat</strong><br /><img src="../assets/donate-wechat.png" width="260" alt="WeChat donation QR code" /></td>
<td align="center"><strong>Alipay</strong><br /><img src="../assets/donate-alipay.jpg" width="260" alt="Alipay donation QR code" /></td>
</tr>
</table>
</div>

---

<a id="feedback"></a>
## Feedback and Star History

- [Open an Issue](https://github.com/L0NE-6/QuWork-Daily/issues)
- [Open a Pull Request](https://github.com/L0NE-6/QuWork-Daily/pulls)
- [Changelog](../CHANGELOG.md)

Include masked logs, outcome, HTTP status, and reproduction steps. Never publish tokens, cookies, account databases, or `.quwork_state.json`.

<a href="https://star-history.com/#L0NE-6/QuWork-Daily&Date">
  <img src="https://api.star-history.com/svg?repos=L0NE-6/QuWork-Daily&type=Date" alt="QuWork Daily Star History" />
</a>
