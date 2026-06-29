"""KATMAN 2 — ölü zeta/Li eksenleri sertifika kimliğinden çıkarıldı (pozitiflik+dürüstlük).

Durumsuz makinede ζ-dist = inf (manifold yok) ve Li = sabit (hardcoded zeros). Bunlar
ADVISORY: certified verdict yalnız dyadic+sturm'a bağlı; sıralama tiebreaker'ı artık
gerçek transport_cost (ölü ζ değil); summary inf yerine 'N/A' gösterir.
"""
import math

from tantrium.core.transport import TransportCertificate, TransportRanking


def test_zeta_dead_axis_sertifikayi_etkilemez(ai):
    """ζ-dist inf olsa bile certified yalnız dyadic AND sturm'a bağlı."""
    tc = ai.transport("EGFR", "ABL1")
    assert math.isinf(tc.zeta_distance)                       # durumsuz → manifold yok → inf
    assert tc.certified == (tc.dyadic_verified and tc.sturm_verified)


def test_summary_inf_yerine_na():
    """summary() ölü ζ ekseninde 'inf' değil 'N/A' gösterir (dürüst log)."""
    tc = TransportCertificate(
        certified=False, dyadic_verified=True, sturm_verified=False,
        zeta_distance=float("inf"), transport_cost=1.0, path_length=2,
    )
    s = tc.summary()
    assert "N/A" in s and "inf" not in s.lower()


def test_best_zeta_yerine_cost():
    """best() artık gerçek transport_cost ile seçer (ölü inf-ζ ile rastgele değil)."""
    a = TransportCertificate(True, True, True, float("inf"), 0.5, 2)
    b = TransportCertificate(True, True, True, float("inf"), 0.2, 2)
    rank = TransportRanking("t", [("a", a), ("b", b)])
    name, _ = rank.best()
    assert name == "b"                                        # düşük cost kazanır


def test_transport_deterministik(ai):
    """Aynı girdi → aynı sertifika (ζ tiebreaker olmadan kararlı)."""
    t1 = ai.transport("EGFR", "ABL1")
    t2 = ai.transport("EGFR", "ABL1")
    assert (t1.certified, t1.dyadic_verified, t1.sturm_verified) == \
           (t2.certified, t2.dyadic_verified, t2.sturm_verified)
