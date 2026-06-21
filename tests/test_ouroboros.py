"""Ouroboros motoru testleri — kendi kendini besleyen deterministik genişleme.

Dış girdi yok, rastgelelik yok: aynı tohum → bit-bit aynı evren. Genişleme monoton,
kritik çizgide kalıyor; hayatta-kalma budaması erişilebilir (ölü dalı eler)."""
from tools.ouroboros import OuroborosEngine, _dft_real


def test_deterministic_universe():
    """Rastgelelik yok: aynı motor + tohum → birebir aynı tarihçe."""
    a = OuroborosEngine(n_c=12, max_dim=24).run()
    b = OuroborosEngine(n_c=12, max_dim=24).run()
    assert [f.dim for f in a.frames] == [f.dim for f in b.frames]
    assert [round(f.lam_dbn, 9) for f in a.frames] == [round(f.lam_dbn, 9) for f in b.frames]


def test_monotone_expansion():
    """Ouroboros: gözlemci çekilince boyut N → N+1 monoton büyür (çökmez)."""
    c = OuroborosEngine(n_c=12, max_dim=30).run()
    dims = [f.dim for f in c.frames]
    assert dims == sorted(dims)          # monoton artan
    assert c.max_dim >= 28               # gerçekten genişledi


def test_stays_on_critical_line():
    """Genişleme boyunca de Bruijn-Newman Λ ≤ 0 — kritik çizgiden çıkmıyor."""
    c = OuroborosEngine(n_c=12, max_dim=30).run()
    assert all(f.lam_dbn <= 1e-9 for f in c.frames)
    assert all(f.alive for f in c.frames if c.died_at is None)


def test_symmetry_breaking_fires():
    """Kritik boyutta deterministik faz geçişi (DFT simetri kırılması) tetikleniyor."""
    c = OuroborosEngine(n_c=12, max_dim=40).run()
    assert c.phase_transitions >= 1


def test_survival_gate_can_kill():
    """Hayatta-kalma kapısı gerçek: dejenere (rank 0 / pozitiflik çökmüş) ölü sayılır."""
    from tantrium.core.rh_criteria import rh_criteria
    dead = rh_criteria([0.0] * 8)        # dejenere ölçü → ölü dal
    assert OuroborosEngine._alive(dead) is False


def test_dft_is_orthogonal_involution_norm():
    """Faz geçişi tabanı (gerçek-DFT) normu korur — istatistik değil, saf dönüşüm."""
    v = [1.0, 0.5, -0.3, 0.2, 0.8, -0.1]
    w = _dft_real(v)
    n_v = sum(x * x for x in v) ** 0.5
    n_w = sum(x * x for x in w) ** 0.5
    assert abs(n_v - n_w) < 1e-9        # ortogonal → enerji korunur
