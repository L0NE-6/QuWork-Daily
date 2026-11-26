<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🧩 QuWork Daily

**QuWork 每日奖励内部 POC：先查状态、写前落账、领取后回读**

> 当前版本：**v0.1.0**（脚本 2026-11-12 · Release 2026-11-24） · 认证方式：Bearer accessToken

**[简体中文](README.md)** · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

状态优先 · confirming 台账 · claim 回读 · Token 续期 · 多账号 · 可选推送

<img src="https://img.shields.io/badge/Version-v0.1.0-2ea44f?style=for-the-badge&logo=github" alt="Version v0.1.0" />
<img src="https://img.shields.io/github/stars/L0NE-6/QuWork-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" alt="Stars" />
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
<img src="https://img.shields.io/badge/Qinglong-ready-4EAA25?style=for-the-badge" alt="Qinglong" />
<img src="https://img.shields.io/badge/GitHub%20Actions-supported-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" alt="GitHub Actions" />
<img src="https://img.shields.io/badge/Status-implemented__unverified-FFA500?style=for-the-badge" alt="Implemented and unverified" />

[边界](#policy) · [速览](#overview) · [协议](#protocol) · [凭据](#credentials) · [快速开始](#quickstart) · [青龙](#qinglong) · [Actions](#actions) · [CLI](#cli) · [结果码](#result-codes) · [成功判据](#success) · [测试](#tests) · [目录](#layout) · [版本](#release) · [赞赏](#donate) · [反馈](#feedback)

</div>

---

<a id="policy"></a>
## 🚫 使用边界

> [!IMPORTANT]
> QuWork Daily 是账号持有人维护自身每日奖励的内部 POC。仓库代码与部署说明保持免费，不接受付费包装、冒充作者或删除版权信息后二次分发。

当前协议状态为 `implemented_unverified`。单元测试证明状态机与请求契约自洽，真实账号是否可领、积分是否到账仍必须用服务端状态回读确认。

---

<a id="overview"></a>
## ✨ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **用途** | 查询 QuWork 每日奖励状态，必要时领取，并在领取后回读确认。 |
| **输入** | `QUWORK_ACCOUNTS` 或 `QUWORK_ACCESS_TOKEN`。 |
| **核心保护** | 提交前写入 `confirming` 台账，结果不明时下一轮只回查。 |
| **输出** | `query`、`done`、`claimed`、`inactive`、`pending`、`failed`。 |
| **部署** | Windows / Linux / 青龙 / 手工 GitHub Actions。 |
| **发布状态** | `v0.1.0` 内部 POC，已发布 [GitHub Release](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0)。 |

---

<a id="what"></a>
## 🧭 这是什么

QuWork Daily 是一个单文件每日奖励执行器。它不把“POST 已发出”当作成功，而是执行完整状态机：

1. 读取账号与本地续期后的 access token。
2. 查询每日奖励状态。
3. 已领取直接完成，不可领取返回中性状态。
4. 可领取时先保存 `confirming` 台账，再提交 claim。
5. 重新查询状态，只有 `claimed=true` 且 `next_refresh_at` 未变化才确认成功。

配套 `quwork_get_token.py` 可从本机 QuWork 客户端 SQLite 数据库只读提取登录态，默认脱敏，只有显式 `--export` 才输出完整 JSON。

---

<a id="protocol"></a>
## 🔁 协议与回读

### 服务契约

| 项目 | 当前值 |
| :--- | :--- |
| 基址 | `https://llm.rrzu.com` |
| 客户端版本 | `1.6.0` |
| 状态 | `GET /api/user/daily-reward/status` |
| 领取 | `POST /api/user/daily-reward/claim` |
| 续期 | `GET /api/user/refresh` |
| 环境头 | `X-QurWork-Env: prod` |
| 版本头 | `X-QurWork-Version: 1.6.0` |

### 状态字段

| 字段 | 类型 | 验收用途 |
| :--- | :--- | :--- |
| `claimed` | boolean | 今日是否已领取 |
| `can_claim` | boolean | 当前是否允许领取 |
| `points` | number | 当前积分余额 |
| `consecutive_days` | integer | 连续领取天数 |
| `next_refresh_at` | timestamp | 下一周期刷新时间 |

### 回读规则

领取后必须再次查询状态。只有 `claimed=true` 且 `next_refresh_at` 与提交前完全一致，才写入 `claimed` 台账并报告成功。若 claim 已返回但状态尚未稳定，结果保留为 `pending`，下一轮只查询，不重复 POST。

---

<a id="credentials"></a>
## 🔑 凭据与账号

| 变量 | 必需 | 说明 |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | 二选一 | JSON 数组；每项至少含 `accessToken`，可带 `name`、`uid`、`proxy` |
| `QUWORK_ACCESS_TOKEN` | 二选一 | 单账号 access token |
| `QUWORK_PROXY` | 否 | 全局 HTTP / HTTPS 代理 |
| `QUWORK_STATE_DIR` | 否 | 状态目录，默认脚本目录 |
| `QUWORK_QUERY_ONLY` | 否 | `1` 时只查询，不领取 |

`QUWORK_ACCOUNTS` 可以是数组、单个账号对象或包含 `accounts` 数组的对象。脚本也会识别嵌套在 `secret`、`session`、`data`、`auth`、`user` 中的 `accessToken`、`access_token` 或 `token`。

```json
{
  "accounts": [
    {
      "name": "主号",
      "accessToken": "REPLACE_WITH_ACCESS_TOKEN",
      "uid": "REPLACE_WITH_UID",
      "proxy": "http://127.0.0.1:7890"
    }
  ]
}
```

本机提取：

```powershell
python .\quwork_get_token.py
python .\quwork_get_token.py --export
```

`--export` 会输出密码级凭据，只用于当前终端或密钥管理系统。

---

<a id="quickstart"></a>
## 🚀 快速开始

```powershell
python -m pip install -r requirements.txt
$env:QUWORK_ACCESS_TOKEN = "REPLACE_WITH_ACCESS_TOKEN"
python .\quwork_daily.py --query
python .\quwork_daily.py
```

多账号示例：

```powershell
$env:QUWORK_ACCOUNTS = '{"accounts":[{"name":"主号","accessToken":"REPLACE_WITH_TOKEN"}]}'
python .\quwork_daily.py
```

首次接入建议先运行 `--query`，确认状态字段完整、账号标签正确、代理可用，再执行领取。

---

<a id="qinglong"></a>
## 🐧 青龙面板

| 步骤 | 操作 |
| :---: | :--- |
| 1. 上传脚本 | 上传 `quwork_daily.py` 与可选 `quwork_get_token.py` |
| 2. 安装依赖 | 安装 `requests>=2.25.0` |
| 3. 设置变量 | 配置 `QUWORK_ACCOUNTS` 或 `QUWORK_ACCESS_TOKEN` |
| 4. 状态目录 | 建议设置持久化 `QUWORK_STATE_DIR` |
| 5. 创建任务 | 先执行 `task quwork_daily.py --query`，确认后改为 `task quwork_daily.py` |

推荐每天执行一次。状态目录必须跨运行保留，否则 `confirming` 台账与续期后的 token 无法恢复。

---

<a id="actions"></a>
## ☁️ GitHub Actions

当前仓库没有随附 `.github/workflows`。若要在私有仓库中手工接入 Actions，应把下列值配置为 Secrets，并自行创建 workflow：

| Secret | 必需 | 说明 |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | 二选一 | 多账号 JSON |
| `QUWORK_ACCESS_TOKEN` | 二选一 | 单账号 token |
| `QUWORK_PROXY` | 否 | 代理地址 |

状态文件包含续期后的 access token，不能作为普通 artifact 上传。需要跨运行保留时，应使用加密缓存或私有持久卷。

---

<a id="cli"></a>
## ⌨️ CLI 与环境变量

### 命令

```powershell
python .\quwork_daily.py --help
python .\quwork_daily.py --query
python .\quwork_daily.py
```

### 运行变量

| 变量 | 默认 | 说明 |
| :--- | :--- | :--- |
| `QUWORK_QUERY_ONLY` | `0` | 设为 `1` 等价于 `--query` |
| `QUWORK_STATE_DIR` | 脚本目录 | 保存 `.quwork_state.json` |
| `QUWORK_PROXY` | 空 | 账号对象内 `proxy` 优先于全局代理 |
| `QYWX_TOKEN` / `WECHAT_WEBHOOK` | 空 | 企业微信推送 |
| `PLUSPLUS_TOKEN` / `PLUSHPLUS_TOKEN` / `PUSHPLUS_TOKEN` | 空 | PushPlus 推送 |

`--query` 只读取状态，不提交 claim。正常模式会执行查询、领取与回读状态机。

---

<a id="result-codes"></a>
## 🚦 结果码

### 业务结果

| 结果 | 含义 | 是否成功 |
| :--- | :--- | :---: |
| `query` | 只查询完成 | 中性 |
| `done` | 今日此前已领取 | 是 |
| `claimed` | 本次领取并完成回读 | 是 |
| `inactive` | 当前不可领取或周期已过期 | 中性 |
| `pending` | 已提交或结果不明，等待下一轮回查 | 否 |
| `failed` | 配置、鉴权、业务或网络硬失败 | 否 |

### 退出码

| 退出码 | 含义 |
| :---: | :--- |
| `0` | 没有 `failed` 账号 |
| `1` | 配置错误、账号为空或至少一个账号失败 |

### HTTP 与续期

- `401` 或明确的“未登录”会触发一次 `/api/user/refresh`，成功后重放当前请求。
- 明确 `4xx` claim 拒绝会写入 `rejected` 并报告失败。
- 网络异常、超时、5xx 或领取后状态未稳定保留为 `pending`，不重复提交。

---

<a id="success"></a>
## ✅ 成功判据

一条账号结果只有满足下列条件才可称为成功：

1. 状态接口返回完整且类型正确的 `claimed`、`can_claim`、`points`、`consecutive_days`、`next_refresh_at`。
2. 领取前 `claimed=false`、`can_claim=true`，或本轮开始时已经是 `claimed=true`。
3. 本次 claim 后重新查询到 `claimed=true`。
4. `next_refresh_at` 与提交前一致。
5. 台账状态从 `confirming` 变为 `claimed`。

单元测试通过只证明上述状态机自洽。真实账号是否可领、积分是否变化仍为 UNVERIFIED，必须用服务端前后回读作为交付证据。

---

<a id="tests"></a>
## 🧪 测试

```powershell
$env:PYTHONUTF8 = "1"
python -m unittest discover -s tests -v
python -m py_compile quwork_daily.py quwork_get_token.py
```

测试文件包含 7 个用例，覆盖：

- 完整 session 解析。
- 已领取时不发 POST。
- claim 后状态回读确认。
- granted 但未回读时保持 pending，下一轮不重复提交。
- 401 后刷新一次并原子保存新 token。
- 明确拒绝写为 failed。
- 状态字段类型异常时硬失败。

---

<a id="design"></a>
## 🧱 设计原则

- **状态优先**：先查 `claimed` 与 `can_claim`，不在未知状态下直接提交。
- **提交前落账**：首次 claim 前写入 `confirming`，进程中断后可恢复。
- **服务端回读**：`claimed=true` 与 `next_refresh_at` 同时满足才算成功。
- **不重复 POST**：结果不明时保留 pending，下一轮只查询。
- **严格契约**：布尔、数值与时间戳类型不符直接失败。
- **原子状态写入**：临时文件 + `fsync` + `os.replace`。
- **凭据脱敏**：日志与错误消息替换 access token，账号名使用掩码。

---

<a id="privacy"></a>
## 🔒 隐私与安全

运行时会生成 `.quwork_state.json`，其中包含续期后的 access token，属于密码级数据。该文件已加入 `.gitignore`。

不得提交、上传、截图或分享：

- `.quwork_state.json`
- `QUWORK_ACCOUNTS` / `QUWORK_ACCESS_TOKEN`
- `quwork_get_token.py --export` 的输出
- 完整 JWT、Cookie、手机号、UID 与代理认证信息

提交 Issue 时只提供脱敏后的结果、HTTP 状态、错误类别和复现步骤。

---

<a id="layout"></a>
## 📁 目录结构

```text
QuWork-Daily/
├── .github/                    # 当前无 workflow
├── assets/
│   ├── donate-alipay.jpg
│   └── donate-wechat.png
├── docs/
│   ├── README.en.md
│   ├── README.ja.md
│   ├── README.ko.md
│   ├── README.pt-BR.md
│   └── README.zh-Hant.md
├── tests/
│   └── test_quwork_daily.py
├── CHANGELOG.md
├── README.md
├── quwork_daily.py
├── quwork_get_token.py
└── requirements.txt
```

运行时还会生成 `.quwork_state.json`，该文件不进入版本库与发布包。

---

<a id="release"></a>
## 📦 版本与发布

| 项目 | 当前值 |
| :--- | :--- |
| 脚本版本 | `v0.1.0` |
| 脚本日期 | `2026-11-12` |
| Git tag | [`v0.1.0`](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0) |
| GitHub Release | [`v0.1.0`](https://github.com/L0NE-6/QuWork-Daily/releases/tag/v0.1.0)（2026-11-24） |
| 协议状态 | `implemented_unverified` |

发布门槛：

1. 真实账号完成 `can_claim=true -> claim -> claimed=true` 回读。
2. 领取前后积分变化可核对。
3. `next_refresh_at` 在领取前后保持同一周期。
4. 失败、pending、rejected 三类状态均有回归证据。
5. 发布包不包含 `.quwork_state.json` 或任何账号导出。

---

<a id="disclaimer"></a>
## ⚠️ 免责声明

本项目用于账号持有人维护自己的每日奖励。使用前应自行确认账号、服务条款与所在地规则。作者不对账号限制、积分变化、接口调整、网络失败或第三方部署造成的损失作出保证。

公开 Release 仅以本仓库的 [Releases](https://github.com/L0NE-6/QuWork-Daily/releases) 页面为准；任何以“官方稳定版”“内部付费版”名义收费的渠道均不可信。

---

<a id="donate"></a>
## ☕ 赞赏码

### 支持与投喂

如果这个项目节省了你的时间，可以扫码支持维护。赞赏完全自愿，不影响代码、文档与 Issue 处理。

<div align="center">
<table>
<tr>
<td align="center"><strong>微信赞赏码</strong><br /><img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" /></td>
<td align="center"><strong>支付宝赞赏码</strong><br /><img src="assets/donate-alipay.jpg" width="260" alt="支付宝赞赏码" /></td>
</tr>
</table>
</div>

---

<a id="feedback"></a>
## 💬 反馈与 Star History

### 反馈与贡献

- [提交 Issue](https://github.com/L0NE-6/QuWork-Daily/issues)
- [提交 Pull Request](https://github.com/L0NE-6/QuWork-Daily/pulls)
- [查看更新日志](CHANGELOG.md)

反馈请附脱敏日志、结果状态、HTTP 状态码和复现步骤。不要贴 access token、完整 JWT、账号数据库或 `.quwork_state.json`。

<a href="https://star-history.com/#L0NE-6/QuWork-Daily&Date">
  <img src="https://api.star-history.com/svg?repos=L0NE-6/QuWork-Daily&type=Date" alt="QuWork Daily Star History" />
</a>
