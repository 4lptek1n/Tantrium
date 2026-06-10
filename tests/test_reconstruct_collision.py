"""Ters rekonstrüksiyon + çakışma avı testleri (Tier 1 — çekirdek iddia)."""
import pytest

from tantrium.core.reconstruct import reconstruct_measure, reconstruction_fidelity
from tantrium.core.collision import CollisionHunter
from tantrium.core.encoder import encode


# ─── Rekonstrüksiyon: moment → ölçü → moment sadakati ────────────────────────

def test_reconstruct_recovers_moments():
    """Geri kurulan ölçünün momentleri orijinalle eşleşmeli (düşük hata)."""
    obj = encode("riemann hypothesis", name="rh")
    rec = reconstruct_measure(obj.moments)
    assert rec.reconstruction_error < 1e-3
    assert rec.well_determined
    assert len(rec.support) == len(rec.weights)


def test_reconstruct_weights_nonnegative():
    """Atomik ölçü ağırlıkları ≥ 0 olmalı (geçerli ölçü)."""
    obj = encode("protein", name="protein")
    rec = reconstruct_measure(obj.moments)
    assert all(w >= 0 for w in rec.weights)


def test_reconstruct_rank_detected():
    """Hankel rankı atom sayısını belirlemeli (≥1)."""
    obj = encode([0.5, 0.3, 0.2, 0.1, 0.05], name="seq")
    rec = reconstruct_measure(obj.moments)
    assert rec.rank >= 1


def test_reconstruction_fidelity_high_for_real_concept():
    """Gerçek kavram için sadakat yüksek olmalı (momentler ölçüyü sabitliyor)."""
    obj = encode("EGFR", name="egfr")
    fid = reconstruction_fidelity(obj.moments)
    assert 0.0 <= fid <= 1.0
    assert fid > 0.5


def test_reconstruct_empty_moments():
    """Boş moment → çökmeden boş ölçü dönmeli."""
    rec = reconstruct_measure([])
    assert rec.rank == 0
    assert rec.support == []


# ─── Çakışma avı: çekirdek iddianın ampirik testi ────────────────────────────

def test_collision_hunt_runs():
    """Çakışma avı çalışmalı ve tutarlı rapor üretmeli."""
    report = CollisionHunter().hunt(n_samples=40, epsilon=1e-4, seed=3)
    assert report.samples_tested > 0
    assert report.pairs_compared > 0
    assert 0.0 <= report.collision_rate <= 1.0


def test_collision_claim_holds_via_labels():
    """Bulunan çakışmalar label-aware kodlamayla ayrışmalı (çekirdek matematik sağlam).

    Hamburger ölçü→moment teklik garantiler; çakışmalar encoder'ın etiket-
    körlüğünden gelir, label-aware mod çözmeli.
    """
    report = CollisionHunter().hunt(n_samples=60, epsilon=1e-4, seed=1)
    # Çakışma varsa, çoğu label-aware ile ayrışmalı
    if report.collisions:
        assert report.resolved_by_labels_count >= len(report.collisions) - 2


def test_identical_inputs_not_collision():
    """Aynı girdiler çakışma sayılmaz (yapısal fark eşiği)."""
    report = CollisionHunter().hunt(n_samples=30, epsilon=1e-4, seed=7,
                                    min_structural_diff=0.99)
    # Çok yüksek yapısal fark eşiği → neredeyse hiç çakışma
    for c in report.collisions:
        assert c.structural_diff >= 0.99
