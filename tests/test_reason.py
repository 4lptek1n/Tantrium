"""ai.reason — AKIL (dil) + BEYİN (matematik) birleşimi: doğal dil → doğru yetenek.

Dil isteği anlar, beynin (forecast/discover_law/anomaly/reverse/entangle/produce/converse)
doğru yeteneğini çağırır, sertifikalı sonucu dile döker. İkisi birleşince tek zihin.
"""
import tantrium


def test_reason_routes_forecast():
    ai = tantrium.AI()
    r = ai.reason("Bu seriyi tahmin et: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55")
    assert r["intent"] == "forecast"
    assert r["result"]["reliable"] is True
    assert 89.0 in r["result"]["forecast"]   # Fibonacci devamı


def test_reason_routes_discover_law():
    ai = tantrium.AI()
    r = ai.reason("Bu verinin yasası ne: 2 4 8 16 32 64 128")
    assert r["intent"] == "discover_law"
    assert r["result"].order >= 1


def test_reason_routes_knowledge():
    ai = tantrium.AI()
    r = ai.reason("EGFR nedir?")
    assert r["intent"] == "knowledge"
    assert r["result"]["grounded"] is True


def test_reason_routes_entangle():
    ai = tantrium.AI()
    r = ai.reason("prime ve zeta arasında gizli bağ var mı")
    assert r["intent"] == "entangle"
    assert "entangled" in r["result"]


def test_extract_numbers():
    ai = tantrium.AI()
    assert ai._extract_numbers("a 1, 2.5, -3 ve 4e0 son") == [1.0, 2.5, -3.0, 4.0]
