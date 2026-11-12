#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuWork 每日奖励脚本（内部 POC，未公开发版）。

流程：
  1. GET  /api/user/daily-reward/status
  2. 已领取直接结束；不可领取返回中性状态
  3. 首次提交前先落 confirming 状态，进程中断也不会盲目重领
  4. POST /api/user/daily-reward/claim
  5. 再次 GET status，只有 claimed=true 且 resetAt 未变化才确认成功
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import requests


VERSION = "0.1.0"
BASE = "https://llm.rrzu.com"
CLIENT_VERSION = "1.6.0"
USER_AGENT = "QuWork/%s" % CLIENT_VERSION

STATUS_PATH = "/api/user/daily-reward/status"
CLAIM_PATH = "/api/user/daily-reward/claim"
REFRESH_PATH = "/api/user/refresh"

HERE = Path(__file__).resolve().parent
STATE_PATH = Path(os.getenv("QUWORK_STATE_DIR", str(HERE))) / ".quwork_state.json"


def now_ms() -> int:
    return int(time.time() * 1000)


def mask(value: Any) -> str:
    text = str(value or "")
    if not text:
        return "未命名"
    if len(text) <= 4:
        return "*" * len(text)
    return text[:2] + "*" * max(2, len(text) - 4) + text[-2:]


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "ok", "success")
    return False


def as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def timestamp_ms(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return int(number if number >= 100_000_000_000 else number * 1000)


def jwt_payload(token: str) -> dict[str, Any]:
    try:
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)
        value = json.loads(base64.urlsafe_b64decode(part))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def token_uid(token: str) -> str:
    claims = jwt_payload(token)
    data = claims.get("data") if isinstance(claims.get("data"), dict) else {}
    user = claims.get("user") if isinstance(claims.get("user"), dict) else {}
    for value in (
        claims.get("sub"),
        claims.get("uid"),
        claims.get("user_id"),
        data.get("id"),
        data.get("uid"),
        user.get("id"),
        user.get("uid"),
    ):
        text = str(value or "").strip()
        if text:
            return text
    return ""


def token_expiry(token: str) -> int | None:
    return timestamp_ms(jwt_payload(token).get("exp"))


def _nested_values(value: Any, depth: int = 0):
    if depth > 6 or not isinstance(value, dict):
        return
    yield value
    for key in ("secret", "session", "data", "auth", "user"):
        nested = value.get(key)
        if isinstance(nested, dict):
            yield from _nested_values(nested, depth + 1)


