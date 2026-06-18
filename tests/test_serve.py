"""F6 — serve.py REST API smoke testi (in-process, HTTP client'sız).

httpx/TestClient kurulu olmayabilir → endpoint'leri app.routes üzerinden ve
route handler'larını doğrudan çağırarak sabitleriz. serve.py'nin AI facade'a
doğru bağlandığını ve app'in beklenen rotaları kaydettiğini doğrular.
"""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")


def test_app_builds():
    from tantrium.serve import app
    assert app is not None, "FastAPI app kurulmalı"


def test_expected_routes_registered():
    """serve.py beklenen endpoint'leri kaydeder."""
    from tantrium.serve import app
    paths = {getattr(r, "path", None) for r in app.routes}
    for p in ("/health", "/status", "/ask", "/grounding", "/learn"):
        assert p in paths, f"'{p}' endpoint'i kayıtlı olmalı"


def test_get_ai_singleton():
    """_get_ai() AI singleton'ı kurar (lazy)."""
    import tantrium
    from tantrium.serve import _get_ai
    ai = _get_ai()
    assert isinstance(ai, tantrium.AI)
    assert _get_ai() is ai, "singleton — ikinci çağrı aynı örnek"


def _handler(app, path: str, method: str = "POST"):
    """app.routes içinden path+method eşleşen route'un endpoint fonksiyonunu bul."""
    for r in app.routes:
        if getattr(r, "path", None) == path and method in getattr(r, "methods", set()):
            return r.endpoint
    raise AssertionError(f"{method} {path} bulunamadı")


def test_health_handler():
    from tantrium.serve import app
    out = _handler(app, "/health", "GET")()
    assert out["status"] == "ok"


def test_ask_handler_wires_to_facade():
    """/ask handler'ı AI.ask()'e bağlanır, 4-eksen JSON döndürür."""
    from tantrium.serve import app, TokenReq
    handler = _handler(app, "/ask", "POST")
    out = handler(TokenReq(token="EGFR"))
    for key in ("query", "certified", "paradigms_passed", "grounding",
                "truth", "confidence"):
        assert key in out, f"/ask yanıtı '{key}' içermeli"
    assert out["query"] == "EGFR"
