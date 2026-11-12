import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import quwork_daily as q


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.trust_env = True

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if not self.responses:
            raise AssertionError("unexpected request: %s %s" % (method, url))
        return self.responses.pop(0)


def status_payload(claimed=False, can_claim=True, points=100, streak=3, reset_at=None):
    return {
        "success": True,
        "data": {
            "claimed": claimed,
            "can_claim": can_claim,
            "points": points,
            "consecutive_days": streak,
            "next_refresh_at": reset_at or 4_000_000_000_000,
        },
    }


def claim_payload(granted=True, points=20):
    return {"success": True, "data": {"granted": granted, "points": points}}


def account(token="token-a"):
    return {"_key": "quwork:1", "name": "账号1", "accessToken": token}


class QuWorkDailyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp.name) / ".quwork_state.json"
        self.patch = mock.patch.object(q, "STATE_PATH", self.state_path)
        self.patch.start()
        self.state = {"version": 1, "accounts": {}, "claims": {}}

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_parse_accounts_accepts_full_session(self):
        raw = json.dumps({"session": {"accessToken": "abc", "llmToken": "def"}, "uid": "42"})
        rows = q.parse_accounts(raw)
        self.assertEqual("abc", rows[0]["accessToken"])
        self.assertEqual("quwork:42", rows[0]["_key"])

    def test_claimed_status_is_done_without_post(self):
        session = FakeSession([FakeResponse(200, status_payload(claimed=True))])
        result = q.QuWorkClient(account(), self.state, session=session).checkin()
        self.assertEqual("done", result["outcome"])
        self.assertEqual(["GET"], [row[0] for row in session.calls])

    def test_claim_is_confirmed_by_status_readback(self):
        session = FakeSession([
            FakeResponse(200, status_payload(False, True, points=100)),
            FakeResponse(200, claim_payload(True, 20)),
            FakeResponse(200, status_payload(True, False, points=120)),
        ])
        result = q.QuWorkClient(account(), self.state, session=session).checkin()
        self.assertEqual("claimed", result["outcome"])
        self.assertEqual(20, result["credit"])
        self.assertEqual(["GET", "POST", "GET"], [row[0] for row in session.calls])

    def test_granted_without_readback_stays_pending_and_is_not_resubmitted(self):
        first = FakeSession([
            FakeResponse(200, status_payload(False, True)),
            FakeResponse(200, claim_payload(True, 20)),
            FakeResponse(200, status_payload(False, False)),
        ])
        result = q.QuWorkClient(account(), self.state, session=first).checkin()
        self.assertEqual("pending", result["outcome"])
        self.assertEqual("confirming", self.state["claims"]["quwork:1"]["state"])

        second = FakeSession([FakeResponse(200, status_payload(False, False))])
        again = q.QuWorkClient(account(), self.state, session=second).checkin()
        self.assertEqual("pending", again["outcome"])
        self.assertEqual(["GET"], [row[0] for row in second.calls])

    def test_401_refreshes_once_and_persists_new_token(self):
        session = FakeSession([
            FakeResponse(401, {"success": False, "message": "未登录"}),
            FakeResponse(200, {"success": True, "data": {"token": "token-b", "expire": 4_000_000_000}}),
            FakeResponse(200, status_payload(claimed=True)),
        ])
        row = account("token-a")
        result = q.QuWorkClient(row, self.state, session=session).checkin()
        self.assertEqual("done", result["outcome"])
        self.assertEqual("token-b", row["accessToken"])
        self.assertEqual("token-b", self.state["accounts"]["quwork:1"]["accessToken"])
        self.assertEqual(["GET", "GET", "GET"], [call[0] for call in session.calls])

    def test_explicit_claim_rejection_is_failed(self):
        session = FakeSession([
            FakeResponse(200, status_payload(False, True)),
            FakeResponse(400, {"success": False, "message": "验证码"}),
            FakeResponse(200, status_payload(False, True)),
        ])
        result = q.QuWorkClient(account(), self.state, session=session).checkin()
        self.assertEqual("failed", result["outcome"])
        self.assertIn("验证码", result["message"])
        self.assertEqual("rejected", self.state["claims"]["quwork:1"]["state"])

    def test_invalid_status_fails_instead_of_faking_success(self):
        bad = {"success": True, "data": {"claimed": "true"}}
        session = FakeSession([FakeResponse(200, bad)])
        with self.assertRaises(q.QuWorkError) as raised:
            q.QuWorkClient(account(), self.state, session=session).checkin()
        self.assertIn("格式异常", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