def account_access_token(account: dict[str, Any]) -> str:
    for row in _nested_values(account):
        for key in ("accessToken", "access_token", "token"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().removeprefix("Bearer ").strip()
    return ""


def account_label(account: dict[str, Any], index: int) -> str:
    for row in _nested_values(account):
        for key in ("name", "nickname", "displayName", "username", "phone", "uid"):
            value = str(row.get(key) or "").strip()
            if value:
                return value
    return "账号%d" % index


def account_key(account: dict[str, Any], token: str) -> str:
    uid = str(account.get("uid") or "").strip() or token_uid(token)
    if uid:
        return "quwork:%s" % uid
    label = account_label(account, 1)
    digest = hashlib.sha256((label + "\0" + token).encode("utf-8")).hexdigest()[:24]
    return "quwork:key:%s" % digest


def parse_accounts(raw: str | None = None) -> list[dict[str, Any]]:
    raw = (raw if raw is not None else os.getenv("QUWORK_ACCOUNTS", "")).strip()
    items: list[Any] = []
    if raw:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("QUWORK_ACCOUNTS 不是合法 JSON: %s" % exc) from exc
        if isinstance(value, dict):
            value = value.get("accounts") or [value]
        if not isinstance(value, list):
            raise ValueError("QUWORK_ACCOUNTS 必须是 JSON 数组或对象")
        items.extend(value)
    elif os.getenv("QUWORK_ACCESS_TOKEN", "").strip():
        items.append({"accessToken": os.getenv("QUWORK_ACCESS_TOKEN", "").strip()})

    accounts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(items, 1):
        if isinstance(item, str):
            item = {"accessToken": item}
        if not isinstance(item, dict):
            raise ValueError("第 %d 个账号必须是对象或 accessToken 字符串" % index)
        account = dict(item)
        token = account_access_token(account)
        if not token:
            raise ValueError("第 %d 个账号缺少 accessToken" % index)
        account["accessToken"] = token
        account["name"] = account_label(account, index)
        key = account_key(account, token)
        if key in seen:
            continue
        seen.add(key)
        account["_key"] = key
        accounts.append(account)
    return accounts


def load_state() -> dict[str, Any]:
    try:
        value = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        value = {}
    if not isinstance(value, dict):
        value = {}
    value.setdefault("version", 1)
    value.setdefault("accounts", {})
    value.setdefault("claims", {})
    if not isinstance(value["accounts"], dict):
        value["accounts"] = {}
    if not isinstance(value["claims"], dict):
        value["claims"] = {}
    return value


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=STATE_PATH.name + ".", suffix=".tmp", dir=str(STATE_PATH.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, STATE_PATH)
    except Exception:
        try:
            os.remove(temp)
        except OSError:
            pass
        raise


class QuWorkError(RuntimeError):
    pass


class QuWorkClient:
    def __init__(
        self,
        account: dict[str, Any],
        state: dict[str, Any],
        log=print,
        session=None,
        timeout: int = 25,
    ):
        self.account = account
        self.key = str(account["_key"])
        self.state = state
        self.log = log
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.trust_env = True
        self.proxy = str(account.get("proxy") or os.getenv("QUWORK_PROXY", "")).strip()

    @property
    def token(self) -> str:
        return str(self.account.get("accessToken") or "").strip()

    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.token,
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-QurWork-Env": "prod",
            "X-QurWork-Version": CLIENT_VERSION,
        }

    def proxies(self):
        if not self.proxy:
            return None
        return {"http": self.proxy, "https": self.proxy}

    def raw(self, method: str, path: str, body: Any = None) -> tuple[int, dict[str, Any]]:
        try:
            response = self.session.request(
                method,
                BASE + path,
                headers=self.headers(),
                json=body,
                timeout=self.timeout,
                proxies=self.proxies(),
            )
        except requests.RequestException as exc:
            raise QuWorkError("网络请求失败: %s" % exc) from exc
        try:
            payload = response.json()
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        return int(response.status_code), payload

    def safe_message(self, payload: dict[str, Any]) -> str:
        error = payload.get("error")
        message = ""
        if isinstance(error, dict):
            message = str(error.get("message") or "")
        message = message or str(payload.get("message") or payload.get("msg") or "")
        message = message.replace(self.token, "[已隐藏]") if self.token else message
        return message[:300]

    def unauthorized(self, status: int, payload: dict[str, Any]) -> bool:
        message = self.safe_message(payload)
        return status == 401 or (
            not truthy(payload.get("success")) and message in ("未登录", "用户未登录")
        )

    def request(self, method: str, path: str, body: Any = None) -> tuple[int, dict[str, Any]]:
        status, payload = self.raw(method, path, body)
        if self.unauthorized(status, payload):
            self.refresh()
            status, payload = self.raw(method, path, body)
        return status, payload

    def persist_token(self, token: str, expires_at: int | None) -> None:
        self.account["accessToken"] = token
        self.state["accounts"][self.key] = {
            "accessToken": token,
            "expiresAt": expires_at,
            "updatedAt": now_ms(),
        }
        save_state(self.state)

    def refresh(self) -> None:
        if not self.token:
            raise QuWorkError("缺少 accessToken，无法续期")
        status, payload = self.raw("GET", REFRESH_PATH)
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        token = str(data.get("token") or "").strip().removeprefix("Bearer ").strip()
        if status < 200 or status >= 300 or not truthy(payload.get("success")) or not token:
            detail = self.safe_message(payload) or "续期未返回新 accessToken"
            raise QuWorkError("登录续期失败: %s" % detail)
        expiry = timestamp_ms(data.get("expire")) or token_expiry(token)
        if token == self.token and expiry and expiry <= now_ms():
            raise QuWorkError("登录续期未更新有效凭证")
        self.persist_token(token, expiry)
        self.log("   🔁 登录凭证已续期")

    def data(self, status: int, payload: dict[str, Any], operation: str) -> dict[str, Any]:
        if status < 200 or status >= 300 or not truthy(payload.get("success")):
            detail = self.safe_message(payload)
            raise QuWorkError("%s失败: HTTP %s%s" % (
                operation, status, (" " + detail) if detail else ""))
        data = payload.get("data")
        if not isinstance(data, dict):
            raise QuWorkError("%s失败: data 不是对象" % operation)
        return data

    def status(self) -> dict[str, Any]:
        status, payload = self.request("GET", STATUS_PATH)
        data = self.data(status, payload, "每日奖励查询")
        fields = {
            "claimed": data.get("claimed"),
            "can_claim": data.get("can_claim"),
        }
        if not all(isinstance(value, bool) for value in fields.values()):
            raise QuWorkError("每日奖励状态格式异常: claimed/can_claim 不是布尔值")
        points = as_float(data.get("points"))
        if points is None:
            raise QuWorkError("每日奖励状态格式异常: points 无效")
        streak = as_float(data.get("consecutive_days"))
        if streak is None or int(streak) != streak:
            raise QuWorkError("每日奖励状态格式异常: consecutive_days 无效")
        reset_at = timestamp_ms(data.get("next_refresh_at"))
        if reset_at is None:
            raise QuWorkError("每日奖励状态格式异常: next_refresh_at 无效")
        return {
            "claimed": fields["claimed"],
            "can_claim": fields["can_claim"],
            "points": points,
            "streak": int(streak),
            "reset_at": reset_at,
        }

    def _save_claim(self, reset_at: int, state: str) -> None:
        self.state["claims"][self.key] = {
            "resetAt": reset_at,
            "state": state,
            "at": now_ms(),
        }
        save_state(self.state)

    def checkin(self) -> dict[str, Any]:
        before = self.status()
        if before["claimed"]:
            self._save_claim(before["reset_at"], "claimed")
            return {"outcome": "done", "status": before, "message": "今日奖励已领取"}

        saved = self.state["claims"].get(self.key)
        if (
            isinstance(saved, dict)
            and saved.get("resetAt") == before["reset_at"]
            and saved.get("state") == "confirming"
        ):
            return {
                "outcome": "pending",
                "status": before,
                "message": "上次领取结果待确认，本轮只回查，不重复提交",
            }
        if not before["can_claim"] or before["reset_at"] <= now_ms():
            return {"outcome": "inactive", "status": before, "message": "当前没有可领取的每日奖励"}

        self._save_claim(before["reset_at"], "confirming")
        try:
            status, payload = self.request("POST", CLAIM_PATH, None)
        except Exception:
            return {
                "outcome": "pending",
                "status": before,
                "message": "领取请求结果不明，已保留 confirming，下一轮只回查",
            }

        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        granted = truthy(data.get("granted"))
        accepted = (
            200 <= status < 300
            and truthy(payload.get("success"))
            and granted
        )
        try:
            after = self.status()
        except Exception:
            after = None
        if after and after["claimed"] and after["reset_at"] == before["reset_at"]:
            self._save_claim(before["reset_at"], "claimed")
            points = as_float(data.get("points"))
            if points is None:
                points = max(0.0, after["points"] - before["points"])
            return {
                "outcome": "claimed",
                "status": after,
                "credit": points,
                "message": "领取成功，已回读 confirmed",
            }

        rejected = (
            (400 <= status < 500 and status != 408)
            or (200 <= status < 300 and not truthy(payload.get("success")))
        )
        if rejected and not accepted:
            self._save_claim(before["reset_at"], "rejected")
            detail = self.safe_message(payload) or "领取未成功"
            return {"outcome": "failed", "status": before, "message": detail}

        return {
            "outcome": "pending",
            "status": before,
            "message": "领取已提交但未回读到 claimed=true，下一轮只回查",
        }


