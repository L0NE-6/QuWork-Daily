#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从本机 QuWork 客户端只读提取登录凭证。默认脱敏，--export 才输出完整 JSON。"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any


def candidate_paths() -> list[Path]:
    paths: list[Path] = []
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA", "")
        if appdata:
            paths.append(Path(appdata) / "qurwork-desktop" / "qurwork-desktop.sqlite")
    elif sys.platform == "darwin":
        paths.append(Path.home() / "Library/Application Support/qurwork-desktop/qurwork-desktop.sqlite")
    else:
        root = Path(os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        paths.append(root / "qurwork-desktop" / "qurwork-desktop.sqlite")
    return paths


def nested_values(value: Any, depth: int = 0):
    if depth > 6 or not isinstance(value, dict):
        return
    yield value
    for key in ("secret", "session", "data", "auth", "user"):
        nested = value.get(key)
        if isinstance(nested, dict):
            yield from nested_values(nested, depth + 1)


def first_text(rows, keys) -> str:
    for row in rows:
        for key in keys:
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def parse_session(raw: str) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("session_json 不是对象")
    rows = list(nested_values(value))
    access = first_text(rows, ("accessToken", "access_token", "token"))
    llm = first_text(rows, ("llmToken", "llm_token", "apiKey"))
    if not access:
        raise ValueError("本机登录态缺少 accessToken")
    user = value.get("user") if isinstance(value.get("user"), dict) else {}
    account = {
        "name": first_text(
            [user, *rows],
            ("display_name", "displayName", "nickname", "username", "phone", "uid"),
        ) or "QuWork",
        "accessToken": access,
    }
    if llm:
        account["llmToken"] = llm
    uid = first_text([user, *rows], ("uid", "id", "userId"))
    if uid:
        account["uid"] = uid
    return account


def read_database(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect("file:%s?mode=ro" % path.as_posix(), uri=True, timeout=3)
    try:
        row = connection.execute(
            "select session_json from auth_session "
            "where id=1 and schema_version=2 and length(session_json)<=262144"
        ).fetchone()
    finally:
        connection.close()
    if not row:
        raise ValueError("QuWork 当前未登录，或数据库 schema 不兼容")
    return parse_session(str(row[0]))


def mask(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * 12 + value[-4:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", help="QuWork qurwork-desktop.sqlite 路径")
    parser.add_argument("--export", action="store_true", help="输出包含 accessToken 的 JSON")
    args = parser.parse_args()

    path = Path(args.db).expanduser() if args.db else next(
        (candidate for candidate in candidate_paths() if candidate.is_file()), None)
    if not path or not path.is_file():
        print("未找到 QuWork 登录数据库，请先登录官方客户端", file=sys.stderr)
        return 1
    try:
        account = read_database(path)
    except Exception as exc:
        print("读取失败:", exc, file=sys.stderr)
        return 1

    if args.export:
        print(json.dumps({"accounts": [account]}, ensure_ascii=False, separators=(",", ":")))
        return 0

    print("账号:", account.get("name", "QuWork"))
    print("UID:", account.get("uid", "未知"))
    print("accessToken:", mask(account["accessToken"]))
    print("llmToken:", "已读取" if account.get("llmToken") else "未找到")
    print("提示: 加 --export 才输出完整 QUWORK_ACCOUNTS JSON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
