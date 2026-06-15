"""Evrensel tahmin + anomali testleri — domain-kör, sertifikalı (L0 dinamik).

Yasa-keşfinin gürültü-dayanıklı gerçek-dünya genişlemesi: herhangi zaman serisini yöneten
yineleme + gelecek tahmini (holdout sertifikalı) + yapısal anomali/sahtelik tespiti.
"""
import numpy as np
import tantrium


def test_forecast_reliable_on_structure():
    """Yapı net olunca tahmin doğru + sertifika güvenilir=True der."""
    np.random.seed(0)
    ai = tantrium.AI()
    g = (1.08 ** np.arange(40) * (1 + 0.01 * np.random.randn(40))).tolist()
    f = ai.forecast(g, steps=5)
    assert f["reliable"] is True
    assert f["holdout_error"] is not None and f["holdout_error"] < 0.05
    assert len(f["forecast"]) == 5
    # üstel büyüme → tahmin artmalı
    assert f["forecast"][-1] > f["forecast"][0]


def test_forecast_certifies_unreliable():
    """Tahmin zor/gürültülü olunca DÜRÜSTÇE güvenilir=False der (kara-kutu değil)."""
    np.random.seed(1)
    ai = tantrium.AI()
    noise = np.random.randn(60).tolist()   # saf gürültü — yasa yok
    f = ai.forecast(noise, steps=8)
    # saf gürültüde holdout hatası büyük → güvenilmez
    assert f["reliable"] is False


def test_detect_anomalies_localizes():
    """Yasaya uymayan noktalar (enjekte anomaliler) yer+şiddetle yakalanmalı."""
    np.random.seed(2)
    ai = tantrium.AI()
    data = (np.sin(0.4 * np.arange(100)) + 0.03 * np.random.randn(100))
    data[37] += 1.5
    data[71] -= 1.2
    r = ai.detect_anomalies(data.tolist(), z=3.0)
    idx = {a["index"] for a in r["anomalies"]}
    assert 37 in idx and 71 in idx, f"enjekte anomaliler bulunmalı: {idx}"


def test_recovers_chaotic_logistic_law():
    """NONLİNEER/KAOTİK yasa: lojistik harita x[n+1]=r·x(1-x) KESİN geri kurulmalı."""
    from tantrium.core.structure import nonlinear_fit
    r = 3.9
    x = [0.4]
    for _ in range(60):
        x.append(r * x[-1] * (1 - x[-1]))
    w, e, d, sigma = nonlinear_fit(x, degree=2, embed=1)
    # w = [sabit, x katsayısı, x² katsayısı] ≈ [0, r, -r]
    assert abs(w[0]) < 1e-6
    assert abs(w[1] - r) < 1e-6
    assert abs(w[2] + r) < 1e-6
    assert sigma < 1e-9, "kaotik yasa makine-hassasiyetinde"


def test_forecast_auto_selects_model():
    """Forecast lineer (Fibonacci) vs nonlineer (lojistik kaos) modeli OTOMATİK seçer."""
    ai = tantrium.AI()
    fib = [float(v) for v in [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]]
    r = 3.9
    chaos = [0.4]
    for _ in range(50):
        chaos.append(r * chaos[-1] * (1 - chaos[-1]))
    f_lin = ai.forecast(fib, steps=4)
    f_nl = ai.forecast(chaos, steps=4)
    assert "lineer" in f_lin["model"]
    assert "nonlineer" in f_nl["model"]


def test_clean_data_no_anomalies():
    """Temiz yapılı veride anomali bulunmamalı (yanlış-pozitif yok)."""
    ai = tantrium.AI()
    clean = np.sin(0.3 * np.arange(80)).tolist()
    r = ai.detect_anomalies(clean, z=5.0)
    assert r["clean"] is True
