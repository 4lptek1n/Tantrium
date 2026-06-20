"""HTTP-JSON transport util (#9 dedup) — ortak primitif + delegasyon testleri.

Ağ ÇAĞIRMAZ: urllib.request.urlopen mock'lanır. Amaç: ingest/growth/researcher
fetch yollarının hepsinin tek `net.http_get_json` ilkelinden geçtiğini sabitlemek.
"""

from __future__ import annotations

import json
from unittest import mock

from tantrium.research import net


class _FakeResp:
    def __init__(self, body: bytes, headers: dict | None = None):
        self._body = body
        self.headers = headers or {}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_http_get_json_parses(monkeypatch):
    payload = {"hello": "world", "n": 42}
    resp = _FakeResp(json.dumps(payload).encode("utf-8"))
    with mock.patch("urllib.request.urlopen", return_value=resp):
        out = net.http_get_json("https://example.com/x")
    assert out == payload


def test_http_get_json_uses_user_agent(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["ua"] = req.headers.get("User-agent")
        captured["timeout"] = timeout
        return _FakeResp(b"[]")

    with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
        net.http_get_json("https://x", timeout=7, user_agent="CustomUA/9")
    assert captured["ua"] == "CustomUA/9"
    assert captured["timeout"] == 7


def test_http_get_json_link_extracts_next():
    body = {"results": [1, 2]}
    headers = {"Link": '<https://api/next?cursor=ABC,DEF>; rel="next"'}
    resp = _FakeResp(json.dumps(body).encode("utf-8"), headers)
    with mock.patch("urllib.request.urlopen", return_value=resp):
        data, next_url = net.http_get_json_link("https://api/start")
    assert data == body
    # URL içinde virgül olsa bile regex doğru yakalar
    assert next_url == "https://api/next?cursor=ABC,DEF"


def test_http_get_json_link_no_next():
    resp = _FakeResp(b'{"x":1}', {})
    with mock.patch("urllib.request.urlopen", return_value=resp):
        data, next_url = net.http_get_json_link("https://api")
    assert data == {"x": 1}
    assert next_url is None


def test_errors_replace_tolerates_bad_utf8():
    """errors='replace' bozuk UTF-8'i çökmeden geçer (growth toleranslı yolu)."""
    bad = b'{"k":"' + b"\xff\xfe" + b'"}'
    resp = _FakeResp(bad)
    with mock.patch("urllib.request.urlopen", return_value=resp):
        # replace → çökme yok (yer tutucu karakterle)
        out = net.http_get_json("https://x", errors="replace")
    assert "k" in out
