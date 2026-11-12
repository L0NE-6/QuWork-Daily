# 更新日志

## v0.1.0（2026-11-12）

- 内部 POC：每日奖励先查状态，再领取，最后回读 `claimed=true`。
- 首次提交前保存 `confirming` 台账；结果不明时下一轮只回查，不重复 POST。
- accessToken 失效时自动调用一次续期并原子回写本地状态。
- 多账号、单账号、代理、只查询模式和企业微信/PushPlus 推送。
- 附带本机 QuWork 凭据只读提取工具，默认脱敏，`--export` 才输出完整 JSON。
- 当前协议来源为 `implemented_unverified`，尚不能用单元测试替代真实账号到账验证。