def merge_cached_token(account: dict[str, Any], state: dict[str, Any]) -> None:
    cached = state["accounts"].get(str(account["_key"]))
    if isinstance(cached, dict) and str(cached.get("accessToken") or "").strip():
        account["accessToken"] = str(cached["accessToken"]).strip()


def run_account(account: dict[str, Any], state: dict[str, Any], query_only: bool = False) -> dict[str, Any]:
    label = mask(account.get("name"))
    client = QuWorkClient(account, state)
    try:
        if query_only:
            status = client.status()
            return {"name": label, "outcome": "query", "status": status, "message": "查询成功"}
        result = client.checkin()
        result["name"] = label
        return result
    except Exception as exc:
        return {"name": label, "outcome": "failed", "message": str(exc)[:300]}


def push_text(title: str, content: str) -> None:
    qywx = os.getenv("QYWX_TOKEN") or os.getenv("WECHAT_WEBHOOK") or ""
    if qywx:
        url = qywx if qywx.startswith("http") else (
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=" + qywx)
        try:
            requests.post(url, json={"msgtype": "text", "text": {"content": content}}, timeout=15)
        except Exception:
            pass
    plusplus = (
        os.getenv("PLUSPLUS_TOKEN")
        or os.getenv("PLUSHPLUS_TOKEN")
        or os.getenv("PUSHPLUS_TOKEN")
        or ""
    )
    if plusplus:
        try:
            requests.post(
                "https://www.pushplus.plus/send",
                json={"token": plusplus, "title": title, "content": content, "template": "txt"},
                timeout=15,
            )
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--help" in argv or "-h" in argv:
        print("用法: python quwork_daily.py [--query]")
        print("环境变量:")
        print("  QUWORK_ACCOUNTS        JSON 数组，每项至少含 accessToken")
        print("  QUWORK_ACCESS_TOKEN    单账号 accessToken")
        print("  QUWORK_PROXY           可选 HTTP/HTTPS 代理")
        print("  QUWORK_STATE_DIR       可选状态目录")
        print("  QYWX_TOKEN / PLUSPLUS_TOKEN  可选推送")
        return 0
    query_only = "--query" in argv or truthy(os.getenv("QUWORK_QUERY_ONLY", "0"))
    try:
        accounts = parse_accounts()
    except ValueError as exc:
        print("❌", exc, file=sys.stderr)
        return 1
    if not accounts:
        print("❌ 未找到账号配置: QUWORK_ACCOUNTS 或 QUWORK_ACCESS_TOKEN", file=sys.stderr)
        return 1

    state = load_state()
    for account in accounts:
        merge_cached_token(account, state)

    print("QuWork Daily v%s · %d 个账号 · %s" % (
        VERSION, len(accounts), "只查询" if query_only else "查询并领取"))
    results = []
    for account in accounts:
        result = run_account(account, state, query_only=query_only)
        results.append(result)
        status = result.get("status") or {}
        suffix = ""
        if status:
            suffix = " · points=%s · streak=%s" % (
                status.get("points"), status.get("streak"))
        print("  [%s] %s · %s%s" % (
            result.get("outcome"), result.get("name"), result.get("message", ""), suffix))

    failed = sum(1 for result in results if result.get("outcome") == "failed")
    pending = sum(1 for result in results if result.get("outcome") == "pending")
    claimed = sum(1 for result in results if result.get("outcome") == "claimed")
    inactive = sum(1 for result in results if result.get("outcome") == "inactive")
    done = sum(1 for result in results if result.get("outcome") == "done")
    summary = (
        "QuWork：claimed=%d, done=%d, inactive=%d, pending=%d, failed=%d"
        % (claimed, done, inactive, pending, failed)
    )
    print(summary)
    push_text("QuWork Daily", "\n".join(
        [summary] + ["%s: %s %s" % (
            result.get("name"), result.get("outcome"), result.get("message", ""))
            for result in results]))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
