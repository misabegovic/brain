"""Tests for per-agent identity + the signed append-only event stream
(wiki/brain/adrs/per-agent-identity.md).

Core functions run against monkeypatched temp state. The hosted HTTP
auth boundary runs a real server subprocess with BRAIN_HOSTED=1 and
cleans up the runtime state it creates.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import brain  # noqa: E402


def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr(brain, "AGENT_KEYS", tmp_path / "agent-keys.json")
    monkeypatch.setattr(brain, "EVENTS_DIR", tmp_path / "events")
    monkeypatch.setattr(brain, "EVENT_CURSORS", tmp_path / "event-cursors.json")


def test_key_issue_rotate_revoke(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    s1 = brain.agent_key_issue("arch")
    assert len(s1) == 64
    # Re-issue without rotate is refused.
    try:
        brain.agent_key_issue("arch")
        raise AssertionError("re-issue should be refused")
    except ValueError:
        pass
    s2 = brain.agent_key_issue("arch", rotate=True)
    assert s2 != s1
    assert brain._agent_secret("arch") == s2
    assert brain.agent_key_revoke("arch") is True
    assert brain._agent_secret("arch") is None  # revoked → no secret


def test_event_append_rejects_forgery_and_unknown(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    brain.agent_key_issue("arch")
    ev = brain.event_emit("arch", "post", "channel:x")
    assert ev["seq"] == 0 and ev["agent"] == "arch"
    # A forged signature is rejected at write time.
    try:
        brain.event_append("arch", "post", "y", "2026-07-14", "deadbeef")
        raise AssertionError("forged append must be rejected")
    except PermissionError:
        pass
    # An unknown agent cannot append.
    try:
        brain.event_emit("ghost", "post", "z")
        raise AssertionError("unknown agent must be rejected")
    except PermissionError:
        pass


def test_read_time_verification_drops_tampered(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    brain.agent_key_issue("arch")
    brain.event_emit("arch", "post", "channel:x")
    assert len(brain.event_read(0)) == 1
    # Tamper the stored line: read-time verification must drop it.
    f = next(brain.EVENTS_DIR.glob("*.jsonl"))
    ev = json.loads(f.read_text().splitlines()[0])
    ev["ref"] = "tampered"
    f.write_text(json.dumps(ev, sort_keys=True) + "\n")
    assert brain.event_read(0) == []


def test_rotation_invalidates_old_signatures(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    brain.agent_key_issue("arch")
    old = brain.event_emit("arch", "post", "channel:x")
    assert brain._event_verify(old) is True
    brain.agent_key_issue("arch", rotate=True)
    assert brain._event_verify(old) is False  # signed under the old key


def test_cursor_advances_past_delivered(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    brain.agent_key_issue("arch")
    brain.agent_key_issue("reader")
    brain.event_emit("arch", "post", "a")
    brain.event_emit("arch", "post", "b")
    first = brain.events_since("reader")
    assert [e["ref"] for e in first] == ["a", "b"]
    assert brain.events_since("reader") == []  # cursor advanced
    brain.event_emit("arch", "post", "c")
    assert [e["ref"] for e in brain.events_since("reader")] == ["c"]


def _serve_hosted(port):
    return subprocess.Popen(
        [sys.executable, str(REPO / "tools" / "brain.py"), "serve",
         "--port", str(port)],
        env={**os.environ, "BRAIN_HOSTED": "1"},
        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


def test_hosted_http_auth_boundary():
    assert not brain.AGENT_KEYS.exists(), "test assumes no live keyring"
    port = 8802
    secret = brain.agent_key_issue("test-agent")

    def sign(msg):
        return hmac.new(bytes.fromhex(secret), msg.encode(),
                        hashlib.sha256).hexdigest()

    def sign_event(kind, ref, ts):
        canon = json.dumps({"agent": "test-agent", "kind": kind, "ref": ref,
                            "ts": ts}, sort_keys=True, separators=(",", ":"))
        return sign(canon)

    proc = _serve_hosted(port)
    made = []
    try:
        for _ in range(40):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api", timeout=3)
                break
            except OSError:
                if proc.poll() is not None:
                    raise AssertionError("server died")
                time.sleep(0.3)

        def post(headers, body):
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/act",
                data=json.dumps(body).encode(),
                headers={"X-Brain-Act": "1", "Content-Type": "application/json",
                         **headers}, method="POST")
            try:
                return urllib.request.urlopen(req, timeout=5).status, json.loads(
                    urllib.request.urlopen(req, timeout=5).read())
            except urllib.error.HTTPError as e:
                return e.code, None

        ts = "2026-07-14T00:00:00"
        # No agent headers → 401.
        code, _ = post({}, {"action": "post", "thread": "t", "note": "x"})
        assert code == 401

        # Forged signature → 401, no event.
        code, _ = post({"X-Agent-Id": "test-agent", "X-Agent-Ts": ts,
                        "X-Agent-Sig": "bad"},
                       {"action": "post", "thread": "t", "note": "x"})
        assert code == 401

        # Valid signed post → 200, an event, and an inbox item authored by
        # the authenticated agent (not the machine).
        sig = sign_event("post", "channel:t", ts)
        code, resp = post({"X-Agent-Id": "test-agent", "X-Agent-Ts": ts,
                           "X-Agent-Sig": sig},
                          {"action": "post", "thread": "t", "note": "hi"})
        assert code == 200 and "event_seq" in resp
        made.append(resp["queued"])
        item = json.loads((brain.INBOX_DIR / f"{resp['queued']}.json").read_text())
        assert item["author"] == "test-agent" and item["channel_post"] is True

        # Authenticated read returns the verified event.
        rsig = sign(f"read:0:{ts}")
        rreq = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/events?since=0",
            headers={"X-Agent-Id": "test-agent", "X-Agent-Ts": ts,
                     "X-Agent-Sig": rsig})
        evs = json.loads(urllib.request.urlopen(rreq, timeout=5).read())["events"]
        assert any(e["ref"] == "channel:t" and e["agent"] == "test-agent"
                   for e in evs)

        # Read with bad auth → 401.
        breq = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/events?since=0",
            headers={"X-Agent-Id": "test-agent", "X-Agent-Ts": ts,
                     "X-Agent-Sig": "bad"})
        try:
            urllib.request.urlopen(breq, timeout=5)
            raise AssertionError("bad-auth read must 401")
        except urllib.error.HTTPError as e:
            assert e.code == 401
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        brain.AGENT_KEYS.unlink(missing_ok=True)
        brain.EVENT_CURSORS.unlink(missing_ok=True)
        shutil.rmtree(brain.EVENTS_DIR, ignore_errors=True)
        for iid in made:
            (brain.INBOX_DIR / f"{iid}.json").unlink(missing_ok=True)


def test_local_mode_unchanged_no_events(monkeypatch, tmp_path):
    """With the hosted tier off, a post is machine-authored and no event
    stream is created."""
    _isolate(monkeypatch, tmp_path)
    monkeypatch.delenv("BRAIN_HOSTED", raising=False)
    assert brain.hosted_mode() is False
    assert not brain.EVENTS_DIR.exists()
