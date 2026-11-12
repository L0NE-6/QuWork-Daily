# QuWork Daily

**QuWork 每日奖励内部 POC：先查状态、写前落 pending、领取后回读。**

> 当前为未公开发版版本。API 依据尚未用真实账号完成领取前后 `claimed/points/resetAt`
> 回读，因此单测通过只代表协议实现自洽，不代表线上账号必然到账。

## 流程

1. 读取账号并恢复上次续期后的 accessToken。
2. `GET /api/user/daily-reward/status`。
3. 已领取直接完成；不可领取返回中性状态。
4. 首次提交前保存 `confirming` 台账。
5. `POST /api/user/daily-reward/claim`。
6. 再次查询状态，只有 `claimed=true` 且 `next_refresh_at` 未变化才确认成功。
7. 结果不明时保留 `confirming`，下一轮只回查，不重复提交。

## 配置

| 变量 | 必需 | 说明 |
| :--- | :---: | :--- |
| `QUWORK_ACCOUNTS` | 二选一 | JSON 数组，每项至少含 `accessToken`，可带 `name`、`uid`、`proxy` |
| `QUWORK_ACCESS_TOKEN` | 二选一 | 单账号 `accessToken` |
| `QUWORK_PROXY` | 否 | 全局 HTTP/HTTPS 代理 |
| `QUWORK_STATE_DIR` | 否 | 状态目录，默认脚本目录 |
| `QUWORK_QUERY_ONLY` | 否 | `1` 时只查询，不领取 |
| `QYWX_TOKEN` / `PLUSPLUS_TOKEN` | 否 | 可选推送 |

```json
[
  {
    "name": "主号",
    "accessToken": "***"
  }
]
```

## 使用

```bash
python quwork_daily.py --query
python quwork_daily.py
```

本机客户端已登录时，只读提取凭据：

```bash
python quwork_get_token.py
python quwork_get_token.py --export
```

`--export` 会输出密码级凭据，不要发群、提交仓库或写入公开日志。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile quwork_daily.py quwork_get_token.py
```

## 发布门槛

- 上游出现正式稳定版本；或
- 真实账号完成一次 `can_claim=true -> claim -> claimed=true` 回读，并能核对积分变化。
